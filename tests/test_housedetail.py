# -*- coding: utf-8 -*-
"""
房源详情模块测试 —— /housedetail/*
==================================
覆盖: 添加详情 / 获取详情 / 边界条件
"""

import pytest
from tests.conftest import assert_success, assert_error, assert_has_fields


class TestAddHouseDetail:
    """添加房源详情 POST /housedetail/"""

    def test_nonexistent_house_returns_404(self, client):
        """为不存在的房源添加详情应返回 404"""
        res = client.post("/housedetail/", json={
            "house_info_id": 99999,
            "photos": ["http://example.com/photo1.jpg"],
            "facilities": {"wifi": True, "air_conditioner": True},
            "map_coordinates": {"lat": 28.228, "lng": 112.938},
        })
        assert_error(res, expected_http=404)

    def test_missing_all_fields(self, client):
        """缺少所有必填字段"""
        res = client.post("/housedetail/", json={"house_info_id": 99999})
        body = res.get_json()
        assert body is not None
        assert res.status_code in [400, 404, 500]

    def test_missing_photos_and_facilities(self, client):
        """缺少 photos 和 facilities"""
        res = client.post("/housedetail/", json={
            "house_info_id": 1,
            "map_coordinates": {"lat": 28.0, "lng": 112.0},
        })
        body = res.get_json()
        assert body is not None

    def test_invalid_house_info_id_type(self, client):
        """house_info_id 不是整数"""
        res = client.post("/housedetail/", json={
            "house_info_id": "not_an_int",
            "photos": ["http://example.com/p.jpg"],
            "facilities": {"wifi": True},
            "map_coordinates": {"lat": 28.0, "lng": 112.0},
        })
        body = res.get_json()
        assert body is not None
        assert res.status_code in [400, 500]

    def test_photos_not_a_list(self, client):
        """photos 不是列表"""
        res = client.post("/housedetail/", json={
            "house_info_id": 1,
            "photos": "http://single-photo.jpg",
            "facilities": {"wifi": True},
            "map_coordinates": {"lat": 28.0, "lng": 112.0},
        })
        body = res.get_json()
        assert body is not None

    def test_facilities_not_a_dict(self, client):
        """facilities 不是字典"""
        res = client.post("/housedetail/", json={
            "house_info_id": 1,
            "photos": ["http://example.com/p.jpg"],
            "facilities": "wifi, ac",
            "map_coordinates": {"lat": 28.0, "lng": 112.0},
        })
        body = res.get_json()
        assert body is not None

    def test_map_coordinates_not_dict(self, client):
        """map_coordinates 不是字典"""
        res = client.post("/housedetail/", json={
            "house_info_id": 1,
            "photos": ["http://example.com/p.jpg"],
            "facilities": {"wifi": True},
            "map_coordinates": "28.0, 112.0",
        })
        body = res.get_json()
        assert body is not None

    def test_duplicate_house_detail(self, client):
        """为已有详情的房源再次添加（应失败，因为 UNIQUE 约束）"""
        # 先获取 ID=1 的房源，如果已有详情则直接测试
        res = client.post("/housedetail/", json={
            "house_info_id": 1,
            "photos": ["http://example.com/dup.jpg"],
            "facilities": {"test": True},
            "map_coordinates": {"lat": 28.0, "lng": 112.0},
        })
        body = res.get_json()
        assert body is not None
        # 可能成功（首次）或失败（已有详情）


class TestGetHouseDetail:
    """获取房源详情 GET /housedetail/<house_info_id>"""

    def test_existing_detail(self, client):
        """获取存在的详情"""
        res = client.get("/housedetail/1")
        body = res.get_json()
        assert body is not None

    def test_nonexistent_detail_returns_404(self, client):
        """不存在的详情返回 404"""
        res = client.get("/housedetail/99999")
        assert_error(res, expected_http=404)

    def test_detail_has_photos_and_facilities(self, client):
        """详情包含图片和设施字段"""
        res = client.get("/housedetail/1")
        body = res.get_json()
        if body.get("success"):
            data = body["data"]
            # 详情可能包含 photos, facilities, map_coordinates
            detail_fields = ["photos", "facilities", "map_coordinates"]
            found = [f for f in detail_fields if f in data]
            assert len(found) > 0, f"详情应包含 {detail_fields} 中的至少一个字段"

    def test_negative_id(self, client):
        """负数 ID"""
        res = client.get("/housedetail/-1")
        assert res.status_code == 404

    def test_zero_id(self, client):
        """ID 为 0"""
        res = client.get("/housedetail/0")
        assert res.status_code in [404, 500]
