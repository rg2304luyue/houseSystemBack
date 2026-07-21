"""FastAPI auth dependencies (replaces Flask @token_required, @role_required)."""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import jwt

from app.core.config import settings
from app.db.session import get_db
from app.models.user import UserModel

security_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: Session = Depends(get_db),
) -> UserModel:
    """Validate JWT token and return the authenticated user."""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = db.get(UserModel, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


def get_current_admin(user: UserModel = Depends(get_current_user)) -> UserModel:
    """Require admin role (userType == 0)."""
    if user.userType != 0:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user


def get_current_landlord(user: UserModel = Depends(get_current_user)) -> UserModel:
    """Require landlord or admin role (userType in (0, 2))."""
    if user.userType not in (0, 2):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Landlord access required")
    return user
