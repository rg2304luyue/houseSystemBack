"""Lazy model factories for DeepSeek chat and DashScope embeddings."""

from functools import lru_cache
import time
from typing import Any

import httpx
from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from requests import exceptions as requests_exceptions

from app.core.config import settings
from app.services.ai_reliability import (
    RetryPolicy,
    full_jitter_delay,
    get_provider_guard,
)


def _require_deepseek_key() -> None:
    if not settings.DEEPSEEK_API_KEY:
        raise RuntimeError("DEEPSEEK_API_KEY is required before using AI chat")


def _require_dashscope_key() -> None:
    if not settings.DASHSCOPE_API_KEY:
        raise RuntimeError("DASHSCOPE_API_KEY is required before using RAG embeddings")


def _retryable_deepseek_error(error: Exception) -> bool:
    status_code = getattr(error, "status_code", None)
    return (
        status_code in {408, 429}
        or (isinstance(status_code, int) and status_code >= 500)
        or type(error).__name__ in {"APIConnectionError", "APITimeoutError"}
    )


class ReliableChatOpenAI(ChatOpenAI):
    """ChatOpenAI with one application-owned retry/circuit policy per API call."""

    def _generate(self, *args: Any, **kwargs: Any):
        guard = get_provider_guard(
            "deepseek",
            max_concurrency=settings.AI_PROVIDER_MAX_CONCURRENT,
            failure_threshold=settings.AI_CIRCUIT_FAILURE_THRESHOLD,
            open_seconds=settings.AI_CIRCUIT_OPEN_SECONDS,
        )
        policy = RetryPolicy(
            max_attempts=settings.AI_PROVIDER_MAX_ATTEMPTS,
            base_seconds=settings.AI_RETRY_BASE_DELAY_SECONDS,
            cap_seconds=settings.AI_RETRY_MAX_DELAY_SECONDS,
        )
        for attempt in range(policy.max_attempts):
            permit = guard.try_acquire()
            try:
                result = super()._generate(*args, **kwargs)
            except Exception as error:
                retryable = _retryable_deepseek_error(error)
                permit.failure(retryable=retryable)
                if not retryable or attempt + 1 >= policy.max_attempts:
                    raise
                time.sleep(full_jitter_delay(
                    attempt,
                    base_seconds=policy.base_seconds,
                    cap_seconds=policy.cap_seconds,
                ))
            except BaseException:
                permit.failure(retryable=False)
                raise
            else:
                permit.success()
                return result
        raise AssertionError("unreachable retry loop")

    def _stream(self, *args: Any, **kwargs: Any):
        """Stream with retries only before the first emitted model chunk."""
        guard = get_provider_guard(
            "deepseek",
            max_concurrency=settings.AI_PROVIDER_MAX_CONCURRENT,
            failure_threshold=settings.AI_CIRCUIT_FAILURE_THRESHOLD,
            open_seconds=settings.AI_CIRCUIT_OPEN_SECONDS,
        )
        policy = RetryPolicy(
            max_attempts=settings.AI_PROVIDER_MAX_ATTEMPTS,
            base_seconds=settings.AI_RETRY_BASE_DELAY_SECONDS,
            cap_seconds=settings.AI_RETRY_MAX_DELAY_SECONDS,
        )
        for attempt in range(policy.max_attempts):
            permit = guard.try_acquire()
            emitted = False
            try:
                for chunk in super()._stream(*args, **kwargs):
                    emitted = True
                    yield chunk
            except GeneratorExit:
                permit.cancel()
                raise
            except BaseException as error:
                if not isinstance(error, Exception):
                    permit.cancel()
                    raise
                retryable = _retryable_deepseek_error(error)
                permit.failure(retryable=retryable)
                if emitted or not retryable or attempt + 1 >= policy.max_attempts:
                    raise
                time.sleep(full_jitter_delay(
                    attempt,
                    base_seconds=policy.base_seconds,
                    cap_seconds=policy.cap_seconds,
                ))
            else:
                permit.success()
                return
        raise AssertionError("unreachable streaming retry loop")


@lru_cache(maxsize=1)
def get_chat_model() -> BaseChatModel:
    """Create the DeepSeek OpenAI-compatible chat model on first use."""
    _require_deepseek_key()
    return ReliableChatOpenAI(
        model=settings.AI_CHAT_MODEL,
        api_key=settings.DEEPSEEK_API_KEY,
        base_url=settings.DEEPSEEK_BASE_URL,
        temperature=0,
        timeout=httpx.Timeout(
            settings.AI_DEEPSEEK_READ_TIMEOUT_SECONDS,
            connect=settings.AI_DEEPSEEK_CONNECT_TIMEOUT_SECONDS,
            write=10.0,
            pool=settings.AI_DEEPSEEK_CONNECT_TIMEOUT_SECONDS,
        ),
        # The application-level reliability layer owns the retry budget.
        max_retries=0,
    )


class DashScopeEmbeddingError(RuntimeError):
    """Normalized failure that does not expose the provider response body."""

    def __init__(self, *, status_code: int | None, code: str | None, retryable: bool):
        super().__init__(f"DashScope embedding request failed ({code or status_code or 'network'})")
        self.status_code = status_code
        self.code = code
        self.retryable = retryable


def _retryable_status(status_code: int | None) -> bool:
    return status_code in {408, 429} or (
        isinstance(status_code, int) and status_code >= 500
    )


class ReliableDashScopeEmbeddings(Embeddings):
    """DashScope embeddings with bounded timeout, retry, capacity and circuit."""

    def __init__(
        self,
        *,
        model: str,
        api_key: str,
        request_timeout: float,
        retry_policy: RetryPolicy,
        batch_size: int = 20,
        client: Any | None = None,
    ):
        if request_timeout <= 0 or batch_size < 1:
            raise ValueError("request_timeout and batch_size must be positive")
        if client is None:
            import dashscope

            client = dashscope.TextEmbedding
        self.model = model
        self.api_key = api_key
        self.request_timeout = request_timeout
        self.retry_policy = retry_policy
        self.batch_size = batch_size
        self.client = client

    def _call(self, inputs: str | list[str], *, text_type: str) -> list[list[float]]:
        guard = get_provider_guard(
            "dashscope",
            max_concurrency=settings.AI_PROVIDER_MAX_CONCURRENT,
            failure_threshold=settings.AI_CIRCUIT_FAILURE_THRESHOLD,
            open_seconds=settings.AI_CIRCUIT_OPEN_SECONDS,
        )
        for attempt in range(self.retry_policy.max_attempts):
            permit = guard.try_acquire()
            try:
                response = self.client.call(
                    model=self.model,
                    input=inputs,
                    text_type=text_type,
                    api_key=self.api_key,
                    request_timeout=self.request_timeout,
                )
            except (
                requests_exceptions.Timeout,
                requests_exceptions.ConnectionError,
                requests_exceptions.HTTPError,
            ) as error:
                status_code = getattr(getattr(error, "response", None), "status_code", None)
                retryable = status_code is None or _retryable_status(status_code)
                permit.failure(retryable=retryable)
                normalized = DashScopeEmbeddingError(
                    status_code=status_code, code=type(error).__name__, retryable=retryable
                )
                if not retryable or attempt + 1 >= self.retry_policy.max_attempts:
                    raise normalized from error
            except Exception:
                # Unknown programming/SDK errors are not safe to replay.
                permit.failure(retryable=False)
                raise
            else:
                status_code = getattr(response, "status_code", None)
                if status_code == 200:
                    items = list((getattr(response, "output", None) or {}).get("embeddings", []))
                    if not items:
                        permit.failure(retryable=False)
                        raise DashScopeEmbeddingError(
                            status_code=200, code="INVALID_RESPONSE", retryable=False
                        )
                    permit.success()
                    items.sort(key=lambda item: item.get("text_index", 0))
                    return [item["embedding"] for item in items]
                retryable = _retryable_status(status_code)
                permit.failure(retryable=retryable)
                normalized = DashScopeEmbeddingError(
                    status_code=status_code,
                    code=getattr(response, "code", None),
                    retryable=retryable,
                )
                if not retryable or attempt + 1 >= self.retry_policy.max_attempts:
                    raise normalized

            time.sleep(full_jitter_delay(
                attempt,
                base_seconds=self.retry_policy.base_seconds,
                cap_seconds=self.retry_policy.cap_seconds,
            ))
        raise AssertionError("unreachable retry loop")

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        result: list[list[float]] = []
        for start in range(0, len(texts), self.batch_size):
            result.extend(
                self._call(texts[start : start + self.batch_size], text_type="document")
            )
        return result

    def embed_query(self, text: str) -> list[float]:
        embeddings = self._call(text, text_type="query")
        if len(embeddings) != 1:
            raise DashScopeEmbeddingError(
                status_code=200, code="INVALID_RESPONSE", retryable=False
            )
        return embeddings[0]


@lru_cache(maxsize=1)
def get_embedding_model() -> Embeddings:
    """Create DashScope embeddings; DeepSeek does not provide this RAG API."""
    _require_dashscope_key()
    return ReliableDashScopeEmbeddings(
        model=settings.AI_EMBEDDING_MODEL,
        api_key=settings.DASHSCOPE_API_KEY,
        request_timeout=settings.AI_DASHSCOPE_TIMEOUT_SECONDS,
        retry_policy=RetryPolicy(
            max_attempts=settings.AI_PROVIDER_MAX_ATTEMPTS,
            base_seconds=settings.AI_RETRY_BASE_DELAY_SECONDS,
            cap_seconds=settings.AI_RETRY_MAX_DELAY_SECONDS,
        ),
    )
