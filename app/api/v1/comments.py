"""Comment routes: list comments for a house and create comments.
Ports from Flask blueprints/comment.py.
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.db.session import get_db
from app.models.comment import CommentModel
from app.models.house import HouseInfo
from app.api.deps import get_current_user
from app.models.user import UserModel
from app.schemas.common import APIResponse

router = APIRouter()


# ---------- schemas ----------

class CommentOut(BaseModel):
    comment_id: int
    house_id: int
    username: str
    type: int
    desc: str
    time: str | None = None
    at: int | None = None


class CommentCreateRequest(BaseModel):
    house_id: int
    desc: str = Field(min_length=1)
    at: int | None = None


# ---------- helpers ----------

def _serialize(comment: CommentModel) -> CommentOut:
    return CommentOut(
        comment_id=comment.comment_id,
        house_id=comment.house_id,
        username=comment.username,
        type=comment.type,
        desc=comment.desc,
        time=comment.time.strftime("%Y-%m-%d %H:%M:%S") if comment.time else None,
        at=comment.at,
    )


# ---------- routes ----------

@router.get("/houses/{house_id}/comments", response_model=APIResponse[list[CommentOut]])
def get_comments(house_id: int, db: Session = Depends(get_db)):
    """List all comments for a given house."""
    if not db.get(HouseInfo, house_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="House not found")
    comments = db.query(CommentModel).filter_by(house_id=house_id).all()
    return APIResponse(data=[_serialize(c) for c in comments], message="Success")


@router.get("/comments/{comment_id}", response_model=APIResponse[CommentOut])
def get_comment_detail(comment_id: int, db: Session = Depends(get_db)):
    """Get a single comment by its id."""
    comment = db.get(CommentModel, comment_id)
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
    return APIResponse(data=_serialize(comment), message="Success")


@router.post(
    "/houses/{house_id}/comments",
    response_model=APIResponse[CommentOut],
    status_code=status.HTTP_201_CREATED,
)
def create_comment(
    house_id: int,
    body: CommentCreateRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Create a new comment on a house. Authentication required."""
    if body.house_id != house_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Path and body house IDs differ")
    if not db.get(HouseInfo, house_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="House not found")

    reply_to = body.at
    if reply_to is not None:
        target = db.get(CommentModel, int(reply_to))
        if target is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reply target not found")
        if target.house_id != house_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Reply target belongs to another house")

    username = current_user.name or current_user.phone
    comment = CommentModel(
        house_id=house_id,
        username=username,
        type=current_user.userType,
        desc=body.desc.strip(),
        time=datetime.now(),
        at=int(reply_to) if reply_to is not None else None,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)

    return APIResponse(code=201, data=_serialize(comment), message="Comment created")
