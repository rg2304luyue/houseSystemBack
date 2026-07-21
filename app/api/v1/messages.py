"""Authenticated REST messaging over the retained legacy message tables."""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.channel import ChannelModel
from app.models.message import MessageModel
from app.models.user import UserModel
from app.schemas.common import APIResponse

router = APIRouter(prefix="/messages")


class MessageCreate(BaseModel):
    receiver_username: str = Field(min_length=1, max_length=50)
    content: str = Field(min_length=1, max_length=500)


def _username(user: UserModel) -> str:
    if not user.name:
        raise HTTPException(status_code=409, detail="Complete your profile name before messaging")
    return user.name


def _channel_between(db: Session, first: int, second: int) -> ChannelModel | None:
    return db.query(ChannelModel).filter(or_(
        and_(ChannelModel.tenant_id == first, ChannelModel.landlord_id == second),
        and_(ChannelModel.tenant_id == second, ChannelModel.landlord_id == first),
    )).first()


@router.get("", response_model=APIResponse[list])
def list_messages(
    other_username: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """List messages involving the current user, optionally with one correspondent."""
    _username(current_user)
    query = db.query(MessageModel).filter(or_(
        MessageModel.sender_id == current_user.id,
        MessageModel.receiver_id == current_user.id,
    ))
    if other_username:
        matching_users = db.query(UserModel).filter_by(name=other_username).all()
        if len(matching_users) != 1:
            raise HTTPException(status_code=409, detail="Correspondent name is not unique")
        other_user_id = matching_users[0].id
        query = query.filter(or_(
            and_(MessageModel.sender_id == current_user.id, MessageModel.receiver_id == other_user_id),
            and_(MessageModel.sender_id == other_user_id, MessageModel.receiver_id == current_user.id),
        ))
    messages = query.order_by(MessageModel.timestamp.desc()).limit(limit).all()
    messages.reverse()
    return APIResponse(data=[message.to_dict() for message in messages])


@router.get("/received", response_model=APIResponse[list])
def received_messages(
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Return the current user's latest received messages for notifications."""
    _username(current_user)
    messages = db.query(MessageModel).filter(
        MessageModel.receiver_id == current_user.id
    ).order_by(MessageModel.timestamp.desc()).limit(limit).all()
    return APIResponse(data=[message.to_dict() for message in messages])


@router.post("", response_model=APIResponse[dict])
def send_message(
    body: MessageCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Send a message; sender identity always comes from the access token."""
    sender = _username(current_user)
    receiver = body.receiver_username.strip()
    content = body.content.strip()
    if not receiver or not content:
        raise HTTPException(status_code=400, detail="Receiver and content are required")
    if receiver == sender:
        raise HTTPException(status_code=400, detail="You cannot message yourself")
    receiver_users = db.query(UserModel).filter_by(name=receiver).all()
    if not receiver_users:
        raise HTTPException(status_code=404, detail="Receiver not found")
    if len(receiver_users) != 1:
        raise HTTPException(status_code=409, detail="Receiver name is not unique")
    receiver_user = receiver_users[0]

    channel = _channel_between(db, current_user.id, receiver_user.id)
    if channel is None:
        channel = ChannelModel(
            tenant_username=sender,
            landlord_username=receiver,
            tenant_id=current_user.id,
            landlord_id=receiver_user.id,
            timestamp=datetime.utcnow(),
        )
        db.add(channel)
        db.flush()
    message = MessageModel(
        content=content,
        sender_username=sender,
        receiver_username=receiver,
        sender_id=current_user.id,
        receiver_id=receiver_user.id,
        channel_id=channel.channel_id,
        timestamp=datetime.utcnow(),
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return APIResponse(code=201, data=message.to_dict(), message="Message sent")
