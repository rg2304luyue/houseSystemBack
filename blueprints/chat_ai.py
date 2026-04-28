from flask import Blueprint, request, current_app, jsonify
import json
from core.agent.react_agent import ReactAgent
from models.house_model import HouseInfo
from exts.db import db
from utils.response_utils import success_response, error_response, Code
from decorators.decorators import token_required
from flask import g
from models.models import ChatSession, ChatMessage

chat_ai_bp = Blueprint('chat_ai', __name__, url_prefix='/chat-ai')
my_agent = ReactAgent()

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
@token_required  # 必须确保加了这一行
def chat_with_ai():
    try:
        # 【安全拦截】检查装饰器是否成功把 user 塞进来了
        if not hasattr(g, 'user') or not g.user:
            return error_response(code=Code.UNAUTHORIZED, message="身份校验失败，请重新登录")

        # 【兼容处理】判断 g.user 是数据库对象还是字典 (防止报错)
        if isinstance(g.user, dict):
            current_user_id = g.user.get('id')
        else:
            current_user_id = getattr(g.user, 'id', None)

        if not current_user_id:
            return error_response(code=Code.INTERNAL_SERVER_ERROR, message="无法获取当前用户ID")

        data = request.get_json()
        user_message = data.get('message', '')
        session_id = data.get('session_id')

        if not user_message:
            return error_response(code=Code.BAD_REQUEST, message="消息内容不能为空")

        # 1. 如果没有 session_id，创建新会话
        if not session_id:
            title = user_message[:15] + "..." if len(user_message) > 15 else user_message
            new_session = ChatSession(user_id=current_user_id, title=title)
            db.session.add(new_session)
            db.session.flush()
            session_id = new_session.id

        # 2. 将用户的消息存入数据库
        user_msg = ChatMessage(session_id=session_id, role='user', content=user_message)
        db.session.add(user_msg)
        db.session.flush()

        # 3. 让后端自己去查历史记录（只查当前会话的最近10条，防止Token爆炸）
        history_records = db.session.query(ChatMessage) \
            .filter(ChatMessage.session_id == session_id) \
            .order_by(ChatMessage.id.desc()) \
            .limit(11).all()  # 取11条是因为包含刚才用户发的那条

        history_records.reverse()  # 因为是倒序查的，所以要反转回正序

        # 组装成 LangChain 需要的格式 (刨除最后一条用户刚发的消息，因为 execute 会自动把当前问题加进去)
        formatted_history = [{"role": msg.role, "content": msg.content} for msg in history_records[:-1]]

        # 4. 呼叫大模型 Agent
        ai_reply = my_agent.execute(user_message, history=formatted_history)

        # 5. 将大模型的回复存入数据库
        assistant_msg = ChatMessage(session_id=session_id, role='assistant', content=ai_reply)
        db.session.add(assistant_msg)

        # 6. 触发会话表的 updated_at 更新（方便前端按时间排序聊天列表）
        session_obj = db.session.query(ChatSession).get(session_id)
        if session_obj:
            session_obj.updated_at = db.func.now()

        db.session.commit()  # 统一提交所有操作

        # 7. 返回结果给前端，一定要带上 session_id，让前端知道现在聊的是哪个窗口
        return success_response(
            code=Code.GET_OK,
            data={
                "reply": ai_reply,
                "session_id": session_id
            },
            message="对话成功"
        )

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Chat AI error: {e}")
        return error_response(code=Code.INTERNAL_SERVER_ERROR, message=f"AI对话失败: {str(e)}")

# ----------------- 2. 获取用户的历史会话列表 -----------------
@chat_ai_bp.route('/sessions', methods=['GET'])
@token_required
def get_sessions():
    # 只查询属于当前登录用户的会话
    sessions = db.session.query(ChatSession).filter_by(user_id=g.user.id)\
        .order_by(ChatSession.updated_at.desc()).all()
    return success_response(code=Code.GET_OK, data=[s.to_dict() for s in sessions])


# ----------------- 3. 获取某个会话的具体聊天记录 -----------------
@chat_ai_bp.route('/sessions/<int:session_id>/messages', methods=['GET'])
def get_session_messages(session_id):
    try:
        messages = db.session.query(ChatMessage).filter_by(session_id=session_id) \
            .order_by(ChatMessage.id.asc()).all()

        return success_response(code=Code.GET_OK, data=[m.to_dict() for m in messages])
    except Exception as e:
        return error_response(code=Code.INTERNAL_SERVER_ERROR, message=str(e))

@chat_ai_bp.route('/houses/search', methods=['POST'])
def search_houses():
    """
    直接按条件搜索房源（不经过AI）
    :接收: min_price, max_price, region, min_area, max_area,
           rooms, rent_type, subway, decoration
    :返回: 符合条件的房源列表（按价格升序，最多20条）
    """
    try:
        data = request.get_json()
        result = house_bot.search_houses_by_criteria(**data)
        
        if result['success']:
            return success_response(
                code=Code.GET_OK,
                data=result,
                message="房源搜索成功"
            )
        else:
            return error_response(
                code=Code.INTERNAL_SERVER_ERROR,
                message=result['error']
            )
    except Exception as e:
        current_app.logger.error(f"Search houses API error: {e}")
        return error_response(
            code=Code.INTERNAL_SERVER_ERROR,
            message=f"搜索失败: {str(e)}"
        )

@chat_ai_bp.route('/houses/<int:house_id>', methods=['GET'])
def get_house_detail(house_id):
    """
    获取单个房源详情（供AI函数调用）
    :param house_id: 房源ID
    :返回: 房源详细信息
    """
    try:
        result = house_bot.get_house_details(house_id)
        
        if result['success']:
            return success_response(
                code=Code.GET_OK,
                data=result,
                message="获取房源详情成功"
            )
        else:
            return error_response(
                code=Code.NOT_FOUND,
                message=result['error']
            )
    except Exception as e:
        current_app.logger.error(f"Get house detail API error: {e}")
        return error_response(
            code=Code.INTERNAL_SERVER_ERROR,
            message=f"获取详情失败: {str(e)}"
        )

@chat_ai_bp.route('/houses/popular', methods=['GET'])
def get_popular_houses():
    """
    获取热门房源列表（按浏览量排序）
    :接收: limit(查询参数，返回数量，默认10)
    :返回: 热门房源列表
    """
    try:
        limit = request.args.get('limit', 10, type=int)
        result = house_bot.get_popular_houses(limit)
        
        if result['success']:
            return success_response(
                code=Code.GET_OK,
                data=result,
                message="获取热门房源成功"
            )
        else:
            return error_response(
                code=Code.INTERNAL_SERVER_ERROR,
                message=result['error']
            )
    except Exception as e:
        current_app.logger.error(f"Get popular houses API error: {e}")
        return error_response(
            code=Code.INTERNAL_SERVER_ERROR,
            message=f"获取热门房源失败: {str(e)}"
        ) 