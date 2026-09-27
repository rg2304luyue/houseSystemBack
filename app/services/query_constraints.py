"""Deterministic rental-search constraints shared by routing and validation.

The language model may choose a tool, but it is not trusted to preserve the
user's filters.  This module extracts the small, auditable set of filters the
SQL tools support and merges conversational updates newest-first.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any, Iterable, Mapping, Sequence


_REGION_ALIASES = {
    "芙蓉": "芙蓉",
    "天心": "天心",
    "岳麓": "岳麓",
    "开福": "开福",
    "雨花": "雨花",
    "望城": "望城",
    "长沙": "长沙县",
    "长沙县": "长沙县",
    "浏阳": "浏阳",
    "宁乡": "宁乡",
}
_REGION_PATTERN = re.compile(
    r"(?:长沙市)?(芙蓉|天心|岳麓|开福|雨花|望城|长沙县|浏阳|宁乡)(?:区|县|市)?"
)
_NUMBER = r"(?:\d{1,7}|[零〇一二两三四五六七八九十百千万]+)"
_ROOM_PATTERN = re.compile(r"([一二两三四五六七八九十\d]+)\s*(?:室|居室)")
_HOUSE_ID_PATTERN = re.compile(r"(?:房源\s*)?(?:ID|编号)\s*[:：#]?\s*(\d+)", re.IGNORECASE)
_ANSWER_HOUSE_ID_PATTERN = re.compile(r"房源\s*(?:ID|编号)\s*[:：#]?\s*(\d+)", re.IGNORECASE)
_ORDINAL_PATTERN = re.compile(r"第\s*([一二两三四五六七八九十\d]+)\s*套")
_SINGULAR_REFERENCE_PATTERN = re.compile(
    r"^(?:这|那)(?:一)?套(?:呢|怎么样|如何)?[\s，。？?!]*$|"
    r"^(?:它|这个|那个)(?:呢|怎么样|如何)?[\s，。？?!]*$"
)
_SINGULAR_REFERENCE_MENTION_PATTERN = re.compile(
    r"(?:这|那)(?:一)?套|(?:这个|那个)房源|(?:^|[，。\s])它(?:的|呢|怎么样|如何|多少钱|多大|有)"
)


_CHINESE_DIGITS = {
    "零": 0,
    "〇": 0,
    "一": 1,
    "二": 2,
    "两": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
}
_CHINESE_UNITS = {"十": 10, "百": 100, "千": 1000, "万": 10000}
_SEARCH_RESET_PATTERN = re.compile(r"重新开始找房|清空条件|忘掉之前(?:的)?条件")


def _current_search_messages(messages: Sequence[Mapping[str, Any] | str]) -> list[Mapping[str, Any] | str]:
    """Discard search history before the user's latest explicit reset."""

    items = list(messages)
    for index in range(len(items) - 1, -1, -1):
        item = items[index]
        content = item if isinstance(item, str) else str(item.get("content", ""))
        is_user = isinstance(item, str) or item.get("role") == "user"
        if is_user and _SEARCH_RESET_PATTERN.search(content):
            return items[index:]
    return items


def parse_number(value: str) -> int:
    """Parse Arabic or common Chinese integer notation."""

    cleaned = value.strip()
    if cleaned.isdigit():
        return int(cleaned)
    if not cleaned or any(
        char not in _CHINESE_DIGITS and char not in _CHINESE_UNITS
        for char in cleaned
    ):
        raise ValueError("不是受支持的数字")

    total = 0
    section = 0
    current = 0
    for char in cleaned:
        if char in _CHINESE_DIGITS:
            current = _CHINESE_DIGITS[char]
            continue
        unit = _CHINESE_UNITS[char]
        if unit == 10000:
            section += current
            total += (section or 1) * unit
            section = 0
            current = 0
        else:
            section += (current or 1) * unit
            current = 0
    return total + section + current


def normalize_region(value: str) -> str:
    """Return the exact region representation stored by ``house_info``."""

    cleaned = value.strip().replace("长沙市", "")
    if cleaned == "长沙县":
        return cleaned
    key = cleaned.removesuffix("区").removesuffix("县").removesuffix("市")
    normalized = _REGION_ALIASES.get(key)
    if normalized is None:
        raise ValueError("region 必须是长沙市有效区县")
    return normalized


@dataclass(frozen=True)
class HouseSearchConstraints:
    region: str | None = None
    min_price: int | None = None
    max_price: int | None = None
    min_area: float | None = None
    max_area: float | None = None
    room_count: int | None = None
    rent_type: str | None = None
    subway: bool | None = None
    decoration: str | None = None
    explicit_fields: frozenset[str] = field(default_factory=frozenset)

    def to_tool_args(self) -> dict[str, Any]:
        values: dict[str, Any] = {
            "region": self.region,
            "min_price": self.min_price,
            "max_price": self.max_price,
            "min_area": self.min_area,
            "max_area": self.max_area,
            "rooms": f"{self.room_count}室" if self.room_count is not None else None,
            "rent_type": self.rent_type,
            "subway": self.subway,
            "decoration": self.decoration,
        }
        return {key: value for key, value in values.items() if value is not None}

    @property
    def has_filters(self) -> bool:
        return bool(self.explicit_fields)


@dataclass(frozen=True)
class HouseReference:
    house_id: int | None = None
    ambiguous: bool = False


def _extract_range(
    text: str, *, unit_pattern: str
) -> tuple[float | None, float | None, bool]:
    range_match = re.search(
        rf"(?P<low>{_NUMBER})\s*(?:-|—|~|～|到|至)\s*"
        rf"(?P<high>{_NUMBER})\s*(?:{unit_pattern})",
        text,
    )
    if range_match:
        return (
            float(parse_number(range_match.group("low"))),
            float(parse_number(range_match.group("high"))),
            True,
        )
    return None, None, False


def _extract_price(text: str) -> tuple[int | None, int | None, bool]:
    if re.search(r"(?:预算|价格|租金|月租)\s*不限|不限\s*(?:预算|价格|租金|月租)", text):
        return None, None, True

    low, high, found = _extract_range(text, unit_pattern=r"元(?:/月|每月)?")
    if found:
        return int(low), int(high), True

    max_match = re.search(
        rf"(?:预算\s*)?(?P<value>{_NUMBER})\s*元?\s*"
        r"(?:以内|以下|封顶|最多|不超过|不高于)",
        text,
    ) or re.search(
        rf"(?:最高|不超过|不高于|至多)\s*(?P<value>{_NUMBER})\s*元?",
        text,
    )
    if max_match:
        return None, parse_number(max_match.group("value")), True

    min_match = re.search(
        rf"(?P<value>{_NUMBER})\s*元?\s*(?:以上|起|起步)", text
    ) or re.search(rf"(?:最低|不少于|不低于)\s*(?P<value>{_NUMBER})\s*元?", text)
    if min_match:
        return parse_number(min_match.group("value")), None, True

    approximate = re.search(rf"(?P<value>{_NUMBER})\s*元?\s*(?:左右|上下)", text)
    if approximate:
        value = parse_number(approximate.group("value"))
        tolerance = max(1, round(value * 0.1))
        return max(0, value - tolerance), value + tolerance, True

    budget = re.search(rf"(?:预算|月租|租金|价格)\s*(?P<value>{_NUMBER})\s*元?", text)
    if budget:
        return None, parse_number(budget.group("value")), True

    # In a rental utterance, a bare amount followed by 元 conventionally means
    # the budget ceiling.  Requiring the unit avoids treating room/area counts
    # as prices.
    bare = re.search(rf"(?P<value>{_NUMBER})\s*元(?:/月|每月)?", text)
    if bare:
        return None, parse_number(bare.group("value")), True
    return None, None, False


def _extract_area(text: str) -> tuple[float | None, float | None, bool]:
    if re.search(r"(?:面积|大小)\s*不限|不限\s*(?:面积|大小)", text):
        return None, None, True
    low, high, found = _extract_range(text, unit_pattern=r"(?:㎡|平米|平方米)")
    if found:
        return low, high, True
    maximum = re.search(
        rf"(?P<value>{_NUMBER})\s*(?:㎡|平米|平方米)\s*(?:以内|以下|不超过)", text
    )
    if maximum:
        return None, float(parse_number(maximum.group("value"))), True
    minimum = re.search(
        rf"(?P<value>{_NUMBER})\s*(?:㎡|平米|平方米)\s*(?:以上|起)", text
    )
    if minimum:
        return float(parse_number(minimum.group("value"))), None, True
    return None, None, False


def extract_house_constraints(text: str) -> HouseSearchConstraints:
    cleaned = " ".join(text.strip().split())[:4000]
    values: dict[str, Any] = {}
    explicit: set[str] = set()

    if re.search(r"(?:地区|区域|区县)\s*不限|不限\s*(?:地区|区域|区县)", cleaned):
        values["region"] = None
        explicit.add("region")
    else:
        region_matches = _positive_entity_matches(_REGION_PATTERN, cleaned)
        if region_matches:
            values["region"] = normalize_region(region_matches[-1].group(0))
            explicit.add("region")

    min_price, max_price, price_found = _extract_price(cleaned)
    if price_found:
        values.update(min_price=min_price, max_price=max_price)
        explicit.update(("min_price", "max_price"))

    min_area, max_area, area_found = _extract_area(cleaned)
    if area_found:
        values.update(min_area=min_area, max_area=max_area)
        explicit.update(("min_area", "max_area"))

    if re.search(r"(?:户型|室数)\s*不限|不限\s*(?:户型|室数)", cleaned):
        values["room_count"] = None
        explicit.add("room_count")
    else:
        room_match = _ROOM_PATTERN.search(cleaned)
        if room_match:
            values["room_count"] = parse_number(room_match.group(1))
            explicit.add("room_count")

    if re.search(r"(?:出租方式|租法|类型)\s*不限|不限\s*(?:出租方式|租法|类型)", cleaned):
        values["rent_type"] = None
        explicit.add("rent_type")
    else:
        rent_matches = _positive_entity_matches(re.compile(r"整租|合租"), cleaned)
        if rent_matches:
            values["rent_type"] = rent_matches[-1].group(0)
            explicit.add("rent_type")

    if re.search(r"(?:地铁|交通)\s*不限|不要求\s*(?:近)?地铁", cleaned):
        values["subway"] = None
        explicit.add("subway")
    elif re.search(r"(?:不要|不近|远离)\s*地铁", cleaned):
        values["subway"] = False
        explicit.add("subway")
    elif re.search(r"(?:近地铁|地铁房|地铁附近|靠近地铁|地铁口)", cleaned):
        values["subway"] = True
        explicit.add("subway")

    if re.search(r"装修\s*不限|不限\s*装修", cleaned):
        values["decoration"] = None
        explicit.add("decoration")
    else:
        for decoration in ("精装", "简装", "毛坯"):
            if decoration in cleaned:
                values["decoration"] = decoration
                explicit.add("decoration")
                break

    return HouseSearchConstraints(**values, explicit_fields=frozenset(explicit))


def _positive_entity_matches(pattern: re.Pattern, text: str) -> list[re.Match]:
    """Keep explicitly requested entities while discarding local negations."""

    return [
        match for match in pattern.finditer(text)
        if not re.search(r"(?:不要|不选|不考虑|排除|不想要|不在|不是)\s*$", text[:match.start()])
    ]


def _user_contents(messages: Sequence[Mapping[str, Any] | str]) -> Iterable[str]:
    for item in messages:
        if isinstance(item, str):
            if item.strip():
                yield item
        elif item.get("role") == "user" and str(item.get("content", "")).strip():
            yield str(item["content"])


def merge_house_constraints(
    messages: Sequence[Mapping[str, Any] | str],
) -> HouseSearchConstraints:
    selected: dict[str, Any] = {}
    resolved: set[str] = set()
    current_messages = _current_search_messages(messages)
    normalized_messages: list[Mapping[str, Any] | str] = []
    for index, item in enumerate(current_messages):
        if isinstance(item, Mapping) and item.get("role") == "user" and index > 0:
            content = str(item.get("content", "")).strip()
            previous = current_messages[index - 1]
            if (
                re.fullmatch(r"\d{1,7}", content)
                and isinstance(previous, Mapping)
                and previous.get("role") == "assistant"
                and "每月租金最多能接受多少元" in str(previous.get("content", ""))
            ):
                item = {**item, "content": f"预算{content}元"}
        normalized_messages.append(item)
    for content in reversed(list(_user_contents(normalized_messages))):
        parsed = extract_house_constraints(content)
        for field_name in parsed.explicit_fields:
            if field_name in resolved:
                continue
            selected[field_name] = getattr(parsed, field_name)
            resolved.add(field_name)
    return HouseSearchConstraints(**selected, explicit_fields=frozenset(resolved))


def get_search_clarification(messages: Sequence[Mapping[str, Any] | str]) -> str | None:
    """Ask for an explicit budget instead of inventing a relative adjustment."""

    contents = list(_user_contents(messages))
    if not contents:
        return None
    latest = contents[-1]
    regions = _positive_entity_matches(_REGION_PATTERN, latest)
    if len({normalize_region(match.group(0)) for match in regions}) > 1:
        correction = re.search(r"(?:改成|改为|换成|换到|换|只要|只看)\s*(?:长沙市)?(?:芙蓉|天心|岳麓|开福|雨花|望城|长沙县|浏阳|宁乡)", latest)
        if correction is None:
            return "你想先看哪个区域？目前一次可以按一个区域筛选，我会保留其他找房条件。"
    parsed = extract_house_constraints(latest)
    if {"min_price", "max_price"} & parsed.explicit_fields:
        return None
    if re.search(r"贵一点|贵些|贵点|便宜一点|便宜些|便宜点|增加预算|提高预算|降低预算|预算.{0,5}(?:加|减|放宽)", latest):
        return "每月租金最多能接受多少元？我会保留你之前的其他找房条件。"
    return None


def recent_house_ids(messages: Sequence[Mapping[str, Any]]) -> list[int]:
    """Return distinct listing IDs from the most recent displayed listing turn."""

    for item in reversed(_current_search_messages(messages)):
        if isinstance(item, str):
            continue
        if item.get("role") != "assistant":
            continue
        ids = [int(value) for value in _ANSWER_HOUSE_ID_PATTERN.findall(str(item.get("content", "")))]
        if ids:
            return list(dict.fromkeys(house_id for house_id in ids if house_id > 0))[:100]
    return []


def resolve_house_reference(messages: Sequence[Mapping[str, Any]]) -> HouseReference:
    user_messages = [
        str(item.get("content", ""))
        for item in messages
        if item.get("role") == "user" and str(item.get("content", "")).strip()
    ]
    if not user_messages:
        return HouseReference()
    latest = user_messages[-1].strip()
    explicit = _HOUSE_ID_PATTERN.search(latest)
    if explicit:
        return HouseReference(house_id=int(explicit.group(1)))

    ids = recent_house_ids(messages)
    ordinal = _ORDINAL_PATTERN.search(latest)
    if ordinal:
        index = parse_number(ordinal.group(1)) - 1
        if 0 <= index < len(ids):
            return HouseReference(house_id=ids[index])
        return HouseReference(ambiguous=True)
    if (
        _SINGULAR_REFERENCE_PATTERN.match(latest)
        or _SINGULAR_REFERENCE_MENTION_PATTERN.search(latest)
    ):
        if len(ids) == 1:
            return HouseReference(house_id=ids[0])
        return HouseReference(ambiguous=True)
    return HouseReference()


def _normalized_room_count(value: Any) -> int | None:
    if value in (None, ""):
        return None
    if isinstance(value, int):
        return value
    match = _ROOM_PATTERN.search(str(value))
    return parse_number(match.group(1)) if match else None


def normalized_applied_filters(filters: Mapping[str, Any] | None) -> dict[str, Any]:
    source = filters or {}
    region = source.get("region")
    subway_value = source.get("subway")
    if isinstance(subway_value, str):
        lowered = subway_value.strip().casefold()
        if lowered in {"true", "1", "yes"}:
            subway_value = True
        elif lowered in {"false", "0", "no"}:
            subway_value = False
        elif lowered:
            raise ValueError("subway 必须是布尔值")
        else:
            subway_value = None
    elif subway_value not in {None, True, False, 0, 1}:
        raise ValueError("subway 必须是布尔值")
    return {
        "region": normalize_region(str(region)) if region else None,
        "min_price": int(source["min_price"]) if source.get("min_price") is not None else None,
        "max_price": int(source["max_price"]) if source.get("max_price") is not None else None,
        "min_area": float(source["min_area"]) if source.get("min_area") is not None else None,
        "max_area": float(source["max_area"]) if source.get("max_area") is not None else None,
        "room_count": _normalized_room_count(source.get("rooms", source.get("room_count"))),
        "rent_type": str(source["rent_type"]).strip() if source.get("rent_type") else None,
        "subway": bool(subway_value) if subway_value is not None else None,
        "decoration": str(source["decoration"]).strip() if source.get("decoration") else None,
    }


def validate_applied_filters(
    expected: HouseSearchConstraints, applied_filters: Mapping[str, Any] | None
) -> bool:
    try:
        applied = normalized_applied_filters(applied_filters)
    except (TypeError, ValueError):
        return False
    for field_name in (
        "region", "min_price", "max_price", "min_area", "max_area",
        "room_count", "rent_type", "subway", "decoration",
    ):
        if applied[field_name] != getattr(expected, field_name):
            return False
    return True


def house_matches_filters(house: Mapping[str, Any], applied_filters: Mapping[str, Any]) -> bool:
    try:
        filters = normalized_applied_filters(applied_filters)
        if filters["region"] is not None and normalize_region(str(house.get("region", ""))) != filters["region"]:
            return False
        price = house.get("price")
        if filters["min_price"] is not None and (price is None or float(price) < filters["min_price"]):
            return False
        if filters["max_price"] is not None and (price is None or float(price) > filters["max_price"]):
            return False
        area = house.get("area")
        if filters["min_area"] is not None and (area is None or float(area) < filters["min_area"]):
            return False
        if filters["max_area"] is not None and (area is None or float(area) > filters["max_area"]):
            return False
        if filters["room_count"] is not None and _normalized_room_count(house.get("rooms")) != filters["room_count"]:
            return False
        if filters["rent_type"] is not None and str(house.get("rent_type") or "") != filters["rent_type"]:
            return False
        if filters["subway"] is not None and bool(house.get("subway")) != filters["subway"]:
            return False
        if filters["decoration"] is not None and filters["decoration"] not in str(house.get("decoration") or ""):
            return False
    except (TypeError, ValueError):
        return False
    return True


__all__ = (
    "HouseReference",
    "HouseSearchConstraints",
    "extract_house_constraints",
    "get_search_clarification",
    "house_matches_filters",
    "merge_house_constraints",
    "normalize_region",
    "normalized_applied_filters",
    "parse_number",
    "resolve_house_reference",
    "recent_house_ids",
    "validate_applied_filters",
)
