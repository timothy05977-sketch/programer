# SPDX-License-Identifier: MIT
# Copyright (c) 2026 xiao
"""L2 mock tests for skills/scavio-amazon/scripts/scavio.py"""
import pytest
import responses

from shared import config as cfg
import scavio


@pytest.fixture(autouse=True)
def _cfg(monkeypatch, tmp_path):
    monkeypatch.setattr(cfg, "_CONFIG_FILE", tmp_path / "noexist.json")
    monkeypatch.setenv("SCAVIO_API_KEY", "test-key-123")


class TestGetProduct:
    @responses.activate
    def test_happy_path(self):
        responses.add(
            responses.POST, "https://api.scavio.dev/api/v1/amazon/product",
            json={
                "name": "Test Widget",
                "asin": "B0TEST00001",
                "price": "$24.99",
                "rating": 4.5,
                "total_reviews": 1200,
                "availability": "In Stock",
                "categories": [{"rank": 42, "name": "Electronics"}],
            },
            status=200,
        )
        snap = scavio.get_product("B0TEST00001")
        assert snap.asin == "B0TEST00001"
        assert snap.title == "Test Widget"
        assert snap.price == "$24.99"
        assert snap.price_value == 24.99
        assert snap.sales_rank == 42
        assert snap.rank_category == "Electronics"
        assert snap.availability == "In Stock"
        assert snap.data_source == "scavio"

    @responses.activate
    def test_missing_optional_fields(self):
        responses.add(
            responses.POST, "https://api.scavio.dev/api/v1/amazon/product",
            json={"name": "X"},
            status=200,
        )
        snap = scavio.get_product("B0TEST00001")
        assert snap.price == "N/A"
        assert snap.price_value is None
        assert snap.sales_rank is None
        assert snap.rating == "N/A"

    @responses.activate
    def test_http_error_raises(self):
        responses.add(
            responses.POST, "https://api.scavio.dev/api/v1/amazon/product",
            status=500,
        )
        with pytest.raises(Exception):
            scavio.get_product("B0TEST00001")

    def test_missing_key_raises(self, monkeypatch):
        monkeypatch.delenv("SCAVIO_API_KEY", raising=False)
        with pytest.raises(RuntimeError, match="SCAVIO_API_KEY"):
            scavio.get_product("B0TEST00001")


class TestGetBestsellers:
    @responses.activate
    def test_returns_capped_list(self):
        items = [
            {"asin": f"B{i:09d}", "name": f"Item {i}",
             "price": f"${i}.00", "rating": 4.0, "total_reviews": 100}
            for i in range(1, 31)
        ]
        responses.add(
            responses.POST, "https://api.scavio.dev/api/v1/amazon/search",
            json={"data": items},
            status=200,
        )
        out = scavio.get_bestsellers("electronics", top_n=10)
        assert len(out) == 10
        assert out[0]["rank"] == 1
        assert out[0]["asin"] == "B000000001"
        assert out[0]["price"] == "$1.00"

    @responses.activate
    def test_unknown_category_uses_query_directly(self):
        responses.add(
            responses.POST, "https://api.scavio.dev/api/v1/amazon/search",
            json={"data": []},
            status=200,
        )
        out = scavio.get_bestsellers("nonsense-category", top_n=5)
        assert out == []

    @responses.activate
    def test_empty_response(self):
        responses.add(
            responses.POST, "https://api.scavio.dev/api/v1/amazon/search",
            json={},
            status=200,
        )
        assert scavio.get_bestsellers() == []
