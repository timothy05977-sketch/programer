from __future__ import annotations
from dataclasses import dataclass
from bs4 import BeautifulSoup
from config import AMAZON_BASE, BESTSELLER_CATEGORIES
from scraper.session import get, new_session


@dataclass
class BestsellerItem:
    rank: int
    asin: str
    title: str
    price: str
    rating: str
    review_count: str
    url: str


def _build_url(category: str, page: int = 1) -> str:
    slug = BESTSELLER_CATEGORIES.get(category, "")
    base = f"{AMAZON_BASE}/Best-Sellers/zgbs/{slug}" if slug else f"{AMAZON_BASE}/Best-Sellers/zgbs"
    if page > 1:
        return f"{base}/ref=zg_bs_pg_{page}?pg={page}"
    return base


def _parse_page(html: str, rank_offset: int = 0) -> list[BestsellerItem]:
    soup = BeautifulSoup(html, "lxml")
    items: list[BestsellerItem] = []

    # Amazon uses two grid containers depending on layout
    cards = soup.select("div.zg-grid-general-faceout, li.zg-item-immersion")

    for i, card in enumerate(cards, start=1):
        # ASIN is stored in a data attribute or extractable from href
        asin = card.get("data-asin", "")
        if not asin:
            link = card.select_one("a.a-link-normal[href*='/dp/']")
            if link:
                href = link["href"]
                parts = href.split("/dp/")
                asin = parts[1].split("/")[0].split("?")[0] if len(parts) > 1 else ""

        title_el = card.select_one("._cDEzb_p13n-sc-css-line-clamp-3_g3dy1, .p13n-sc-truncated, a.a-link-normal span")
        title = title_el.get_text(strip=True) if title_el else "N/A"

        price_el = card.select_one("._cDEzb_p13n-sc-price_3mJ9Z, .p13n-sc-price")
        price = price_el.get_text(strip=True) if price_el else "N/A"

        rating_el = card.select_one("span.a-icon-alt")
        rating = rating_el.get_text(strip=True).split(" ")[0] if rating_el else "N/A"

        review_el = card.select_one("span.a-size-small")
        review_count = review_el.get_text(strip=True) if review_el else "N/A"

        url = f"{AMAZON_BASE}/dp/{asin}" if asin else "N/A"

        items.append(BestsellerItem(
            rank=rank_offset + i,
            asin=asin,
            title=title,
            price=price,
            rating=rating,
            review_count=review_count,
            url=url,
        ))

    return items


def fetch_bestsellers(category: str = "all", pages: int = 1) -> list[BestsellerItem]:
    """Fetch top bestsellers for a given category across one or more pages."""
    session = new_session()
    results: list[BestsellerItem] = []

    for page in range(1, pages + 1):
        url = _build_url(category, page)
        resp = get(url, session)
        items = _parse_page(resp.text, rank_offset=len(results))
        if not items:
            break
        results.extend(items)

    return results
