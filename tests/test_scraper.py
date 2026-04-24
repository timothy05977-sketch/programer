# SPDX-License-Identifier: MIT
# Copyright (c) 2026 xiao
"""L2 mock tests for skills/amz-monitor/scripts/scraper.py"""
import pytest
import responses

from shared import config as cfg
import scraper


@pytest.fixture(autouse=True)
def _cfg(monkeypatch, tmp_path):
    monkeypatch.setattr(cfg, "_CONFIG_FILE", tmp_path / "noexist.json")
    # Remove delay between requests so tests are fast
    monkeypatch.setattr(scraper, "_DELAY", 0.0)
    monkeypatch.setattr(scraper, "_last_req", 0.0)


_PRODUCT_HTML = """
<html><body>
  <span id="productTitle">Test Widget Pro</span>
  <span class="a-price"><span class="a-offscreen">$24.99</span></span>
  <span id="acrPopover"><span class="a-icon-alt">4.5 out of 5 stars</span></span>
  <span id="acrCustomerReviewText">1,234 ratings</span>
  <div id="availability"><span>In Stock</span></div>
  <div id="detailBullets_feature_div">
    <li>Best Sellers Rank #42 in Electronics (See Top 100)</li>
  </div>
</body></html>
"""


class TestGetProduct:
    @responses.activate
    def test_parses_product_page(self):
        responses.add(
            responses.GET, "https://www.amazon.com/dp/B0TEST00001",
            body=_PRODUCT_HTML, status=200,
            content_type="text/html",
        )
        snap = scraper.get_product("B0TEST00001")
        assert snap.asin == "B0TEST00001"
        assert snap.title == "Test Widget Pro"
        assert snap.price == "$24.99"
        assert snap.price_value == 24.99
        assert snap.rating == "4.5"
        assert snap.sales_rank == 42
        assert snap.rank_category == "Electronics"
        assert snap.data_source == "scraper"

    @responses.activate
    def test_http_error_raises(self):
        responses.add(
            responses.GET, "https://www.amazon.com/dp/B0TEST00001",
            status=503,
        )
        with pytest.raises(Exception):
            scraper.get_product("B0TEST00001")

    @responses.activate
    def test_missing_fields_default_na(self):
        responses.add(
            responses.GET, "https://www.amazon.com/dp/B0TEST00001",
            body="<html><body></body></html>", status=200,
            content_type="text/html",
        )
        snap = scraper.get_product("B0TEST00001")
        assert snap.title == "N/A"
        assert snap.price == "N/A"
        assert snap.price_value is None
        assert snap.sales_rank is None


class TestParsePrice:
    def test_usd(self):
        assert scraper._parse_price("$24.99") == 24.99

    def test_gbp(self):
        assert scraper._parse_price("£19.50") == 19.50

    def test_eur_comma_decimal(self):
        assert scraper._parse_price("€29,90") == 29.90

    def test_eur_dot_thousands_comma_decimal(self):
        assert scraper._parse_price("1.234,56 €") == 1234.56

    def test_us_thousands(self):
        assert scraper._parse_price("$1,234.56") == 1234.56

    def test_jpy_no_decimals(self):
        assert scraper._parse_price("￥1,980") == 1980.0

    def test_canadian(self):
        assert scraper._parse_price("CA$34.00") == 34.00

    def test_na_returns_none(self):
        assert scraper._parse_price("N/A") is None

    def test_empty_returns_none(self):
        assert scraper._parse_price("") is None


class TestGetBestsellers:
    @responses.activate
    def test_empty_page(self):
        responses.add(
            responses.GET, "https://www.amazon.com/Best-Sellers/zgbs/electronics",
            body="<html><body></body></html>", status=200,
            content_type="text/html",
        )
        out = scraper.get_bestsellers("electronics", top_n=20)
        assert out == []
