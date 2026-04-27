# SPDX-License-Identifier: MIT
# Copyright (c) 2026 xiao
"""Direct Amazon scraper — fallback when Rainforest API is unavailable."""
from __future__ import annotations
import random
import re
import time
import sys
from pathlib import Path
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).parents[3]))
from shared import config as cfg
from shared.models import Snapshot


def _parse_price(raw: str):
    # Support US/JP/UK/DE/CA price strings. Strips currency symbols, then
    # normalizes thousands/decimal separators using the "later wins" rule.
    s = re.sub(r"[^\d.,]", "", raw or "")
    if not s:
        return None
    last_dot, last_comma = s.rfind("."), s.rfind(",")
    if last_dot >= 0 and last_comma >= 0:
        s = s.replace(",", "") if last_dot > last_comma else s.replace(".", "").replace(",", ".")
    elif last_comma >= 0:
        # Single comma: 3-digit tail → thousands (e.g. JPY 1,980), else EU decimal.
        s = s.replace(",", "") if len(s) - last_comma - 1 == 3 else s.replace(",", ".")
    elif last_dot >= 0 and len(s) - last_dot - 1 == 3:
        # Single dot with 3-digit tail → EU thousands (e.g. DE "1.234").
        s = s.replace(".", "")
    try:
        return float(s)
    except ValueError:
        return None

_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_3) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
]

_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
}

_last_req = 0.0
_DELAY = 2.5


def _get(url: str) -> requests.Response:
    global _last_req
    gap = time.time() - _last_req
    if gap < _DELAY:
        time.sleep(_DELAY - gap)
    headers = {**_HEADERS, "User-Agent": random.choice(_USER_AGENTS)}
    resp = requests.get(url, headers=headers, timeout=15)
    _last_req = time.time()
    resp.raise_for_status()
    return resp


def _clean(el) -> str:
    return el.get_text(strip=True) if el else "N/A"


def get_product(asin: str) -> Snapshot:
    base = f"https://www.{cfg.amazon_domain()}"
    soup = BeautifulSoup(_get(f"{base}/dp/{asin}").text, "lxml")

    title = _clean(soup.select_one("#productTitle"))

    price = "N/A"
    price_val = None
    for sel in ["span.a-price span.a-offscreen", "#priceblock_ourprice",
                "#priceblock_dealprice"]:
        el = soup.select_one(sel)
        if el:
            price = _clean(el)
            price_val = _parse_price(price)
            break

    rating_el = soup.select_one("#acrPopover span.a-icon-alt")
    rating = _clean(rating_el).split(" ")[0] if rating_el else "N/A"

    review_el = soup.select_one("#acrCustomerReviewText")
    review_count = _clean(review_el)

    avail_el = soup.select_one("#availability span")
    availability = _clean(avail_el)

    rank = None
    rank_cat = ""
    for row in soup.select("#detailBullets_feature_div li, #productDetails_detailBullets_sections1 tr"):
        text = row.get_text(" ", strip=True)
        if "Best Sellers Rank" in text or "Best-sellers rank" in text:
            m = re.search(r"#([\d,]+)\s+in\s+(.+?)(?:\s+\(|$)", text)
            if m:
                rank = int(m.group(1).replace(",", ""))
                rank_cat = m.group(2).strip()
            break

    return Snapshot(
        asin=asin, title=title, price=price, price_value=price_val,
        rating=rating, review_count=review_count, availability=availability,
        sales_rank=rank, rank_category=rank_cat,
        data_source="scraper",
        fetched_at=datetime.now(timezone.utc).isoformat(),
    )


def get_bestsellers(category: str = "all", top_n: int = 50) -> list[dict]:
    _slugs = {
        "electronics": "electronics", "books": "books", "toys": "toys-and-games",
        "kitchen": "kitchen", "clothing": "apparel", "sports": "sporting-goods",
        "beauty": "beauty", "home": "home-garden",
    }
    slug = _slugs.get(category, "")
    base = f"https://www.{cfg.amazon_domain()}"
    url = f"{base}/Best-Sellers/zgbs/{slug}" if slug else f"{base}/Best-Sellers/zgbs"

    soup = BeautifulSoup(_get(url).text, "lxml")
    cards = soup.select("div.zg-grid-general-faceout, li.zg-item-immersion")[:top_n]
    results = []
    for i, card in enumerate(cards, 1):
        asin = card.get("data-asin", "")
        if not asin:
            link = card.select_one("a.a-link-normal[href*='/dp/']")
            if link:
                parts = link["href"].split("/dp/")
                asin = parts[1].split("/")[0].split("?")[0] if len(parts) > 1 else ""
        title_el = card.select_one("._cDEzb_p13n-sc-css-line-clamp-3_g3dy1, .p13n-sc-truncated")
        price_el = card.select_one("._cDEzb_p13n-sc-price_3mJ9Z, .p13n-sc-price")
        results.append({
            "rank": i, "asin": asin,
            "title": title_el.get_text(strip=True) if title_el else "N/A",
            "price": price_el.get_text(strip=True) if price_el else "N/A",
            "rating": "N/A", "review_count": "N/A",
        })
    return results
