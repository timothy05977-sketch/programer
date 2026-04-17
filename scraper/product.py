from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from bs4 import BeautifulSoup
from config import AMAZON_BASE
from scraper.session import get, new_session


@dataclass
class ProductSnapshot:
    asin: str
    title: str
    price: str
    rating: str
    review_count: str
    availability: str
    sales_rank: str
    fetched_at: str  # ISO-8601


def _clean(text: str | None) -> str:
    return text.strip() if text else "N/A"


def fetch_product(asin: str) -> ProductSnapshot:
    """Scrape a single product page and return a snapshot."""
    url = f"{AMAZON_BASE}/dp/{asin}"
    session = new_session()
    resp = get(url, session)
    soup = BeautifulSoup(resp.text, "lxml")

    title = _clean(soup.select_one("#productTitle, #title")and
                   (soup.select_one("#productTitle") or soup.select_one("#title")).get_text())

    # Price: try multiple selectors Amazon uses
    price = "N/A"
    for sel in [
        "span.a-price span.a-offscreen",
        "#priceblock_ourprice",
        "#priceblock_dealprice",
        ".a-price .a-offscreen",
        "#apex_offerDisplay_desktop span.a-price span.a-offscreen",
    ]:
        el = soup.select_one(sel)
        if el:
            price = _clean(el.get_text())
            break

    rating_el = soup.select_one("#acrPopover span.a-icon-alt, #averageCustomerReviews span.a-icon-alt")
    rating = _clean(rating_el.get_text()).split(" ")[0] if rating_el else "N/A"

    review_el = soup.select_one("#acrCustomerReviewText")
    review_count = _clean(review_el.get_text()) if review_el else "N/A"

    avail_el = soup.select_one("#availability span, #outOfStock")
    availability = _clean(avail_el.get_text()) if avail_el else "N/A"

    # Sales/Best Sellers Rank appears in product details table
    rank = "N/A"
    for row in soup.select("#productDetails_detailBullets_sections1 tr, #detailBullets_feature_div li"):
        text = row.get_text(" ", strip=True)
        if "Best Sellers Rank" in text or "Best-sellers rank" in text:
            rank = text.split(":", 1)[-1].strip()
            break

    return ProductSnapshot(
        asin=asin,
        title=title,
        price=price,
        rating=rating,
        review_count=review_count,
        availability=availability,
        sales_rank=rank,
        fetched_at=datetime.utcnow().isoformat(),
    )
