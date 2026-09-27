"""Opt-in read-only integration checks against the configured local MySQL."""

from __future__ import annotations

import json
import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.core.time import utc_now_naive
from app.db.session import SessionLocal
from app.main import app
from app.models.appointment import AppointmentModel
from app.models.contract import Contract
from app.models.house import HouseInfo
from app.services.occupancy import expired_pending_condition
from app.services.occupancy import market_available_house_condition
from app.services.house_capabilities import public_visible_house_condition
from app.services.react_tools import search_houses_by_criteria


pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        os.getenv("RUN_MYSQL_INTEGRATION") != "1",
        reason="set RUN_MYSQL_INTEGRATION=1 to use the configured local MySQL",
    ),
]


def test_mysql_schema_and_seed_inventory_are_available():
    with SessionLocal() as db:
        version = db.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
        assert version == "013_reconciliation_workflow"
        assert db.query(HouseInfo).count() >= 1
        assert db.execute(text("SELECT COUNT(*) FROM user_info")).scalar_one() >= 1
        assert db.query(HouseInfo).filter(
            HouseInfo.ownership_status.is_(None)
            | HouseInfo.ownership_status.notin_(("pending", "verified", "rejected"))
        ).count() == 0
        assert db.query(HouseInfo).filter(
            HouseInfo.ownership_status == "verified", HouseInfo.landlord_id.is_(None)
        ).count() == 0


def test_legacy_pending_states_are_normalized():
    now = utc_now_naive()
    with SessionLocal() as db:
        assert db.query(Contract).filter(Contract.payment_status == "pending", Contract.expires_at.is_(None)).count() == 0
        assert db.query(Contract).filter(expired_pending_condition(now)).count() == 0
        assert db.query(AppointmentModel).filter(
            AppointmentModel.status == "pending",
            AppointmentModel.time <= now,
        ).count() == 0


def test_public_house_api_matches_mysql_counts_and_filters():
    client = TestClient(app)
    with SessionLocal() as db:
        total = db.query(HouseInfo).filter(public_visible_house_condition()).count()
        available = db.query(HouseInfo).filter(
            market_available_house_condition(utc_now_naive()),
            public_visible_house_condition(),
        ).count()

    count_response = client.get("/api/v1/houses/count")
    assert count_response.status_code == 200
    assert count_response.json()["data"] == total

    list_response = client.get(
        "/api/v1/houses/",
        params={"available": 1, "per_page": 100, "no_cache": True},
    )
    assert list_response.status_code == 200
    payload = list_response.json()["data"]
    assert payload["total"] == available
    assert len(payload["items"]) == available
    assert all(item["available"] == 1 for item in payload["items"])


def test_public_house_api_paginates_every_mysql_house_exactly_once():
    client = TestClient(app)
    seen_ids: list[int] = []
    page = 1
    while True:
        response = client.get(
            "/api/v1/houses/",
            params={"page": page, "per_page": 13, "no_cache": True},
        )
        assert response.status_code == 200
        data = response.json()["data"]
        seen_ids.extend(item["id"] for item in data["items"])
        if page >= data["pages"]:
            break
        page += 1
    with SessionLocal() as db:
        expected_ids = {row[0] for row in db.query(HouseInfo.id).all()}
    assert len(seen_ids) == len(set(seen_ids))
    assert set(seen_ids) == expected_ids


@pytest.mark.parametrize("minimum,maximum", [
    (0, 999),
    (1000, 1999),
    (2000, 2999),
    (3000, 4999),
    (5000, 20_000),
])
def test_public_house_api_price_bands_match_mysql(minimum, maximum):
    response = TestClient(app).get(
        "/api/v1/houses/",
        params={
            "min_price": minimum,
            "max_price": maximum,
            "per_page": 100,
            "no_cache": True,
        },
    )
    assert response.status_code == 200
    with SessionLocal() as db:
        expected = db.query(HouseInfo).filter(
            HouseInfo.price >= minimum,
            HouseInfo.price <= maximum,
        ).count()
    data = response.json()["data"]
    assert data["total"] == expected
    assert all(minimum <= item["price"] <= maximum for item in data["items"])


def test_legacy_cross_table_references_have_no_house_or_chat_orphans():
    statements = {
        "contract_house": """
            SELECT COUNT(*) FROM contract c LEFT JOIN house_info h ON h.id=c.houseId
            WHERE c.houseId IS NOT NULL AND h.id IS NULL
        """,
        "rental_house": """
            SELECT COUNT(*) FROM rental r LEFT JOIN house_info h ON h.id=r.house_id
            WHERE r.house_id IS NOT NULL AND h.id IS NULL
        """,
        "chat_session_user": """
            SELECT COUNT(*) FROM chat_session s LEFT JOIN user_info u ON u.id=s.user_id
            WHERE u.id IS NULL
        """,
        "chat_message_session": """
            SELECT COUNT(*) FROM chat_message m LEFT JOIN chat_session s ON s.id=m.session_id
            WHERE s.id IS NULL
        """,
    }
    with SessionLocal() as db:
        assert {name: db.execute(text(sql)).scalar_one() for name, sql in statements.items()} == {
            name: 0 for name in statements
        }


@pytest.mark.parametrize("params", [
    {"min_price": -1},
    {"max_price": -1},
    {"min_price": 2000, "max_price": 1000},
])
def test_public_house_api_rejects_invalid_price_ranges(params):
    assert TestClient(app).get("/api/v1/houses/", params=params).status_code == 422


@pytest.mark.parametrize(
    "region",
    ["岳麓", "芙蓉", "天心", "开福", "雨花", "望城", "长沙县", "浏阳", "宁乡"],
)
def test_ai_sql_tool_rows_are_real_available_mysql_rows(region):
    result = json.loads(search_houses_by_criteria.invoke({
        "region": region,
        "min_price": 0,
        "max_price": 20_000,
        "limit": 5,
    }))
    assert "error" not in result
    with SessionLocal() as db:
        expected_total = db.query(HouseInfo).filter(
            market_available_house_condition(utc_now_naive()),
            HouseInfo.region == region,
            HouseInfo.price >= 0,
            HouseInfo.price <= 20_000,
        ).count()
        assert result["total_count"] == expected_total
        for item in result["houses"]:
            row = db.get(HouseInfo, item["id"])
            assert row is not None
            assert row.available == 1
            assert row.region == region
            assert 0 <= row.price <= 20_000


def test_market_search_excludes_every_guarded_legacy_rental():
    response = TestClient(app).get(
        "/api/v1/houses/",
        params={"available": 1, "per_page": 100, "no_cache": True},
    )
    returned_ids = {item["id"] for item in response.json()["data"]["items"]}
    with SessionLocal() as db:
        guarded_ids = {
            row[0]
            for row in db.execute(text("""
                SELECT DISTINCT h.id
                FROM house_info h
                JOIN rental r ON r.house_id = h.id
                WHERE h.available = 1 AND r.contract_id IS NULL
            """))
        }
    # Legacy rentals are intentionally purged; retain the invariant if any
    # guarded rows are introduced by future fixtures.
    assert returned_ids.isdisjoint(guarded_ids)


def test_yuelu_budget_listing_is_verified_and_title_matches_rooms():
    result = json.loads(search_houses_by_criteria.invoke({
        "region": "岳麓区",
        "min_price": 1000,
        "max_price": 2000,
        "limit": 5,
    }))

    assert result["total_count"] >= 1
    house = next(item for item in result["houses"] if item["id"] == 50)
    assert house["title"] == "整租·桃花村 2室1厅 南北"
    assert house["rooms"] == "2室1厅1卫"
    assert house["verification_status"] == "verified"
    assert house["verification_issues"] == []
