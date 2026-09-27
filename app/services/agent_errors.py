"""Public, sanitized error contracts shared by AI tools and HTTP endpoints."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any


_ERROR_CODE_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]{0,49}$")
_PROVIDER_PATTERN = re.compile(r"^[a-z][a-z0-9_-]{0,31}$")
_CONTROL_CHARACTER_PATTERN = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_SECRET_VALUE_PATTERNS = (
    re.compile(r"(?i)(?:sk-|bearer\s+)[A-Za-z0-9._-]{8,}"),
    re.compile(
        r"(?i)(?:api[_-]?key|access[_-]?token|authorization|token|key)"
        r"\s*[=:]\s*[^\s,;]+"
    ),
    re.compile(r"(?i)[?&](?:api[_-]?key|access[_-]?token|token|key)=[^&#\s]+"),
)


@dataclass(frozen=True)
class _ErrorDefinition:
    message: str
    provider: str | None = None


_ERROR_DEFINITIONS: dict[str, _ErrorDefinition] = {
    "AGENT_FAILED": _ErrorDefinition("AI 服务暂时不可用，请稍后重试。"),
    "AGENT_BUSY": _ErrorDefinition("AI 请求繁忙，请稍后重试。"),
    "AUTH_FAILED": _ErrorDefinition("AI 服务鉴权失败，请联系管理员检查配置。", "deepseek"),
    "INSUFFICIENT_BALANCE": _ErrorDefinition("AI 服务账户余额不足，请联系管理员。", "deepseek"),
    "RATE_LIMITED": _ErrorDefinition("AI 请求过于频繁，请稍后重试。", "deepseek"),
    "PROVIDER_UNAVAILABLE": _ErrorDefinition("暂时无法连接 AI 服务，请稍后重试。", "deepseek"),
    "PROVIDER_BUSY": _ErrorDefinition("AI 服务当前繁忙，请稍后重试。", "deepseek"),
    "PROVIDER_FAILED": _ErrorDefinition("AI 服务调用失败，请稍后重试。", "deepseek"),
    "RAG_UNAVAILABLE": _ErrorDefinition("知识库暂时不可用，请稍后重试。", "rag"),
    "RAG_CONFIG_ERROR": _ErrorDefinition("知识库尚未正确配置，请联系管理员。", "rag"),
    "CLIENT_DISCONNECTED": _ErrorDefinition("连接已中断，可尝试恢复本次回答。"),
    "PROCESS_INTERRUPTED": _ErrorDefinition("AI 任务曾意外中断，可尝试恢复。"),
    "RETRY_EXHAUSTED": _ErrorDefinition("本次 AI 任务已达到最大重试次数。"),
    "CANCELLED": _ErrorDefinition("本次生成已停止。"),
    "REQUEST_ID_MISMATCH": _ErrorDefinition("request_id 与原请求不匹配。"),
    "RUN_IN_PROGRESS": _ErrorDefinition("本次 AI 任务仍在运行，请等待结果。"),
    "RUN_RETRY_WAIT": _ErrorDefinition("本次 AI 任务正在等待重试。"),
    "RUN_NOT_RESUMABLE": _ErrorDefinition("本次 AI 任务当前无法恢复。"),
    "RUN_RESULT_MISSING": _ErrorDefinition("任务已完成，但结果暂时无法读取。"),
    "DUPLICATE_REQUEST": _ErrorDefinition("该请求已提交，请勿重复发送。"),
}


def normalize_error_code(value: object) -> str:
    """Return a bounded public code, never arbitrary database/provider text."""
    code = str(value or "AGENT_FAILED").strip().upper()
    return code if _ERROR_CODE_PATTERN.fullmatch(code) else "AGENT_FAILED"


def _normalize_provider(value: object) -> str | None:
    if value is None:
        return None
    provider = str(value).strip().lower()
    return provider if _PROVIDER_PATTERN.fullmatch(provider) else None


def _normalize_retry_after(value: object) -> int | None:
    if value is None:
        return None
    try:
        return max(0, min(3600, int(value)))
    except (TypeError, ValueError, OverflowError):
        return None


def _safe_public_message(value: object, *, fallback: str) -> str:
    message = _CONTROL_CHARACTER_PATTERN.sub("", str(value or "")).strip()[:500]
    if not message:
        return fallback
    if any(pattern.search(message) for pattern in _SECRET_VALUE_PATTERNS):
        return fallback
    return message


class AgentPublicError(RuntimeError):
    """A deliberately sanitized error that may cross the HTTP/SSE boundary."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "AGENT_FAILED",
        provider: str | None = None,
        retryable: bool = False,
        retry_after: int | None = None,
    ) -> None:
        normalized_code = normalize_error_code(code)
        definition = _ERROR_DEFINITIONS.get(
            normalized_code, _ERROR_DEFINITIONS["AGENT_FAILED"]
        )
        safe_message = _safe_public_message(message, fallback=definition.message)
        super().__init__(safe_message)
        self.code = normalized_code
        self.provider = _normalize_provider(provider) or definition.provider
        self.retryable = bool(retryable)
        self.retry_after = (
            _normalize_retry_after(retry_after) if self.retryable else None
        )


def error_details_for_code(
    code: str | None,
    *,
    retryable: bool = False,
    retry_after: int | None = None,
) -> dict[str, Any]:
    """Rebuild a stable safe error object from a persisted error code."""
    normalized_code = normalize_error_code(code)
    definition = _ERROR_DEFINITIONS.get(
        normalized_code, _ERROR_DEFINITIONS["AGENT_FAILED"]
    )
    actual_retryable = bool(retryable)
    return {
        "code": normalized_code,
        "message": definition.message,
        "provider": definition.provider,
        "retryable": actual_retryable,
        "retry_after": (
            _normalize_retry_after(retry_after) if actual_retryable else None
        ),
    }


def public_error_details(
    error: AgentPublicError,
    *,
    retryable: bool | None = None,
    retry_after: int | None = None,
) -> dict[str, Any]:
    """Serialize an AgentPublicError using the run's actual retry decision."""
    actual_retryable = error.retryable if retryable is None else bool(retryable)
    definition = _ERROR_DEFINITIONS.get(
        error.code, _ERROR_DEFINITIONS["AGENT_FAILED"]
    )
    actual_retry_after = error.retry_after if retry_after is None else retry_after
    return {
        "code": normalize_error_code(error.code),
        "message": _safe_public_message(str(error), fallback=definition.message),
        "provider": _normalize_provider(error.provider) or definition.provider,
        "retryable": actual_retryable,
        "retry_after": (
            _normalize_retry_after(actual_retry_after) if actual_retryable else None
        ),
    }


__all__ = (
    "AgentPublicError",
    "error_details_for_code",
    "normalize_error_code",
    "public_error_details",
)
