from functools import lru_cache

from langchain_community.chat_models import ChatTongyi
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel

from app.core.config import settings


def _require_dashscope_key() -> None:
    if not settings.DASHSCOPE_API_KEY:
        raise RuntimeError("DASHSCOPE_API_KEY is required before using AI chat")


@lru_cache(maxsize=1)
def get_chat_model() -> BaseChatModel:
    """Create the chat model only when an AI request actually needs it."""
    _require_dashscope_key()
    return ChatTongyi(
        model=settings.AI_CHAT_MODEL,
        api_key=settings.DASHSCOPE_API_KEY,
    )


@lru_cache(maxsize=1)
def get_embedding_model() -> Embeddings:
    """Create the optional RAG embedding model lazily."""
    _require_dashscope_key()
    return DashScopeEmbeddings(
        model=settings.AI_EMBEDDING_MODEL,
        dashscope_api_key=settings.DASHSCOPE_API_KEY,
    )
