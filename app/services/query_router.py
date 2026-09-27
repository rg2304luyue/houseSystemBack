"""Deterministic routing boundaries for the rental assistant.

The router is intentionally provider-independent: current inventory belongs to
SQL, while policies, guides, and explicitly historical snapshots belong to RAG.
"""

from __future__ import annotations

from enum import Enum
import re
from typing import Sequence

from app.services.query_constraints import extract_house_constraints


class QueryRoute(str, Enum):
    SQL = "sql"
    RAG = "rag"
    HISTORICAL_SNAPSHOT = "historical_snapshot"
    MIXED = "mixed"
    GENERAL = "general"
    WEATHER = "weather"


_SQL_PATTERN = re.compile(
    r"(?:当前|现在|目前|在租|可租|随时看房|推荐|帮我找|找房|"
    r"预算|月租|租金|价格|均价|\d+\s*元|[一二两三四五六七八九十百千万]+\s*元|"
    r"\d+\s*左右|户型|几室|面积|平方米|"
    r"地铁|整租|合租|精装|简装|毛坯|房源\s*(?:id|编号)|热门房源)",
    re.IGNORECASE,
)
_RAG_PATTERN = re.compile(
    r"(?:租房流程|签约|合同|押金|维修责任|纠纷|退租|"
    r"违约|备案|政策|规定|法规|指南|注意事项|看房检查|不退(?:钱|款|押金)|"
    r"补贴|申请条件|申请资格|税率|办理入口|申请材料|需要哪些材料|"
    r"租赁知识|如何签|怎么签|如何处理|怎么处理|怎么办|什么意思|"
    r"押一付[一二两三四五六七八九十\d]+|"
    r"(?:房东|中介).{0,12}(?:不修|拒修|维修|不退|扣押金))",
    re.IGNORECASE,
)
_HISTORICAL_PATTERN = re.compile(
    r"(?:历史|快照|采集日期|采集时间|当时|过去|"
    r"公开记录|快照来源|数据来源)",
    re.IGNORECASE,
)
_WEATHER_PATTERN = re.compile(r"(?:天气|气温|下雨|晴天|看房日期|出行天气)", re.IGNORECASE)
_HOUSE_PATTERN = re.compile(r"(?:房源|小区|商圈|出租|租一套|租房)", re.IGNORECASE)
_LISTING_PATTERN = re.compile(r"(?:房源|小区|商圈|出租|租一套|找房|推荐)", re.IGNORECASE)
_LIVE_PATTERN = re.compile(r"(?:当前|现在|目前|在租|可租|还有房|库存|随时看房)", re.IGNORECASE)
_ANAPHORA_PATTERN = re.compile(
    r"^(?:(?:(?:这|那)(?:一)?套|它|(?:这个|那个)(?:房源)?|"
    r"第[\d一二三四五六七八九十]+套)(?:的)?"
    r"(?:呢|怎么样|如何|多少钱|价格多少|租金多少|多大|面积多大|"
    r"什么户型|朝向如何|有地铁吗|离地铁近吗|还能租吗)?|还有呢|呢)"
    r"[\s，。？?!]*$"
)


_SEARCH_FOLLOWUP_PATTERN = re.compile(
    r"(?:换一批|换几套|还有别的|其他房源|贵一点|贵些|贵点|便宜一点|便宜些|便宜点|"
    r"增加预算|提高预算|降低预算|预算.{0,5}(?:加|减|放宽))"
)


def route_query(query: str, previous_user_queries: Sequence[str] | None = None) -> QueryRoute:
    """Return a deterministic data-source route for one user query.

    Ambiguous short follow-ups inherit the most recent classifiable user query.
    Explicit real-time and historical requirements together are treated as a
    mixed request so callers can compare SQL state with a dated snapshot.
    """

    cleaned = " ".join(query.strip().split())[:4000]
    if not cleaned:
        return QueryRoute.GENERAL

    has_sql = bool(_SQL_PATTERN.search(cleaned))
    has_rag = bool(_RAG_PATTERN.search(cleaned))
    has_history = bool(_HISTORICAL_PATTERN.search(cleaned))
    has_weather = bool(_WEATHER_PATTERN.search(cleaned))
    has_house_context = bool(_HOUSE_PATTERN.search(cleaned))
    has_listing_context = bool(_LISTING_PATTERN.search(cleaned))
    has_live = bool(_LIVE_PATTERN.search(cleaned))
    has_constraints = extract_house_constraints(cleaned).has_filters

    if has_weather and not has_house_context and not has_rag and not has_history:
        return QueryRoute.WEATHER
    # Policy evolution is still policy knowledge.  A mixed query is reserved
    # for an explicit comparison between live SQL inventory and dated listing
    # snapshots, not merely for the coexistence of "历史" and a policy word.
    if has_history and has_live and (has_listing_context or has_constraints):
        return QueryRoute.MIXED
    has_listing_reference = bool(re.search(r"第\s*[\d一二三四五六七八九十]+\s*套|(?:这|那)(?:一)?套", cleaned))
    if has_rag and (has_listing_context or has_listing_reference) and not has_history:
        return QueryRoute.MIXED
    if has_rag:
        return QueryRoute.RAG
    if has_history:
        return QueryRoute.HISTORICAL_SNAPSHOT
    if has_sql or has_house_context or has_constraints:
        return QueryRoute.SQL
    if has_weather:
        return QueryRoute.WEATHER

    if (_ANAPHORA_PATTERN.match(cleaned) or _SEARCH_FOLLOWUP_PATTERN.search(cleaned)) and previous_user_queries:
        for previous in reversed(previous_user_queries):
            inherited = route_query(previous)
            if inherited is not QueryRoute.GENERAL:
                return inherited
    return QueryRoute.GENERAL


__all__ = ("QueryRoute", "route_query")
