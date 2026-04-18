#!/usr/bin/env python3
"""Aggregate snapshot history for weekly/monthly report generation."""
from __future__ import annotations
import argparse
import json
import sys
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[3]))
from shared import db

DB_PATH = db.DB_PATH


def aggregate(asin: str, since: datetime) -> dict:
    con = sqlite3.connect(str(DB_PATH))
    con.row_factory = sqlite3.Row
    rows = con.execute(
        "SELECT * FROM snapshots WHERE asin = ? AND fetched_at >= ? ORDER BY fetched_at",
        (asin, since.isoformat()),
    ).fetchall()
    con.close()

    if not rows:
        return {"asin": asin, "snapshot_count": 0}

    ranks = [r["sales_rank"] for r in rows if r["sales_rank"] is not None]
    prices = [r["price_value"] for r in rows if r["price_value"] is not None]
    first = dict(rows[0])
    last = dict(rows[-1])

    rank_delta = None
    if ranks:
        rank_delta = ranks[0] - ranks[-1]  # positive = improved over period

    trend = "稳定"
    if rank_delta is not None and len(ranks) >= 3:
        std = (sum((r - sum(ranks) / len(ranks)) ** 2 for r in ranks) / len(ranks)) ** 0.5
        avg = sum(ranks) / len(ranks)
        if std > avg * 0.2:
            trend = "波动"
        elif rank_delta > 5:
            trend = "持续上升"
        elif rank_delta < -5:
            trend = "持续下降"

    return {
        "asin": asin,
        "title": last.get("title", "N/A"),
        "snapshot_count": len(rows),
        "period_start": first["fetched_at"],
        "period_end": last["fetched_at"],
        "rank": {
            "min": min(ranks) if ranks else None,
            "max": max(ranks) if ranks else None,
            "avg": round(sum(ranks) / len(ranks)) if ranks else None,
            "delta": rank_delta,
        },
        "price": {
            "min": min(prices) if prices else None,
            "max": max(prices) if prices else None,
        },
        "trend_summary": trend,
        "data_source": last.get("data_source", "unknown"),
    }


def run(days: int) -> dict:
    db.init()
    since = datetime.now(timezone.utc) - timedelta(days=days)
    products = db.list_products()
    reports = [aggregate(p.asin, since) for p in products]

    valid = [r for r in reports if r.get("snapshot_count", 0) > 0]
    focus = max(valid, key=lambda r: abs(r["rank"]["delta"] or 0)) if valid else None

    return {
        "report_type": "weekly" if days <= 7 else "monthly",
        "days": days,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "product_count": len(products),
        "total_snapshots": sum(r.get("snapshot_count", 0) for r in reports),
        "focus_asin": focus["asin"] if focus else None,
        "focus_title": focus["title"] if focus else None,
        "products": reports,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=7)
    args = parser.parse_args()
    print(json.dumps(run(args.days), ensure_ascii=False, default=str))
