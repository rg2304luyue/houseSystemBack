"""House CRUD, search, hot/new lists, landlord endpoint.
Ported from Flask blueprints/houseinfo.py.
"""
from collections import defaultdict
import datetime
import logging
import re
from typing import Literal, Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, func
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from pydantic import BaseModel, Field, field_validator, model_validator

from app.db.session import get_db
from app.models.house import HouseInfo
from app.models.house_detail import HouseDetail
from app.models.rental import Rental
from app.models.contract import Contract
from app.schemas.common import APIResponse, PaginatedData
from app.api.deps import get_current_user, get_current_landlord, get_current_admin
from app.models.user import UserModel
from app.core.time import utc_now_naive
from app.services.house_cache import RedisCache, invalidate_house_caches
from app.services.occupancy import (
    active_contract_condition,
    active_rental_condition,
    market_available_house_condition,
)
from app.services.house_capabilities import (
    capability_fields,
    public_visible_house_condition,
    serialize_houses,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["houses"])


def _has_active_rental(db: Session, house_id: int) -> bool:
    """Treat linked, ended rentals as historical; unknown legacy rentals stay active."""
    return db.query(Rental.id).outerjoin(
        Contract, Rental.contract_id == Contract.id
    ).filter(
        Rental.house_id == house_id,
        active_rental_condition(utc_now_naive()),
    ).first() is not None


def _has_active_contract(db: Session, house_id: int) -> bool:
    now = utc_now_naive()
    return db.query(Contract.id).filter(
        Contract.houseId == house_id,
        active_contract_condition(now),
    ).first() is not None

# ---------------------------------------------------------------------------
# Pydantic request / response schemas
# ---------------------------------------------------------------------------

class HouseCreateRequest(BaseModel):
    title: str
    region: str
    community: str
    area: float
    rooms: str
    price: int
    rent_type: str
    block: Optional[str] = None
    direction: Optional[str] = None
    decoration: Optional[str] = None
    subway: Optional[bool] = False
    available: Optional[bool] = True
    tag_new: Optional[bool] = False
    image_url: Optional[str] = None
    publish_time: Optional[str] = None  # "YYYY-MM-DD"
    house_num: Optional[int] = None


class HouseUpdateRequest(BaseModel):
    title: Optional[str] = None
    region: Optional[str] = None
    block: Optional[str] = None
    community: Optional[str] = None
    area: Optional[float] = None
    direction: Optional[str] = None
    rooms: Optional[str] = None
    price: Optional[int] = None
    rent_type: Optional[str] = None
    decoration: Optional[str] = None
    subway: Optional[bool] = None
    available: Optional[bool] = None
    tag_new: Optional[bool] = None
    image_url: Optional[str] = None
    publish_time: Optional[str] = None
    house_num: Optional[int] = None
    phone_num: Optional[str] = None
    landlord: Optional[str] = None


class IncrementViewRequest(BaseModel):
    houseid: int


class HouseVerificationRequest(BaseModel):
    ownership_status: Literal["verified", "rejected"]


class HouseDetailRequest(BaseModel):
    photos: list[str] = Field(default_factory=list, max_length=50)
    facilities: dict[str, bool] = Field(default_factory=dict)
    map_coordinates: dict[str, float]

    @field_validator("photos")
    @classmethod
    def validate_photos(cls, value: list[str]) -> list[str]:
        if any(not photo.strip() for photo in value):
            raise ValueError("图片地址不能为空")
        return value

    @model_validator(mode="after")
    def validate_coordinates(self):
        if set(self.map_coordinates) != {"lat", "lng"}:
            raise ValueError("地图坐标必须且只能包含 lat 和 lng")
        lat = self.map_coordinates["lat"]
        lng = self.map_coordinates["lng"]
        if not -90 <= lat <= 90 or not -180 <= lng <= 180:
            raise ValueError("地图坐标超出有效范围")
        return self


# ---------------------------------------------------------------------------
# Helper: paginated response
# ---------------------------------------------------------------------------

def _paginated(items: list, total: int, page: int, per_page: int) -> dict:
    pages = max((total + per_page - 1) // per_page, 1)
    return {"items": items, "total": total, "page": page, "per_page": per_page, "pages": pages}


def _require_house_owner(house: HouseInfo, user: UserModel) -> None:
    if user.userType == 0:
        return
    if house.landlord_id != user.id:
        raise HTTPException(status_code=403, detail="无权修改该房源详情")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

# ----- 1. House count -----
@router.get("/houses/count", response_model=APIResponse[int])
def house_count(db: Session = Depends(get_db)):
    """Return total number of houses in the database."""
    total = db.query(HouseInfo).filter(public_visible_house_condition()).count()
    return APIResponse(data=total, message="查询成功")


# ----- 2. Hot houses (top 4 by views) -----
@router.get("/houses/hot", response_model=APIResponse[list])
def hot_houses(
    no_cache: bool = Query(False, alias="no_cache"),
    db: Session = Depends(get_db),
):
    """Return top 4 houses by page views (cached 5 min)."""
    cache_key = "house_hot_lists:v3"
    if not no_cache:
        cached = RedisCache.get_cache(cache_key)
        if cached is not None:
            return APIResponse(data=cached, message="查询成功")

    houses = db.query(HouseInfo).filter(
        market_available_house_condition(utc_now_naive()),
        public_visible_house_condition(),
    ).order_by(HouseInfo.page_views.desc()).limit(4).all()
    data = serialize_houses(db, houses)
    if not no_cache:
        RedisCache.set_cache(cache_key, data)
    return APIResponse(data=data, message="查询成功")


# ----- 3. New houses (latest 4) -----
@router.get("/houses/new", response_model=APIResponse[list])
def new_houses(
    no_cache: bool = Query(False, alias="no_cache"),
    db: Session = Depends(get_db),
):
    """Return latest 4 houses by publish_time (cached 5 min)."""
    cache_key = "house_new_lists:v3"
    if not no_cache:
        cached = RedisCache.get_cache(cache_key)
        if cached is not None:
            return APIResponse(data=cached, message="查询成功")

    houses = db.query(HouseInfo).filter(
        market_available_house_condition(utc_now_naive()),
        public_visible_house_condition(),
    ).order_by(HouseInfo.publish_time.desc()).limit(4).all()
    data = serialize_houses(db, houses)
    if not no_cache:
        RedisCache.set_cache(cache_key, data)
    return APIResponse(data=data, message="查询成功")


# ----- 4. Create house (landlord / admin) -----
@router.post("/houses/", response_model=APIResponse[dict], status_code=201)
def create_house(
    body: HouseCreateRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_landlord),
):
    """Publish a new house listing (landlord or admin only)."""
    data = body.model_dump()

    # Parse date
    if body.publish_time:
        try:
            data["publish_time"] = datetime.date.fromisoformat(body.publish_time)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="日期格式错误，应为 YYYY-MM-DD")
    else:
        data["publish_time"] = datetime.date.today()

    # Boolean -> int
    for field_name in ("subway", "available", "tag_new"):
        data[field_name] = 1 if data[field_name] else 0

    data["landlord"] = current_user.name or current_user.phone
    data["phone_num"] = current_user.phone
    data["landlord_id"] = current_user.id
    data["ownership_status"] = "pending"

    new_house = HouseInfo(**data)
    try:
        db.add(new_house)
        db.commit()
        db.refresh(new_house)
        invalidate_house_caches(new_house.id)
        item = new_house.to_dict()
        item.update(capability_fields(new_house, market_available=bool(new_house.available)))
        return APIResponse(data=item, message="房源信息添加成功", code=201)
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"添加房源失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="数据库错误")
    except Exception as e:
        db.rollback()
        logger.error(f"添加房源时发生未知错误: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="添加房源失败")


# ----- 5. List / search houses -----
@router.get("/houses/", response_model=APIResponse[dict])
def list_houses(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    no_cache: bool = Query(False),
    region: Optional[str] = Query(None),
    block: Optional[str] = Query(None),
    community: Optional[str] = Query(None),
    rooms: Optional[str] = Query(None),
    orientation: Optional[str] = Query(None, alias="orientation"),
    min_price: Optional[int] = Query(None, ge=0),
    max_price: Optional[int] = Query(None, ge=0),
    rent_type: Optional[str] = Query(None),
    subway: Optional[int] = Query(None),
    decoration: Optional[str] = Query(None),
    available: Optional[int] = Query(None),
):
    """List houses with optional filters and pagination (DB-side paging)."""
    if min_price is not None and max_price is not None and min_price > max_price:
        raise HTTPException(status_code=422, detail="最低租金不能高于最高租金")
    # Build cache key for total count
    cache_key = "all_house_infos_count:v3"
    for key in sorted([
        "region", "block", "community", "rooms", "orientation",
        "min_price", "max_price", "rent_type", "subway", "decoration", "available",
    ]):
        val = locals().get(key)
        if val is not None:
            cache_key += f":{key}:{val}"

    query = db.query(HouseInfo).filter(public_visible_house_condition())

    # Region (comma-separated, OR)
    if region:
        regions = [r.strip() for r in region.split(",") if r.strip()]
        if regions:
            query = query.filter(or_(*[HouseInfo.region.ilike(f"%{r}%") for r in regions]))

    if block:
        query = query.filter(HouseInfo.block.ilike(f"%{block}%"))

    if community:
        query = query.filter(HouseInfo.community.ilike(f"%{community}%"))

    # Rooms filter (一居/两居/三居/四居/四居+)
    if rooms:
        raw_filters = [r.strip() for r in rooms.split(",") if r.strip()]
        room_conditions = []
        for rf in raw_filters:
            if rf == "一居":
                room_conditions.append(HouseInfo.rooms.ilike("1室%"))
            elif rf == "两居":
                room_conditions.append(HouseInfo.rooms.ilike("2室%"))
            elif rf == "三居":
                room_conditions.append(HouseInfo.rooms.ilike("3室%"))
            elif rf == "四居":
                room_conditions.append(HouseInfo.rooms.ilike("4室%"))
            elif rf == "四居+":
                plus = [HouseInfo.rooms.ilike(f"{i}室%") for i in range(4, 10)]
                if plus:
                    room_conditions.append(or_(*plus))
        if room_conditions:
            query = query.filter(or_(*room_conditions))

    # Orientation (comma-separated, OR)
    if orientation:
        ori_list = [o.strip() for o in orientation.split(",") if o.strip()]
        if ori_list:
            query = query.filter(or_(*[HouseInfo.direction.ilike(f"%{o}%") for o in ori_list]))

    if min_price is not None:
        query = query.filter(HouseInfo.price >= min_price)
    if max_price is not None:
        query = query.filter(HouseInfo.price <= max_price)
    if rent_type:
        query = query.filter(HouseInfo.rent_type == rent_type)
    if subway is not None and subway in (0, 1):
        query = query.filter(HouseInfo.subway == subway)
    if decoration:
        query = query.filter(HouseInfo.decoration.ilike(f"%{decoration}%"))
    if available == 1:
        query = query.filter(market_available_house_condition(utc_now_naive()))
    elif available == 0:
        query = query.filter(HouseInfo.available == 0)

    # Total count with cache
    total = None
    if not no_cache:
        cached_total = RedisCache.get_cache(cache_key)
        if cached_total is not None:
            total = cached_total

    if total is None:
        total = query.count()
        if not no_cache:
            RedisCache.set_cache(cache_key, total)

    offset = (page - 1) * per_page
    houses = (
        query.order_by(HouseInfo.publish_time.desc(), HouseInfo.id.desc())
        .limit(per_page)
        .offset(offset)
        .all()
    )
    items = serialize_houses(db, houses)

    response_data = _paginated(items, total, page, per_page)
    msg = "暂无房源信息" if (not items and page == 1) else "查询成功"
    return APIResponse(data=response_data, message=msg)


# ----- 6. Single house -----
@router.get("/houses/{house_id:int}", response_model=APIResponse[dict])
def get_house(
    house_id: int,
    no_cache: bool = Query(False),
    db: Session = Depends(get_db),
):
    """Get a single house by ID (cached 5 min)."""
    cache_key = f"house_info:{house_id}"
    if not no_cache:
        cached = RedisCache.get_cache(cache_key)
        if cached is not None:
            return APIResponse(data=cached, message="查询成功")

    house = db.get(HouseInfo, house_id)
    if not house or house.ownership_status == "rejected":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="房源信息未找到")

    data = serialize_houses(db, [house])[0]
    if not no_cache:
        RedisCache.set_cache(cache_key, data)
    return APIResponse(data=data, message="查询成功")


@router.get("/houses/{house_id}/detail", response_model=APIResponse[dict])
def get_house_detail(house_id: int, db: Session = Depends(get_db)):
    """Return public presentation details for a house."""
    house = db.get(HouseInfo, house_id)
    if house is None or house.ownership_status == "rejected":
        raise HTTPException(status_code=404, detail="房源信息未找到")
    detail = db.query(HouseDetail).filter(HouseDetail.house_info_id == house_id).first()
    if detail is None:
        return APIResponse(
            data={
                "detail_id": None,
                "house_info_id": house_id,
                "photos": [],
                "facilities": {},
                "map_coordinates": None,
                "created_at": None,
                "updated_at": None,
            },
            message="暂无扩展详情",
        )
    return APIResponse(data=detail.to_dict(), message="查询成功")


@router.post("/houses/{house_id}/detail", response_model=APIResponse[dict], status_code=201)
def create_house_detail(
    house_id: int,
    body: HouseDetailRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Create details for a house (administrator or owner only)."""
    house = (
        db.query(HouseInfo)
        .filter(HouseInfo.id == house_id)
        .with_for_update()
        .first()
    )
    if house is None:
        raise HTTPException(status_code=404, detail="房源信息未找到")
    _require_house_owner(house, current_user)
    existing = db.query(HouseDetail).filter(HouseDetail.house_info_id == house_id).first()
    if existing is not None:
        raise HTTPException(status_code=409, detail="房源详情已存在")
    detail = HouseDetail(house_info_id=house_id, **body.model_dump())
    if current_user.userType != 0 and house.ownership_status == "verified":
        house.ownership_status = "pending"
    try:
        db.add(detail)
        db.commit()
        db.refresh(detail)
        invalidate_house_caches(house_id)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="创建房源详情失败")
    return APIResponse(code=201, data=detail.to_dict(), message="创建成功")


@router.put("/houses/{house_id}/detail", response_model=APIResponse[dict])
def update_house_detail(
    house_id: int,
    body: HouseDetailRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Replace details for a house (administrator or owner only)."""
    house = (
        db.query(HouseInfo)
        .filter(HouseInfo.id == house_id)
        .with_for_update()
        .first()
    )
    if house is None:
        raise HTTPException(status_code=404, detail="房源信息未找到")
    _require_house_owner(house, current_user)
    detail = db.query(HouseDetail).filter(HouseDetail.house_info_id == house_id).first()
    if detail is None:
        raise HTTPException(status_code=404, detail="房源详情未找到")
    detail_changed = any(getattr(detail, key) != value for key, value in body.model_dump().items())
    if detail_changed and current_user.userType != 0 and house.ownership_status == "verified":
        house.ownership_status = "pending"
    for key, value in body.model_dump().items():
        setattr(detail, key, value)
    try:
        db.commit()
        db.refresh(detail)
        invalidate_house_caches(house_id)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="更新房源详情失败")
    return APIResponse(data=detail.to_dict(), message="更新成功")


# ----- 7. Update house -----
@router.put("/houses/{house_id}", response_model=APIResponse[dict])
def update_house(
    house_id: int,
    body: HouseUpdateRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Update a house listing (admin or owner only)."""
    house = (
        db.query(HouseInfo)
        .filter(HouseInfo.id == house_id)
        .with_for_update()
        .first()
    )
    if not house:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="房源信息未找到")

    # Admin bypass or ownership check
    if current_user.userType != 0 and house.landlord_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No permission to update this house")

    update_data = body.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请求体不能为空")

    if update_data.get("available") is True:
        occupied = (
            _has_active_contract(db, house_id)
            or _has_active_rental(db, house_id)
        )
        if occupied:
            raise HTTPException(status_code=409, detail="房源存在待支付合同或有效租约，不能重新上架")

    # Ownership fields are server-managed. Only an administrator may transfer
    # a listing to another landlord.
    if current_user.userType != 0:
        update_data.pop("landlord", None)
        update_data.pop("phone_num", None)
        if not update_data:
            raise HTTPException(status_code=400, detail="房东信息不能由普通用户修改")
        material_fields = {
            "title", "region", "block", "community", "area", "direction", "rooms",
            "price", "rent_type", "decoration", "subway", "image_url", "house_num",
        }
        if house.ownership_status == "verified" and any(
            key in material_fields and getattr(house, key) != value for key, value in update_data.items()
        ):
            house.ownership_status = "pending"

    try:
        for key, value in update_data.items():
            if hasattr(house, key) and key != "id":
                if key == "publish_time" and isinstance(value, str):
                    try:
                        value = datetime.date.fromisoformat(value)
                    except ValueError:
                        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="日期格式错误，应为 YYYY-MM-DD")
                elif key in ("subway", "available", "tag_new") and isinstance(value, bool):
                    value = 1 if value else 0
                setattr(house, key, value)

        db.commit()
        invalidate_house_caches(house_id)
        return APIResponse(data=serialize_houses(db, [house])[0], message="房源信息更新成功", code=200)
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"更新房源 {house_id} 失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="数据库错误")
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"更新房源 {house_id} 时发生未知错误: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="更新房源失败")


# ----- 8. Delete house -----
@router.delete("/houses/{house_id}", response_model=APIResponse)
def delete_house(
    house_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Delete a house listing (admin or owner only)."""
    house = (
        db.query(HouseInfo)
        .filter(HouseInfo.id == house_id)
        .with_for_update()
        .first()
    )
    if not house:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="房源信息未找到")

    if current_user.userType != 0 and house.landlord_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No permission to delete this house")

    occupied = (
        _has_active_contract(db, house_id)
        or _has_active_rental(db, house_id)
    )
    if occupied:
        raise HTTPException(status_code=409, detail="房源存在待支付合同或有效租约，不能删除")

    try:
        db.delete(house)
        db.commit()
        invalidate_house_caches(house_id)
        return APIResponse(message="房源信息删除成功", code=200)
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"删除房源 {house_id} 失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="删除房源失败")


# ----- 9. Upload image (placeholder) -----
@router.post("/houses/{house_id}/upload-image", response_model=APIResponse)
def upload_house_image(
    house_id: int,
    db: Session = Depends(get_db),
):
    """Upload an image for a house (placeholder - not yet implemented)."""
    house = db.get(HouseInfo, house_id)
    if not house:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="房源信息未找到")
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="文件上传功能暂未完全实现，仅为示例接口")


# ----- 10. Pie chart data (house type distribution) -----
@router.get("/houses/stats/pie", response_model=APIResponse[list])
def house_pie_data(db: Session = Depends(get_db)):
    """Return house type distribution for admin dashboard pie chart."""
    results = (
        db.query(HouseInfo.rooms, func.count())
        .group_by(HouseInfo.rooms)
        .order_by(func.count().desc())
        .all()
    )
    merge: dict[str, int] = defaultdict(int)
    for room_name, count in results:
        m = re.match(r"(\d)室", room_name or "")
        if m:
            num = int(m.group(1))
            if num == 1:
                merge["一居室"] += count
            elif num == 2:
                merge["二居室"] += count
            elif num == 3:
                merge["三居室"] += count
            elif num == 4:
                merge["四居室"] += count
            elif num >= 5:
                merge["五居及以上"] += count
            else:
                merge["其他"] += count
        else:
            merge["其他"] += count

    data = [{"name": k, "value": v} for k, v in merge.items()]
    return APIResponse(data=data, message="查询成功")


# ----- 11. Column chart data (top 20 communities) -----
@router.get("/houses/stats/column", response_model=APIResponse[dict])
def house_column_data(db: Session = Depends(get_db)):
    """Return top-20 communities by house count for admin dashboard column chart."""
    results = (
        db.query(HouseInfo.community, func.count())
        .group_by(HouseInfo.community)
        .order_by(func.count().desc())
        .all()
    )
    community_list = [c for c, _ in results]
    num_list = [n for _, n in results]
    if len(num_list) > 20:
        community_list = community_list[:20]
        num_list = num_list[:20]
    return APIResponse(data={"community_list": community_list, "num_list": num_list}, message="查询成功")


# ----- 12. Most viewed house -----
@router.get("/houses/most-viewed", response_model=APIResponse[dict])
def most_viewed_house(db: Session = Depends(get_db)):
    """Return the single most-viewed house."""
    house = db.query(HouseInfo).filter(
        market_available_house_condition(utc_now_naive()),
        public_visible_house_condition(),
    ).order_by(HouseInfo.page_views.desc()).first()
    if not house:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="获取失败")
    return APIResponse(data=serialize_houses(db, [house])[0], message="获取成功")


# ----- 13. Increment views -----
@router.post("/houses/{house_id}/increment-view", response_model=APIResponse)
def increment_view(
    house_id: int,
    db: Session = Depends(get_db),
):
    """Increment the page_view counter for a specific house."""
    try:
        updated = db.query(HouseInfo).filter(HouseInfo.id == house_id).update(
            {HouseInfo.page_views: func.coalesce(HouseInfo.page_views, 0) + 1},
            synchronize_session=False,
        )
        if updated == 0:
            db.rollback()
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="不存在该房源")
        db.commit()
        return APIResponse(message="增加成功")
    except HTTPException:
        raise
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="增加浏览量失败")


# ----- 14. Landlord's own houses -----
@router.get("/houses/landlord/me", response_model=APIResponse[list])
def landlord_houses(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_landlord),
):
    """Return all houses owned by the authenticated landlord."""
    houses = db.query(HouseInfo).filter(HouseInfo.landlord_id == current_user.id).all()
    house_list = serialize_houses(db, houses)
    now = utc_now_naive()
    for entry in house_list:
        entry["isRant"] = bool(
            db.query(Rental.id)
            .outerjoin(Contract, Rental.contract_id == Contract.id)
            .filter(Rental.house_id == entry["id"], active_rental_condition(now))
            .first()
        )

    return APIResponse(data=house_list, message="获取成功")


@router.put("/houses/{house_id}/verification", response_model=APIResponse[dict])
def verify_house_ownership(
    house_id: int,
    body: HouseVerificationRequest,
    db: Session = Depends(get_db),
    _admin: UserModel = Depends(get_current_admin),
):
    """Allow administrators to verify or reject an explicit landlord relation."""

    house = db.query(HouseInfo).filter(HouseInfo.id == house_id).with_for_update().first()
    if house is None:
        raise HTTPException(status_code=404, detail="房源信息未找到")
    if body.ownership_status == "verified" and house.landlord_id is None:
        raise HTTPException(status_code=409, detail="房源尚未关联平台房东，不能通过归属核验")
    house.ownership_status = body.ownership_status
    try:
        db.commit()
        db.refresh(house)
        invalidate_house_caches(house_id)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="更新房源核验状态失败")
    return APIResponse(data=serialize_houses(db, [house])[0], message="核验状态已更新")
