# SPDX-License-Identifier: MIT
# Copyright (c) 2026 xiao
"""Rainforest API client — primary Amazon data source."""
from __future__ import annotations
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parents[3]))
from shared import config as cfg
from shared.models import Snapshot
from datetime import datetime, timezone

BASE_URL = "https://api.rainforestapi.com/request"

_CATEGORY_URLS = {
    "electronics": "https://www.amazon.com/Best-Sellers/zgbs/electronics",
    "books":       "https://www.amazon.com/Best-Sellers/zgbs/books",
    "toys":        "https://www.amazon.com/Best-Sellers/zgbs/toys-and-games",
    "kitchen":     "https://www.amazon.com/Best-Sellers/zgbs/kitchen",
    "clothing":    "https://www.amazon.com/Best-Sellers/zgbs/apparel",
    "sports":      "https://www.amazon.com/Best-Sellers/zgbs/sporting-goods",
    "beauty":      "https://www.amazon.com/Best-Sellers/zgbs/beauty",
    "home":        "https://www.amazon.com/Best-Sellers/zgbs/home-garden",
    "all":         "https://www.amazon.com/Best-Sellers/zgbs",
}


def _key() -> str:
    key = cfg.get("rainforest_api_key")
    if not key:
        raise ValueError("rainforest_api_key not configured")
    return key


def _params(extra: dict) -> dict:
    return {"api_key": _key(), "amazon_domain": cfg.amazon_domain(), **extra}


def get_product(asin: str) -> Snapshot:
    resp = requests.get(BASE_URL, params=_params({"type": "product", "asin": asin}),
                        timeout=20)
    resp.raise_for_status()
    data = resp.json().get("product", {})

    price_raw = "N/A"
    price_val = None
    buybox = data.get("buybox_winner") or {}
    if buybox.get("price"):
        price_raw = buybox["price"].get("raw", "N/A")
        price_val = buybox["price"].get("value")

    rank = None
    rank_cat = ""
    for r in (data.get("bestsellers_rank") or []):
        rank = r.get("rank")
        rank_cat = r.get("category", "")
        break

    avail = "N/A"
    if buybox.get("availability"):
        avail = buybox["availability"].get("raw", "N/A")

    return Snapshot(
        asin=asin,
        title=data.get("title", "N/A"),
        price=price_raw,
        price_value=price_val,
        rating=str(data.get("rating", "N/A")),
        review_count=str(data.get("ratings_total", "N/A")),
        availability=avail,
        sales_rank=rank,
        rank_category=rank_cat,
        data_source="rainforest",
        fetched_at=datetime.now(timezone.utc).isoformat(),
    )


def get_bestsellers(category: str = "all", top_n: int = 50) -> list[dict]:
    url = _CATEGORY_URLS.get(category, _CATEGORY_URLS["all"])
    resp = requests.get(BASE_URL, params=_params({"type": "bestsellers", "url": url}),
                        timeout=20)
    resp.raise_for_status()
    items = resp.json().get("bestsellers", [])[:top_n]
    return [
        {
            "rank": item.get("rank"),
            "asin": item.get("asin", ""),
            "title": item.get("title", ""),
            "price": (item.get("price") or {}).get("raw", "N/A"),
            "rating": item.get("rating", "N/A"),
            "review_count": item.get("ratings_total", "N/A"),
        }
        for item in items
    ]
