"""User profile routes — ported from Flask blueprints/user.py.

Paths (under /api/v1 prefix):
    GET    /users/me                    — get current user profile
    PUT    /users/me                    — update current user profile
    PUT    /users/me/password           — change password (authenticated)
    POST   /users/password-reset/send-code  — send password-reset verification code
    PUT    /users/password-reset        — reset password via email + verification code
    POST   /users/me/landlord/send-code — send landlord-upgrade verification code
    PUT    /users/me/landlord           — upgrade to landlord (verify code)
    GET    /users/avatar                — get avatar by user id (query param)
    POST   /users/me/avatar             — upload avatar
    GET    /users/by-name/{name}        — get user by name
    POST   /users/by-phone              — get user by phone
"""

import os
import random
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, status
from app.core.time import utc_now_naive
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.db.session import get_db
from app.models.user import UserModel
from app.models.contract import Contract
from app.models.house import HouseInfo
from app.models.rental import Rental
from app.api.deps import get_current_user, get_current_admin
from app.schemas.common import APIResponse
from app.core.redis import get_redis, is_redis_available
from app.services.email import send_password_reset_email, send_landlord_upgrade_email

router = APIRouter()


@router.get("/users", response_model=APIResponse[list])
def list_users(
    db: Session = Depends(get_db),
    _admin: UserModel = Depends(get_current_admin),
):
    """Return all users for the local administration page."""
    users = db.query(UserModel).order_by(UserModel.id.asc()).all()
    return APIResponse(data=[user.to_dict() for user in users], message="获取用户列表成功")


@router.delete("/users/{user_id}", response_model=APIResponse)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: UserModel = Depends(get_current_admin),
):
    """Delete a user, while preventing an administrator deleting themselves."""
    if user_id == admin.id:
        raise HTTPException(status_code=409, detail="不能删除当前登录管理员")
    user = db.get(UserModel, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    has_related_data = any((
        db.query(HouseInfo.id).filter(HouseInfo.landlord_id == user_id).first(),
        db.query(Rental.id).filter(
            (Rental.tenant_id == user_id) | (Rental.landlord_id == user_id)
        ).first(),
        db.query(Contract.id).filter(
            (Contract.tenantId == user_id) | (Contract.landlordId == user_id)
        ).first(),
    ))
    if has_related_data:
        raise HTTPException(status_code=409, detail="该用户仍有关联房源、合同或租约，暂不能删除")
    try:
        db.delete(user)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="该用户仍有关联数据，暂不能删除")
    return APIResponse(message="用户删除成功")

# ---------------------------------------------------------------------------
# Pydantic request / response schemas
# ---------------------------------------------------------------------------


class UpdateProfileRequest(BaseModel):
    name: str | None = None
    addr: str | None = None
    email: str | None = None
    identityCard: str | None = None
    phone: str | None = None


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1)
    password: str = Field(min_length=6)


class SendPasswordResetCodeRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    email: str
    password: str = Field(min_length=6)
    code: str


class SendLandlordCodeRequest(BaseModel):
    email: str


class UpgradeLandlordRequest(BaseModel):
    code: str


class GetUserByPhoneRequest(BaseModel):
    phone: str


# ---------------------------------------------------------------------------
# GET /users/me
# ---------------------------------------------------------------------------


@router.get("/users/me", response_model=APIResponse)
def get_current_user_profile(
    current_user: UserModel = Depends(get_current_user),
):
    """Return the authenticated user's profile."""
    return APIResponse(code=200, data=current_user.to_dict(), message="获取用户信息成功")


# ---------------------------------------------------------------------------
# PUT /users/me
# ---------------------------------------------------------------------------


@router.put("/users/me", response_model=APIResponse)
def update_current_user_profile(
    body: UpdateProfileRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Update the authenticated user's profile fields."""
    data = body.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请求数据不能为空")

    # --- identityCard immutability logic ---
    if "identityCard" in data:
        new_identity_card = data["identityCard"]
        existing = current_user.identityCard
        if existing is not None:
            if new_identity_card != existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="您已填写过身份证号，不可更改",
                )
        else:
            if not new_identity_card or len(new_identity_card) != 18:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="身份证号不能为空，且长度必须为18位",
                )

    allowed_fields = {"name", "addr", "email", "identityCard", "phone"}

    try:
        for key in allowed_fields:
            if key in data and hasattr(current_user, key):
                setattr(current_user, key, data[key])
        db.commit()
        db.refresh(current_user)
        return APIResponse(
            code=200, data=current_user.to_dict(), message="用户信息更新成功"
        )
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="数据库唯一性约束冲突，更新失败",
        )
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="服务器内部错误",
        )


# ---------------------------------------------------------------------------
# PUT /users/me/password  (authenticated password change)
# ---------------------------------------------------------------------------


@router.put("/users/me/password", response_model=APIResponse)
def change_password(
    body: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Change the authenticated user's password."""
    if not current_user.check_password(body.current_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="当前密码不正确",
        )
    try:
        current_user.set_password(body.password)
        db.commit()
        return APIResponse(code=200, message="密码更新成功")
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="数据库唯一性约束冲突，更新失败",
        )
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="服务器内部错误",
        )


# ---------------------------------------------------------------------------
# POST /users/password-reset/send-code
# ---------------------------------------------------------------------------


@router.post("/users/password-reset/send-code", response_model=APIResponse)
def send_password_reset_code(
    body: SendPasswordResetCodeRequest,
    db: Session = Depends(get_db),
):
    """Send a 6-digit password-reset code to the given email (stored in Redis, 2-min TTL)."""
    user = db.query(UserModel).filter_by(email=body.email).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="不存在该用户"
        )

    if not is_redis_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="验证码服务暂不可用，请稍后重试",
        )

    verification_code = "".join(str(random.randint(0, 9)) for _ in range(6))
    redis_key = f"password_reset_code:{body.email}"
    get_redis().set(redis_key, verification_code, ex=120)

    send_password_reset_email(body.email, verification_code)

    return APIResponse(code=200, message="验证码发送中，请查收邮件")


# ---------------------------------------------------------------------------
# PUT /users/password-reset  (password reset via email + code)
# ---------------------------------------------------------------------------


@router.put("/users/password-reset", response_model=APIResponse)
def reset_password(
    body: ResetPasswordRequest,
    db: Session = Depends(get_db),
):
    """Reset password using email and verification code."""
    if not is_redis_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="验证码服务暂不可用",
        )

    redis_key = f"password_reset_code:{body.email}"
    stored_code = get_redis().get(redis_key)
    if not stored_code or stored_code != body.code:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="验证码错误或已过期",
        )

    user = db.query(UserModel).filter_by(email=body.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在"
        )

    try:
        user.set_password(body.password)
        db.commit()
        get_redis().delete(redis_key)
        return APIResponse(code=200, message="密码更新成功")
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="数据库唯一性约束冲突，更新失败",
        )
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="服务器内部错误",
        )


# ---------------------------------------------------------------------------
# POST /users/me/landlord/send-code
# ---------------------------------------------------------------------------


@router.post("/users/me/landlord/send-code", response_model=APIResponse)
def send_landlord_upgrade_code(
    body: SendLandlordCodeRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Send a verification code for upgrading to landlord (5-min TTL)."""
    user = db.query(UserModel).filter_by(email=body.email).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="不存在该用户"
        )

    if not is_redis_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="验证码服务暂不可用，请稍后重试",
        )

    verification_code = "".join(str(random.randint(0, 9)) for _ in range(6))
    redis_key = f"email_verification_code:{body.email}"
    get_redis().set(redis_key, verification_code, ex=300)

    send_landlord_upgrade_email(body.email, verification_code)

    return APIResponse(code=200, message="验证码发送中，请查收邮件")


# ---------------------------------------------------------------------------
# PUT /users/me/landlord
# ---------------------------------------------------------------------------


@router.put("/users/me/landlord", response_model=APIResponse)
def upgrade_to_landlord(
    body: UpgradeLandlordRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Upgrade the authenticated user to landlord (requires verification code)."""
    if current_user.userType != 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="当前用户类型无法升级",
        )

    if not is_redis_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="验证码服务暂不可用",
        )

    email = current_user.email
    redis_key = f"email_verification_code:{email}"
    stored_code = get_redis().get(redis_key)

    if not stored_code or stored_code != body.code:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="验证码错误或已过期",
        )

    get_redis().delete(redis_key)
    current_user.userType = 2
    db.commit()
    db.refresh(current_user)

    return APIResponse(code=200, data=current_user.to_dict(), message="已成为房东")


# ---------------------------------------------------------------------------
# GET /users/avatar  (by user id query param)
# ---------------------------------------------------------------------------


@router.get("/users/avatar", response_model=APIResponse)
def get_user_avatar(
    id: int = Query(..., description="用户ID"),
    db: Session = Depends(get_db),
):
    """Get a user's avatar URL by user id."""
    user = db.get(UserModel, id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="不存在该用户"
        )

    user_dict = user.to_dict()
    if user_dict.get("avatarUrl") is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="该用户无头像"
        )

    return APIResponse(code=200, data=user_dict, message="获取成功")


# ---------------------------------------------------------------------------
# POST /users/me/avatar
# ---------------------------------------------------------------------------


@router.post("/users/me/avatar", response_model=APIResponse)
def upload_avatar(
    avatar: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Upload an avatar image for the authenticated user."""
    if not avatar.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="缺少头像文件"
        )
    allowed_content_types = {"image/jpeg", "image/png", "image/webp", "image/gif"}
    if avatar.content_type not in allowed_content_types:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="头像仅支持 JPEG、PNG、WebP 或 GIF 图片",
        )

    # --- Save file to images directory ---
    project_root = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..")
    )
    images_folder = os.path.join(project_root, "images")
    os.makedirs(images_folder, exist_ok=True)

    # Build a unique filename
    extension_by_type = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
        "image/gif": ".gif",
    }
    ext = extension_by_type[avatar.content_type]
    filename = f"{current_user.id}_{utc_now_naive().strftime('%Y%m%d%H%M%S')}{ext}"
    filepath = os.path.join(images_folder, filename)

    max_avatar_bytes = 5 * 1024 * 1024
    content = avatar.file.read(max_avatar_bytes + 1)
    if not content:
        raise HTTPException(status_code=400, detail="头像文件为空")
    if len(content) > max_avatar_bytes:
        raise HTTPException(status_code=413, detail="头像文件不能超过 5MB")
    with open(filepath, "wb") as f:
        f.write(content)

    # Construct the avatar URL (kept relative for frontend to resolve)
    avatar_url = f"/images/{filename}"

    old_avatar_url = current_user.avatarUrl
    try:
        current_user.avatarUrl = avatar_url
        db.commit()
        db.refresh(current_user)
    except Exception:
        db.rollback()
        try:
            os.remove(filepath)
        except OSError:
            pass
        raise HTTPException(status_code=500, detail="头像保存失败")

    if old_avatar_url and old_avatar_url.startswith("/images/"):
        old_filename = os.path.basename(old_avatar_url)
        old_path = os.path.join(images_folder, old_filename)
        if old_path != filepath:
            try:
                os.remove(old_path)
            except FileNotFoundError:
                pass
            except OSError:
                # The new avatar is already committed; stale-file cleanup must
                # not turn a successful upload into an API failure.
                pass

    return APIResponse(
        code=200, data={"avatarUrl": avatar_url}, message="头像上传成功"
    )


# ---------------------------------------------------------------------------
# GET /users/by-name/{name}
# ---------------------------------------------------------------------------


@router.get("/users/by-name/{name}", response_model=APIResponse)
def get_user_by_name(
    name: str,
    db: Session = Depends(get_db),
):
    """Look up a user by their name."""
    user = db.query(UserModel).filter_by(name=name).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="无该用户"
        )

    return APIResponse(code=200, data=user.to_dict(), message="获取成功")


# ---------------------------------------------------------------------------
# POST /users/by-phone
# ---------------------------------------------------------------------------


@router.post("/users/by-phone", response_model=APIResponse)
def get_user_by_phone(
    body: GetUserByPhoneRequest,
    db: Session = Depends(get_db),
    _current_user: UserModel = Depends(get_current_user),
):
    """Look up a user by phone number (authenticated)."""
    user = db.query(UserModel).filter_by(phone=body.phone).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="不存在该用户"
        )

    return APIResponse(code=200, data=user.to_dict(), message="返回成功")
