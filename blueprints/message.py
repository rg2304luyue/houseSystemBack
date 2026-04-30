from flask import Blueprint, request, jsonify, current_app
from services.message_service import (
    get_messages_by_sender,
    create_message,
    get_messages_by_channel,
    get_messages_by_receiver,
    get_messages_between_users
)
from services.channel_service import get_channel
from services.user_service import get_user_by_id
from decorators.decorators import token_required
from socketio_init import socketio
from flask_socketio import join_room, leave_room
from utils.response_utils import success_response, error_response, Code
import jwt
import logging
from functools import wraps

logger = logging.getLogger(__name__)

message_bp = Blueprint("message", __name__, url_prefix="/comments")

# sid -> username 映射，用于 Socket.IO 事件中获取已认证用户
_authenticated_sockets: dict[str, str] = {}


# ──────────── REST API ────────────

def handle_errors(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValueError as e:
            logger.exception("输入参数错误")
            return jsonify({
                "status": "error",
                "message": "输入参数错误",
                "detail": str(e)
            }), 400
        except Exception as e:
            logger.exception("服务器内部错误")
            return jsonify({
                "status": "error",
                "message": "服务器内部错误",
                "detail": str(e)
            }), 500
    return wrapper


@message_bp.route("/messages", methods=["GET"])
@handle_errors
def get_messages():
    """获取消息列表，支持 sender / receiver / user1+user2 三种查询"""
    sender = request.args.get('sender')
    user1 = request.args.get('user1')
    user2 = request.args.get('user2')
    receiver = request.args.get('receiver')

    if sender and receiver and sender == receiver:
        return error_response(code=Code.GET_ERR, message="发送者和接收者不能是同一个人")
    if user1 and user2 and user1 == user2:
        return error_response(code=Code.GET_ERR, message="不能与自己进行对话")

    if sender:
        messages = get_messages_by_sender(sender)
    elif receiver:
        messages = get_messages_by_receiver(receiver)
    elif user1 and user2:
        messages = get_messages_between_users(user1, user2)
    else:
        return jsonify({
            "status": "error",
            "message": "必须提供sender/receiver参数或user1和user2参数"
        }), 400

    return success_response(data={"messages": [msg.to_dict() for msg in messages]})


@message_bp.route("/messages", methods=["POST"])
@token_required
@handle_errors
def post_message():
    """通过 REST 发送消息（备用通道）"""
    if not request.is_json:
        return error_response(code=Code.BAD_REQUEST, message="请求必须为JSON格式")

    data = request.get_json()
    required_fields = ['content', 'sender_username', 'receiver_username']
    if not all(field in data for field in required_fields):
        return error_response(
            code=Code.BAD_REQUEST,
            message=f"缺少必要字段，需要: {', '.join(required_fields)}"
        )

    sender = data['sender_username']
    receiver = data['receiver_username']
    channel = get_channel(sender, receiver)
    new_message = create_message(
        content=data['content'],
        sender_username=sender,
        receiver_username=receiver,
        channel_id=channel.channel_id
    )

    socketio.emit('new_message', new_message.to_dict(), room=f'channel_{channel.channel_id}')

    return success_response(data={"message": new_message.to_dict()}, code=201)


@message_bp.route("/messages/<string:sender_username>", methods=["GET"])
@handle_errors
def get_sender_message(sender_username):
    messages = get_messages_by_sender(sender_username)
    return success_response(data={"messages": [msg.to_dict() for msg in messages]})


@message_bp.route("/messages/receiver/<string:receiver_username>", methods=["GET"])
@handle_errors
def get_receiver_message(receiver_username):
    messages = get_messages_by_receiver(receiver_username)
    return success_response(data={"messages": [msg.to_dict() for msg in messages]})


# ──────────── Socket.IO 事件 ────────────

@socketio.on('connect')
def handle_connect():
    logger.info(f"Socket 连接: {request.sid}")


@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    _authenticated_sockets.pop(sid, None)
    logger.info(f"Socket 断开: {sid}")


@socketio.on('authenticate')
def handle_authenticate(data):
    """客户端连接后发送 token 进行认证"""
    token = data.get('token') if data else None
    if not token:
        return {'status': 'error', 'message': '缺少认证token'}

    try:
        payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
        user = get_user_by_id(payload['user_id'])
        if not user:
            return {'status': 'error', 'message': '用户不存在'}

        _authenticated_sockets[request.sid] = user.name
        logger.info(f"Socket 认证成功: sid={request.sid}, user={user.name}")
        return {'status': 'ok', 'username': user.name}
    except jwt.ExpiredSignatureError:
        return {'status': 'error', 'message': 'Token已过期'}
    except jwt.InvalidTokenError:
        return {'status': 'error', 'message': 'Token无效'}
    except Exception as e:
        logger.exception("认证异常")
        return {'status': 'error', 'message': f'认证失败: {str(e)}'}


@socketio.on('join_chat')
def handle_join_chat(data):
    """加入与指定用户的聊天房间"""
    other_username = data.get('other_username') if data else None
    username = _authenticated_sockets.get(request.sid)
    if not username:
        return {'status': 'error', 'message': '未认证'}
    if not other_username:
        return {'status': 'error', 'message': '缺少对方用户名'}

    try:
        channel = get_channel(username, other_username)
        room = f'channel_{channel.channel_id}'
        join_room(room)
        logger.info(f"{username} 加入房间 {room}")
        return {'status': 'ok', 'channel_id': channel.channel_id, 'room': room}
    except Exception as e:
        logger.exception("加入聊天失败")
        return {'status': 'error', 'message': f'加入聊天失败: {str(e)}'}


@socketio.on('leave_chat')
def handle_leave_chat(data):
    """离开聊天房间"""
    username = _authenticated_sockets.get(request.sid)
    if not data or not username:
        return {'status': 'error', 'message': '参数错误'}

    other_username = data.get('other_username')
    if not other_username:
        return {'status': 'error', 'message': '缺少对方用户名'}

    try:
        channel = get_channel(username, other_username)
        room = f'channel_{channel.channel_id}'
        leave_room(room)
        return {'status': 'ok'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


@socketio.on('send_message')
def handle_send_message(data):
    """接收客户端消息 → 持久化 → 仅广播给该 channel 房间"""
    sid = request.sid
    username = _authenticated_sockets.get(sid)
    if not username:
        return {'status': 'error', 'message': '未认证'}

    receiver = data.get('receiver_username') if data else None
    content = data.get('content') if data else None

    if not receiver or not content:
        return {'status': 'error', 'message': '缺少 receiver_username 或 content'}

    try:
        channel = get_channel(username, receiver)
        new_message = create_message(
            content=content,
            sender_username=username,
            receiver_username=receiver,
            channel_id=channel.channel_id
        )
        room = f'channel_{channel.channel_id}'
        socketio.emit('new_message', new_message.to_dict(), room=room, skip_sid=sid)

        return {
            'status': 'ok',
            'message_id': new_message.message_id,
            'timestamp': new_message.timestamp.isoformat() + "Z"
        }
    except Exception as e:
        logger.exception("发送消息失败")
        return {'status': 'error', 'message': f'发送失败: {str(e)}'}
