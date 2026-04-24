# SPDX-License-Identifier: MIT
# Copyright (c) 2026 xiao
"""L2 mock tests for skills/amz-monitor/scripts/rainforest.py"""
import pytest
import responses

from shared import config as cfg
import rainforest


@pytest.fixture(autouse=True)
def _cfg(monkeypatch, tmp_path):
    """Isolate config: point at an empty file, set key via env."""
    monkeypatch.setattr(cfg, "_CONFIG_FILE", tmp_path / "noexist.json")
    monkeypatch.setenv("RAINFOREST_API_KEY", "test-key-123")


class TestGetProduct:
    @responses.activate
    def test_happy_path(self):
        responses.add(
            responses.GET, "https://api.rainforestapi.com/request",
            json={"product": {
                "title": "Test Widget",
                "buybox_winner": {
                    "price": {"raw": "$24.99", "value": 24.99},
                    "availability": {"raw": "In Stock"},
                },
                "bestsellers_rank": [{"rank": 42, "category": "Electronics"}],
                "rating": 4.5,
                "ratings_total": 1200,
            }},
            status=200,
        )
        snap = rainforest.get_product("B0TEST00001")
        assert snap.asin == "B0TEST00001"
        assert snap.title == "Test Widget"
        assert snap.price == "$24.99"
        assert snap.price_value == 24.99
        assert snap.sales_rank == 42
        assert snap.rank_category == "Electronics"
        assert snap.availability == "In Stock"
        assert snap.data_source == "rainforest"

    @responses.activate
    def test_missing_buybox_no_price(self):
        responses.add(
            responses.GET, "https://api.rainforestapi.com/request",
            json={"product": {"title": "X"}}, status=200,
        )
        snap = rainforest.get_product("B0TEST00001")
        assert snap.price == "N/A"
        assert snap.price_value is None
        assert snap.sales_rank is None

    @responses.activate
    def test_http_error_raises(self):
        responses.add(
            responses.GET, "https://api.rainforestapi.com/request",
            status=500,
        )
        with pytest.raises(Exception):
            rainforest.get_product("B0TEST00001")

    def test_missing_key_raises(self, monkeypatch):
        monkeypatch.delenv("RAINFOREST_API_KEY", raising=False)
        with pytest.raises(ValueError, match="rainforest_api_key"):
            rainforest.get_product("B0TEST00001")


class TestGetBestsellers:
    @responses.activate
    def test_returns_capped_list(self):
        items = [
            {"rank": i, "asin": f"B{i:09d}", "title": f"Item {i}",
             "price": {"raw": f"${i}.00"}, "rating": 4.0, "ratings_total": 100}
            for i in range(1, 31)
        ]
        responses.add(
            responses.GET, "https://api.rainforestapi.com/request",
            json={"bestsellers": items}, status=200,
        )
        out = rainforest.get_bestsellers("electronics", top_n=10)
        assert len(out) == 10
        assert out[0]["rank"] == 1
        assert out[0]["asin"] == "B000000001"
        assert out[0]["price"] == "$1.00"

    @responses.activate
    def test_unknown_category_falls_back_to_all(self):
        responses.add(
            responses.GET, "https://api.rainforestapi.com/request",
            json={"bestsellers": []}, status=200,
        )
        out = rainforest.get_bestsellers("nonsense-category", top_n=5)
        assert out == []
