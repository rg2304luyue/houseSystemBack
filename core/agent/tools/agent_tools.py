import json
import logging
from langchain_core.tools import tool
from models.house_model import HouseInfo
from exts.db import db
from flask import current_app

logger = logging.getLogger(__name__)


# 如果你还需要保留原来的 RAG 工具，可以把 rag_summarize 留着
# @tool(description="从向量存储中检索租房指南、政策等参考资料")
# def rag_summarize(query: str) -> str: ...

@tool(
    description="根据条件搜索房源。参数需提供 JSON 字符串格式的条件，可包含 min_price, max_price, region, rooms, subway(bool) 等")
def search_houses_by_criteria(query_params_json: str) -> str:
    try:
        kwargs = json.loads(query_params_json)
        query = db.session.query(HouseInfo).filter(HouseInfo.available == 1)

        if kwargs.get('min_price'): query = query.filter(HouseInfo.price >= kwargs['min_price'])
        if kwargs.get('max_price'): query = query.filter(HouseInfo.price <= kwargs['max_price'])
        if kwargs.get('region'): query = query.filter(HouseInfo.region.like(f"%{kwargs['region']}%"))
        if kwargs.get('rooms'): query = query.filter(HouseInfo.rooms.like(f"%{kwargs['rooms']}%"))
        if kwargs.get('subway'): query = query.filter(HouseInfo.subway == 1)

        houses = query.order_by(HouseInfo.price.asc()).limit(5).all()  # 建议限制返回数量给大模型
        if not houses:
            return "没有找到符合条件的房源，请建议用户放宽条件。"

        return json.dumps([house.to_dict() for house in houses], ensure_ascii=False)
    except Exception as e:
        logger.error(f"Tool search error: {e}")
        return f"查询出错: {str(e)}"


@tool(description="根据房源ID获取详细信息，参数为房源ID(int)")
def get_house_details(house_id: int) -> str:
    try:
        house = db.session.query(HouseInfo).filter(HouseInfo.id == house_id).first()
        if house:
            return json.dumps(house.to_dict(), ensure_ascii=False)
        return "未找到该ID的房源"
    except Exception as e:
        return f"查询出错: {str(e)}"


@tool(description="获取热门房源推荐，默认返回浏览量最高的前5套")
def get_popular_houses(limit: int = 5) -> str:
    try:
        houses = db.session.query(HouseInfo).filter(HouseInfo.available == 1) \
            .order_by(HouseInfo.page_views.desc()).limit(limit).all()
        return json.dumps([house.to_dict() for house in houses], ensure_ascii=False)
    except Exception as e:
        return f"查询出错: {str(e)}"