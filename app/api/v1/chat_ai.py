"""FastAPI chat endpoints used by the local AI assistant page."""
from datetime import datetime
import json
import re
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.time import utc_now_naive
from app.db.session import SessionLocal, get_db
from app.models.chat import AIAgentRun, ChatMessage, ChatSession
from app.models.user import UserModel
from app.schemas.common import APIResponse

router = APIRouter(tags=["chat-ai"])

_PRIVATE_PROTOCOL_PATTERN = re.compile(
    r"(?:Action|Observation|Final Answer|Thought)\s*[:：]|"
    r"(?:思考|思维链)\s*[:：]|</?think>|search_houses_by_criteria|"
    r"(?:get_house_details|get_popular_houses|search_rental_knowledge|"
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


def _session_for_user(db: Session, session_id: int, user_id: int) -> ChatSession:
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == user_id,
    ).first()
    if session is None:
        raise HTTPException(status_code=404, detail="会话不存在或无权访问")
    return session


def _history(db: Session, session_id: int) -> list[dict[str, str]]:
    records = db.query(ChatMessage).filter(
        ChatMessage.session_id == session_id
    ).order_by(ChatMessage.id.asc()).all()
    return [
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
    error_code: str | None = None,
) -> bool:
    with SessionLocal() as db:
        run = db.get(AIAgentRun, request_id)
        if run is None:
            return False
        if run.status in {"completed", "cancelled"} and run.status != status:
            return False
        run.status = status
        run.assistant_message_id = assistant_message_id
        run.error_code = error_code
        run.updated_at = utc_now_naive()
        db.commit()
        return True


def _stream_events(
    session_id: int, history: list[dict[str, str]], request_id: str | None = None
):
    """Generate SSE events without retaining request-scoped ORM state."""
    from app.services.react_agent import AgentPublicError, stream_react_agent

    run_id = request_id or str(uuid4())
    yield f"data: {json.dumps({'type': 'start', 'request_id': run_id, 'session_id': session_id}, ensure_ascii=False)}\n\n"
    yield f"data: {json.dumps({'type': 'status', 'stage': 'thinking', 'label': '正在思考中'}, ensure_ascii=False)}\n\n"
    try:
        reply = None
        for event in stream_react_agent(history):
            if request_id and _run_cancelled(run_id):
                _set_run_state(run_id, "cancelled", error_code="CANCELLED")
                yield f"data: {json.dumps({'type': 'cancelled', 'request_id': run_id}, ensure_ascii=False)}\n\n"
                return
            if event["type"] == "answer":
                reply = str(event["content"]).strip()
            else:
                public_event = {
                    "type": "status",
                    "stage": "thinking",
                    "label": event.get("status", "正在思考中"),
                }
                yield f"data: {json.dumps(public_event, ensure_ascii=False)}\n\n"
        if request_id and _run_cancelled(run_id):
            _set_run_state(run_id, "cancelled", error_code="CANCELLED")
            yield f"data: {json.dumps({'type': 'cancelled', 'request_id': run_id}, ensure_ascii=False)}\n\n"
            return
        if not reply or _contains_private_protocol(reply):
            raise RuntimeError("unsafe_or_empty_final_answer")
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
                    .filter(AIAgentRun.request_id == run_id)
                    .with_for_update()
                    .first()
                )
                if run is None or run.cancel_requested:
                    stream_db.rollback()
                    _set_run_state(run_id, "cancelled", error_code="CANCELLED")
                    return
                run.status = "completed"
                run.assistant_message_id = assistant.id
                run.updated_at = utc_now_naive()
            stream_db.commit()
        yield f"data: {json.dumps({'type': 'chunk', 'content': reply}, ensure_ascii=False)}\n\n"
        yield f"data: {json.dumps({'type': 'done', 'request_id': run_id, 'session_id': session_id}, ensure_ascii=False)}\n\n"
    except Exception as error:
        if request_id and _run_cancelled(run_id):
            _set_run_state(run_id, "cancelled", error_code="CANCELLED")
            yield f"data: {json.dumps({'type': 'cancelled', 'request_id': run_id}, ensure_ascii=False)}\n\n"
            return
        if request_id:
            _set_run_state(run_id, "failed", error_code="AGENT_FAILED")
        if isinstance(error, AgentPublicError):
            public_error = {"type": "error", "code": "AGENT_FAILED", "message": str(error)}
            yield f"data: {json.dumps(public_error, ensure_ascii=False)}\n\n"
            return
        yield f"data: {json.dumps({'type': 'error', 'code': 'AGENT_FAILED', 'message': 'AI 服务暂时不可用，请稍后重试'}, ensure_ascii=False)}\n\n"


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


@router.post("/chat-ai/chat", response_model=APIResponse[dict])
def chat(
    body: ChatRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    session, _, history = _prepare_chat(body, db, current_user)
    try:
        reply = _reply(history)
    except Exception as error:
        db.rollback()
        raise HTTPException(status_code=503, detail=f"AI 服务暂不可用: {error}")
    db.add(ChatMessage(session_id=session.id, role="assistant", content=reply))
    session.updated_at = utc_now_naive()
    db.commit()
    return APIResponse(data={"reply": reply, "session_id": session.id})


@router.post("/chat-ai/chat/stream")
def chat_stream(
    body: ChatRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    request_id = str(body.request_id or uuid4())
    existing = db.get(AIAgentRun, request_id)
    if existing is not None:
        if existing.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="运行记录不存在")
        original_message = db.get(ChatMessage, existing.user_message_id)
        if (
            original_message is None
            or original_message.content != body.message.strip()
            or (body.session_id is not None and body.session_id != existing.session_id)
        ):
            raise HTTPException(status_code=409, detail="request_id 与原请求不匹配")
        if existing.status == "completed" and existing.assistant_message_id:
            message = db.get(ChatMessage, existing.assistant_message_id)
            if message is not None:
                return StreamingResponse(
                    iter([
                        f"data: {json.dumps({'type': 'start', 'request_id': request_id, 'session_id': existing.session_id}, ensure_ascii=False)}\n\n",
                        f"data: {json.dumps({'type': 'chunk', 'content': message.content}, ensure_ascii=False)}\n\n",
                        f"data: {json.dumps({'type': 'done', 'request_id': request_id, 'session_id': existing.session_id}, ensure_ascii=False)}\n\n",
                    ]),
                    media_type="text/event-stream",
                )
        raise HTTPException(status_code=409, detail=f"运行状态为 {existing.status}")

    session, user_message, history = _prepare_chat(body, db, current_user)
    session_id = session.id
    db.add(AIAgentRun(
        request_id=request_id,
        user_id=current_user.id,
        session_id=session_id,
        user_message_id=user_message.id,
        status="running",
    ))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="该请求已提交，请勿重复发送")

    return StreamingResponse(
        _stream_events(session_id, history, request_id),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
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
    if run.status == "running":
        run.cancel_requested = True
        run.status = "cancelled"
        run.error_code = "CANCELLED"
        run.updated_at = utc_now_naive()
        db.commit()
    return APIResponse(data={"status": run.status}, message="已请求停止")
