# app/routes/house_info_routes.py
from collections import defaultdict
from flask import Blueprint, request, current_app
from models.house_model import HouseInfo  # , SessionLocal # 如果不使用Flask-SQLAlchemy
from utils.response_utils import success_response, error_response, Code
from sqlalchemy.exc import SQLAlchemyError
import datetime
# 如果使用 Flask-SQLAlchemy
from exts import db
from sqlalchemy import or_, func
from services.house_info_service import (get_housenum, get_house_by_views,
                                         get_house_hot_list, get_house_new_list,
                                         add_views_by_id, get_house_by_landlord,
                                         get_house_rental)
from exts.redis import  RedisCache
import json
import re
house_info_bp = Blueprint('houseinfo', __name__,url_prefix="/houseinfo")

def get_db_session():
    return db.session

#1.1房源总数接口
@house_info_bp.route('/houseNums', methods=['GET'])
def get_housenums():
    """
    获取数据库中房源总数
    :返回: 房源总数量
    """
    house_total_num=HouseInfo.query.count()
    return success_response(house_total_num)

#1.2热点房源
@house_info_bp.route('/hotLists', methods=['GET'])
def get_hotlists():
    """
    获取浏览量最高的前4条热门房源
    :说明: 结果缓存到Redis，有效期5分钟
    :返回: 热门房源列表
    """
    # 构建缓存键
    cache_key = 'house_hot_lists'

    # 检查缓存
    cached_data = RedisCache.get_cache(cache_key)
    if cached_data:
        return success_response(cached_data)

    current_app.logger.debug("hotlists无缓存")

    house_hot_List=HouseInfo.query.order_by(HouseInfo.page_views.desc()).limit(4).all()
    data = [a.to_dict() for a in house_hot_List]

    # 将查询结果存入 Redis 缓存
    RedisCache.set_cache(cache_key, data)
    return success_response(data)

#1.3最新房源
@house_info_bp.route('/newLists', methods=['GET'])
def get_newlists():
    """
    获取最新发布的前4条房源
    :说明: 结果缓存到Redis，有效期5分钟
    :返回: 最新房源列表
    """
    # 构建缓存键
    cache_key = 'house_new_lists'

    # 检查缓存
    cached_data = RedisCache.get_cache(cache_key)
    if cached_data:
        return success_response(cached_data)

    current_app.logger.debug("newlists无缓存")

    house_info_num=HouseInfo.query.count()
    #获取前六条数据
    house_new_list=HouseInfo.query.order_by(HouseInfo.publish_time.desc()).limit(4).all()
    data = [a.to_dict() for a in house_new_list]

    # 将查询结果存入缓存
    RedisCache.set_cache(cache_key, data)
    return success_response(data)

# 1. 新增房源信息 (对应房东发布房源)
@house_info_bp.route('/', methods=['POST'])
def add_house_info():
    """
    发布新房源
    :接收: title, region, community, area, rooms, price, rent_type等必填字段
    :说明: 布尔字段subway/available/tag_new转为0/1存储，发布时间默认当天
    :返回: 创建成功的房源信息
    """
    data = request.get_json()
    if not data:
        return error_response("请求体不能为空", code=Code.BAD_REQUEST)

    # 基本的数据校验 (可以做得更完善，例如使用 Pydantic)
    required_fields = ['title', 'region', 'community', 'area', 'rooms', 'price', 'rent_type']
    for field in required_fields:
        if field not in data or data[field] is None:  # 确保字段存在且不为None (除非模型允许)
            return error_response(f"缺少必填字段: {field}", code=Code.BAD_REQUEST)

    # 处理日期
    if 'publish_time' in data and isinstance(data['publish_time'], str):
        try:
            data['publish_time'] = datetime.date.fromisoformat(data['publish_time'])
        except ValueError:
            return error_response("日期格式错误，应为 YYYY-MM-DD", code=Code.BAD_REQUEST)
    elif 'publish_time' not in data:  # 如果前端不传，可以设置为当前日期
        data['publish_time'] = datetime.date.today()

    # 处理布尔型字段 (TINYINT(1))
    bool_fields = ['subway', 'available', 'tag_new']
    for field in bool_fields:
        if field in data:
            data[field] = 1 if data[field] else 0
        # else: # 如果前端不传，模型中的server_default会生效
        #     data[field] = HouseInfo.__table__.columns[field].server_default.arg.text.strip("'") # 获取默认值

    new_house = HouseInfo(**data)

    session = get_db_session()
    try:
        session.add(new_house)
        session.commit()
        session.refresh(new_house)  # 获取自动生成的ID等
        RedisCache.delete_cache('house_new_lists')
        RedisCache.delete_cache('house_hot_lists')
        RedisCache.delete_by_prefix('all_house_infos:')

        return success_response(data=new_house.to_dict(), message="房源信息添加成功", code=Code.SAVE_OK)
    except SQLAlchemyError as e:
        session.rollback()
        current_app.logger.error(f"添加房源失败: {e}")
        return error_response(f"数据库错误: {str(e)}", code=Code.INTERNAL_SERVER_ERROR)
    except Exception as e:
        session.rollback()
        current_app.logger.error(f"添加房源时发生未知错误: {e}")
        return error_response(f"添加房源失败: {str(e)}", code=Code.INTERNAL_SERVER_ERROR)


# 2. 查询所有房源信息 / 搜索房源 (对应房源展示首页和搜索)
@house_info_bp.route('/', methods=['GET'])
def get_all_house_infos():
    """
    获取房源列表，支持多条件筛选和分页
    :接收查询参数:
        - page/per_page: 分页参数
        - region: 区域（支持逗号分隔多选，OR逻辑）
        - community: 小区名关键词
        - rooms: 户型（支持一居/两居/三居/四居/四居+）
        - orientation: 朝向（支持多选）
        - min_price/max_price: 价格范围
        - rent_type: 整租或合租
        - subway: 是否近地铁（0/1）
        - decoration: 装修情况
        - available: 是否上架
    :说明: 结果缓存到Redis
    :返回: 分页房源列表及总数
    """
    session = get_db_session()
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)  # 每页数量，前端可控

        # 构建缓存键（不含 page，缓存完整查询结果，所有分页共用同一缓存）
        cache_key = 'all_house_infos'
        for key in sorted(request.args.keys()):
            if key not in ['page', 'per_page']:
                cache_key += f':{key}:{request.args[key]}'

        # 检查缓存（返回完整结果集，由代码分页）
        cached_data = RedisCache.get_cache(cache_key)
        if cached_data:
            all_items = cached_data['items']
            total = cached_data['total']
            start = (page - 1) * per_page
            end = start + per_page
            paged_items = all_items[start:end]

            response_data = {
                "items": paged_items,
                "total": total,
                "page": page,
                "per_page": per_page,
                "pages": (total + per_page - 1) // per_page
            }
            return success_response(data=response_data, message="查询成功", code=Code.GET_OK)

        current_app.logger.debug("houseinfo获取所有房源无缓存")

        # 构建查询
        query = session.query(HouseInfo)

        # ----- 智能搜索/过滤条件 -----
        # 按地区搜索 (改进以支持逗号分隔的多选 "OR" 逻辑)
        if 'region' in request.args and request.args['region']:
            regions_to_filter = [r.strip() for r in request.args['region'].split(',') if r.strip()]
            if regions_to_filter:
                region_conditions = [HouseInfo.region.ilike(f"%{r}%") for r in regions_to_filter]
                query = query.filter(or_(*region_conditions))

        if 'block' in request.args and request.args['block']:  # block 通常是单选或作为 community 搜索的一部分
            query = query.filter(HouseInfo.block.ilike(f"%{request.args['block']}%"))

        if 'community' in request.args and request.args['community']:  # 主搜索框
            query = query.filter(HouseInfo.community.ilike(f"%{request.args['community']}%"))

        # 按户型搜索 (改进以支持逗号分隔的多选 "OR" 逻辑)
        if 'rooms' in request.args and request.args['rooms']:
            raw_room_filters = [r.strip() for r in request.args['rooms'].split(',') if r.strip()]

            if raw_room_filters:
                individual_room_type_conditions = []

                for room_filter_text in raw_room_filters:
                    if room_filter_text == '一居':
                        individual_room_type_conditions.append(HouseInfo.rooms.ilike("1室%"))
                    elif room_filter_text == '两居':
                        individual_room_type_conditions.append(HouseInfo.rooms.ilike("2室%"))
                    elif room_filter_text == '三居':
                        individual_room_type_conditions.append(HouseInfo.rooms.ilike("3室%"))
                    elif room_filter_text == '四居':
                        individual_room_type_conditions.append(HouseInfo.rooms.ilike("4室%"))
                    elif room_filter_text == '四居+':
                        plus_conditions = []
                        for i in range(4, 10):
                            plus_conditions.append(HouseInfo.rooms.ilike(f"{i}室%"))
                        if plus_conditions:
                            individual_room_type_conditions.append(or_(*plus_conditions))

                if individual_room_type_conditions:
                    query = query.filter(or_(*individual_room_type_conditions))

        # 按朝向搜索
        if 'orientation' in request.args and request.args['orientation']:
            orientations_to_filter = [o.strip() for o in request.args['orientation'].split(',') if o.strip()]
            if orientations_to_filter:
                orientation_conditions = [HouseInfo.direction.ilike(f"%{o}%") for o in orientations_to_filter]
                query = query.filter(or_(*orientation_conditions))

        # 按价格范围
        if 'min_price' in request.args:
            try:
                query = query.filter(HouseInfo.price >= int(request.args['min_price']))
            except ValueError:
                pass
        if 'max_price' in request.args:
            try:
                query = query.filter(HouseInfo.price <= int(request.args['max_price']))
            except ValueError:
                pass

        # 按租赁方式
        if 'rent_type' in request.args and request.args['rent_type']:
            query = query.filter(HouseInfo.rent_type == request.args['rent_type'])

        # 按是否近地铁
        if 'subway' in request.args:
            try:
                subway_val = int(request.args['subway'])
                if subway_val in [0, 1]:
                    query = query.filter(HouseInfo.subway == subway_val)
            except ValueError:
                pass

        # 按装修情况
        if 'decoration' in request.args and request.args['decoration']:
            query = query.filter(HouseInfo.decoration.ilike(f"%{request.args['decoration']}%"))

        # 按房源状态 (available)
        if 'available' in request.args:
            try:
                available_val = int(request.args['available'])
                if available_val in [0, 1]:
                    query = query.filter(HouseInfo.available == available_val)
            except ValueError:
                pass

        # 排序
        query = query.order_by(HouseInfo.publish_time.desc(), HouseInfo.id.desc())

        # 查询所有匹配记录（不分页），缓存完整结果供多分页共用
        all_items = [house.to_dict() for house in query.all()]
        total = len(all_items)

        # 将完整结果集存入缓存（不分页）
        RedisCache.set_cache(cache_key, {"items": all_items, "total": total})

        # 从完整结果集中分页
        start = (page - 1) * per_page
        end = start + per_page
        paged_items = all_items[start:end]

        response_data = {
            "items": paged_items,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": (total + per_page - 1) // per_page
        }

        if not paged_items and page == 1:  # 如果第一页就没有数据
            return success_response(data=response_data, message="暂无房源信息", code=Code.GET_OK)  # 仍然是成功，只是数据为空

        return success_response(data=response_data, message="查询成功", code=Code.GET_OK)

    except SQLAlchemyError as e:
        current_app.logger.error(f"查询房源失败: {e}")
        return error_response(f"数据库错误: {str(e)}", code=Code.INTERNAL_SERVER_ERROR)
    except Exception as e:
        current_app.logger.error(f"查询房源时发生未知错误: {e}")
        return error_response(f"查询房源失败: {str(e)}", code=Code.INTERNAL_SERVER_ERROR)


# 3. 查询单个房源信息 (对应点击查看房源详情)
@house_info_bp.route('/<int:house_id>', methods=['GET'])
def get_house_info_by_id(house_id):
    """
    根据ID获取单个房源详情
    :param house_id: 房源ID
    :说明: 优先从Redis缓存读取
    :返回: 房源详细信息
    """
    session = get_db_session()
    try:
        # 构建缓存键
        cache_key = f'house_info:{house_id}'

        # 检查 Redis 中是否存在缓存数据
        cached_data = RedisCache.get_cache(cache_key)
        if cached_data:
            return success_response(data=cached_data, message="查询成功", code=Code.GET_OK)

        current_app.logger.debug(f"house{house_id}无缓存信息")

        house = session.get(HouseInfo, house_id)  # SQLAlchemy 2.0 style
        # 或者 house = session.query(HouseInfo).filter_by(id=house_id).first()
        if house:
            house_data = house.to_dict()
            # 正确：在找到数据时设置缓存，且不重复使用 json.dumps
            RedisCache.set_cache(cache_key, house_data)
            return success_response(data=house_data, code=Code.GET_OK)
        else:
            return error_response("房源信息未找到", code=Code.NOT_FOUND)

    except SQLAlchemyError as e:
        current_app.logger.error(f"查询房源 {house_id} 失败: {e}")
        return error_response(f"数据库错误: {str(e)}", code=Code.INTERNAL_SERVER_ERROR)


# 4. 更新房源信息 (对应房东编辑房源)
@house_info_bp.route('/<int:house_id>', methods=['PUT'])
def update_house_info(house_id):
    """
    更新房源信息
    :param house_id: 房源ID
    :接收: 需要更新的字段（不允许修改id）
    :返回: 更新后的房源信息
    """
    session = get_db_session()
    house = session.get(HouseInfo, house_id)
    if not house:
        return error_response("房源信息未找到", code=Code.NOT_FOUND)

    data = request.get_json()
    if not data:
        return error_response("请求体不能为空", code=Code.BAD_REQUEST)

    try:
        for key, value in data.items():
            if hasattr(house, key) and key != 'id':  # 不允许修改id
                if key == 'publish_time' and isinstance(value, str):
                    try:
                        value = datetime.date.fromisoformat(value)
                    except ValueError:
                        return error_response("日期格式错误，应为 YYYY-MM-DD", code=Code.BAD_REQUEST)
                elif key in ['subway', 'available', 'tag_new'] and isinstance(value, bool):
                    value = 1 if value else 0

                setattr(house, key, value)

        session.commit()
        RedisCache.delete_cache(f'house_info:{house_id}')
        # 建议同时清理列表缓存，因为列表中的价格等信息也已过期
        RedisCache.delete_cache('house_hot_lists')
        RedisCache.delete_cache('house_new_lists')
        RedisCache.delete_by_prefix('all_house_infos:')

        return success_response(data=house.to_dict(), message="房源信息更新成功", code=Code.UPDATE_OK)
    except SQLAlchemyError as e:
        session.rollback()
        current_app.logger.error(f"更新房源 {house_id} 失败: {e}")
        return error_response(f"数据库错误: {str(e)}", code=Code.INTERNAL_SERVER_ERROR)
    except Exception as e:
        session.rollback()
        current_app.logger.error(f"更新房源 {house_id} 时发生未知错误: {e}")
        return error_response(f"更新房源失败: {str(e)}", code=Code.INTERNAL_SERVER_ERROR)


# 5. 删除房源信息 (对应房东删除房源)
@house_info_bp.route('/<int:house_id>', methods=['DELETE'])
def delete_house_info(house_id):
    """
    删除房源
    :param house_id: 房源ID
    :说明: 同时清除Redis缓存
    :返回: 删除成功信息
    """
    session = get_db_session()
    house = session.get(HouseInfo, house_id)
    if not house:
        return error_response("房源信息未找到", code=Code.NOT_FOUND)

    try:
        session.delete(house)
        session.commit()

        # 删除相关缓存,保证一致性
        RedisCache.delete_cache(f'house_info:{house_id}')
        RedisCache.delete_cache('house_hot_lists')
        RedisCache.delete_cache('house_new_lists')
        RedisCache.delete_by_prefix('all_house_infos:')

        return success_response(message="房源信息删除成功", code=Code.DELETE_OK)
    except SQLAlchemyError as e:
        session.rollback()
        current_app.logger.error(f"删除房源 {house_id} 失败: {e}")
        return error_response(f"数据库错误: {str(e)}", code=Code.INTERNAL_SERVER_ERROR)


@house_info_bp.route('/<int:house_id>/upload_image', methods=['POST'])
def upload_house_image(house_id):
    session = get_db_session()
    house = session.get(HouseInfo, house_id)
    if not house:
        return error_response("房源信息未找到", code=Code.NOT_FOUND)

    if 'file' not in request.files:
        return error_response("缺少文件部分", code=Code.BAD_REQUEST)

    file = request.files['file']
    if file.filename == '':
        return error_response("未选择文件", code=Code.BAD_REQUEST)

    if file:
        return error_response("文件上传功能暂未完全实现，仅为示例接口", code=Code.INTERNAL_SERVER_ERROR)


# 智能管理员统计
#1、户型占比
@house_info_bp.route('/piedata', methods=['GET'])
def get_house_piedata():
    """
    获取房源户型分布统计（用于管理后台饼图）
    :说明: 将户型归并为一居室/二居室/三居室/四居室/五居及以上
    :返回: 各户型的名称和数量
    """
    result= (HouseInfo.query.with_entities(HouseInfo.rooms,func.count())
             .group_by(HouseInfo.rooms).order_by(func.count().desc()).all())
    data=[]

    # 统计合并后的结果
    merge_dict = defaultdict(int)

    for room_name, count in result:
        # 提取几室的信息（如“3室2厅”提取“3”）
        match = re.match(r"(\d)室", room_name)
        if match:
            num = int(match.group(1))
            if num == 1:
                merge_dict["一居室"] += count
            elif num == 2:
                merge_dict["二居室"] += count
            elif num == 3:
                merge_dict["三居室"] += count
            elif num == 4:
                merge_dict["四居室"] += count
            elif num >= 5:
                merge_dict["五居及以上"] += count
            else:
                merge_dict["其他"] += count
        else:
            merge_dict["其他"] += count

    data = [{"name": k, "value": v} for k, v in merge_dict.items()]

    return success_response(data=data, message="查询成功", code=Code.GET_OK)

#小区房源前20
@house_info_bp.route('/columndata', methods=['GET'])
def get_house_columndata():
    """
    获取各小区房源数量前20排名（用于管理后台柱状图）
    :返回: 小区名称列表和对应数量列表
    """
    result= (HouseInfo.query.with_entities(HouseInfo.community,func.count()).group_by(HouseInfo.community)
             .order_by(func.count().desc()).all())
    community_list = []
    num_list = []
    for community, count in result:
        community_list.append(community)
        num_list.append(count)
    if len(num_list) > 20:
        data={'community_list': community_list[:20], 'num_list': num_list[:20]}
    else:
        data={'community_list': community_list, 'num_list': num_list}
    return success_response(data=data, message="查询成功", code=Code.GET_OK)

# 获取浏览量最高的房源
@house_info_bp.route('/views', methods=['GET'])
def get_house_info_views():
    """
    获取浏览量最高的单个房源
    :返回: 浏览量第一的房源信息
    """
    house = get_house_by_views()
    if not house:
        return error_response("获取失败", code=Code.NOT_FOUND)

    return success_response(data=house.to_dict(), message="获取成功", code=Code.GET_OK)

# 增加浏览次数
@house_info_bp.route('/views', methods=['POST'])
def add_house_info_views():
    """
    给指定房源增加1次浏览量
    :接收: houseid(房源ID)
    :返回: 操作成功或失败信息
    """
    data = request.get_json()
    if add_views_by_id(data):
        return success_response(message="增加成功", code=Code.GET_OK)
    else:
        return error_response(message="不存在该房源", code=Code.NOT_FOUND)


# 根据房东名字查找房源
@house_info_bp.route('/landlord', methods=['POST'])
def get_house_info_landlord():
    """
    根据房东用户名查询其名下所有房源
    :接收: username(房东用户名)
    :说明: 同时标记每个房源是否已有租约(isRant字段)
    :返回: 房源列表
    """
    data = request.get_json()
    if data is None:
        return error_response("请求数据为空", code=Code.NOT_FOUND)

    landlord = data['username']

    try:
        houses = get_house_by_landlord(landlord)
        house_list = []
        for house in houses:
            b = house.to_dict()
            b['isRant'] = False
            if get_house_rental(b['id']):
                b['isRant'] = True
            house_list.append(b)

        return success_response(data=house_list, message="获取成功", code=Code.GET_OK)
    except KeyError:
        return error_response("获取错误", code=Code.NOT_FOUND)