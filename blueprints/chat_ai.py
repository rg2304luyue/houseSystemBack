from flask import Blueprint, request, current_app, jsonify, stream_with_context, Response
import json
from core.agent.react_agent import ReactAgent
from models.house_model import HouseInfo
from exts.db import db
from utils.response_utils import success_response, error_response, Code
from decorators.decorators import token_required
from flask import g
from models.chat_model import ChatSession, ChatMessage

chat_ai_bp = Blueprint('chat_ai', __name__, url_prefix='/chat-ai')
my_agent = ReactAgent()

def _get_user_id():
    if not hasattr(g, 'user') or not g.user:
        return None
    if isinstance(g.user, dict):
        return g.user.get('id')
    return getattr(g.user, 'id', None)

class HouseRecommendationBot:
    def __init__(self):
        self.house_search_functions = [
            {
                "name": "search_houses_by_criteria",
                "description": "根据用户提供的条件搜索房源，支持价格、区域、面积、房间数量等条件",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "min_price": {
                            "type": "integer",
                            "description": "最低价格（元/月）"
                        },
                        "max_price": {
                            "type": "integer", 
                            "description": "最高价格（元/月）"
                        },
                        "region": {
                            "type": "string",
                            "description": "区域，如：雨花、岳麓、天心等"
                        },
                        "min_area": {
                            "type": "number",
                            "description": "最小面积（平方米）"
                        },
                        "max_area": {
                            "type": "number",
                            "description": "最大面积（平方米）"
                        },
                        "rooms": {
                            "type": "string",
                            "description": "房间配置，如：1室1厅、2室1厅、3室2厅等"
                        },
                        "rent_type": {
                            "type": "string",
                            "description": "租赁类型：整租 或 合租"
                        },
                        "subway": {
                            "type": "boolean",
                            "description": "是否需要近地铁"
                        },
                        "decoration": {
                            "type": "string",
                            "description": "装修情况：精装、简装、毛坯等"
                        }
                    }
                }
            },
            {
                "name": "get_house_details",
                "description": "获取特定房源的详细信息",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "house_id": {
                            "type": "integer",
                            "description": "房源ID"
                        }
                    },
                    "required": ["house_id"]
                }
            },
            {
                "name": "get_popular_houses",
                "description": "获取热门房源（按浏览量排序）",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "返回的房源数量，默认10个",
                            "default": 10
                        }
                    }
                }
            }
        ]

    def search_houses_by_criteria(self, **kwargs):
        """根据条件搜索房源"""
        try:
            query = db.session.query(HouseInfo).filter(HouseInfo.available == 1)
            
            # 价格筛选
            if kwargs.get('min_price'):
                query = query.filter(HouseInfo.price >= kwargs['min_price'])
            if kwargs.get('max_price'):
                query = query.filter(HouseInfo.price <= kwargs['max_price'])
            
            # 区域筛选
            if kwargs.get('region'):
                query = query.filter(HouseInfo.region.like(f"%{kwargs['region']}%"))
            
            # 面积筛选
            if kwargs.get('min_area'):
                query = query.filter(HouseInfo.area >= kwargs['min_area'])
            if kwargs.get('max_area'):
                query = query.filter(HouseInfo.area <= kwargs['max_area'])
            
            # 房间配置筛选
            if kwargs.get('rooms'):
                query = query.filter(HouseInfo.rooms.like(f"%{kwargs['rooms']}%"))
            
            # 租赁类型筛选
            if kwargs.get('rent_type'):
                query = query.filter(HouseInfo.rent_type == kwargs['rent_type'])
            
            # 地铁筛选
            if kwargs.get('subway'):
                query = query.filter(HouseInfo.subway == 1)
            
            # 装修情况筛选
            if kwargs.get('decoration'):
                query = query.filter(HouseInfo.decoration.like(f"%{kwargs['decoration']}%"))
            
            # 限制返回数量并按价格排序
            houses = query.order_by(HouseInfo.price.asc()).limit(20).all()
            
            return {
                "success": True,
                "houses": [house.to_dict() for house in houses],
                "count": len(houses)
            }
        except Exception as e:
            current_app.logger.error(f"Search houses error: {e}")
            return {"success": False, "error": str(e)}

    def get_house_details(self, house_id):
        """获取房源详细信息"""
        try:
            house = db.session.query(HouseInfo).filter(HouseInfo.id == house_id).first()
            if house:
                return {
                    "success": True,
                    "house": house.to_dict()
                }
            else:
                return {"success": False, "error": "房源不存在"}
        except Exception as e:
            current_app.logger.error(f"Get house details error: {e}")
            return {"success": False, "error": str(e)}

    def get_popular_houses(self, limit=10):
        """获取热门房源"""
        try:
            houses = db.session.query(HouseInfo)\
                .filter(HouseInfo.available == 1)\
                .order_by(HouseInfo.page_views.desc())\
                .limit(limit).all()
            
            return {
                "success": True,
                "houses": [house.to_dict() for house in houses],
                "count": len(houses)
            }
        except Exception as e:
            current_app.logger.error(f"Get popular houses error: {e}")
            return {"success": False, "error": str(e)}

    def execute_function_call(self, function_name, arguments):
        """执行函数调用"""
        if function_name == "search_houses_by_criteria":
            return self.search_houses_by_criteria(**arguments)
        elif function_name == "get_house_details":
            return self.get_house_details(arguments['house_id'])
        elif function_name == "get_popular_houses":
            return self.get_popular_houses(arguments.get('limit', 10))
        else:
            return {"success": False, "error": f"未知的函数: {function_name}"}

# 创建房产推荐机器人实例
house_bot = HouseRecommendationBot()


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

        history_records = db.session.query(ChatMessage) \
            .filter(ChatMessage.session_id == session_id) \
            .order_by(ChatMessage.id.desc()) \
            .limit(11).all()
        history_records.reverse()
        formatted_history = [{"role": msg.role, "content": msg.content} for msg in history_records[:-1]]

        ai_reply = my_agent.execute(user_message, history=formatted_history)

        assistant_msg = ChatMessage(session_id=session_id, role='assistant', content=ai_reply)
        db.session.add(assistant_msg)

        session_obj = db.session.query(ChatSession).get(session_id)
        if session_obj:
            session_obj.updated_at = db.func.now()

        db.session.commit()

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

        history_records = db.session.query(ChatMessage) \
            .filter(ChatMessage.session_id == session_id) \
            .order_by(ChatMessage.id.desc()) \
            .limit(11).all()
        history_records.reverse()
        formatted_history = [{"role": msg.role, "content": msg.content} for msg in history_records[:-1]]

        # 必须在进入流式生成器前 commit，确保 ChatSession 和用户消息已写入数据库
        # 否则 generate() 内部的新 db.session 会因外键约束失败
        db.session.commit()
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
# 4. 会话消息记录
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
# 5. 房源搜索（直接查询，不经过AI）
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
