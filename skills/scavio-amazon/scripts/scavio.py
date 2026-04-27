# SPDX-License-Identifier: MIT
# Copyright (c) 2026 xiao
"""Scavio Amazon API client — primary data source (replaces Rainforest)."""
from __future__ import annotations
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parents[3]))
from shared import config as cfg
from shared.models import Snapshot

BASE_URL = "https://api.scavio.dev"

_DOMAIN_MAP = {
    "US": "com",    "UK": "co.uk", "DE": "de",     "JP": "co.jp",
    "CA": "ca",     "FR": "fr",    "IT": "it",     "ES": "es",
    "IN": "in",     "AU": "com.au","BR": "com.br", "MX": "com.mx",
}

_CATEGORY_QUERIES = {
    "electronics": "electronics",
    "books":       "books",
    "toys":        "toys and games",
    "kitchen":     "kitchen",
    "clothing":    "clothing",
    "sports":      "sports and outdoors",
    "beauty":      "beauty",
    "home":        "home and garden",
    "all":         "bestsellers",
}


def _key() -> str:
    key = cfg.get("scavio_api_key")
    if not key:
        raise RuntimeError(
            "SCAVIO_API_KEY not set — run: init_config.py save --scavio-api-key <KEY>"
        )
    return key


def _headers() -> dict:
    return {"Authorization": f"Bearer {_key()}"}


def _domain() -> str:
    market = cfg.get("amazon_marketplace", "US")
    return _DOMAIN_MAP.get(market, "com")


def _parse_price(raw: str | None) -> float | None:
    if not raw or raw == "N/A":
        return None
    digits = re.sub(r"[^\d.]", "", raw.replace(",", ""))
    try:
        return float(digits) if digits else None
    except ValueError:
        return None


def get_product(asin: str) -> Snapshot:
    resp = requests.post(
        f"{BASE_URL}/api/v1/amazon/product",
        headers=_headers(),
        json={"query": asin, "domain": _domain()},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()

    price_raw = data.get("price") or "N/A"
    price_val = _parse_price(price_raw)

    rating = data.get("rating")
    rating_str = str(rating) if rating is not None else "N/A"

    total_reviews = data.get("total_reviews")
    review_str = str(total_reviews) if total_reviews is not None else "N/A"

    availability = data.get("availability") or "N/A"

    # Extract sales rank from categories list if Scavio provides it
    rank = None
    rank_cat = ""
    for cat in (data.get("categories") or []):
        if isinstance(cat, dict) and cat.get("rank"):
            rank = int(cat["rank"])
            rank_cat = cat.get("name", "")
            break

    return Snapshot(
        asin=asin,
        title=data.get("name") or "N/A",
        price=price_raw,
        price_value=price_val,
        rating=rating_str,
        review_count=review_str,
        availability=availability,
        sales_rank=rank,
        rank_category=rank_cat,
        data_source="scavio",
        fetched_at=datetime.now(timezone.utc).isoformat(),
    )


def get_bestsellers(category: str = "all", top_n: int = 50) -> list[dict]:
    query = _CATEGORY_QUERIES.get(category, category)
    resp = requests.post(
        f"{BASE_URL}/api/v1/amazon/search",
        headers=_headers(),
        json={"query": query, "sort_by": "bestsellers", "domain": _domain()},
        timeout=30,
    )
    resp.raise_for_status()
    items = (resp.json().get("data") or [])[:top_n]
    return [
        {
            "rank":         i + 1,
            "asin":         item.get("asin", ""),
            "title":        item.get("name", "N/A"),
            "price":        item.get("price", "N/A"),
            "rating":       item.get("rating", "N/A"),
            "review_count": item.get("total_reviews", "N/A"),
        }
        for i, item in enumerate(items)
    ]
