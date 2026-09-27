"""FastAPI chat endpoints used by the local AI assistant page."""
from datetime import timedelta
import hashlib
import hmac
import json
import math
from pathlib import Path
import re
import time
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from starlette.background import BackgroundTask
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.time import utc_now_naive
from app.db.session import SessionLocal, get_db
from app.models.chat import AIAgentRun, ChatMessage, ChatSession
from app.models.rag_feedback import RAGFailureCase
from app.models.user import UserModel
from app.schemas.common import APIResponse
from app.services.agent_errors import (
    AgentPublicError,
    error_details_for_code,
    normalize_error_code,
    public_error_details,
)

router = APIRouter(tags=["chat-ai"])

_PRIVATE_PROTOCOL_PATTERN = re.compile(
    r"(?:Action|Observation|Final Answer|Thought)\s*[:：]|"
    r"(?:思考|思维链)\s*[:：]|</?think>|search_houses_by_criteria|"
    r"(?:get_house_details|get_popular_houses|search_rental_knowledge|"
    r"search_rental_guidance|search_historical_snapshots|"
    r"get_weather_for_visit)|正在(?:为您)?搜索",
    re.IGNORECASE,
)


def _contains_private_protocol(content: str) -> bool:
    return bool(_PRIVATE_PROTOCOL_PATTERN.search(content))


def _public_history_content(content: str) -> str:
    if _contains_private_protocol(content):
        return "抱歉，这条旧回复包含无效的内部处理信息，请重新提问。"
    return content


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    session_id: int | None = None
    request_id: UUID | None = None


class RunFeedbackRequest(BaseModel):
    failure_type: str = Field(min_length=1, max_length=40)
    feedback: str = Field(min_length=1, max_length=2000)


class RunFeedbackReviewRequest(BaseModel):
    review_status: str
    expected_route: str | None = Field(default=None, max_length=30)
    expected_sources: list[str] = Field(default_factory=list, max_length=10)
    notes: str | None = Field(default=None, max_length=2000)


_FEEDBACK_TYPES = {
    "routing_error", "retrieval_miss", "ranking_error", "stale_document",
    "incorrect_refusal", "source_conflict", "citation_error",
    "generation_not_grounded", "provider_failure", "other",
}
_SENSITIVE_TEXT_PATTERNS = (
    (re.compile(r"(?<!\d)1\d{10}(?!\d)"), "[PHONE]"),
    (re.compile(r"(?<!\d)\d{17}[0-9Xx](?!\d)"), "[IDENTITY]"),
    (re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"), "[EMAIL]"),
    (re.compile(r"(?i)(?:sk-|bearer\s+)[A-Za-z0-9._-]{12,}"), "[SECRET]"),
    (re.compile(r"(?<!\d)\d{16,19}(?!\d)"), "[BANK_CARD]"),
    (re.compile(r"(?i)(?:微信|wechat|qq)\s*[:：号]?\s*[A-Za-z0-9_-]{5,30}"), "[SOCIAL_ACCOUNT]"),
    (re.compile(r"(?:护照|证件号)\s*[:：]?\s*[A-Za-z0-9]{6,20}"), "[DOCUMENT_ID]"),
    (re.compile(r"(?:姓名|联系人)\s*[:：]?\s*[\u4e00-\u9fff]{2,4}"), "[NAME]"),
    (re.compile(r"(?:地址|住址)\s*[:：]?\s*[^，。\n]{4,80}"), "[ADDRESS]"),
)
_HISTORY_MESSAGE_LIMIT = 30
_HISTORY_CHARACTER_BUDGET = 24_000


def _sanitize_failure_text(value: str) -> str:
    cleaned = value.strip()[:4000]
    for pattern, replacement in _SENSITIVE_TEXT_PATTERNS:
        cleaned = pattern.sub(replacement, cleaned)
    return cleaned


def _active_index_signature() -> str | None:
    """Read the active signature without initializing Chroma or an API client."""
    try:
        from core.agent_utils.config_handler import chroma_config
        from core.agent_utils.path_tool import get_abs_path

        path = Path(get_abs_path(chroma_config.get("manifest_path", "rag_state/index_manifest.json")))
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("state") == "ready" and isinstance(payload.get("index_signature"), str):
            return payload["index_signature"]
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return None
    return None


def _session_for_user(db: Session, session_id: int, user_id: int) -> ChatSession:
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == user_id,
    ).first()
    if session is None:
        raise HTTPException(status_code=404, detail="会话不存在或无权访问")
    return session


def _history(
    db: Session, session_id: int, *, through_message_id: int | None = None
) -> list[dict[str, str]]:
    query = db.query(ChatMessage).filter(ChatMessage.session_id == session_id)
    if through_message_id is not None:
        query = query.filter(ChatMessage.id <= through_message_id)
    records = list(reversed(query.order_by(ChatMessage.id.desc()).limit(_HISTORY_MESSAGE_LIMIT).all()))
    history = [
        {
            "role": item.role,
            "content": (
                _public_history_content(item.content)
                if item.role == "assistant"
                else item.content
            ),
        }
        for item in records
    ]
    selected: list[dict[str, str]] = []
    used = 0
    for item in reversed(history):
        remaining = _HISTORY_CHARACTER_BUDGET - used
        if remaining <= 0:
            break
        content = item["content"][-remaining:]
        selected.append({"role": item["role"], "content": content})
        used += len(content)
    return list(reversed(selected))


def _reply(history: list[dict[str, str]]) -> str:
    from app.services.react_agent import invoke_react_agent

    reply = invoke_react_agent(history).strip()
    if not reply or _contains_private_protocol(reply):
        raise RuntimeError("模型未能生成可安全展示的最终答复，请重试")
    return reply


def _run_cancelled(request_id: str) -> bool:
    with SessionLocal() as db:
        run = db.get(AIAgentRun, request_id)
        return run is None or run.cancel_requested


def _set_run_state(
    request_id: str, status: str, *, assistant_message_id: int | None = None,
    error_code: str | None = None, lease_token: str | None = None,
    next_retry_at=None,
) -> bool:
    with SessionLocal() as db:
        query = db.query(AIAgentRun).filter(AIAgentRun.request_id == request_id)
        if lease_token is not None:
            query = query.filter(AIAgentRun.lease_token == lease_token)
        run = query.with_for_update().first()
        if run is None:
            return False
        if run.status in {"completed", "cancelled"} and run.status != status:
            return False
        run.status = status
        run.assistant_message_id = assistant_message_id
        run.error_code = error_code
        run.next_retry_at = next_retry_at
        if status in {"completed", "failed", "cancelled"}:
            run.finished_at = utc_now_naive()
        if status != "running":
            run.lease_token = None
            run.lease_expires_at = None
        run.updated_at = utc_now_naive()
        db.commit()
        return True


def recover_stale_agent_runs(db: Session, *, now=None) -> int:
    """Turn abandoned leases into resumable work after restart or disconnect."""
    now = now or utc_now_naive()
    stale_filter = (
        AIAgentRun.status == "running",
        (AIAgentRun.lease_expires_at.is_(None)) | (AIAgentRun.lease_expires_at < now),
    )
    cancelled = db.query(AIAgentRun).filter(
        *stale_filter, AIAgentRun.cancel_requested.is_(True)
    ).update({
        AIAgentRun.status: "cancelled",
        AIAgentRun.error_code: "CANCELLED",
        AIAgentRun.heartbeat_at: now,
        AIAgentRun.lease_token: None,
        AIAgentRun.lease_expires_at: None,
        AIAgentRun.next_retry_at: None,
        AIAgentRun.finished_at: now,
        AIAgentRun.updated_at: now,
    }, synchronize_session=False)
    retrying = db.query(AIAgentRun).filter(
        *stale_filter,
        AIAgentRun.cancel_requested.is_(False),
        AIAgentRun.attempt_count < settings.AI_RUN_MAX_ATTEMPTS,
    ).update({
        AIAgentRun.status: "retry_wait",
        AIAgentRun.error_code: "PROCESS_INTERRUPTED",
        AIAgentRun.heartbeat_at: now,
        AIAgentRun.lease_token: None,
        AIAgentRun.lease_expires_at: None,
        AIAgentRun.next_retry_at: now,
        AIAgentRun.updated_at: now,
    }, synchronize_session=False)
    exhausted = db.query(AIAgentRun).filter(
        *stale_filter,
        AIAgentRun.cancel_requested.is_(False),
        AIAgentRun.attempt_count >= settings.AI_RUN_MAX_ATTEMPTS,
    ).update({
        AIAgentRun.status: "failed",
        AIAgentRun.error_code: "RETRY_EXHAUSTED",
        AIAgentRun.heartbeat_at: now,
        AIAgentRun.lease_token: None,
        AIAgentRun.lease_expires_at: None,
        AIAgentRun.next_retry_at: None,
        AIAgentRun.finished_at: now,
        AIAgentRun.updated_at: now,
    }, synchronize_session=False)
    recovered = cancelled + retrying + exhausted
    if recovered:
        db.commit()
    return recovered


def _touch_lease(request_id: str, lease_token: str) -> bool:
    now = utc_now_naive()
    with SessionLocal() as db:
        updated = db.query(AIAgentRun).filter(
            AIAgentRun.request_id == request_id,
            AIAgentRun.status == "running",
            AIAgentRun.lease_token == lease_token,
            AIAgentRun.cancel_requested.is_(False),
        ).update({
            AIAgentRun.heartbeat_at: now,
            AIAgentRun.lease_expires_at: now + timedelta(seconds=settings.AI_RUN_LEASE_SECONDS),
            AIAgentRun.updated_at: now,
        }, synchronize_session=False)
        db.commit()
        return updated == 1


def _run_can_retry(request_id: str, lease_token: str | None) -> bool:
    with SessionLocal() as db:
        query = db.query(AIAgentRun).filter(AIAgentRun.request_id == request_id)
        if lease_token is not None:
            query = query.filter(AIAgentRun.lease_token == lease_token)
        run = query.first()
        return bool(run is not None and run.attempt_count < settings.AI_RUN_MAX_ATTEMPTS)


def _seconds_until(value, *, now=None) -> int | None:
    if value is None:
        return None
    current = now or utc_now_naive()
    return max(0, math.ceil((value - current).total_seconds()))


def _current_run_recovery_state(request_id: str) -> tuple[str, int | None]:
    """Read the persisted state after a lease-guarded update lost a race."""
    with SessionLocal() as db:
        run = db.get(AIAgentRun, request_id)
        if run is None:
            return "failed", None
        return run.status, (
            (_seconds_until(run.next_retry_at) or 0)
            if run.status == "retry_wait"
            else None
        )


def _agent_http_exception(
    status_code: int,
    code: str,
    *,
    request_id: str,
    retryable: bool = False,
    retry_after: int | None = None,
    run_status: str | None = None,
) -> HTTPException:
    details = error_details_for_code(
        code, retryable=retryable, retry_after=retry_after
    )
    details.update({
        "type": "error",
        "request_id": request_id,
        "run_status": run_status,
    })
    headers = None
    if retryable and retry_after is not None:
        headers = {"Retry-After": str(max(0, int(retry_after)))}
    return HTTPException(status_code=status_code, detail=details, headers=headers)


def _safe_text_chunks(value: str, *, max_chars: int = 24):
    """Split validated text for progressive display without cutting code points."""
    start = 0
    preferred_breaks = set("\n。！？；，,.!?;：:")
    while start < len(value):
        end = min(len(value), start + max_chars)
        if end < len(value):
            for index in range(end, start + max_chars // 2, -1):
                if value[index - 1] in preferred_breaks:
                    end = index
                    break
        yield value[start:end]
        start = end


def _stream_events(
    session_id: int, history: list[dict[str, str]], request_id: str | None = None,
    *, lease_token: str | None = None, admission=None,
):
    """Generate SSE events without retaining request-scoped ORM state."""
    from app.services.react_agent import stream_react_agent

    run_id = request_id or str(uuid4())
    reply = None
    streamed_reply = False
    override_streamed = False
    streamed_parts: list[str] = []
    pending_public = ""
    protocol_scan_tail = ""
    try:
        yield f"data: {json.dumps({'type': 'start', 'request_id': run_id, 'session_id': session_id}, ensure_ascii=False)}\n\n"
        yield f"data: {json.dumps({'type': 'status', 'stage': 'thinking', 'label': '正在思考中'}, ensure_ascii=False)}\n\n"
        last_lease_check = 0.0
        lease_check_interval = min(5.0, max(1.0, settings.AI_RUN_LEASE_SECONDS / 4))
        for event in stream_react_agent(history):
            now_monotonic = time.monotonic()
            if (
                request_id and lease_token
                and now_monotonic - last_lease_check >= lease_check_interval
            ):
                last_lease_check = now_monotonic
                if not _touch_lease(run_id, lease_token):
                    if _run_cancelled(run_id):
                        _set_run_state(run_id, "cancelled", error_code="CANCELLED")
                        yield f"data: {json.dumps({'type': 'cancelled', 'request_id': run_id, 'session_id': session_id, 'run_status': 'cancelled'}, ensure_ascii=False)}\n\n"
                    return
            if event["type"] == "token":
                token = str(event.get("content", ""))
                if token:
                    streamed_reply = True
                    streamed_parts.append(token)
                    pending_public += token
                    protocol_candidate = protocol_scan_tail + token
                    if _contains_private_protocol(protocol_candidate):
                        raise RuntimeError("unsafe_streamed_answer")
                    protocol_scan_tail = protocol_candidate[-128:]
                    # Keep a tail server-side so protocol markers split across model
                    # chunks can be rejected before they reach the browser.
                    while len(pending_public) > 48:
                        public_chunk = pending_public[:24]
                        pending_public = pending_public[24:]
                        yield f"data: {json.dumps({'type': 'chunk', 'content': public_chunk}, ensure_ascii=False)}\n\n"
            elif event["type"] == "answer":
                content = event.get("content")
                if not isinstance(content, str) or not content.strip():
                    raise RuntimeError("unsafe_or_empty_final_answer")
                reply = content
            elif event["type"] == "answer_override":
                # The routed agent streamed pre-validation tokens; the
                # validated answer differs and must replace what was shown.
                content = event.get("content")
                if not isinstance(content, str) or not content.strip():
                    raise RuntimeError("unsafe_or_empty_final_answer")
                reply = content
                override_streamed = True
            else:
                public_event = {
                    "type": "status",
                    "stage": "thinking",
                    "label": event.get("status", "正在思考中"),
                }
                yield f"data: {json.dumps(public_event, ensure_ascii=False)}\n\n"
        if request_id and _run_cancelled(run_id):
            _set_run_state(run_id, "cancelled", error_code="CANCELLED")
            yield f"data: {json.dumps({'type': 'cancelled', 'request_id': run_id, 'session_id': session_id, 'run_status': 'cancelled'}, ensure_ascii=False)}\n\n"
            return
        if not reply or not reply.strip() or _contains_private_protocol(reply):
            raise RuntimeError("unsafe_or_empty_final_answer")
        if override_streamed and streamed_reply:
            # Tokens already shown were pre-validation output; tell the
            # browser to swap them for the authoritative validated answer.
            yield f"data: {json.dumps({'type': 'replace', 'content': reply}, ensure_ascii=False)}\n\n"
        with SessionLocal() as stream_db:
            assistant = ChatMessage(session_id=session_id, role="assistant", content=reply)
            stream_db.add(assistant)
            chat_session = stream_db.get(ChatSession, session_id)
            if chat_session is None:
                raise RuntimeError("聊天会话不存在")
            chat_session.updated_at = utc_now_naive()
            stream_db.flush()
            if request_id:
                run = (
                    stream_db.query(AIAgentRun)
                    .filter(
                        AIAgentRun.request_id == run_id,
                        AIAgentRun.status == "running",
                        AIAgentRun.lease_token == lease_token,
                    )
                    .with_for_update()
                    .first()
                )
                if run is None:
                    stream_db.rollback()
                    return
                if run.cancel_requested:
                    stream_db.rollback()
                    return
                run.status = "completed"
                run.assistant_message_id = assistant.id
                run.finished_at = utc_now_naive()
                run.lease_token = None
                run.lease_expires_at = None
                run.updated_at = utc_now_naive()
            stream_db.commit()
        if streamed_reply and not override_streamed:
            for chunk in _safe_text_chunks(pending_public):
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk}, ensure_ascii=False)}\n\n"
        elif not streamed_reply:
            for chunk in _safe_text_chunks(reply):
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk}, ensure_ascii=False)}\n\n"
        yield f"data: {json.dumps({'type': 'done', 'request_id': run_id, 'session_id': session_id}, ensure_ascii=False)}\n\n"
    except GeneratorExit:
        if request_id:
            retryable = not streamed_reply and _run_can_retry(run_id, lease_token)
            _set_run_state(
                run_id, "retry_wait" if retryable else "failed",
                error_code="CLIENT_DISCONNECTED",
                lease_token=lease_token,
                next_retry_at=utc_now_naive() if retryable else None,
            )
        raise
    except Exception as error:
        if request_id and _run_cancelled(run_id):
            _set_run_state(run_id, "cancelled", error_code="CANCELLED")
            yield f"data: {json.dumps({'type': 'cancelled', 'request_id': run_id, 'session_id': session_id, 'run_status': 'cancelled'}, ensure_ascii=False)}\n\n"
            return
        is_public_error = isinstance(error, AgentPublicError)
        error_code = normalize_error_code(
            error.code if is_public_error else "AGENT_FAILED"
        )
        desired_retryable = False
        retry_after = None
        if is_public_error and error.retryable and not streamed_reply and request_id:
            try:
                desired_retryable = _run_can_retry(run_id, lease_token)
            except Exception:
                desired_retryable = False
            if desired_retryable:
                retry_after = error.retry_after if error.retry_after is not None else 2

        desired_status = "retry_wait" if desired_retryable else "failed"
        actual_status = "failed"
        actual_retry_after = None
        if request_id:
            next_retry_at = (
                utc_now_naive() + timedelta(seconds=retry_after)
                if desired_retryable and retry_after is not None
                else None
            )
            try:
                updated = _set_run_state(
                    run_id,
                    desired_status,
                    error_code=error_code,
                    lease_token=lease_token,
                    next_retry_at=next_retry_at,
                )
                if updated:
                    actual_status = desired_status
                    actual_retry_after = retry_after if desired_retryable else None
                else:
                    actual_status, actual_retry_after = _current_run_recovery_state(run_id)
            except Exception:
                try:
                    actual_status, actual_retry_after = _current_run_recovery_state(run_id)
                except Exception:
                    actual_status = "failed"
                    actual_retry_after = None

        actual_retryable = actual_status == "retry_wait"
        if is_public_error:
            details = public_error_details(
                error,
                retryable=actual_retryable,
                retry_after=actual_retry_after,
            )
        else:
            details = error_details_for_code(
                error_code,
                retryable=actual_retryable,
                retry_after=actual_retry_after,
            )
        public_error = {
            "type": "error",
            **details,
            "request_id": run_id,
            "session_id": session_id,
            "run_status": actual_status,
        }
        yield f"data: {json.dumps(public_error, ensure_ascii=False)}\n\n"
    finally:
        if admission is not None:
            admission.release()


def _prepare_chat(
    body: ChatRequest, db: Session, current_user: UserModel
) -> tuple[ChatSession, ChatMessage, list[dict[str, str]]]:
    message = body.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="消息不能为空")
    if body.session_id is None:
        session = ChatSession(user_id=current_user.id, title=message[:15])
        db.add(session)
        db.flush()
    else:
        session = _session_for_user(db, body.session_id, current_user.id)
    user_message = ChatMessage(session_id=session.id, role="user", content=message)
    db.add(user_message)
    db.flush()
    return session, user_message, _history(db, session.id)


@router.get("/chat-ai/sessions", response_model=APIResponse[list])
def list_sessions(
    db: Session = Depends(get_db), current_user: UserModel = Depends(get_current_user)
):
    sessions = db.query(ChatSession).filter(
        ChatSession.user_id == current_user.id
    ).order_by(ChatSession.updated_at.desc()).all()
    return APIResponse(data=[item.to_dict() for item in sessions])


@router.get("/chat-ai/sessions/{session_id}/messages", response_model=APIResponse[list])
def list_messages(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    _session_for_user(db, session_id, current_user.id)
    messages = db.query(ChatMessage).filter(
        ChatMessage.session_id == session_id
    ).order_by(ChatMessage.id.asc()).all()
    data = []
    for item in messages:
        message = item.to_dict()
        if item.role == "assistant":
            message["content"] = _public_history_content(item.content)
        data.append(message)
    return APIResponse(data=data)


@router.delete("/chat-ai/sessions/{session_id}", response_model=APIResponse)
def delete_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    session = _session_for_user(db, session_id, current_user.id)
    db.query(ChatMessage).filter(ChatMessage.session_id == session.id).delete()
    db.delete(session)
    db.commit()
    return APIResponse(message="删除成功")


@router.post("/chat-ai/chat", response_model=APIResponse[dict], deprecated=True)
def chat(
    body: ChatRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    raise HTTPException(
        status_code=410,
        detail="该旧接口已停用，请使用支持 request_id 与任务恢复的 /chat-ai/chat/stream",
    )


@router.post("/chat-ai/chat/stream")
def chat_stream(
    body: ChatRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    from app.services.ai_reliability import agent_limiter

    recover_stale_agent_runs(db)
    request_id = str(body.request_id or uuid4())
    existing = db.query(AIAgentRun).filter(
        AIAgentRun.request_id == request_id
    ).with_for_update().first()
    if existing is not None:
        if existing.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="运行记录不存在")
        original_message = db.get(ChatMessage, existing.user_message_id)
        if (
            original_message is None
            or original_message.content != body.message.strip()
            or (body.session_id is not None and body.session_id != existing.session_id)
        ):
            raise _agent_http_exception(
                409,
                "REQUEST_ID_MISMATCH",
                request_id=request_id,
                run_status=existing.status,
            )
        if existing.status == "completed" and existing.assistant_message_id:
            message = db.get(ChatMessage, existing.assistant_message_id)
            if message is not None:
                return StreamingResponse(
                    iter([
                        f"data: {json.dumps({'type': 'start', 'request_id': request_id, 'session_id': existing.session_id}, ensure_ascii=False)}\n\n",
                        f"data: {json.dumps({'type': 'chunk', 'content': _public_history_content(message.content)}, ensure_ascii=False)}\n\n",
                        f"data: {json.dumps({'type': 'done', 'request_id': request_id, 'session_id': existing.session_id}, ensure_ascii=False)}\n\n",
                    ]),
                    media_type="text/event-stream",
                )
        now = utc_now_naive()
        resumable = (
            existing.status == "retry_wait"
            and (existing.next_retry_at is None or existing.next_retry_at <= now)
        ) or (
            existing.status == "running"
            and existing.lease_expires_at is not None
            and existing.lease_expires_at <= now
        )
        if not resumable:
            if existing.status == "running":
                code, retryable, retry_after = "RUN_IN_PROGRESS", False, None
            elif existing.status == "retry_wait":
                code, retryable = "RUN_RETRY_WAIT", True
                retry_after = _seconds_until(existing.next_retry_at, now=now) or 0
            elif existing.status == "completed":
                code, retryable, retry_after = "RUN_RESULT_MISSING", False, None
            else:
                code, retryable, retry_after = "RUN_NOT_RESUMABLE", False, None
            raise _agent_http_exception(
                409,
                code,
                request_id=request_id,
                retryable=retryable,
                retry_after=retry_after,
                run_status=existing.status,
            )
        if existing.attempt_count >= settings.AI_RUN_MAX_ATTEMPTS:
            existing.status = "failed"
            existing.error_code = "RETRY_EXHAUSTED"
            existing.finished_at = now
            existing.lease_token = None
            existing.lease_expires_at = None
            existing.next_retry_at = None
            db.commit()
            raise _agent_http_exception(
                409,
                "RETRY_EXHAUSTED",
                request_id=request_id,
                run_status="failed",
            )
        admission = agent_limiter.acquire(current_user.id)
        if admission is None:
            raise _agent_http_exception(
                429,
                "AGENT_BUSY",
                request_id=request_id,
                retryable=True,
                retry_after=2,
                run_status=existing.status,
            )
        lease_token = str(uuid4())
        existing.status = "running"
        existing.attempt_count += 1
        existing.heartbeat_at = now
        existing.lease_token = lease_token
        existing.lease_expires_at = now + timedelta(seconds=settings.AI_RUN_LEASE_SECONDS)
        existing.next_retry_at = None
        existing.finished_at = None
        existing.error_code = None
        history = _history(db, existing.session_id, through_message_id=existing.user_message_id)
        try:
            db.commit()
        except Exception:
            db.rollback()
            admission.release()
            raise
        return StreamingResponse(
            _stream_events(
                existing.session_id, history, request_id,
                lease_token=lease_token, admission=admission,
            ),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
            background=BackgroundTask(admission.release),
        )

    admission = agent_limiter.acquire(current_user.id)
    if admission is None:
        raise _agent_http_exception(
            429,
            "AGENT_BUSY",
            request_id=request_id,
            retryable=True,
            retry_after=2,
        )
    try:
        session, user_message, history = _prepare_chat(body, db, current_user)
    except BaseException:
        admission.release()
        raise
    session_id = session.id
    now = utc_now_naive()
    lease_token = str(uuid4())
    db.add(AIAgentRun(
        request_id=request_id,
        user_id=current_user.id,
        session_id=session_id,
        user_message_id=user_message.id,
        status="running",
        attempt_count=1,
        heartbeat_at=now,
        lease_token=lease_token,
        lease_expires_at=now + timedelta(seconds=settings.AI_RUN_LEASE_SECONDS),
    ))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        admission.release()
        raise _agent_http_exception(
            409,
            "DUPLICATE_REQUEST",
            request_id=request_id,
        )
    except Exception:
        db.rollback()
        admission.release()
        raise

    return StreamingResponse(
        _stream_events(
            session_id, history, request_id,
            lease_token=lease_token, admission=admission,
        ),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        background=BackgroundTask(admission.release),
    )


@router.post("/chat-ai/runs/{request_id}/cancel", response_model=APIResponse)
def cancel_agent_run(
    request_id: UUID,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    run = (
        db.query(AIAgentRun)
        .filter(AIAgentRun.request_id == str(request_id))
        .with_for_update()
        .first()
    )
    if run is None or run.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="运行记录不存在")
    if run.status in {"running", "retry_wait"}:
        run.cancel_requested = True
        run.status = "cancelled"
        run.error_code = "CANCELLED"
        run.finished_at = utc_now_naive()
        run.lease_token = None
        run.lease_expires_at = None
        run.next_retry_at = None
        run.updated_at = utc_now_naive()
        db.commit()
    return APIResponse(data={"status": run.status}, message="已请求停止")


@router.get("/chat-ai/runs/{request_id}", response_model=APIResponse[dict])
def get_agent_run(
    request_id: UUID,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    recover_stale_agent_runs(db)
    run = db.get(AIAgentRun, str(request_id))
    if run is None or run.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="运行记录不存在")
    retryable = bool(
        run.status == "retry_wait"
        and not run.cancel_requested
        and run.attempt_count < settings.AI_RUN_MAX_ATTEMPTS
    )
    retry_after = (
        (_seconds_until(run.next_retry_at) or 0) if retryable else None
    )
    error = (
        error_details_for_code(
            run.error_code,
            retryable=retryable,
            retry_after=retry_after,
        )
        if run.error_code
        else None
    )
    return APIResponse(data={
        "request_id": run.request_id,
        "session_id": run.session_id,
        "user_message_id": run.user_message_id,
        "assistant_message_id": run.assistant_message_id,
        "status": run.status,
        "attempt_count": run.attempt_count,
        "error_code": run.error_code,
        "error": error,
        "retryable": retryable,
        "retry_after": retry_after,
        "heartbeat_at": run.heartbeat_at.isoformat() if run.heartbeat_at else None,
        "next_retry_at": run.next_retry_at.isoformat() if run.next_retry_at else None,
        "finished_at": run.finished_at.isoformat() if run.finished_at else None,
    })


@router.post("/chat-ai/runs/{request_id}/feedback", response_model=APIResponse[dict])
def submit_run_feedback(
    request_id: UUID,
    body: RunFeedbackRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Store one sanitized, review-required failure candidate per owned run."""
    failure_type = body.failure_type.strip()
    if failure_type not in _FEEDBACK_TYPES:
        raise HTTPException(status_code=400, detail="不支持的失败类型")
    run = db.get(AIAgentRun, str(request_id))
    if run is None or run.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="运行记录不存在")
    original = db.get(ChatMessage, run.user_message_id)
    if original is None:
        raise HTTPException(status_code=409, detail="原始问题不存在")
    sanitized_query = _sanitize_failure_text(original.content)
    feedback = _sanitize_failure_text(body.feedback)
    existing = db.query(RAGFailureCase).filter(
        RAGFailureCase.request_id == str(request_id)
    ).first()
    created = existing is None
    if existing is None:
        from app.services.query_router import route_query

        existing = RAGFailureCase(
            request_id=str(request_id),
            user_id=current_user.id,
            origin="user_feedback",
            query_hash=hmac.new(
                settings.SECRET_KEY.encode("utf-8"),
                original.content.encode("utf-8"),
                hashlib.sha256,
            ).hexdigest(),
            sanitized_query=sanitized_query,
            route=route_query(original.content).value,
            failure_type=failure_type,
            index_signature=_active_index_signature(),
            feedback=feedback,
            review_status="pending",
        )
        db.add(existing)
        db.commit()
        db.refresh(existing)
    return APIResponse(
        code=201 if created else 200,
        data={"id": existing.id, "review_status": existing.review_status},
        message="反馈已进入脱敏审核队列",
    )


@router.post("/chat-ai/failures/{failure_id}/review", response_model=APIResponse[dict])
def review_failure_case(
    failure_id: int,
    body: RunFeedbackReviewRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Approve/reject a sanitized case; only approved cases may be exported."""
    if current_user.userType != 0:
        raise HTTPException(status_code=403, detail="仅管理员可审核失败案例")
    if body.review_status not in {"accepted", "rejected"}:
        raise HTTPException(status_code=400, detail="review_status 必须为 accepted 或 rejected")
    if body.expected_route is not None:
        from app.services.query_router import QueryRoute

        if body.expected_route not in {route.value for route in QueryRoute}:
            raise HTTPException(status_code=400, detail="expected_route 无效")
    case = db.get(RAGFailureCase, failure_id)
    if case is None:
        raise HTTPException(status_code=404, detail="失败案例不存在")
    case.review_status = body.review_status
    case.expected_route = body.expected_route
    case.expected_sources = [
        _sanitize_failure_text(value)[:300] for value in body.expected_sources if value.strip()
    ]
    case.review_notes = _sanitize_failure_text(body.notes) if body.notes else None
    case.reviewed_at = utc_now_naive()
    db.commit()
    return APIResponse(
        data={"id": case.id, "review_status": case.review_status},
        message="失败案例审核结果已保存",
    )
