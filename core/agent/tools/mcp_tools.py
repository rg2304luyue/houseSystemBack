"""
mcp_tools.py - MCP（Model Context Protocol）风格的扩展工具集
这些工具让 Agent 能获取外部实时信息，提升推荐质量

工具列表：
1. get_weather_for_visit - 获取天气信息，帮助用户决定看房时间
2. search_nearby_facilities - 查询房源周边配套（地铁、学校、医院等）
3. calculate_commute_time - 计算通勤时间估算
4. get_rental_market_tips - 获取当前租房市场行情建议
"""

import json
import logging
import requests
from langchain_core.tools import tool
from datetime import datetime
from config import Config

logger = logging.getLogger(__name__)

# 高德天气 API：城市名 → adcode 映射（常用城市）
# 完整列表见：https://lbs.amap.com/api/webservice/download（城市数据）
CITY_ADCODE = {
    "长沙": "430100",
    "岳麓": "430100",   # 岳麓区属长沙市
    "天心": "430100",
    "雨花": "430100",
    "开福": "430100",
    "芙蓉": "430100",
    "北京": "110000",
    "上海": "310000",
    "广州": "440100",
    "深圳": "440300",
}

# 天气状况 → 看房建议
WEATHER_ADVICE = {
    "晴":   ("☀️ 晴天", "光线充足，是看房的最佳时机！建议上午10点到下午4点之间去，采光效果一目了然。"),
    "多云": ("⛅ 多云", "天气不错，适合看房，注意观察房间采光是否充足。"),
    "阴":   ("☁️ 阴天", "阴天看房可以真实感受采光情况，也是不错的选择。"),
    "雨":   ("🌧️ 雨天", "雨天是检验房屋防水性能的绝佳时机！注意查看天花板、窗台有无渗水。"),
    "雪":   ("❄️ 雪天", "建议改期，路面湿滑注意安全。若必须看房，重点检查暖气和保温情况。"),
    "雾":   ("🌫️ 雾霾", "能见度低，建议改期。可借此机会了解该区域空气质量情况。"),
    "霾":   ("😷 霾", "空气质量差，建议改期，也可顺便了解小区周边的通风环境。"),
    "大风": ("💨 大风", "注意窗户密封性，看房时可测试窗户关闭后是否有风声漏入。"),
}


def _get_weather_advice(weather_text: str) -> tuple:
    """根据天气文字返回 (emoji标签, 建议文字)"""
    for keyword, advice in WEATHER_ADVICE.items():
        if keyword in weather_text:
            return advice
    return ("🌤️ " + weather_text, "天气状况一般，看房时注意携带雨具以备不时之需。")


@tool(
    description="""
    获取指定城市或区域的实时天气和未来3天预报，帮助用户选择合适的看房日期。
    参数：city (str) - 城市或区域名，如 "长沙"、"岳麓"，默认为"长沙"
    返回：实时天气、未来预报和看房时间建议
    """
)
def get_weather_for_visit(city: str = "长沙") -> str:
    """调用高德天气 API 获取真实天气数据"""
    try:
        api_key = Config.GaoDeWeatherKey
        # 将区名映射到 adcode，找不到就直接用城市名让高德自己解析
        adcode = CITY_ADCODE.get(city.replace("区", "").strip(), city)

        logger.info(f"[Tool:get_weather] 查询城市: {city}, adcode/city: {adcode}")

        # ---- 1. 获取实时天气 ----
        live_url = "https://restapi.amap.com/v3/weather/weatherInfo"
        live_resp = requests.get(live_url, params={
            "key": api_key,
            "city": adcode,
            "extensions": "base",   # base = 实时天气
            "output": "JSON"
        }, timeout=8)
        live_data = live_resp.json()

        if live_data.get("status") != "1" or not live_data.get("lives"):
            logger.warning(f"[Tool:get_weather] 实时天气接口返回异常: {live_data}")
            return json.dumps({"error": "天气数据获取失败，请稍后重试"}, ensure_ascii=False)

        live = live_data["lives"][0]
        current_weather = live.get("weather", "未知")
        current_temp = live.get("temperature", "?")
        current_wind = live.get("windpower", "?")
        current_humidity = live.get("humidity", "?")
        report_time = live.get("reporttime", "")

        # ---- 2. 获取未来3天预报 ----
        forecast_url = "https://restapi.amap.com/v3/weather/weatherInfo"
        forecast_resp = requests.get(forecast_url, params={
            "key": api_key,
            "city": adcode,
            "extensions": "all",   # all = 预报天气
            "output": "JSON"
        }, timeout=8)
        forecast_data = forecast_resp.json()

        forecast_list = []
        if forecast_data.get("status") == "1" and forecast_data.get("forecasts"):
            casts = forecast_data["forecasts"][0].get("casts", [])
            for cast in casts[:3]:   # 取未来3天
                day_weather = cast.get("dayweather", "")
                _, day_advice = _get_weather_advice(day_weather)
                forecast_list.append({
                    "date": cast.get("date", ""),
                    "day_weather": day_weather,
                    "night_weather": cast.get("nightweather", ""),
                    "day_temp": cast.get("daytemp", "?"),
                    "night_temp": cast.get("nighttemp", "?"),
                    "wind": cast.get("daywind", "?") + "风 " + cast.get("daypower", "?") + "级",
                })

        # ---- 3. 生成看房建议 ----
        weather_label, visit_advice = _get_weather_advice(current_weather)

        # 从未来3天里找最适合看房的日期
        best_day = None
        for f in forecast_list:
            if any(good in f["day_weather"] for good in ["晴", "多云"]):
                best_day = f
                break

        result = {
            "city": live.get("city", city),
            "report_time": report_time,
            "current": {
                "weather": f"{weather_label}  {current_weather}",
                "temperature": f"{current_temp}°C",
                "wind": f"{current_wind}级",
                "humidity": f"{current_humidity}%",
            },
            "forecast_3days": forecast_list,
            "visit_advice": visit_advice,
            "best_visit_day": (
                f"建议选择 {best_day['date']}（{best_day['day_weather']}，{best_day['day_temp']}°C）去看房"
                if best_day else "近期天气一般，建议选择白天温度适中的时段看房"
            )
        }

        logger.info(f"[Tool:get_weather] 查询成功: {current_weather} {current_temp}°C")
        return json.dumps(result, ensure_ascii=False)

    except requests.Timeout:
        logger.error("[Tool:get_weather] 请求超时")
        return "天气查询超时，请稍后重试。"
    except Exception as e:
        logger.error(f"[Tool:get_weather] 查询失败: {e}", exc_info=True)
        return f"天气查询失败: {str(e)}"


@tool(
    description="""
    查询房源周边的配套设施信息，包括：地铁站、学校、医院、超市、商场等。
    参数：
    - region (str): 所在区域，如 "岳麓"
    - community (str): 小区名称，如 "锦源小区"
    返回：周边主要配套设施列表和评价
    """
)
def search_nearby_facilities(region: str, community: str = "") -> str:
    """
    查询周边配套。实际项目可接入高德地图 POI 搜索 API。
    """
    try:
        logger.info(f"[Tool:nearby] 查询周边配套 - 区域: {region}, 小区: {community}")

        # ---- 接入高德地图 API 示例（需替换 key）----
        # amap_key = "YOUR_AMAP_KEY"
        # 先获取小区坐标，再查周边 POI
        # url = f"https://restapi.amap.com/v3/place/text?keywords={community}&city={region}&key={amap_key}"

        # 当前使用知识库内容返回区域介绍
        area_info = {
            "岳麓": {
                "metro": "地铁2号线、4号线",
                "schools": "湖南大学、中南大学、湖南师范大学",
                "hospitals": "中南大学湘雅三医院、岳麓区人民医院",
                "shopping": "梅溪湖国际新城、万达广场、步步高超市",
                "parks": "岳麓山、梅溪湖公园",
                "rating": "⭐⭐⭐⭐ 生活配套完善，高校氛围浓厚"
            },
            "天心": {
                "metro": "地铁1号线、4号线",
                "schools": "长沙市第一中学、师大附中",
                "hospitals": "湖南省儿童医院、长沙市第三医院",
                "shopping": "黄兴南路步行街、坡子街、东塘商圈",
                "parks": "天心阁、白沙液景区",
                "rating": "⭐⭐⭐⭐⭐ 老城核心区，商业最繁华"
            },
            "雨花": {
                "metro": "地铁3号线、6号线",
                "schools": "长郡中学、雅礼中学",
                "hospitals": "湖南省第二人民医院",
                "shopping": "万家丽广场、红星商业广场、步步高超市",
                "parks": "烈士公园、浏阳河风光带",
                "rating": "⭐⭐⭐⭐ 新兴居住区，性价比高"
            },
            "开福": {
                "metro": "地铁4号线",
                "schools": "开福区第一小学",
                "hospitals": "湖南省中医药研究院附属医院",
                "shopping": "德思勤城市广场、万达广场",
                "parks": "洋湖湿地公园",
                "rating": "⭐⭐⭐ 新区发展中，未来潜力大"
            }
        }

        region_key = region.replace('区', '').strip()
        info = area_info.get(region_key, None)

        if info:
            result = {
                "region": region,
                "community": community or "该区域",
                "metro_lines": info["metro"],
                "nearby_schools": info["schools"],
                "nearby_hospitals": info["hospitals"],
                "shopping": info["shopping"],
                "parks": info["parks"],
                "overall_rating": info["rating"],
                "tip": "以上为区域整体配套，具体小区周边情况建议实地考察"
            }
        else:
            result = {
                "region": region,
                "message": f"暂无 {region} 区域的详细配套数据",
                "tip": "建议通过高德地图或百度地图搜索具体小区周边配套"
            }

        return json.dumps(result, ensure_ascii=False)

    except Exception as e:
        logger.error(f"[Tool:nearby] 查询失败: {e}")
        return f"周边配套查询失败: {str(e)}"


@tool(
    description="""
    估算从房源所在区域到指定目的地（如公司、学校）的通勤时间。
    参数：
    - from_region (str): 出发区域，如 "岳麓"
    - to_destination (str): 目的地，如 "五一广场" 或 "天心区"
    - transport (str): 交通方式，可选 "地铁"/"公交"/"驾车"，默认"地铁"
    返回：估算通勤时间和路线建议
    """
)
def calculate_commute_time(from_region: str, to_destination: str, transport: str = "地铁") -> str:
    """
    估算通勤时间。实际项目可接入高德路线规划 API。
    """
    try:
        logger.info(f"[Tool:commute] {from_region} → {to_destination}, 方式: {transport}")

        # 简单的区域间通勤时间估算（基于长沙实际情况）
        commute_matrix = {
            ("岳麓", "天心"): {"地铁": "约35分钟（2号线直达）", "驾车": "约20分钟"},
            ("岳麓", "雨花"): {"地铁": "约50分钟（需换乘）", "驾车": "约30分钟"},
            ("雨花", "天心"): {"地铁": "约25分钟（3号线）", "驾车": "约15分钟"},
            ("开福", "天心"): {"地铁": "约30分钟（4号线）", "驾车": "约20分钟"},
        }

        from_key = from_region.replace('区', '').strip()
        to_key = to_destination.replace('区', '').strip()

        # 查找通勤时间
        time_info = commute_matrix.get((from_key, to_key)) or commute_matrix.get((to_key, from_key))

        if time_info:
            commute_time = time_info.get(transport, time_info.get("地铁", "约30-60分钟"))
        else:
            commute_time = "约30-60分钟（建议通过高德地图规划具体路线）"

        result = {
            "from": from_region,
            "to": to_destination,
            "transport": transport,
            "estimated_time": commute_time,
            "tip": "实际通勤时间受早晚高峰影响，建议实际测试一次。早高峰（8:00-9:00）通勤时间通常增加30-50%。"
        }
        return json.dumps(result, ensure_ascii=False)

    except Exception as e:
        logger.error(f"[Tool:commute] 估算失败: {e}")
        return f"通勤时间估算失败: {str(e)}"


@tool(
    description="""
    获取当前租房市场的行情分析和租房小贴士。
    参数：region (str) - 区域名，如 "岳麓"。留空则返回全市整体行情。
    返回：该区域租金水平参考、租房时机建议
    """
)
def get_rental_market_tips(region: str = "") -> str:
    """
    提供租房市场行情参考（基于知识库静态数据，实际项目可定期更新）。
    """
    try:
        logger.info(f"[Tool:market_tips] 查询区域行情: {region or '全市'}")

        market_data = {
            "岳麓": {
                "avg_price_share": "800-1500元/月（合租）",
                "avg_price_whole": "1500-3500元/月（整租）",
                "trend": "稳中略涨，梅溪湖板块需求旺盛",
                "best_time": "3-5月、9-10月为租房旺季，价格略高；6-8月、11-2月为淡季，可以争取更好的价格",
                "tips": "高校附近供需两旺，建议提前1个月找房"
            },
            "天心": {
                "avg_price_share": "1000-2000元/月（合租）",
                "avg_price_whole": "2000-5000元/月（整租）",
                "trend": "核心地段价格坚挺，老旧小区性价比高",
                "best_time": "全年需求较稳定，节后（春节后）是找性价比房源的好时机",
                "tips": "老城区房龄较大，看房时注意管道、隔音等问题"
            },
            "雨花": {
                "avg_price_share": "800-1500元/月（合租）",
                "avg_price_whole": "1500-4000元/月（整租）",
                "trend": "新房供应充足，价格平稳",
                "best_time": "全年均衡，春节后房东急出租时可谈价",
                "tips": "万家丽、井湾子板块交通便利，性价比突出"
            },
        }

        region_key = region.replace('区', '').strip() if region else ""

        if region_key and region_key in market_data:
            data = market_data[region_key]
            result = {
                "region": region,
                "price_reference": {
                    "share_rent": data["avg_price_share"],
                    "whole_rent": data["avg_price_whole"]
                },
                "market_trend": data["trend"],
                "best_rental_timing": data["best_time"],
                "pro_tips": data["tips"],
                "negotiation_tips": "签约时可尝试争取：首月半价、免费停车位、更换新家电等附加条件"
            }
        else:
            result = {
                "city": "长沙",
                "overview": "长沙整体租房市场平稳，各区域价格差异明显",
                "affordable_areas": "雨花区、岳麓区性价比最高",
                "premium_areas": "天心区、芙蓉区配套最成熟但租金较贵",
                "general_tips": [
                    "建议预留1-2周时间看房，不要仓促决定",
                    "春节前后是砍价好时机，房东急于出租",
                    "看房时务必实地查看，照片与实际可能有差距",
                    "签约前确认周边噪音、采光、楼层等实际情况"
                ]
            }

        return json.dumps(result, ensure_ascii=False)

    except Exception as e:
        logger.error(f"[Tool:market_tips] 查询失败: {e}")
        return f"行情查询失败: {str(e)}"