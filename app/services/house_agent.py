"""Deterministic house context for the AI rental assistant."""

import re

from sqlalchemy.orm import Session

from app.models.house import HouseInfo


RENTAL_KEYWORDS = ("房", "租", "预算", "地铁", "小区", "公寓")


def parse_house_constraints(message: str) -> tuple[str | None, int | None]:
    region_match = re.search(r"([\u4e00-\u9fff]{2}(?:区|县))", message)
    budget_match = re.search(
        r"(?:最高|预算|不超过|以下|以内)?\s*(\d{3,6})\s*元?\s*(?:以下|以内|每月|/月)?",
        message,
    )
    region = region_match.group(1).removesuffix("区").removesuffix("县") if region_match else None
    max_price = int(budget_match.group(1)) if budget_match else None
    return region, max_price


def parse_rent_type(message: str) -> str | None:
    for rent_type in ("整租", "合租"):
        if rent_type in message:
            return rent_type
    return None


def merge_house_queries(messages: list[str]) -> str:
    if not any(keyword in message for message in messages for keyword in RENTAL_KEYWORDS):
        return ""
    region = None
    max_price = None
    rent_type = None
    for message in reversed(messages):
        parsed_region, parsed_price = parse_house_constraints(message)
        region = region or parsed_region
        max_price = max_price or parsed_price
        rent_type = rent_type or parse_rent_type(message)
        if region and max_price and rent_type:
            break
    parts = ["房源"]
    if region:
        parts.append(f"{region}区")
    if max_price:
        parts.append(f"预算{max_price}元以内")
    if rent_type:
        parts.append(rent_type)
    return " ".join(parts)


def find_house_candidates(db: Session, message: str, limit: int = 5) -> list[dict]:
    if not any(keyword in message for keyword in RENTAL_KEYWORDS):
        return []

    region, max_price = parse_house_constraints(message)
    rent_type = parse_rent_type(message)
    query = db.query(HouseInfo).filter(HouseInfo.available == 1)
    if region:
        query = query.filter(HouseInfo.region.contains(region))
    if max_price is not None:
        query = query.filter(HouseInfo.price <= max_price)
    if rent_type:
        query = query.filter(HouseInfo.rent_type == rent_type)
    houses = query.order_by(HouseInfo.page_views.desc(), HouseInfo.id.desc()).limit(limit).all()
    return [
        {
            "id": house.id,
            "title": house.title,
            "region": house.region,
            "community": house.community,
            "price": house.price,
            "area": house.area,
            "rooms": house.rooms,
            "rent_type": house.rent_type,
            "subway": bool(house.subway),
        }
        for house in houses
    ]


def format_house_context(candidates: list[dict]) -> str:
    if not candidates:
        return "房源查询结果（内部数据）：匹配数量=0。"
    lines = ["以下是数据库中的当前可用房源。只能依据这些事实推荐，不得编造价格、位置或房源编号："]
    for house in candidates:
        lines.append(
            "- ID {id}: {title}; 区域={region}; 小区={community}; 月租={price}; "
            "面积={area}; 户型={rooms}; 类型={rent_type}; 近地铁={subway}".format(**house)
        )
    return "\n".join(lines)
