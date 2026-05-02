from models.channel_model import Channel
from models.user_model import UserModel
from exts.db import db
from sqlalchemy import or_, and_, select
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def get_or_create_channel(user1, user2):
    """获取或创建两个用户之间的channel。

    自动判断tenant/landlord角色（userType=1为房东，其余为租客）。
    支持任意参数顺序，同一个用户对只会有一个channel。
    """
    try:
        stmt = select(Channel).where(
            or_(
                and_(Channel.tenant_username == user1, Channel.landlord_username == user2),
                and_(Channel.tenant_username == user2, Channel.landlord_username == user1)
            )
        )
        existing = db.session.execute(stmt).scalars().first()
        if existing:
            return existing

        # 确定角色：查找用户类型，userType=1 为房东
        tenant, landlord = _assign_roles(user1, user2)
        new_channel = Channel(
            tenant_username=tenant,
            landlord_username=landlord,
            timestamp=datetime.now()
        )
        db.session.add(new_channel)
        db.session.commit()
        return new_channel
    except Exception as e:
        db.session.rollback()
        logger.error(f"获取或创建channel失败: {str(e)}")
        raise


def _assign_roles(user1, user2):
    """根据用户类型分配租客/房东角色。userType=1为房东。"""
    u1 = db.session.query(UserModel).filter_by(name=user1).first()
    u2 = db.session.query(UserModel).filter_by(name=user2).first()

    u1_type = u1.userType if u1 else None
    u2_type = u2.userType if u2 else None

    if u1_type == 1:       # user1 是房东
        return user2, user1
    elif u2_type == 1:     # user2 是房东
        return user1, user2
    else:
        return user1, user2  # 无法判断时保持参数顺序


# 保持向后兼容的别名
def get_channel(user1, user2):
    return get_or_create_channel(user1, user2)
