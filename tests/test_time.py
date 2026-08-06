from datetime import datetime, timezone

from app.core.time import utc_now_naive
from app.models.chat import ChatSession
from app.models.message import MessageModel


def test_utc_now_naive_preserves_mysql_datetime_semantics():
    before = datetime.now(timezone.utc).replace(tzinfo=None)
    current = utc_now_naive()
    after = datetime.now(timezone.utc).replace(tzinfo=None)

    assert current.tzinfo is None
    assert before <= current <= after


def test_orm_datetime_defaults_use_the_shared_clock():
    chat_default = ChatSession.__table__.c.created_at.default.arg
    message_default = MessageModel.__table__.c.timestamp.default.arg

    assert callable(chat_default)
    assert callable(message_default)
    assert chat_default.__name__ == utc_now_naive.__name__
    assert message_default.__name__ == utc_now_naive.__name__
