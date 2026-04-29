"""
agent_tools.py - LangChain 工具集
修复内容：
1. search_houses_by_criteria：增加详细调试日志，排查 region 搜索问题
2. region 字段：支持"岳麓"和"岳麓区"两种写法（自动去掉"区"再匹配）
3. 返回结果增加字段说明，帮助大模型更好理解数据
"""
import json
import logging
from langchain_core.tools import tool
from models.house_model import HouseInfo
from exts.db import db

logger = logging.getLogger(__name__)

@tool(
    description="""
    根据条件搜索房源。参数为 JSON 字符串，可包含以下字段：
    - min_price (int): 最低租金（元/月）
    - max_price (int): 最高租金（元/月）
    - region (str): 区域名，如 "岳麓" 或 "岳麓区"，支持模糊匹配
    - rooms (str): 户型，如 "2室1厅"
    - subway (bool): 是否需要近地铁
    - decoration (str): 装修情况，如 "精装"

    示例：{"region": "岳麓", "max_price": 3000}
    注意：region 只需传区的名字，不需要加"区"字，如传 "岳麓" 即可。
    """
)
def search_houses_by_criteria(query_params_json: str) -> str:
    try:
        kwargs = json.loads(query_params_json)
        logger.info(f"[Tool:search_houses] 收到参数: {kwargs}")

        query = db.session.query(HouseInfo).filter(HouseInfo.available == 1)

        if kwargs.get('min_price'):
            query = query.filter(HouseInfo.price >= kwargs['min_price'])
            logger.info(f"[Tool:search_houses] 过滤最低价: {kwargs['min_price']}")

        if kwargs.get('max_price'):
            query = query.filter(HouseInfo.price <= kwargs['max_price'])
            logger.info(f"[Tool:search_houses] 过滤最高价: {kwargs['max_price']}")

        if kwargs.get('region'):
            # 去掉"区"字，防止大模型传入"岳麓区"而数据库存的是"岳麓"（或反过来）
            region_keyword = kwargs['region'].replace('区', '').strip()
            query = query.filter(HouseInfo.region.like(f"%{region_keyword}%"))
            logger.info(f"[Tool:search_houses] 过滤区域: {region_keyword}")

        if kwargs.get('rooms'):
            query = query.filter(HouseInfo.rooms.like(f"%{kwargs['rooms']}%"))
            logger.info(f"[Tool:search_houses] 过滤户型: {kwargs['rooms']}")

        if kwargs.get('subway'):
            query = query.filter(HouseInfo.subway == 1)
            logger.info("[Tool:search_houses] 过滤近地铁")

        if kwargs.get('decoration'):
            query = query.filter(HouseInfo.decoration.like(f"%{kwargs['decoration']}%"))
            logger.info(f"[Tool:search_houses] 过滤装修: {kwargs['decoration']}")

        # 先统计总数，帮助调试
        total = query.count()
        logger.info(f"[Tool:search_houses] 符合条件总数: {total}")

        houses = query.order_by(HouseInfo.price.asc()).limit(5).all()

        if not houses:
            # 输出数据库中实际存在的区域，帮助排查
            all_regions = db.session.query(HouseInfo.region).distinct().all()
            region_list = [r[0] for r in all_regions if r[0]]
            logger.warning(f"[Tool:search_houses] 未找到房源！数据库中存在的区域有: {region_list}")
            return (
                f"没有找到符合条件的房源。"
                f"数据库中目前有以下区域的房源：{', '.join(region_list)}，"
                f"请建议用户从这些区域中选择，或放宽其他条件。"
            )

        result = [house.to_dict() for house in houses]
        logger.info(f"[Tool:search_houses] 返回 {len(result)} 套房源")
        return json.dumps(result, ensure_ascii=False, default=str)

    except json.JSONDecodeError as e:
        logger.error(f"[Tool:search_houses] JSON解析失败: {e}, 原始输入: {query_params_json}")
        return f"参数格式错误，请传入合法的JSON字符串。错误: {str(e)}"
    except Exception as e:
        logger.error(f"[Tool:search_houses] 查询出错: {e}", exc_info=True)
        return f"查询出错: {str(e)}"


@tool(description="根据房源ID获取该房源的详细信息，参数为整数类型的房源ID")
def get_house_details(house_id: int) -> str:
    try:
        logger.info(f"[Tool:get_house_details] 查询房源ID: {house_id}")
        house = db.session.query(HouseInfo).filter(HouseInfo.id == house_id).first()
        if house:
            return json.dumps(house.to_dict(), ensure_ascii=False, default=str)
        return f"未找到ID为 {house_id} 的房源"
    except Exception as e:
        logger.error(f"[Tool:get_house_details] 查询出错: {e}")
        return f"查询出错: {str(e)}"


@tool(description="获取当前平台浏览量最高的热门房源推荐，默认返回前5套。适合用户没有明确条件时调用。")
def get_popular_houses(limit: int = 5) -> str:
    try:
        logger.info(f"[Tool:get_popular_houses] 获取热门房源，数量: {limit}")
        houses = db.session.query(HouseInfo) \
            .filter(HouseInfo.available == 1) \
            .order_by(HouseInfo.page_views.desc()) \
            .limit(limit).all()

        if not houses:
            return "暂无热门房源数据"

        logger.info(f"[Tool:get_popular_houses] 返回 {len(houses)} 套热门房源")
        return json.dumps([house.to_dict() for house in houses], ensure_ascii=False, default=str)
    except Exception as e:
        logger.error(f"[Tool:get_popular_houses] 查询出错: {e}")
        return f"查询出错: {str(e)}"