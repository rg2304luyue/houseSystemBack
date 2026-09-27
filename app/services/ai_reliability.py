"""Thread-safe, process-local reliability helpers for synchronous AI calls."""

from __future__ import annotations

from dataclasses import dataclass
import random
import threading
import time
from typing import Callable


class CapacityExceededError(RuntimeError):
    """Raised immediately when a local concurrency limit has been reached."""


class CircuitOpenError(RuntimeError):
    """Raised when a provider circuit is open and calls must fail fast."""


def full_jitter_delay(
    attempt: int, *, base_seconds: float = 0.5, cap_seconds: float = 8.0
) -> float:
    """Return a full-jitter exponential delay for a zero-based retry number."""
    if attempt < 0:
        raise ValueError("attempt must be non-negative")
    if base_seconds < 0 or cap_seconds < 0:
        raise ValueError("retry delays must be non-negative")
    return random.uniform(0.0, min(cap_seconds, base_seconds * (2**attempt)))


class _RunPermit:
    def __init__(self, limiter: "ConcurrentRunLimiter", user_id: int):
        self._limiter = limiter
        self._user_id = user_id
        self._released = False
        self._lock = threading.Lock()

    def release(self) -> None:
        """Release once; safe in both error and generator-finally paths."""
        with self._lock:
            if self._released:
                return
            self._released = True
        self._limiter._release(self._user_id)

    def __enter__(self) -> "_RunPermit":
        return self

    def __exit__(self, *_args: object) -> None:
        self.release()


class ConcurrentRunLimiter:
    """Non-blocking global and per-user admission control for worker threads."""

    def __init__(self, *, global_limit: int, per_user_limit: int):
        if global_limit < 1 or per_user_limit < 1:
            raise ValueError("concurrency limits must be positive")
        self.global_limit = global_limit
        self.per_user_limit = per_user_limit
        self._active_total = 0
        self._active_by_user: dict[int, int] = {}
        self._lock = threading.Lock()

    def try_acquire(self, user_id: int) -> _RunPermit:
        with self._lock:
            user_active = self._active_by_user.get(user_id, 0)
            if self._active_total >= self.global_limit:
                raise CapacityExceededError("AI service is at global capacity")
            if user_active >= self.per_user_limit:
                raise CapacityExceededError("user already has an active AI request")
            self._active_total += 1
            self._active_by_user[user_id] = user_active + 1
        return _RunPermit(self, user_id)

    def _release(self, user_id: int) -> None:
        with self._lock:
            active = self._active_by_user.get(user_id, 0)
            if active <= 0:
                return
            if active == 1:
                self._active_by_user.pop(user_id, None)
            else:
                self._active_by_user[user_id] = active - 1
            self._active_total -= 1

    @property
    def active_total(self) -> int:
        with self._lock:
            return self._active_total


class CircuitBreaker:
    """Closed/open/half-open circuit breaker safe across worker threads."""

    def __init__(
        self,
        *,
        failure_threshold: int = 5,
        open_seconds: float = 30.0,
        clock: Callable[[], float] = time.monotonic,
    ):
        if failure_threshold < 1 or open_seconds < 0:
            raise ValueError("invalid circuit breaker configuration")
        self.failure_threshold = failure_threshold
        self.open_seconds = open_seconds
        self._clock = clock
        self._state = "closed"
        self._failure_count = 0
        self._open_until = 0.0
        self._probe_active = False
        self._lock = threading.Lock()

    def before_call(self) -> None:
        with self._lock:
            if self._state == "open":
                if self._clock() < self._open_until:
                    raise CircuitOpenError("provider circuit is open")
                self._state = "half_open"
            if self._state == "half_open":
                if self._probe_active:
                    raise CircuitOpenError("provider circuit probe is already running")
                self._probe_active = True

    def record_success(self) -> None:
        with self._lock:
            self._state = "closed"
            self._failure_count = 0
            self._open_until = 0.0
            self._probe_active = False

    def record_failure(self, *, retryable: bool) -> None:
        with self._lock:
            if not retryable:
                # A valid 4xx response proves the provider is reachable.
                if self._state == "half_open":
                    self._state = "closed"
                    self._failure_count = 0
                self._probe_active = False
                return
            self._failure_count += 1
            if self._state == "half_open" or self._failure_count >= self.failure_threshold:
                self._state = "open"
                self._open_until = self._clock() + self.open_seconds
            self._probe_active = False

    def record_cancel(self) -> None:
        """Release a half-open probe without treating consumer cancellation as health."""
        with self._lock:
            self._probe_active = False

    @property
    def state(self) -> str:
        with self._lock:
            if self._state == "open" and self._clock() >= self._open_until:
                return "half_open"
            return self._state


class _ProviderPermit:
    def __init__(self, guard: "ProviderGuard"):
        self._guard = guard
        self._finished = False
        self._lock = threading.Lock()

    def success(self) -> None:
        self._finish(retryable=None)

    def failure(self, *, retryable: bool) -> None:
        self._finish(retryable=retryable)

    def cancel(self) -> None:
        with self._lock:
            if self._finished:
                return
            self._finished = True
        try:
            self._guard.breaker.record_cancel()
        finally:
            self._guard._semaphore.release()

    def _finish(self, retryable: bool | None) -> None:
        with self._lock:
            if self._finished:
                return
            self._finished = True
        try:
            if retryable is None:
                self._guard.breaker.record_success()
            else:
                self._guard.breaker.record_failure(retryable=retryable)
        finally:
            self._guard._semaphore.release()


class ProviderGuard:
    """Non-blocking provider capacity guard coupled to a circuit breaker."""

    def __init__(
        self,
        provider: str,
        *,
        max_concurrency: int,
        failure_threshold: int = 5,
        open_seconds: float = 30.0,
    ):
        if max_concurrency < 1:
            raise ValueError("provider max_concurrency must be positive")
        self.provider = provider
        self.breaker = CircuitBreaker(
            failure_threshold=failure_threshold, open_seconds=open_seconds
        )
        self._semaphore = threading.BoundedSemaphore(max_concurrency)

    def try_acquire(self) -> _ProviderPermit:
        if not self._semaphore.acquire(blocking=False):
            raise CapacityExceededError(f"{self.provider} provider is at capacity")
        try:
            self.breaker.before_call()
        except Exception:
            self._semaphore.release()
            raise
        return _ProviderPermit(self)


_PROVIDER_GUARDS: dict[str, ProviderGuard] = {}
_PROVIDER_GUARDS_LOCK = threading.Lock()


def get_provider_guard(
    provider: str,
    *,
    max_concurrency: int,
    failure_threshold: int = 5,
    open_seconds: float = 30.0,
) -> ProviderGuard:
    """Return the process-wide guard for one provider."""
    with _PROVIDER_GUARDS_LOCK:
        guard = _PROVIDER_GUARDS.get(provider)
        if guard is None:
            guard = ProviderGuard(
                provider,
                max_concurrency=max_concurrency,
                failure_threshold=failure_threshold,
                open_seconds=open_seconds,
            )
            _PROVIDER_GUARDS[provider] = guard
        return guard


def clear_provider_guards() -> None:
    """Clear cached guards; intended for configuration reloads and tests."""
    with _PROVIDER_GUARDS_LOCK:
        _PROVIDER_GUARDS.clear()


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 3
    base_seconds: float = 0.5
    cap_seconds: float = 8.0

    def __post_init__(self) -> None:
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be positive")
        if self.base_seconds < 0 or self.cap_seconds < 0:
            raise ValueError("retry delays must be non-negative")


class _ConfiguredRunLimiter:
    """Lazy facade so settings are resolved once without import cycles."""

    def __init__(self) -> None:
        from app.core.config import settings

        self._limiter = ConcurrentRunLimiter(
            global_limit=settings.AI_AGENT_MAX_CONCURRENT,
            per_user_limit=settings.AI_AGENT_MAX_CONCURRENT_PER_USER,
        )

    def acquire(self, user_id: int) -> _RunPermit | None:
        try:
            return self._limiter.try_acquire(user_id)
        except CapacityExceededError:
            return None


agent_limiter = _ConfiguredRunLimiter()
