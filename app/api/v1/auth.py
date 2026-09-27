"""Auth routes: register, login, email-login.
Ports from Flask blueprints/user.py login/register routes.
"""
import secrets
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel, Field

from app.db.session import get_db
from app.models.user import UserModel
from app.core.security import create_access_token
from app.core.redis import get_redis, is_redis_available
from app.core.config import settings
from app.core.time import utc_now_naive
from app.schemas.common import APIResponse
from app.services.email import send_login_verification_email
from app.core.validation import normalize_email

router = APIRouter()

_CONSUME_CODE_SCRIPT = """
local value = redis.call('GET', KEYS[1])
if not value then return -2 end
if value == ARGV[1] then
    redis.call('DEL', KEYS[1], KEYS[2])
    return 1
end
local attempts = redis.call('INCR', KEYS[2])
if attempts == 1 then
    local ttl = redis.call('TTL', KEYS[1])
    if ttl > 0 then redis.call('EXPIRE', KEYS[2], ttl) else redis.call('EXPIRE', KEYS[2], 300) end
end
if attempts >= tonumber(ARGV[2]) then
    redis.call('DEL', KEYS[1], KEYS[2])
    return -1
end
return 0
"""

_MAX_CODE_ATTEMPTS = 5


class RegisterRequest(BaseModel):
    phone: str = Field(min_length=11, max_length=11)
    password: str = Field(min_length=6)
    email: str


class LoginRequest(BaseModel):
    phone: str = Field(min_length=11, max_length=11)
    password: str


class EmailLoginRequest(BaseModel):
    email: str
    password: str


class EmailCodeRequest(BaseModel):
    email: str


class EmailCodeLoginRequest(BaseModel):
    email: str
    code: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")


class TokenResponse(BaseModel):
    token: str


@router.post("/auth/register", response_model=APIResponse)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user."""
    email = normalize_email(body.email)
    if db.query(UserModel).filter_by(phone=body.phone).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该手机号已被注册")
    if db.query(UserModel).filter_by(email=email).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该邮箱已被注册")

    user = UserModel(phone=body.phone, email=email)
    user.set_password(body.password)
    user.userType = 1
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="该手机号或邮箱已被注册")

    return APIResponse(code=201, message="注册成功！")


@router.post("/auth/login", response_model=APIResponse[TokenResponse])
def login(body: LoginRequest, db: Session = Depends(get_db)):
    """Phone + password login."""
    user = db.query(UserModel).filter_by(phone=body.phone).first()
    if not user or not user.check_password(body.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="手机号或密码错误")

    token = create_access_token(user.id, phone=user.phone, user_type=user.userType)
    return APIResponse(code=201, data=TokenResponse(token=token), message="登录成功")


@router.post("/auth/email-code", response_model=APIResponse)
def send_email_code(
    body: EmailCodeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Issue a rate-limited, five-minute code for passwordless email login."""
    email = normalize_email(body.email)
    if db.query(UserModel).filter_by(email=email).first() is None:
        raise HTTPException(status_code=404, detail="Email is not registered")
    if not settings.QQ_SMTP_EMAIL or not settings.QQ_SMTP_AUTH_CODE:
        raise HTTPException(status_code=503, detail="Email delivery is not configured")
    if not is_redis_available():
        raise HTTPException(status_code=503, detail="Verification-code service is unavailable")

    redis_client = get_redis()
    last_send_key = f"email_login_last_send:{email}"
    if not redis_client.set(last_send_key, "1", ex=60, nx=True):
        raise HTTPException(status_code=429, detail="Please wait before requesting another code")

    daily_key = f"email_login_daily_count:{email}:{utc_now_naive():%Y%m%d}"
    pipeline = redis_client.pipeline(transaction=True)
    pipeline.incr(daily_key)
    pipeline.expire(daily_key, 86400, nx=True)
    daily_count = pipeline.execute()[0]
    if daily_count > 10:
        redis_client.delete(last_send_key)
        raise HTTPException(status_code=429, detail="Daily verification-code limit reached")

    code = f"{secrets.randbelow(1_000_000):06d}"
    redis_client.set(f"email_login_code:{email}", code, ex=300)
    background_tasks.add_task(send_login_verification_email, email, code)
    return APIResponse(message="Verification code is being sent")


@router.post("/auth/email-code/login", response_model=APIResponse[TokenResponse])
def email_code_login(body: EmailCodeLoginRequest, db: Session = Depends(get_db)):
    """Consume an email verification code and issue a normal access token."""
    email = normalize_email(body.email)
    if not is_redis_available():
        raise HTTPException(status_code=503, detail="Verification-code service is unavailable")

    redis_client = get_redis()
    code_key = f"email_login_code:{email}"
    attempts_key = f"email_login_code_attempts:{email}"
    consumed = redis_client.eval(
        _CONSUME_CODE_SCRIPT, 2, code_key, attempts_key, body.code, _MAX_CODE_ATTEMPTS
    )
    if consumed == -2 or consumed == 0:
        raise HTTPException(status_code=401, detail="Verification code is invalid or expired")
    if consumed == -1:
        raise HTTPException(status_code=401, detail="Too many attempts; request a new code")

    user = db.query(UserModel).filter_by(email=email).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    token = create_access_token(
        user.id, phone=user.phone, email=user.email, user_type=user.userType
    )
    return APIResponse(data=TokenResponse(token=token), message="Email login successful")


@router.post("/auth/email-login", response_model=APIResponse[TokenResponse])
def email_login(body: EmailLoginRequest, db: Session = Depends(get_db)):
    """Email + password login."""
    email = normalize_email(body.email)
    user = db.query(UserModel).filter_by(email=email).first()
    if not user or not user.check_password(body.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="邮箱或密码错误")

    token = create_access_token(user.id, phone=user.phone, email=user.email, user_type=user.userType)
    return APIResponse(code=201, data=TokenResponse(token=token), message="邮箱登录成功")
