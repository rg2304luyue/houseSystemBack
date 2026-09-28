"""FastAPI-native tools for the rental assistant ReAct agent."""

from functools import lru_cache
import json
import logging
import re

from langchain_core.tools import tool
from pydantic import StrictInt
import requests
from sqlalchemy import or_

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.house import HouseInfo
from app.services.agent_errors import AgentPublicError
from app.services.query_constraints import normalize_region, parse_number
from app.core.time import utc_now_naive
from app.services.occupancy import market_available_house_condition


logger = logging.getLogger(__name__)

_PUBLIC_HOUSE_FIELDS = (
    "id",
    "title",
    "region",
    "block",
    "community",
    "area",
    "direction",
    "rooms",
    "price",
    "rent_type",
    "decoration",
    "subway",
    "tag_new",
    "image_url",
    "publish_time",
    "page_views",
    "house_num",
)
_CITY_ADCODES = {
    "长沙": "430100",
    "芙蓉": "430102",
    "天心": "430103",
    "岳麓": "430104",
    "开福": "430105",
    "雨花": "430111",
}
_BLOCK_REGION_MAP = {
    # Only include reviewed, unambiguous locations.  Unknown blocks are simply
    # not cross-checked here (the map is far from exhaustive); a mapped block
    # whose region disagrees is still flagged as a real data conflict.
    "德政园": "芙蓉",
    "树木岭": "雨花",
    "泉塘": "长沙县",
    "麓谷": "岳麓",
    "麓谷西": "岳麓",
    "东方红": "岳麓",
    "桃花村": "岳麓",
}
_TITLE_RENT_TYPE_PATTERN = re.compile(r"^\s*(整租|合租)\s*[·・]?")
_TITLE_ROOMS_PATTERN = re.compile(r"(?<!\d)(\d+)\s*(?:室|居室)")
_ROOMS_PATTERN = re.compile(r"(?<!\d)(\d+)\s*(?:室|居室)")
_TOOL_ROOMS_PATTERN = re.compile(r"([一二两三四五六七八九十\d]+)\s*(?:室|居室)")


def _normalized_region(value: str) -> str:
    """Backward-compatible alias for the shared canonical normalizer."""

    return normalize_region(value)


def _validate_range(name: str, minimum: float | None, maximum: float | None) -> None:
    if minimum is not None and minimum < 0:
        raise ValueError(f"{name}下限不能为负数")
    if maximum is not None and maximum < 0:
        raise ValueError(f"{name}上限不能为负数")
    if minimum is not None and maximum is not None and minimum > maximum:
        raise ValueError(f"{name}下限不能大于上限")


def _normalized_room_filter(value: str | None) -> tuple[int | None, str | None]:
    if not value:
        return None, None
    match = _TOOL_ROOMS_PATTERN.search(value.strip())
    if match is None:
        raise ValueError("rooms 必须使用几室或几居室格式")
    count = parse_number(match.group(1))
    if count < 1 or count > 20:
        raise ValueError("rooms 超出支持范围")
    return count, f"{count}室"


def _house_verification(house: HouseInfo) -> dict[str, object]:
    """Classify inconsistent listing metadata without hiding the row."""

    issues: list[str] = []
    title = str(getattr(house, "title", "") or "").strip()
    rent_type = str(getattr(house, "rent_type", "") or "").strip()
    rooms = str(getattr(house, "rooms", "") or "").strip()
    region = str(getattr(house, "region", "") or "").strip()
    block = str(getattr(house, "block", "") or "").strip()

    if (
        not title or not region or not block or not rent_type or not rooms
        or getattr(house, "price", None) is None
    ):
        issues.append("missing_core_field")

    title_rent_type = _TITLE_RENT_TYPE_PATTERN.search(title)
    if title_rent_type and rent_type and title_rent_type.group(1) != rent_type:
        issues.append("title_rent_type_conflict")

    title_rooms = _TITLE_ROOMS_PATTERN.search(title)
    stored_rooms = _ROOMS_PATTERN.search(rooms)
    if title_rooms and stored_rooms and title_rooms.group(1) != stored_rooms.group(1):
        issues.append("title_rooms_conflict")

    expected_region = _BLOCK_REGION_MAP.get(block)
    if expected_region and region and expected_region != region:
        issues.append("region_block_conflict")

    return {
        "status": "pending_verification" if issues else "verified",
        "issues": issues,
    }


def _house_payload(house: HouseInfo) -> dict:
    payload = {}
    for field in _PUBLIC_HOUSE_FIELDS:
        value = getattr(house, field, None)
        if hasattr(value, "isoformat"):
            value = value.isoformat()
        payload[field] = value
    payload["subway"] = bool(payload["subway"])
    payload["tag_new"] = bool(payload["tag_new"])
    verification = _house_verification(house)
    payload["verification_status"] = verification["status"]
    payload["verification_issues"] = verification["issues"]
    return payload


def _verification_counts(houses: list[dict]) -> dict[str, int]:
    verified = sum(item.get("verification_status") == "verified" for item in houses)
    return {
        "verified_count": verified,
        "pending_verification_count": len(houses) - verified,
    }


def _json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, default=str)


@tool
def search_houses_by_criteria(
    region: str | None = None,
    min_price: int | None = None,
    max_price: int | None = None,
    min_area: float | None = None,
    max_area: float | None = None,
    rooms: str | None = None,
    rent_type: str | None = None,
    subway: bool | None = None,
    decoration: str | None = None,
    limit: int = 5,
    exclude_ids: list[StrictInt] | None = None,
) -> str:
    """Search currently available houses using the supplied rental criteria."""
    try:
        if exclude_ids is not None and (
            len(exclude_ids) > 100
            or any(type(house_id) is not int or house_id <= 0 for house_id in exclude_ids)
        ):
            raise ValueError("exclude_ids 最多包含100个正整数房源编号")
        excluded_ids = list(dict.fromkeys(exclude_ids or []))
        _validate_range("价格", min_price, max_price)
        _validate_range("面积", min_area, max_area)
        safe_limit = max(1, min(limit, 5))
        region_name = _normalized_region(region) if region else None
        room_count, room_query = _normalized_room_filter(rooms)
        rent_type_name = rent_type.strip() if rent_type else None
        if rent_type_name not in {None, "整租", "合租"}:
            raise ValueError("rent_type 只能是整租或合租")
        decoration_name = decoration.strip() if decoration else None
        applied_filters = {
            "region": region_name,
            "min_price": min_price,
            "max_price": max_price,
            "min_area": min_area,
            "max_area": max_area,
            "rooms": room_query,
            "rent_type": rent_type_name,
            "subway": bool(subway) if subway is not None else None,
            "decoration": decoration_name,
        }
        with SessionLocal() as db:
            query = db.query(HouseInfo).filter(
                market_available_house_condition(utc_now_naive())
            )
            if excluded_ids:
                query = query.filter(~HouseInfo.id.in_(excluded_ids))
            if region_name:
                query = query.filter(HouseInfo.region == region_name)
            if min_price is not None:
                query = query.filter(HouseInfo.price >= min_price)
            if max_price is not None:
                query = query.filter(HouseInfo.price <= max_price)
            if min_area is not None:
                query = query.filter(HouseInfo.area >= min_area)
            if max_area is not None:
                query = query.filter(HouseInfo.area <= max_area)
            if room_query:
                query = query.filter(or_(
                    HouseInfo.rooms.contains(f"{room_count}室"),
                    HouseInfo.rooms.contains(f"{room_count}居室"),
                ))
            if rent_type_name:
                query = query.filter(HouseInfo.rent_type == rent_type_name)
            if subway is not None:
                query = query.filter(HouseInfo.subway == int(subway))
            if decoration_name:
                query = query.filter(HouseInfo.decoration.contains(decoration_name))
            total_count = query.count()
            houses = query.order_by(HouseInfo.price.asc(), HouseInfo.id.desc()).limit(
                min(safe_limit * 4, 20)
            ).all()
            house_payloads = [_house_payload(house) for house in houses]
            # Surface verified listings first: truncation must not hide a
            # recommendable house behind unverified ones.
            house_payloads.sort(
                key=lambda item: item.get("verification_status") != "verified"
            )
            house_payloads = house_payloads[:safe_limit]
            return _json({
                "tool_kind": "criteria_search",
                "excluded_ids": excluded_ids,
                "applied_filters": applied_filters,
                "total_count": total_count,
                "returned_count": len(house_payloads),
                "has_more": total_count > len(house_payloads),
                "houses": house_payloads,
                **_verification_counts(house_payloads),
            })
    except ValueError as error:
        return _json({"error": str(error)})
    except Exception:
        logger.exception("House criteria tool failed")
        return _json({"error": "房源查询暂时不可用，请稍后重试。"})


@tool
def get_house_details(house_id: int) -> str:
    """Get public details for one currently available house by its numeric ID."""
    try:
        with SessionLocal() as db:
            house = db.query(HouseInfo).filter(
                HouseInfo.id == house_id,
                market_available_house_condition(utc_now_naive()),
            ).first()
            if house is None:
                return _json({"error": "未找到该房源或房源当前不可用。"})
            payload = _house_payload(house)
            return _json({
                "tool_kind": "house_detail",
                "applied_filters": {"house_id": house_id},
                "house": payload,
                **_verification_counts([payload]),
            })
    except Exception:
        logger.exception("House detail tool failed")
        return _json({"error": "房源详情暂时不可用，请稍后重试。"})


@tool
def get_popular_houses(limit: int = 5) -> str:
    """Return the most-viewed currently available houses, up to five entries."""
    try:
        safe_limit = max(1, min(limit, 5))
        with SessionLocal() as db:
            query = db.query(HouseInfo).filter(
                market_available_house_condition(utc_now_naive())
            )
            total_count = query.count()
            houses = query.order_by(
                HouseInfo.page_views.desc(), HouseInfo.id.desc()
            ).limit(min(safe_limit * 4, 20)).all()
            house_payloads = [_house_payload(house) for house in houses]
            house_payloads.sort(
                key=lambda item: item.get("verification_status") != "verified"
            )
            house_payloads = house_payloads[:safe_limit]
            return _json({
                "tool_kind": "popular_houses",
                "applied_filters": {},
                "total_count": total_count,
                "returned_count": len(house_payloads),
                "has_more": total_count > len(house_payloads),
                "houses": house_payloads,
                **_verification_counts(house_payloads),
            })
    except Exception:
        logger.exception("Popular houses tool failed")
        return _json({"error": "热门房源暂时不可用，请稍后重试。"})


@lru_cache(maxsize=1)
def _rag_service():
    from core.rag.retrieval_service import RagRetrievalService

    return RagRetrievalService()


def normalize_rag_query(query: str) -> str:
    """Return the exact bounded query recorded in RAG tool payloads."""

    return query.strip()[:1000]


def _rental_knowledge_payload(
    query: str, *, knowledge_types: tuple[str, ...] | None = None
) -> str:
    cleaned_query = normalize_rag_query(query)
    if not cleaned_query:
        return _json({"query": "", "grounded": False, "chunks": []})
    try:
        return _json(
            _rag_service().retrieve(
                cleaned_query, knowledge_types=knowledge_types
            ).to_dict()
        )
    except AgentPublicError:
        raise
    except Exception as error:
        error_name = type(error).__name__
        status_code = getattr(error, "status_code", None)
        # Never log the exception text: provider HTTP exceptions may contain
        # request URLs or credentials.  Type/status are sufficient for triage.
        logger.warning(
            "rental_knowledge_retrieval_failed error_type=%s status=%s",
            error_name,
            status_code,
        )
        is_config_error = isinstance(error, (FileNotFoundError, KeyError)) or (
            isinstance(error, RuntimeError)
            and "required before using RAG embeddings" in str(error)
        )
        if is_config_error:
            raise AgentPublicError(
                "知识库尚未正确配置，请联系管理员。",
                code="RAG_CONFIG_ERROR",
                provider="rag",
                retryable=False,
            ) from None
        retryable = bool(getattr(error, "retryable", False)) or (
            status_code in {408, 429}
            or isinstance(status_code, int) and status_code >= 500
            or error_name in {
                "Timeout",
                "ConnectTimeout",
                "ReadTimeout",
                "ConnectionError",
                "CircuitOpenError",
                "CapacityExceededError",
            }
        )
        provider = "dashscope" if (
            "DashScope" in error_name or getattr(error, "provider", None) == "dashscope"
        ) else "rag"
        raise AgentPublicError(
            "知识库暂时不可用，请稍后重试。",
            code="RAG_UNAVAILABLE",
            provider=provider,
            retryable=retryable,
            retry_after=2 if retryable else None,
        ) from None


@tool
def search_rental_guidance(query: str) -> str:
    """Search non-live rental guides and policies; cite evidence as [1], [2]."""
    return _rental_knowledge_payload(query, knowledge_types=("guide", "policy"))


@tool
def search_historical_snapshots(query: str) -> str:
    """Search explicitly historical public listing snapshots, never current availability."""
    return _rental_knowledge_payload(query, knowledge_types=("historical_snapshot",))


@tool
def get_weather_for_visit(city: str = "长沙") -> str:
    """Get current weather and a three-day forecast to help plan a house visit."""
    if not settings.GAODE_WEATHER_KEY:
        return _json({"error": "天气服务尚未配置。"})
    city_name = city.replace("区", "").strip()[:30] or "长沙"
    city_code = _CITY_ADCODES.get(city_name, city_name)
    url = "https://restapi.amap.com/v3/weather/weatherInfo"
    base_params = {"key": settings.GAODE_WEATHER_KEY, "city": city_code, "output": "JSON"}
    try:
        live_response = requests.get(
            url, params={**base_params, "extensions": "base"}, timeout=(3.05, 8)
        )
        live_response.raise_for_status()
        forecast_response = requests.get(
            url, params={**base_params, "extensions": "all"}, timeout=(3.05, 8)
        )
        forecast_response.raise_for_status()
        live_data = live_response.json()
        forecast_data = forecast_response.json()
        if live_data.get("status") != "1" or not live_data.get("lives"):
            return _json({"error": "未能获取该地区的天气。"})
        live = live_data["lives"][0]
        casts = []
        if forecast_data.get("status") == "1" and forecast_data.get("forecasts"):
            for cast in forecast_data["forecasts"][0].get("casts", [])[:3]:
                casts.append({
                    "date": cast.get("date"),
                    "day_weather": cast.get("dayweather"),
                    "night_weather": cast.get("nightweather"),
                    "day_temperature": cast.get("daytemp"),
                    "night_temperature": cast.get("nighttemp"),
                })
        return _json({
            "city": live.get("city", city_name),
            "reported_at": live.get("reporttime"),
            "current": {
                "weather": live.get("weather"),
                "temperature_celsius": live.get("temperature"),
                "humidity_percent": live.get("humidity"),
                "wind_direction": live.get("winddirection"),
                "wind_power": live.get("windpower"),
            },
            "forecast": casts,
        })
    except (requests.RequestException, ValueError, TypeError) as error:
        status_code = getattr(getattr(error, "response", None), "status_code", None)
        # HTTPError.__str__ includes the prepared URL, which contains the API
        # key in this provider's query string.  Log bounded metadata only.
        logger.warning(
            "weather_tool_failed error_type=%s status=%s",
            type(error).__name__,
            status_code,
        )
        return _json({"error": "天气查询暂时不可用，请稍后重试。"})
