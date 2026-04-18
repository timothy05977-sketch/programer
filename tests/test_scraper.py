"""L2 mock tests for skills/monitor/scripts/scraper.py"""
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
