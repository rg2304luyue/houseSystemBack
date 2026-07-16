from flask import Blueprint, request, current_app, jsonify, stream_with_context, Response
import json
import logging
from datetime import timedelta
from cachetools import TTLCache
from core.agent.react_agent import ReactAgent
from models.house_model import HouseInfo
from exts.db import db
from exts.redis import redis_store
from utils.response_utils import success_response, error_response, Code
from decorators.decorators import token_required
from flask import g
from models.chat_model import ChatSession, ChatMessage

logger = logging.getLogger(__name__)

chat_ai_bp = Blueprint('chat_ai', __name__, url_prefix='/chat-ai')
my_agent = ReactAgent()

# ── 短期记忆三级存储配置 ──
CHAT_HISTORY_TTL = timedelta(hours=2)       # L2 Redis 过期时间
CHAT_HISTORY_MAX_MESSAGES = 10              # 保留最近 10 条消息
CHAT_L1_TTL = 30                            # L1 本地缓存 TTL（秒）
CHAT_L1_MAXSIZE = 256                       # L1 最多缓存 256 个会话
chat_history_l1 = TTLCache(maxsize=CHAT_L1_MAXSIZE, ttl=CHAT_L1_TTL)

def _redis_history_key(session_id):
    return f"chat_history:{session_id}"

def _load_l2_history(session_id):
    """L2 Redis 加载最近 N 条消息，不可用时返回 None"""
    try:
        raw = redis_store.lrange(
            _redis_history_key(session_id),
            -CHAT_HISTORY_MAX_MESSAGES, -1
        )
        if raw:
            return [json.loads(item) for item in raw]
    except Exception:
        pass
    return None


def _append_history(session_id, role, content):
    """追加一条消息到 L1 + L2，L2 先写"""
    item = {"role": role, "content": content}
    # L2 Redis 先写
    try:
        key = _redis_history_key(session_id)
        pipe = redis_store.pipeline()
        pipe.rpush(key, json.dumps(item))
        pipe.ltrim(key, -CHAT_HISTORY_MAX_MESSAGES, -1)
        pipe.expire(key, CHAT_HISTORY_TTL)
        pipe.execute()
        new_len = redis_store.llen(key)
        logger.info(f"[History] session={session_id} → Redis 追加 [{role}], 当前 {new_len} 条")
    except Exception as e:
        logger.warning(f"Redis 历史追加失败: {e}")
    # L1 本地内存追加 + 裁剪（L2 成功后才更新，保持一致性）
    try:
        if session_id in chat_history_l1:
            chat_history_l1[session_id].append(item)
            # 同步裁剪，和 Redis LTRIM 保持一致
            chat_history_l1[session_id] = chat_history_l1[session_id][-CHAT_HISTORY_MAX_MESSAGES:]
            logger.info(f"[History] session={session_id} → L1 同步追加 [{role}]")
    except Exception:
        pass


def _backfill_history(session_id, history):
    """MySQL 数据回填 L2 + L1"""
    # L2 Redis 先写
    try:
        key = _redis_history_key(session_id)
        pipe = redis_store.pipeline()
        for item in history:
            pipe.rpush(key, json.dumps(item))
        pipe.ltrim(key, -CHAT_HISTORY_MAX_MESSAGES, -1)
        pipe.expire(key, CHAT_HISTORY_TTL)
        pipe.execute()
    except Exception:
        pass
    # L1 本地内存（L2 成功后回填）
    try:
        chat_history_l1[session_id] = list(history)
    except Exception:
        pass


def _delete_history(session_id):
    """删除 L1 + L2 中的会话历史"""
    # L2 先删
    try:
        redis_store.delete(_redis_history_key(session_id))
        logger.info(f"[History] session={session_id} ← Redis 已删除")
    except Exception:
        pass
    # L1 后删
    try:
        chat_history_l1.pop(session_id, None)
    except Exception:
        pass

def _get_user_id():
    if not hasattr(g, 'user') or not g.user:
        return None
    if isinstance(g.user, dict):
        return g.user.get('id')
    return getattr(g.user, 'id', None)

def _load_history(session_id: int, max_chars: int = 8000) -> list:
    """加载对话历史：L1 本地 → L2 Redis → MySQL 兜底 → 回填"""
    # L1: 本地内存缓存
    try:
        if session_id in chat_history_l1:
            logger.info(f"[History] session={session_id} ← L1 命中, {len(chat_history_l1[session_id])} 条")
            return chat_history_l1[session_id]
    except Exception:
        pass

    # L2: Redis 短期记忆
    redis_history = _load_l2_history(session_id)
    if redis_history:
        logger.info(f"[History] session={session_id} ← L2 Redis 命中, {len(redis_history)} 条")
        try:
            chat_history_l1[session_id] = redis_history
        except Exception:
            pass
        return redis_history

    # L3: MySQL 持久化
    all_records = db.session.query(ChatMessage) \
        .filter(ChatMessage.session_id == session_id) \
        .order_by(ChatMessage.id.asc()) \
        .all()

    if not all_records:
        return []

    # 从最新向旧累计字符数，超过阈值则截断旧消息
    total = 0
    start_idx = len(all_records)
    for i in range(len(all_records) - 1, -1, -1):
        total += len(all_records[i].content or '')
        if total > max_chars:
            start_idx = i + 1
            break
        start_idx = i

    history = [{"role": m.role, "content": m.content} for m in all_records[start_idx:]]

    # 回填 L2 + L1
    logger.info(f"[History] session={session_id} ← MySQL 加载, {len(history)} 条，回填 Redis")
    _backfill_history(session_id, history)

    return history


@chat_ai_bp.route('/chat', methods=['POST'])
@token_required
def chat_with_ai():
    try:
        current_user_id = _get_user_id()
        if not current_user_id:
            return error_response(code=Code.UNAUTHORIZED, message="身份校验失败，请重新登录")

        data = request.get_json()
        user_message = data.get('message', '')
        session_id = data.get('session_id')

        if not user_message:
            return error_response(code=Code.BAD_REQUEST, message="消息内容不能为空")

        if not session_id:
            title = user_message[:15] + "..." if len(user_message) > 15 else user_message
            new_session = ChatSession(user_id=current_user_id, title=title)
            db.session.add(new_session)
            db.session.flush()
            session_id = new_session.id

        user_msg = ChatMessage(session_id=session_id, role='user', content=user_message)
        db.session.add(user_msg)
        db.session.flush()

        formatted_history = _load_history(session_id)

        ai_reply = my_agent.execute(user_message, history=formatted_history)

        assistant_msg = ChatMessage(session_id=session_id, role='assistant', content=ai_reply)
        db.session.add(assistant_msg)

        session_obj = db.session.query(ChatSession).get(session_id)
        if session_obj:
            session_obj.updated_at = db.func.now()

        db.session.commit()

        # 同步到 Redis 短期记忆
        _append_history(session_id, 'user', user_message)
        _append_history(session_id, 'assistant', ai_reply)

        return success_response(
            code=Code.GET_OK,
            data={"reply": ai_reply, "session_id": session_id},
            message="对话成功"
        )

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Chat AI error: {e}")
        return error_response(code=Code.INTERNAL_SERVER_ERROR, message=f"AI对话失败: {str(e)}")


# ============================================================
# 2. 流式聊天接口（SSE）- 核心新功能
# ============================================================
@chat_ai_bp.route('/chat/stream', methods=['POST'])
@token_required
def chat_stream():
    """
    SSE 流式聊天接口
    前端使用 EventSource 或 fetch + ReadableStream 接收
    每个数据块格式：data: {"type": "chunk", "content": "..."}\n\n
    结束时：data: {"type": "done", "session_id": 123}\n\n
    """
    current_user_id = _get_user_id()
    if not current_user_id:
        return error_response(code=Code.UNAUTHORIZED, message="身份校验失败")

    data = request.get_json()
    user_message = data.get('message', '').strip()
    session_id = data.get('session_id')

    if not user_message:
        return error_response(code=Code.BAD_REQUEST, message="消息不能为空")

    # 在流开始前先处理数据库（session 创建、用户消息写入）
    try:
        if not session_id:
            title = user_message[:15] + "..." if len(user_message) > 15 else user_message
            new_session = ChatSession(user_id=current_user_id, title=title)
            db.session.add(new_session)
            db.session.flush()
            session_id = new_session.id

        user_msg = ChatMessage(session_id=session_id, role='user', content=user_message)
        db.session.add(user_msg)

        formatted_history = _load_history(session_id)

        # 必须在进入流式生成器前 commit，确保 ChatSession 和用户消息已写入数据库
        # 否则 generate() 内部的新 db.session 会因外键约束失败
        db.session.commit()

        # 同步用户消息到 Redis 短期记忆
        _append_history(session_id, 'user', user_message)
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Stream pre-process error: {e}")
        return error_response(code=Code.INTERNAL_SERVER_ERROR, message="初始化失败")

    # 捕获 app 引用（stream 中需要）
    app = current_app._get_current_object()
    final_session_id = session_id

    def generate():
        full_reply = ""
        try:
            # 流式生成
            for chunk in my_agent.execute_stream_with_history(user_message, history=formatted_history):
                if chunk:
                    full_reply += chunk
                    payload = json.dumps({"type": "chunk", "content": chunk}, ensure_ascii=False)
                    yield f"data: {payload}\n\n"

            # 保存完整回复到数据库
            with app.app_context():
                try:
                    assistant_msg = ChatMessage(
                        session_id=final_session_id,
                        role='assistant',
                        content=full_reply
                    )
                    db.session.add(assistant_msg)
                    session_obj = db.session.query(ChatSession).get(final_session_id)
                    if session_obj:
                        session_obj.updated_at = db.func.now()
                    db.session.commit()

                    # 同步 AI 回复到 Redis 短期记忆
                    _append_history(final_session_id, 'assistant', full_reply)
                except Exception as e:
                    db.session.rollback()
                    app.logger.error(f"Stream save error: {e}")

            # 发送完成信号
            done_payload = json.dumps({
                "type": "done",
                "session_id": final_session_id
            }, ensure_ascii=False)
            yield f"data: {done_payload}\n\n"

        except Exception as e:
            app.logger.error(f"Stream generation error: {e}")
            err_payload = json.dumps({"type": "error", "message": str(e)}, ensure_ascii=False)
            yield f"data: {err_payload}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',  # 关闭 Nginx 缓冲
            'Connection': 'keep-alive',
            'Access-Control-Allow-Origin': '*',
        }
    )

# ============================================================
# 3. 会话列表
# ============================================================
@chat_ai_bp.route('/sessions', methods=['GET'])
@token_required
def get_sessions():
    sessions = db.session.query(ChatSession).filter_by(user_id=g.user.id) \
        .order_by(ChatSession.updated_at.desc()).all()
    return success_response(code=Code.GET_OK, data=[s.to_dict() for s in sessions])

# ============================================================
# 4. 删除会话
# ============================================================
@chat_ai_bp.route('/sessions/<int:session_id>', methods=['DELETE'])
@token_required
def delete_session(session_id):
    current_user_id = _get_user_id()
    if not current_user_id:
        return error_response("身份校验失败", code=Code.UNAUTHORIZED)

    session = db.session.get(ChatSession, session_id)
    if not session:
        return error_response("会话不存在", code=Code.NOT_FOUND)
    if session.user_id != current_user_id:
        return error_response("无权操作", code=Code.FORBIDDEN)

    try:
        db.session.delete(session)
        db.session.commit()
        _delete_history(session_id)
        return success_response(message="删除成功", code=Code.DELETE_OK)
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"删除会话 {session_id} 失败: {e}")
        return error_response(f"删除失败: {str(e)}", code=Code.INTERNAL_SERVER_ERROR)

# ============================================================
# 5. 会话消息记录
# ============================================================
@chat_ai_bp.route('/sessions/<int:session_id>/messages', methods=['GET'])
def get_session_messages(session_id):
    try:
        messages = db.session.query(ChatMessage).filter_by(session_id=session_id) \
            .order_by(ChatMessage.id.asc()).all()
        return success_response(code=Code.GET_OK, data=[m.to_dict() for m in messages])
    except Exception as e:
        return error_response(code=Code.INTERNAL_SERVER_ERROR, message=str(e))

# ============================================================
# 6. 房源搜索（直接查询，不经过AI）
# ============================================================
@chat_ai_bp.route('/houses/search', methods=['POST'])
def search_houses():
    try:
        data = request.get_json()

        # ---- 调试日志：打印接收到的搜索参数 ----
        current_app.logger.info(f"[HouseSearch] 搜索参数: {data}")

        query = db.session.query(HouseInfo).filter(HouseInfo.available == 1)

        if data.get('min_price'):
            query = query.filter(HouseInfo.price >= data['min_price'])
        if data.get('max_price'):
            query = query.filter(HouseInfo.price <= data['max_price'])
        if data.get('region'):
            # 模糊匹配，支持"岳麓"匹配"岳麓区"
            query = query.filter(HouseInfo.region.like(f"%{data['region']}%"))
            current_app.logger.info(f"[HouseSearch] 按区域筛选: {data['region']}")
        if data.get('min_area'):
            query = query.filter(HouseInfo.area >= data['min_area'])
        if data.get('max_area'):
            query = query.filter(HouseInfo.area <= data['max_area'])
        if data.get('rooms'):
            query = query.filter(HouseInfo.rooms.like(f"%{data['rooms']}%"))
        if data.get('rent_type'):
            query = query.filter(HouseInfo.rent_type == data['rent_type'])
        if data.get('subway'):
            query = query.filter(HouseInfo.subway == 1)
        if data.get('decoration'):
            query = query.filter(HouseInfo.decoration.like(f"%{data['decoration']}%"))

        houses = query.order_by(HouseInfo.price.asc()).limit(20).all()
        current_app.logger.info(f"[HouseSearch] 查询结果数量: {len(houses)}")

        result = {"success": True, "houses": [h.to_dict() for h in houses], "count": len(houses)}
        return success_response(code=Code.GET_OK, data=result, message="房源搜索成功")

    except Exception as e:
        current_app.logger.error(f"Search houses API error: {e}")
        return error_response(code=Code.INTERNAL_SERVER_ERROR, message=f"搜索失败: {str(e)}")


@chat_ai_bp.route('/houses/<int:house_id>', methods=['GET'])
def get_house_detail(house_id):
    try:
        house = db.session.query(HouseInfo).filter(HouseInfo.id == house_id).first()
        if house:
            return success_response(code=Code.GET_OK, data={"success": True, "house": house.to_dict()})
        return error_response(code=Code.NOT_FOUND, message="房源不存在")
    except Exception as e:
        return error_response(code=Code.INTERNAL_SERVER_ERROR, message=str(e))


@chat_ai_bp.route('/houses/popular', methods=['GET'])
def get_popular_houses():
    try:
        limit = request.args.get('limit', 10, type=int)
        houses = db.session.query(HouseInfo) \
            .filter(HouseInfo.available == 1) \
            .order_by(HouseInfo.page_views.desc()) \
            .limit(limit).all()
        result = {"success": True, "houses": [h.to_dict() for h in houses], "count": len(houses)}
        return success_response(code=Code.GET_OK, data=result, message="获取热门房源成功")
    except Exception as e:
        return error_response(code=Code.INTERNAL_SERVER_ERROR, message=str(e))
