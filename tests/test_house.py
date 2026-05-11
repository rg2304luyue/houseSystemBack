# -*- coding: utf-8 -*-
"""
房源模块测试 —— /houseinfo/*
=============================
覆盖: 列表分页 / 多维筛选 / 统计图表 / 详情 / 浏览量 / CRUD
"""

import pytest
from tests.conftest import assert_success, assert_error, assert_has_fields


# ══════════════════════════════════════════════════════════════
#  房源列表 & 分页
# ══════════════════════════════════════════════════════════════

class TestHouseList:
    """房源列表 GET /houseinfo/"""

    def test_get_all_houses_returns_valid_structure(self, client):
        """列表接口返回正确的数据结构"""
        res = client.get("/houseinfo/")
        body = assert_success(res)
        data = body["data"]
        assert_has_fields(data, "items", "total", "page", "per_page", "pages")
        assert isinstance(data["items"], list)
        assert isinstance(data["total"], int)

    def test_pagination_page1_per3(self, client):
        """分页 —— 第1页每页3条"""
        res = client.get("/houseinfo/?page=1&per_page=3")
        body = assert_success(res)
        data = body["data"]
        assert len(data["items"]) <= 3
        assert data["per_page"] == 3
        assert data["page"] == 1

    def test_pagination_page2(self, client):
        """分页 —— 第2页"""
        res = client.get("/houseinfo/?page=2&per_page=5")
        body = assert_success(res)
        assert body["data"]["page"] == 2

    def test_pagination_large_per_page(self, client):
        """分页 —— 每页100条"""
        res = client.get("/houseinfo/?per_page=100")
        body = assert_success(res)
        assert len(body["data"]["items"]) <= 100

    def test_page_out_of_range_returns_empty(self, client):
        """超出范围的页码返回空列表"""
        res = client.get("/houseinfo/?page=99999&per_page=10")
        body = assert_success(res)
        assert body["data"]["items"] == []

    def test_default_per_page(self, client):
        """默认每页条数应为 10"""
        res = client.get("/houseinfo/")
        body = assert_success(res)
        assert body["data"]["per_page"] == 10

    def test_pages_calculation(self, client):
        """总页数计算正确"""
        res = client.get("/houseinfo/?page=1&per_page=5")
        body = assert_success(res)
        data = body["data"]
        expected_pages = (data["total"] + 4) // 5
        assert data["pages"] == expected_pages


# ══════════════════════════════════════════════════════════════
#  多维筛选
# ══════════════════════════════════════════════════════════════

class TestHouseFilter:
    """房源筛选"""

    @pytest.mark.parametrize("rent_type", ["整租", "合租"])
    def test_filter_by_rent_type(self, client, rent_type):
        """按租赁方式筛选"""
        res = client.get(f"/houseinfo/?rent_type={rent_type}")
        body = assert_success(res)
        for item in body["data"]["items"]:
            assert item["rent_type"] == rent_type, (
                f"房源 {item['id']} 的 rent_type 为 {item['rent_type']}，预期 {rent_type}"
            )

    def test_filter_by_price_range(self, client):
        """按价格范围筛选"""
        res = client.get("/houseinfo/?min_price=1000&max_price=5000")
        body = assert_success(res)
        for item in body["data"]["items"]:
            assert 1000 <= item["price"] <= 5000, (
                f"房源 {item['id']} 价格 {item['price']} 不在 [1000, 5000] 范围内"
            )

    def test_filter_min_price_only(self, client):
        """仅设置最低价"""
        res = client.get("/houseinfo/?min_price=3000")
        body = assert_success(res)
        for item in body["data"]["items"]:
            assert item["price"] >= 3000

    def test_filter_max_price_only(self, client):
        """仅设置最高价"""
        res = client.get("/houseinfo/?max_price=2000")
        body = assert_success(res)
        for item in body["data"]["items"]:
            assert item["price"] <= 2000

    @pytest.mark.slow
    @pytest.mark.parametrize("region", ["岳麓", "雨花", "天心", "开福", "芙蓉"])
    def test_filter_by_region(self, client, region):
        """按区域筛选"""
        res = client.get(f"/houseinfo/?region={region}")
        body = assert_success(res)
        for item in body["data"]["items"]:
            assert region in item.get("region", ""), (
                f"房源 {item['id']} 的 region '{item.get('region')}' 不包含 '{region}'"
            )

    def test_filter_by_subway(self, client):
        """按近地铁筛选"""
        res = client.get("/houseinfo/?subway=1")
        body = assert_success(res)
        for item in body["data"]["items"]:
            assert item["subway"] == 1

    def test_filter_not_near_subway(self, client):
        """筛选不近地铁"""
        res = client.get("/houseinfo/?subway=0")
        body = assert_success(res)
        for item in body["data"]["items"]:
            assert item["subway"] == 0

    def test_filter_by_available(self, client):
        """按上架状态筛选"""
        res = client.get("/houseinfo/?available=1")
        body = assert_success(res)
        for item in body["data"]["items"]:
            assert item["available"] == 1

    def test_filter_by_multiple_rooms(self, client):
        """多选户型（一居和两居）"""
        res = client.get("/houseinfo/?rooms=一居,两居")
        body = assert_success(res)
        for item in body["data"]["items"]:
            rooms = item.get("rooms", "")
            assert ("1室" in rooms or "2室" in rooms), (
                f"房源 {item['id']} rooms='{rooms}' 不是一居或两居"
            )

    def test_filter_by_four_plus_rooms(self, client):
        """四居及以上"""
        res = client.get("/houseinfo/?rooms=四居+")
        body = assert_success(res)
        for item in body["data"]["items"]:
            rooms = item.get("rooms", "")
            assert any(f"{i}室" in rooms for i in range(4, 10)), (
                f"房源 {item['id']} rooms='{rooms}' 不是四居及以上"
            )

    def test_filter_by_orientation(self, client):
        """按朝向筛选"""
        res = client.get("/houseinfo/?orientation=南")
        body = assert_success(res)
        for item in body["data"]["items"]:
            assert "南" in item.get("direction", "")

    def test_filter_by_decoration(self, client):
        """按装修筛选"""
        res = client.get("/houseinfo/?decoration=精装")
        body = assert_success(res)
        for item in body["data"]["items"]:
            assert "精装" in item.get("decoration", "")

    def test_filter_by_community_keyword(self, client):
        """按小区关键词搜索"""
        res = client.get("/houseinfo/?community=小区")
        body = assert_success(res)
        # 所有结果的小区名应包含关键词
        for item in body["data"]["items"]:
            assert "小区" in item.get("community", "")

    def test_combined_filters(self, client):
        """组合筛选条件"""
        res = client.get(
            "/houseinfo/?region=岳麓&rent_type=整租&min_price=1000&max_price=5000&subway=1"
        )
        body = assert_success(res)
        for item in body["data"]["items"]:
            assert "岳麓" in item.get("region", "")
            assert item["rent_type"] == "整租"
            assert item["price"] >= 1000


# ══════════════════════════════════════════════════════════════
#  统计接口
# ══════════════════════════════════════════════════════════════

class TestHouseStats:
    """统计类接口"""

    def test_house_nums(self, client):
        """房源总数"""
        res = client.get("/houseinfo/houseNums")
        body = assert_success(res)
        assert isinstance(body["data"], int)
        assert body["data"] >= 0

    def test_hot_lists(self, client):
        """热门房源 Top 4"""
        res = client.get("/houseinfo/hotLists")
        body = assert_success(res)
        data = body["data"]
        assert isinstance(data, list)
        assert len(data) <= 4

    def test_new_lists(self, client):
        """最新房源 Top 4"""
        res = client.get("/houseinfo/newLists")
        body = assert_success(res)
        data = body["data"]
        assert isinstance(data, list)
        assert len(data) <= 4

    def test_pie_data_structure(self, client):
        """户型饼图数据结构"""
        res = client.get("/houseinfo/piedata")
        body = assert_success(res)
        data = body["data"]
        assert isinstance(data, list)
        for item in data:
            assert_has_fields(item, "name", "value")
            assert isinstance(item["value"], int)

    def test_pie_data_sum_matches_total(self, client):
        """饼图数据总和等于房源总数"""
        res_pie = client.get("/houseinfo/piedata")
        res_nums = client.get("/houseinfo/houseNums")
        pie_total = sum(item["value"] for item in res_pie.get_json()["data"])
        house_total = res_nums.get_json()["data"]
        assert pie_total == house_total, (
            f"饼图总和 {pie_total} != 房源总数 {house_total}"
        )

    def test_column_data(self, client):
        """小区房源前20柱状图数据"""
        res = client.get("/houseinfo/columndata")
        body = assert_success(res)
        data = body["data"]
        assert_has_fields(data, "community_list", "num_list")
        assert len(data["community_list"]) <= 20
        assert len(data["community_list"]) == len(data["num_list"])


# ══════════════════════════════════════════════════════════════
#  房源详情
# ══════════════════════════════════════════════════════════════

class TestHouseDetail:
    """房源详情 GET /houseinfo/<id>"""

    def test_get_existing_house(self, client):
        """获取存在的房源"""
        res = client.get("/houseinfo/1")
        body = assert_success(res)
        assert body["data"]["id"] == 1

    def test_existing_house_has_required_fields(self, client):
        """房源详情包含必要字段"""
        res = client.get("/houseinfo/1")
        body = assert_success(res)
        data = body["data"]
        required = ["id", "title", "region", "price", "rent_type", "rooms", "area"]
        assert_has_fields(data, *required)

    def test_get_nonexistent_house(self, client):
        """不存在的房源返回 404"""
        res = client.get("/houseinfo/99999")
        assert_error(res, expected_http=404)

    def test_get_house_with_zero_id(self, client):
        """ID 为 0"""
        res = client.get("/houseinfo/0")
        # 通常返回 404，因为 ID 从 1 开始
        assert res.status_code in [404, 500]

    def test_get_house_with_string_id(self, client):
        """传入字符串 ID"""
        res = client.get("/houseinfo/abc")
        assert res.status_code == 404

    def test_get_house_with_negative_id(self, client):
        """传入负数 ID"""
        res = client.get("/houseinfo/-1")
        assert res.status_code == 404


# ══════════════════════════════════════════════════════════════
#  浏览量
# ══════════════════════════════════════════════════════════════

class TestHouseViews:
    """浏览量相关"""

    def test_get_most_viewed(self, client):
        """获取浏览量最高的房源"""
        res = client.get("/houseinfo/views")
        body = res.get_json()
        assert body is not None

    def test_add_view_no_json(self, client):
        """增加浏览量 —— 不传 JSON"""
        res = client.post("/houseinfo/views", data=b"not json",
                          content_type="application/json")
        assert res.status_code in [400, 404, 500]

    def test_add_view_invalid_houseid(self, client):
        """增加浏览量 —— 不存在的房源"""
        res = client.post("/houseinfo/views", json={"houseid": 99999})
        body = res.get_json()
        assert body is not None
        if body.get("success") is False:
            pass  # 符合预期


# ══════════════════════════════════════════════════════════════
#  房源 CRUD
# ══════════════════════════════════════════════════════════════

class TestHouseCRUD:
    """房源增删改"""

    @pytest.fixture
    def new_house_id(self, client):
        """创建测试房源，返回 ID，测试结束后自动删除"""
        res = client.post("/houseinfo/", json={
            "title": "Pytest 测试房源-自动化",
            "region": "测试区",
            "community": "自动化测试小区",
            "area": 80,
            "rooms": "2室1厅",
            "price": 3000,
            "rent_type": "整租",
            "subway": True,
            "decoration": "精装",
            "available": True,
        })
        body = assert_success(res, expected_http=201)
        house_id = body["data"]["id"]
        yield house_id
        # 清理：删除测试房源
        client.delete(f"/houseinfo/{house_id}")

    def test_create_house_full_fields(self, client, new_house_id):
        """创建房源 —— 完整字段"""
        assert new_house_id > 0
        # 验证创建后可以查到
        res = client.get(f"/houseinfo/{new_house_id}")
        body = assert_success(res)
        assert body["data"]["title"] == "Pytest 测试房源-自动化"
        assert body["data"]["price"] == 3000

    def test_create_house_minimal_fields(self, client):
        """创建房源 —— 仅必填字段"""
        res = client.post("/houseinfo/", json={
            "title": "最小字段房源",
            "region": "测试区",
            "community": "最小测试",
            "area": 50,
            "rooms": "1室1厅",
            "price": 1500,
            "rent_type": "合租",
        })
        body = assert_success(res, expected_http=201)
        # 清理
        client.delete(f"/houseinfo/{body['data']['id']}")

    def test_create_house_missing_title(self, client):
        """缺少 title"""
        res = client.post("/houseinfo/", json={
            "region": "测试区",
            "community": "测试小区",
            "area": 80,
            "rooms": "2室1厅",
            "price": 3000,
            "rent_type": "整租",
        })
        assert_error(res, expected_http=400)

    def test_create_house_missing_region(self, client):
        """缺少 region"""
        res = client.post("/houseinfo/", json={
            "title": "无区域",
            "community": "测试",
            "area": 80,
            "rooms": "2室1厅",
            "price": 3000,
            "rent_type": "整租",
        })
        assert_error(res, expected_http=400)

    def test_create_house_missing_community(self, client):
        """缺少 community"""
        res = client.post("/houseinfo/", json={
            "title": "无小区",
            "region": "测试区",
            "area": 80,
            "rooms": "2室1厅",
            "price": 3000,
            "rent_type": "整租",
        })
        assert_error(res, expected_http=400)

    def test_create_house_missing_price(self, client):
        """缺少 price"""
        res = client.post("/houseinfo/", json={
            "title": "无价格",
            "region": "测试区",
            "community": "测试小区",
            "area": 80,
            "rooms": "2室1厅",
            "rent_type": "整租",
        })
        assert_error(res, expected_http=400)

    def test_create_house_empty_body(self, client):
        """空请求体"""
        res = client.post("/houseinfo/", json={})
        assert_error(res, expected_http=400)

    def test_create_house_invalid_json(self, client):
        """无效 JSON"""
        res = client.post("/houseinfo/", data="这不是JSON",
                          content_type="application/json")
        assert res.status_code in [400, 415, 500]

    def test_update_house_title_and_price(self, client, new_house_id):
        """更新房源标题和价格"""
        res = client.put(f"/houseinfo/{new_house_id}", json={
            "title": "更新后的标题",
            "price": 4500,
        })
        body = assert_success(res)
        assert body["data"]["title"] == "更新后的标题"
        assert body["data"]["price"] == 4500

    def test_update_house_partial_fields(self, client, new_house_id):
        """仅更新部分字段不影响其他字段"""
        res = client.put(f"/houseinfo/{new_house_id}", json={
            "decoration": "简装",
        })
        body = assert_success(res)
        assert body["data"]["decoration"] == "简装"
        assert body["data"]["title"] == "Pytest 测试房源-自动化"  # 未变更

    def test_update_house_invalid_date(self, client, new_house_id):
        """更新时传入无效日期"""
        res = client.put(f"/houseinfo/{new_house_id}", json={
            "publish_time": "not-a-date",
        })
        body = res.get_json()
        assert body is not None
        if body.get("success") is False:
            assert res.status_code in [400, 500]

    def test_update_nonexistent_house(self, client):
        """更新不存在的房源"""
        res = client.put("/houseinfo/99999", json={"title": "test"})
        assert_error(res, expected_http=404)

    def test_delete_then_get_returns_404(self, client):
        """删除后查询返回 404"""
        # 创建
        res = client.post("/houseinfo/", json={
            "title": "待删测试房源",
            "region": "测试区",
            "community": "删除测试小区",
            "area": 50,
            "rooms": "1室1厅",
            "price": 1200,
            "rent_type": "合租",
        })
        house_id = res.get_json()["data"]["id"]

        # 删除
        res = client.delete(f"/houseinfo/{house_id}")
        assert_success(res)

        # 确认已删除
        res = client.get(f"/houseinfo/{house_id}")
        assert_error(res, expected_http=404)

    def test_delete_nonexistent_house(self, client):
        """删除不存在的房源"""
        res = client.delete("/houseinfo/99999")
        assert_error(res, expected_http=404)

    def test_delete_same_house_twice(self, client):
        """删除同一房源两次"""
        # 创建
        res = client.post("/houseinfo/", json={
            "title": "双重删除测试",
            "region": "测试区",
            "community": "双重删除小区",
            "area": 60,
            "rooms": "2室1厅",
            "price": 2000,
            "rent_type": "整租",
        })
        house_id = res.get_json()["data"]["id"]

        # 第一次删除
        client.delete(f"/houseinfo/{house_id}")
        # 第二次删除应返回 404
        res = client.delete(f"/houseinfo/{house_id}")
        assert_error(res, expected_http=404)


# ══════════════════════════════════════════════════════════════
#  房东房源查询
# ══════════════════════════════════════════════════════════════

class TestLandlordHouses:
    """按房东查询 POST /houseinfo/landlord"""

    def test_landlord_houses_no_data(self, client):
        """空请求 —— 应返回错误"""
        res = client.post("/houseinfo/landlord", json={})
        assert_error(res, expected_http=400)

    def test_landlord_houses_nonexistent(self, client):
        """不存在的房东"""
        res = client.post("/houseinfo/landlord", json={
            "username": "nonexistent_landlord_999"
        })
        body = res.get_json()
        assert body is not None

    def test_landlord_houses_existing(self, client):
        """存在的房东"""
        res = client.post("/houseinfo/landlord", json={
            "username": "auto_test_user"
        })
        body = res.get_json()
        assert body is not None
