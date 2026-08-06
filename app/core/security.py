"""JWT token creation/verification and password hashing."""
from datetime import datetime, timedelta
import jwt
from passlib.context import CryptContext
from passlib.exc import UnknownHashError
from app.core.config import settings
from app.core.time import utc_now_naive

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return pwd_context.verify(plain, hashed)
    except (TypeError, ValueError, UnknownHashError):
        # Treat legacy/corrupted stored values as failed credentials, not a 500.
        return False


def create_access_token(user_id: int, phone: str | None = None,
                        email: str | None = None, user_type: int | None = None) -> str:
    """Create a JWT access token with 24-hour expiry."""
    payload = {
        "user_id": user_id,
        "phone": phone,
        "email": email,
        "type": user_type,
        "exp": utc_now_naive() + timedelta(hours=24),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


def decode_access_token(token: str) -> dict:
    """Decode and validate a JWT token. Raises on invalid/expired."""
    return jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
