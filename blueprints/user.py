import jwt
import datetime
from flask import Blueprint, request, current_app, g, send_from_directory # 引入 g
from sqlalchemy.exc import IntegrityError
from services.user_service import (get_user_by_email, get_user_by_name,
                                   get_user_by_id, get_user_by_phone)
from models.user_model import UserModel
from exts import db
from utils.response_utils import success_response, error_response, Code
from decorators.decorators import token_required
import random
from exts.redis import redis_store, is_redis_available
from blueprints.celery_bp import send_verification_email, send_verification_email_up
import os
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename

user = Blueprint("user", __name__, url_prefix="/user")

@user.route("/register", methods=["POST"])
def register():
    """
    用户注册接口
    :接收: phone(手机号), password(密码), email(邮箱)
    :返回: 注册成功或失败信息
    :说明: 检查手机号和邮箱是否已注册，密码会自动哈希加密存储
    """
    phone = request.form.get('phone')
    password = request.form.get('password')
    email = request.form.get('email')

    if not phone or not password:
        # 修正点：使用 message 参数，并传入正确的 Code
        return error_response(code=Code.BAD_REQUEST, message="手机号和密码不能为空")
    if not email:
        return error_response(code=Code.BAD_REQUEST, message="邮箱不能为空")

    if UserModel.query.filter_by(phone=phone).first():
        # 修正点：使用 message 参数
        return error_response(code=Code.GET_ERR, message="注册失败，该手机号已被注册")
    if UserModel.query.filter_by(email=email).first():
        return error_response(code=Code.GET_ERR, message="注册失败，该邮箱已被注册")

    try:
        new_user = UserModel(phone=phone)
        new_user.set_password(password)
        new_user.email = email
        new_user.userType = 1
        db.session.add(new_user)
        db.session.commit()
        # 修正点：使用 message 参数
        return success_response(code=Code.SAVE_OK, message="注册成功！") # 这里 data 为 None，会自动省略
    except IntegrityError:
        db.session.rollback()
        # 修正点：使用 message 参数
        return error_response(code=Code.UPDATE_ERR, message="数据库唯一性约束冲突，该手机号可能已被注册")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Register error: {e}")
        # 修正点：使用 message 参数
        return error_response(code=Code.INTERNAL_SERVER_ERROR, message="服务器内部错误")

@user.route("/login", methods=["POST"])
def login():
    """
    手机号+密码登录接口
    :接收: phone(手机号), password(密码)
    :返回: JWT token，有效期24小时
    """
    phone = request.form.get('phone')
    password = request.form.get('password')

    if not phone or not password:
        return error_response(code=Code.BAD_REQUEST, message="手机号和密码不能为空")

    user_model = UserModel.query.filter_by(phone=phone).first()

    if user_model and user_model.check_password(password):
        token_payload = {
            'user_id': user_model.id,
            'phone': user_model.phone,
            'type': user_model.userType,
            'exp': datetime.utcnow() + timedelta(hours=24)
        }
        token = jwt.encode(token_payload, current_app.config['SECRET_KEY'], algorithm="HS256")

        # 修正点：将 token 放入 data 字典中返回，并使用 message 参数
        return success_response(code=Code.SAVE_OK, data={"token": token}, message="登录成功")
    else:
        # 修正点：使用 message 参数
        return error_response(code=Code.UNAUTHORIZED, message="登录失败，手机号或密码错误")


@user.route("/email-login", methods=["POST"])
def email_login():
    """
    邮箱+密码登录接口
    :接收: email(邮箱), password(密码)
    :返回: JWT token，有效期24小时
    """
    email = request.form.get('email')
    password = request.form.get('password')

    if not email or not password:
        return error_response(code=Code.BAD_REQUEST, message="邮箱和密码不能为空")

    user_model = UserModel.query.filter_by(email=email).first()

    if user_model and user_model.check_password(password):
        token_payload = {
            'user_id': user_model.id,
            'phone': user_model.phone,
            'email': user_model.email,
            'type': user_model.userType,
            'exp': datetime.utcnow() + timedelta(hours=24)
        }
        token = jwt.encode(token_payload, current_app.config['SECRET_KEY'], algorithm="HS256")

        return success_response(code=Code.SAVE_OK, data={"token": token}, message="邮箱登录成功")
    else:
        return error_response(code=Code.UNAUTHORIZED, message="登录失败，邮箱或密码错误")


@user.route("/userinfo", methods=["GET"])
@token_required
def userinfo():
    """
    获取当前登录用户信息
    :需要: Authorization请求头中携带token
    :返回: 用户基本信息（不含密码）
    """
    current_user = g.user
    # 修正点：使用 message 参数
    return success_response(code=Code.GET_OK, data=current_user.to_dict(), message="获取用户信息成功")

# 根据用户名获取用户
@user.route("/userinfo/<string:name>", methods=["GET"])
def get_user_by_username(name):
    """
    根据用户名查询用户信息
    :param name: 用户名
    :返回: 用户基本信息
    """
    user = get_user_by_name(name)

    if user is None:
        return error_response(code=Code.GET_ERR, message="无该用户")

    return success_response(code=Code.GET_OK, data=user.to_dict(), message="获取成功")

# 用户密码修改接口,通过id修改
@user.route("/userinfo/password", methods=["PUT"])
@token_required
def userinfo_password():
    """
    根据用户ID修改密码
    :接收: id(用户ID), password(新密码)
    :返回: 更新成功或失败信息
    """
    data = request.json
    if not data:
        return error_response(code=Code.BAD_REQUEST, message="密码不能为空")

    password = data.get('password')
    if not password:
        return error_response(code=Code.BAD_REQUEST, message="Password cannot be empty")
    current_user = g.user

    try:
        # 设置新密码
        current_user.set_password(password)
        # 提交数据库更改
        db.session.commit()
        return success_response(code=Code.UPDATE_OK, message="密码更新成功")
    except IntegrityError:
        db.session.rollback()
        return error_response(code=Code.UPDATE_ERR, message="数据库唯一性约束冲突，更新失败")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Update user password error: {e}")
        return error_response(code=Code.INTERNAL_SERVER_ERROR, message="服务器内部错误")

# 根据手机号返回用户
@user.route("/userinfo/phone", methods=["GET"])
@token_required
def userinfo_phone():
    """
    根据手机号查询用户信息
    :接收: phone(手机号)
    :需要: Authorization请求头中携带token
    :返回: 用户基本信息
    """
    data = request.json
    if not data:
        return error_response(code=Code.BAD_REQUEST, message="请求数据不能为空")

    phone = data.get('phone')
    current_user = get_user_by_phone(phone)

    if current_user is None:
        return error_response(code=Code.GET_ERR, message="不存在该用户")

    return success_response(code=Code.GET_OK, data=current_user.to_dict(), message="返回成功")

# 用户信息修改接口，修改部分内容
@user.route("/userinfo", methods=["PUT"])
@token_required
def userinfo_update():
    """
    更新用户基本信息
    :接收: id, name, addr, email, identityCard, phone
    :说明: 身份证号一旦填写不可更改，允许修改的字段有限
    :返回: 更新后的用户信息
    """
    data = request.json
    if not data:
        return error_response(code=Code.BAD_REQUEST, message="请求数据不能为空")

    current_user = g.user

    if not current_user:
        return error_response(code=Code.NOT_FOUND, message="用户不存在")

    # 身份证号处理逻辑
    if 'identityCard' in data:
        new_identity_card = data['identityCard']
        existing_identity_card = current_user.identityCard

        # 已经填写过，不能更改（除非是重复提交相同值）
        if existing_identity_card is not None:
            if new_identity_card != existing_identity_card:
                return error_response(code=Code.UPDATE_ERR, message="您已填写过身份证号，不可更改")
        else:
            # 首次填写，校验长度
            if not new_identity_card or len(new_identity_card) != 18:
                return error_response(code=Code.UPDATE_ERR, message="身份证号不能为空，且长度必须为18位")

    # 定义允许修改的字段
    allowed_fields = ['name', 'addr', 'email', 'identityCard', 'phone']

    try:
        for key in allowed_fields:
            if key in data and hasattr(current_user, key):
                setattr(current_user, key, data[key])

        db.session.commit()
        return success_response(code=Code.UPDATE_OK, data=current_user.to_dict(), message="用户信息更新成功")

    except IntegrityError:
        db.session.rollback()
        return error_response(code=Code.UPDATE_ERR, message="数据库唯一性约束冲突，更新失败")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Update user info error: {e}")
        return error_response(code=Code.INTERNAL_SERVER_ERROR, message="服务器内部错误")


# 修改，使用celery异步实现发送邮件验证码
@user.route("/userinfo/password", methods=["POST"])
def password_reset():
    """
    发送密码重置邮箱验证码
    :接收: email(邮箱)
    :说明: 生成6位验证码存入Redis，有效期2分钟，通过Celery异步发送邮件
    :返回: 验证码发送状态
    """
    data = request.json
    if not data:
        return error_response(code=Code.BAD_REQUEST, message="请求数据不能为空")

    email = data.get('email')
    newuser = get_user_by_email(email)
    if newuser is None:
        return error_response(code=Code.GET_ERR, message="不存在该用户")

    if not is_redis_available():
        return error_response(code=Code.INTERNAL_SERVER_ERROR,
                              message="验证码服务暂不可用，请稍后重试")

    verification_code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
    redis_key = f'password_reset_code:{email}'
    redis_store.set(redis_key, verification_code, ex=120)

    # 异步调用
    send_verification_email.delay(email, verification_code)
    # Do not expose reset credentials in the response body.
    verification_code = None

    return success_response(data=verification_code, message="验证码发送中，请查收邮件", code=200)

# 成为房东的验证码
@user.route("/userinfo/tolanlord", methods=["POST"])
def tolanlord():
    """
    发送申请成为房东的邮箱验证码
    :接收: email(邮箱)
    :说明: 生成6位验证码存入Redis，有效期2分钟，通过Celery异步发送邮件
    :返回: 验证码发送状态
    """
    data = request.json
    if not data:
        return error_response(code=Code.BAD_REQUEST, message="请求数据不能为空")

    email = data.get('email')
    newuser = get_user_by_email(email)
    if newuser is None:
        return error_response(code=Code.GET_ERR, message="不存在该用户")

    if not is_redis_available():
        return error_response(code=Code.INTERNAL_SERVER_ERROR,
                              message="验证码服务暂不可用，请稍后重试")

    verification_code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
    redis_key = f'verification_code:{email}'
    redis_store.set(redis_key, verification_code, ex=120)

    # 异步调用
    send_verification_email_up.delay(email, verification_code)

    return success_response(data=verification_code, message="验证码发送中，请查收邮件", code=200)

# 根据邮箱改密码
@user.route('/userinfo/password_e', methods=['PUT'])
def userinfo_password_e():
    """
    根据邮箱修改密码（用于忘记密码场景）
    :接收: email(邮箱), password(新密码)
    :返回: 更新成功或失败信息
    """
    data = request.json
    if not data:
        return error_response(code=Code.BAD_REQUEST, message="密码不能为空")

    password = data.get('password')
    email = data.get('email')
    verification_code = data.get('code')
    if not email or not password or not verification_code:
        return error_response(code=Code.BAD_REQUEST, message="email, password and code are required")
    if not is_redis_available():
        return error_response(code=Code.INTERNAL_SERVER_ERROR, message="Verification service unavailable")
    redis_key = f'password_reset_code:{email}'
    stored_code = redis_store.get(redis_key)
    if not stored_code or stored_code.decode('utf-8') != str(verification_code):
        return error_response(code=Code.UNAUTHORIZED, message="Invalid or expired verification code")

    current_user = get_user_by_email(email)
    if not current_user:
        return error_response(code=Code.NOT_FOUND, message="User not found")

    try:
        # 设置新密码
        current_user.set_password(password)
        # 提交数据库更改
        db.session.commit()
        redis_store.delete(redis_key)
        return success_response(code=Code.UPDATE_OK, message="密码更新成功")
    except IntegrityError:
        db.session.rollback()
        return error_response(code=Code.UPDATE_ERR, message="数据库唯一性约束冲突，更新失败")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Update user password error: {e}")
        return error_response(code=Code.INTERNAL_SERVER_ERROR, message="服务器内部错误")


# 改变userType
@user.route("/userinfo/usertype", methods=["PUT"])
def to_landlord():
    """
    将普通用户升级为房东
    :接收: email(邮箱)
    :说明: userType从1改为2，需要前端先验证邮箱验证码
    :返回: 更新后的用户信息
    """
    data = request.json
    if not data:
        return error_response(code=Code.BAD_REQUEST, message="请求数据不能为空")

    email = data.get('email')
    newuser = get_user_by_email(email)

    if newuser is None:
        return error_response(code=Code.GET_ERR, message="不存在该用户")

    user = newuser.to_dict()
    if user['userType'] == 1:
        newuser.userType = 2
        db.session.add(newuser)
        db.session.commit()
        return success_response(data=newuser.to_dict(), message="已成为房东", code=200)
    else:
        db.session.rollback()
        return error_response(code=Code.UPDATE_ERR, message="修改错误")

# 获取avatarUrl
@user.route("/userinfo/avatar", methods=["GET"])
def get_avatar():
    """
    根据用户ID获取头像URL
    :接收: id(查询参数，用户ID)
    :返回: 包含avatarUrl的用户信息
    """
    id = request.args.get('id')  # 改为获取查询参数
    if not id:
        return error_response(code=Code.BAD_REQUEST, message="用户ID不能为空")

    user = get_user_by_id(id)

    if user is None:
        return error_response(code=Code.GET_ERR, message="不存在该用户")

    user1 = user.to_dict()

    if user1['avatarUrl'] is None:
        return error_response(code=Code.GET_ERR, message="该用户无头像")
    else:
        return success_response(data=user1, message="获取成功", code=200)

# 保存用户上传头像，并处理成url
@user.route("/userinfo/avatarurl", methods=["POST"])
def add_avatar():
    """
    上传用户头像到本地服务器
    :接收: userId(表单), avatar(图片文件)
    :说明: 将图片保存到项目根目录的images文件夹，生成本地URL存入数据库
    :返回: 新头像的访问URL
    """
    user_id = request.form.get("userId")  # 注意这里是 userId 而不是 id
    file = request.files.get("avatar")

    if not user_id or not file:
        return error_response(code=400, message="缺少用户ID或头像文件")

    user = get_user_by_id(user_id)
    if not user:
        return error_response(code=404, message="用户不存在")

    # 设定 images 目录路径（项目根目录下）
    project_root = os.path.abspath(os.path.dirname(__file__))
    images_folder = os.path.join(project_root, '..', 'images')
    os.makedirs(images_folder, exist_ok=True)

    # 构造唯一文件名
    ext = os.path.splitext(file.filename)[1]
    filename = secure_filename(f"{user_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}{ext}")
    filepath = os.path.join(images_folder, filename)
    file.save(filepath)

    # 构造相对 URL，用于前端显示
    avatar_url = f"http://localhost:5000/user/images/{filename}"

    # 保存到数据库
    user.avatarUrl = avatar_url
    db.session.commit()

    return success_response(data={"avatarUrl": avatar_url}, message="头像上传成功", code=200)

# 提供images目录下的静态访问
@user.route('/images/<filename>')
def serve_image(filename):
    """
    提供本地图片的静态访问服务
    :param filename: 图片文件名
    :返回: 图片文件内容
    """
    project_root = os.path.abspath(os.path.dirname(__file__))
    images_folder = os.path.join(project_root, '..', 'images')
    return send_from_directory(images_folder, filename)
