"""FastAPI-native tools for the rental assistant ReAct agent."""

from functools import lru_cache
import json
import logging

from langchain_core.tools import tool
import requests

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.house import HouseInfo


logger = logging.getLogger(__name__)

_PUBLIC_HOUSE_FIELDS = (
    "id",
    "title",
    "region",
    "block",
    "community",
    "area",
    "direction",
    "rooms",
    "price",
    "rent_type",
    "decoration",
    "subway",
    "tag_new",
    "image_url",
    "publish_time",
    "page_views",
    "house_num",
)
_CITY_ADCODES = {
    "长沙": "430100",
    "芙蓉": "430102",
    "天心": "430103",
    "岳麓": "430104",
    "开福": "430105",
    "雨花": "430111",
}


def _house_payload(house: HouseInfo) -> dict:
    payload = {}
    for field in _PUBLIC_HOUSE_FIELDS:
        value = getattr(house, field, None)
        if hasattr(value, "isoformat"):
            value = value.isoformat()
        payload[field] = value
    payload["subway"] = bool(payload["subway"])
    payload["tag_new"] = bool(payload["tag_new"])
    return payload


def _json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, default=str)


@tool
def search_houses_by_criteria(
    region: str | None = None,
    min_price: int | None = None,
    max_price: int | None = None,
    min_area: float | None = None,
    max_area: float | None = None,
    rooms: str | None = None,
    rent_type: str | None = None,
    subway: bool | None = None,
    decoration: str | None = None,
    limit: int = 5,
) -> str:
    """Search currently available houses using the supplied rental criteria."""
    try:
        safe_limit = max(1, min(limit, 5))
        with SessionLocal() as db:
            query = db.query(HouseInfo).filter(HouseInfo.available == 1)
            if region:
                region_key = region.replace("区", "").replace("县", "").strip()
                query = query.filter(HouseInfo.region.contains(region_key))
            if min_price is not None:
                query = query.filter(HouseInfo.price >= max(0, min_price))
            if max_price is not None:
                query = query.filter(HouseInfo.price <= max_price)
            if min_area is not None:
                query = query.filter(HouseInfo.area >= max(0, min_area))
            if max_area is not None:
                query = query.filter(HouseInfo.area <= max_area)
            if rooms:
                query = query.filter(HouseInfo.rooms.contains(rooms.strip()))
            if rent_type:
                query = query.filter(HouseInfo.rent_type == rent_type.strip())
            if subway is not None:
                query = query.filter(HouseInfo.subway == int(subway))
            if decoration:
                query = query.filter(HouseInfo.decoration.contains(decoration.strip()))
            houses = query.order_by(HouseInfo.price.asc(), HouseInfo.id.desc()).limit(safe_limit).all()
            return _json({"count": len(houses), "houses": [_house_payload(house) for house in houses]})
    except Exception:
        logger.exception("House criteria tool failed")
        return _json({"error": "房源查询暂时不可用，请稍后重试。"})


@tool
def get_house_details(house_id: int) -> str:
    """Get public details for one currently available house by its numeric ID."""
    try:
        with SessionLocal() as db:
            house = db.query(HouseInfo).filter(
                HouseInfo.id == house_id,
                HouseInfo.available == 1,
            ).first()
            if house is None:
                return _json({"error": "未找到该房源或房源当前不可用。"})
            return _json({"house": _house_payload(house)})
    except Exception:
        logger.exception("House detail tool failed")
        return _json({"error": "房源详情暂时不可用，请稍后重试。"})


@tool
def get_popular_houses(limit: int = 5) -> str:
    """Return the most-viewed currently available houses, up to five entries."""
    try:
        safe_limit = max(1, min(limit, 5))
        with SessionLocal() as db:
            houses = db.query(HouseInfo).filter(HouseInfo.available == 1).order_by(
                HouseInfo.page_views.desc(), HouseInfo.id.desc()
            ).limit(safe_limit).all()
            return _json({"count": len(houses), "houses": [_house_payload(house) for house in houses]})
    except Exception:
        logger.exception("Popular houses tool failed")
        return _json({"error": "热门房源暂时不可用，请稍后重试。"})


@lru_cache(maxsize=1)
def _rag_service():
    from core.rag.retrieval_service import RagRetrievalService

    return RagRetrievalService()


def _rental_knowledge_payload(query: str) -> str:
    cleaned_query = query.strip()[:1000]
    if not cleaned_query:
        return _json({"query": "", "grounded": False, "chunks": []})
    try:
        return _json(_rag_service().retrieve(cleaned_query).to_dict())
    except Exception:
        logger.exception("Rental knowledge retrieval failed")
        return _json({
            "query": cleaned_query,
            "grounded": False,
            "chunks": [],
            "error": "knowledge_base_unavailable",
        })


@tool
def search_rental_knowledge(query: str) -> str:
    """Return scored evidence. Cite chunks as [1], [2]; if grounded is false, do not answer from memory."""
    return _rental_knowledge_payload(query)


@tool
def get_weather_for_visit(city: str = "长沙") -> str:
    """Get current weather and a three-day forecast to help plan a house visit."""
    if not settings.GAODE_WEATHER_KEY:
        return _json({"error": "天气服务尚未配置。"})
    city_name = city.replace("区", "").strip()[:30] or "长沙"
    city_code = _CITY_ADCODES.get(city_name, city_name)
    url = "https://restapi.amap.com/v3/weather/weatherInfo"
    base_params = {"key": settings.GAODE_WEATHER_KEY, "city": city_code, "output": "JSON"}
    try:
        live_response = requests.get(
            url, params={**base_params, "extensions": "base"}, timeout=(3.05, 8)
        )
        live_response.raise_for_status()
        forecast_response = requests.get(
            url, params={**base_params, "extensions": "all"}, timeout=(3.05, 8)
        )
        forecast_response.raise_for_status()
        live_data = live_response.json()
        forecast_data = forecast_response.json()
        if live_data.get("status") != "1" or not live_data.get("lives"):
            return _json({"error": "未能获取该地区的天气。"})
        live = live_data["lives"][0]
        casts = []
        if forecast_data.get("status") == "1" and forecast_data.get("forecasts"):
            for cast in forecast_data["forecasts"][0].get("casts", [])[:3]:
                casts.append({
                    "date": cast.get("date"),
                    "day_weather": cast.get("dayweather"),
                    "night_weather": cast.get("nightweather"),
                    "day_temperature": cast.get("daytemp"),
                    "night_temperature": cast.get("nighttemp"),
                })
        return _json({
            "city": live.get("city", city_name),
            "reported_at": live.get("reporttime"),
            "current": {
                "weather": live.get("weather"),
                "temperature_celsius": live.get("temperature"),
                "humidity_percent": live.get("humidity"),
                "wind_direction": live.get("winddirection"),
                "wind_power": live.get("windpower"),
            },
            "forecast": casts,
        })
    except (requests.RequestException, ValueError, TypeError):
        logger.exception("Weather tool failed")
        return _json({"error": "天气查询暂时不可用，请稍后重试。"})


REACT_TOOLS = (
    search_houses_by_criteria,
    get_house_details,
    get_popular_houses,
    search_rental_knowledge,
    get_weather_for_visit,
)
