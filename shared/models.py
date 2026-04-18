"""Shared data models."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Snapshot:
    asin: str
    title: str = ""
    price: str = "N/A"
    price_value: Optional[float] = None
    rating: str = "N/A"
    review_count: str = "N/A"
    availability: str = "N/A"
    sales_rank: Optional[int] = None
    rank_category: str = ""
    data_source: str = "unknown"
    fetched_at: str = ""
