from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

import pytest
from requests import exceptions as requests_exceptions


def test_full_jitter_uses_exponential_cap(monkeypatch):
    from app.services import ai_reliability

    seen = []
    monkeypatch.setattr(ai_reliability.random, "uniform", lambda low, high: seen.append((low, high)) or high)
    assert ai_reliability.full_jitter_delay(0, base_seconds=0.5, cap_seconds=8) == 0.5
    assert ai_reliability.full_jitter_delay(6, base_seconds=0.5, cap_seconds=8) == 8
    assert seen == [(0.0, 0.5), (0.0, 8)]


def test_run_limiter_is_non_blocking_and_release_is_idempotent():
    from app.services.ai_reliability import CapacityExceededError, ConcurrentRunLimiter

    limiter = ConcurrentRunLimiter(global_limit=2, per_user_limit=1)
    first = limiter.try_acquire(1)
    with pytest.raises(CapacityExceededError):
        limiter.try_acquire(1)
    second = limiter.try_acquire(2)
    with pytest.raises(CapacityExceededError):
        limiter.try_acquire(3)
    first.release()
    first.release()
    second.release()
    assert limiter.active_total == 0


def test_run_limiter_is_thread_safe():
    from app.services.ai_reliability import CapacityExceededError, ConcurrentRunLimiter

    limiter = ConcurrentRunLimiter(global_limit=8, per_user_limit=1)

    def acquire_once():
        try:
            return limiter.try_acquire(7)
        except CapacityExceededError:
            return None

    with ThreadPoolExecutor(max_workers=8) as pool:
        permits = list(pool.map(lambda _: acquire_once(), range(8)))
    acquired = [permit for permit in permits if permit is not None]
    assert len(acquired) == 1
    acquired[0].release()


def test_circuit_breaker_opens_then_allows_one_half_open_probe():
    from app.services.ai_reliability import CircuitBreaker, CircuitOpenError

    now = [10.0]
    breaker = CircuitBreaker(failure_threshold=2, open_seconds=30, clock=lambda: now[0])
    breaker.before_call()
    breaker.record_failure(retryable=True)
    breaker.before_call()
    breaker.record_failure(retryable=True)
    assert breaker.state == "open"
    with pytest.raises(CircuitOpenError):
        breaker.before_call()
    now[0] = 41.0
    breaker.before_call()
    with pytest.raises(CircuitOpenError):
        breaker.before_call()
    breaker.record_success()
    assert breaker.state == "closed"


class _FakeDashScopeClient:
    calls = []
    responses = []

    @classmethod
    def call(cls, **kwargs):
        cls.calls.append(kwargs)
        response = cls.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def _embedding(client=None, *, attempts=3):
    from app.services.ai_reliability import RetryPolicy
    from core.agent_model.factor import ReliableDashScopeEmbeddings

    return ReliableDashScopeEmbeddings(
        model="qwen3.7-text-embedding",
        api_key="secret",
        request_timeout=12,
        retry_policy=RetryPolicy(max_attempts=attempts, base_seconds=0, cap_seconds=0),
        client=client or _FakeDashScopeClient,
    )


@pytest.fixture(autouse=True)
def _reset_guards():
    from app.services.ai_reliability import clear_provider_guards

    clear_provider_guards()
    _FakeDashScopeClient.calls = []
    _FakeDashScopeClient.responses = []
    yield
    clear_provider_guards()


def test_dashscope_passes_timeout_and_retries_transient_response(monkeypatch):
    import core.agent_model.factor as factor

    monkeypatch.setattr(factor.time, "sleep", lambda _seconds: None)
    _FakeDashScopeClient.responses = [
        SimpleNamespace(status_code=500, code="InternalError", output=None),
        SimpleNamespace(
            status_code=200,
            code=None,
            output={"embeddings": [{"text_index": 0, "embedding": [1.0, 2.0]}]},
        ),
    ]
    assert _embedding().embed_query("长沙租房") == [1.0, 2.0]
    assert len(_FakeDashScopeClient.calls) == 2
    assert _FakeDashScopeClient.calls[0]["request_timeout"] == 12
    assert _FakeDashScopeClient.calls[0]["api_key"] == "secret"
    assert _FakeDashScopeClient.calls[0]["text_type"] == "query"


def test_dashscope_does_not_retry_authentication_failure(monkeypatch):
    import core.agent_model.factor as factor
    from core.agent_model.factor import DashScopeEmbeddingError

    sleeps = []
    monkeypatch.setattr(factor.time, "sleep", sleeps.append)
    _FakeDashScopeClient.responses = [
        SimpleNamespace(status_code=401, code="InvalidApiKey", output=None)
    ]
    with pytest.raises(DashScopeEmbeddingError) as caught:
        _embedding().embed_query("x")
    assert caught.value.retryable is False
    assert len(_FakeDashScopeClient.calls) == 1
    assert sleeps == []


def test_dashscope_retries_network_timeout_at_most_three_times(monkeypatch):
    import core.agent_model.factor as factor
    from core.agent_model.factor import DashScopeEmbeddingError

    sleeps = []
    monkeypatch.setattr(factor.time, "sleep", sleeps.append)
    _FakeDashScopeClient.responses = [requests_exceptions.Timeout("private") for _ in range(3)]
    with pytest.raises(DashScopeEmbeddingError) as caught:
        _embedding().embed_query("x")
    assert caught.value.retryable is True
    assert len(_FakeDashScopeClient.calls) == 3
    assert len(sleeps) == 2


def test_chat_factory_sets_explicit_timeout_and_disables_sdk_retry(monkeypatch):
    from app.core.config import settings
    from core.agent_model.factor import get_chat_model

    get_chat_model.cache_clear()
    monkeypatch.setattr(settings, "DEEPSEEK_API_KEY", "test-key")
    monkeypatch.setattr(settings, "AI_DEEPSEEK_CONNECT_TIMEOUT_SECONDS", 4.0)
    monkeypatch.setattr(settings, "AI_DEEPSEEK_READ_TIMEOUT_SECONDS", 40.0)
    model = get_chat_model()
    assert model.max_retries == 0
    assert model.request_timeout.connect == 4.0
    assert model.request_timeout.read == 40.0
    get_chat_model.cache_clear()


def test_deepseek_retry_classification():
    from core.agent_model.factor import _retryable_deepseek_error

    server_error = type("ServerError", (Exception,), {"status_code": 503})
    auth_error = type("AuthError", (Exception,), {"status_code": 401})
    timeout_error = type("APITimeoutError", (Exception,), {})
    assert _retryable_deepseek_error(server_error()) is True
    assert _retryable_deepseek_error(timeout_error()) is True
    assert _retryable_deepseek_error(auth_error()) is False


def test_deepseek_stream_retries_only_before_first_chunk(monkeypatch):
    from langchain_core.messages import AIMessageChunk
    from langchain_core.outputs import ChatGenerationChunk
    from langchain_openai import ChatOpenAI

    import core.agent_model.factor as factor

    calls = []
    timeout_error = type("APITimeoutError", (Exception,), {})

    def fake_stream(_self, *_args, **_kwargs):
        calls.append(1)
        if len(calls) == 1:
            raise timeout_error("temporary")
        yield ChatGenerationChunk(message=AIMessageChunk(content="ok"))

    monkeypatch.setattr(ChatOpenAI, "_stream", fake_stream)
    monkeypatch.setattr(factor.time, "sleep", lambda _seconds: None)
    model = factor.ReliableChatOpenAI(
        model="deepseek-chat", api_key="test", base_url="https://example.invalid"
    )

    chunks = list(model._stream([]))

    assert len(calls) == 2
    assert chunks[0].text == "ok"


def test_deepseek_stream_never_replays_after_first_chunk(monkeypatch):
    from langchain_core.messages import AIMessageChunk
    from langchain_core.outputs import ChatGenerationChunk
    from langchain_openai import ChatOpenAI

    import core.agent_model.factor as factor

    calls = []
    timeout_error = type("APITimeoutError", (Exception,), {})

    def fake_stream(_self, *_args, **_kwargs):
        calls.append(1)
        yield ChatGenerationChunk(message=AIMessageChunk(content="partial"))
        raise timeout_error("failed after output")

    monkeypatch.setattr(ChatOpenAI, "_stream", fake_stream)
    monkeypatch.setattr(factor.time, "sleep", lambda _seconds: None)
    model = factor.ReliableChatOpenAI(
        model="deepseek-chat", api_key="test", base_url="https://example.invalid"
    )

    iterator = model._stream([])
    assert next(iterator).text == "partial"
    with pytest.raises(timeout_error):
        next(iterator)
    assert len(calls) == 1
