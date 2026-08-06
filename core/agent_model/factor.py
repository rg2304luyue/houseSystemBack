"""Lazy model factories for DeepSeek chat and DashScope embeddings."""

from functools import lru_cache

from langchain_community.embeddings import DashScopeEmbeddings
from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI

from app.core.config import settings


def _require_deepseek_key() -> None:
    if not settings.DEEPSEEK_API_KEY:
        raise RuntimeError("DEEPSEEK_API_KEY is required before using AI chat")


def _require_dashscope_key() -> None:
    if not settings.DASHSCOPE_API_KEY:
        raise RuntimeError("DASHSCOPE_API_KEY is required before using RAG embeddings")


@lru_cache(maxsize=1)
def get_chat_model() -> BaseChatModel:
    """Create the DeepSeek OpenAI-compatible chat model on first use."""
    _require_deepseek_key()
    return ChatOpenAI(
        model=settings.AI_CHAT_MODEL,
        api_key=settings.DEEPSEEK_API_KEY,
        base_url=settings.DEEPSEEK_BASE_URL,
        temperature=0,
    )


@lru_cache(maxsize=1)
def get_embedding_model() -> Embeddings:
    """Create DashScope embeddings; DeepSeek does not provide this RAG API."""
    _require_dashscope_key()
    return DashScopeEmbeddings(
        model=settings.AI_EMBEDDING_MODEL,
        dashscope_api_key=settings.DASHSCOPE_API_KEY,
    )
