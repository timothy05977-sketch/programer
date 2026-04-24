#!/usr/bin/env python3
"""Weekly/monthly report aggregation — pure computation, no DB access.

Input via stdin JSON:
{
  "products": [
    {
      "asin": "B0CHWX8DFH",
      "title": "...",
      "snapshots": [
        {"sales_rank": 18, "price_value": 24.99, "fetched_at": "2026-04-18T14:20:00"},
        ...
      ]
    }
  ]
}
Snapshots may be in any order; script sorts by fetched_at.
"""
from __future__ import annotations
import argparse
import json
import sys
from datetime import datetime, timezone


def aggregate(p: dict) -> dict:
    asin      = p["asin"]
    snapshots = sorted(p.get("snapshots", []), key=lambda s: s.get("fetched_at", ""))

    if not snapshots:
        return {"asin": asin, "title": p.get("title", ""),
                "snapshot_count": 0, "trend_summary": "数据不足"}

    ranks  = [s["sales_rank"]  for s in snapshots if s.get("sales_rank")  is not None]
    prices = [s["price_value"] for s in snapshots if s.get("price_value") is not None]
    rank_delta = (ranks[0] - ranks[-1]) if len(ranks) >= 2 else None

    trend = "数据不足"
    if len(ranks) >= 5:
        # 持续上升/下降：相邻快照的方向占比 ≥ 70% 且终点较起点有显著变化。
        # 否则用 std/avg 比例区分「波动」与「稳定」。
        deltas = [ranks[i + 1] - ranks[i] for i in range(len(ranks) - 1)]
        pos = sum(1 for d in deltas if d > 0)
        neg = sum(1 for d in deltas if d < 0)
        avg = sum(ranks) / len(ranks)
        total_change = ranks[-1] - ranks[0]
        significant = abs(total_change) >= max(5, avg * 0.1)
        majority = len(deltas) * 0.7
        if significant and neg >= majority and total_change < 0:
            trend = "持续上升"
        elif significant and pos >= majority and total_change > 0:
            trend = "持续下降"
        else:
            std = (sum((r - avg) ** 2 for r in ranks) / len(ranks)) ** 0.5
            trend = "波动" if std > avg * 0.2 else "稳定"
    elif len(ranks) >= 2:
        trend = "稳定" if abs(ranks[-1] - ranks[0]) <= 5 else "波动"

    return {
        "asin":           asin,
        "title":          p.get("title", snapshots[-1].get("title", "")),
        "snapshot_count": len(snapshots),
        "period_start":   snapshots[0].get("fetched_at"),
        "period_end":     snapshots[-1].get("fetched_at"),
        "rank":  {"min": min(ranks)  if ranks  else None,
                  "max": max(ranks)  if ranks  else None,
                  "avg": round(sum(ranks) / len(ranks)) if ranks else None,
                  "delta": rank_delta},
        "price": {"min": min(prices) if prices else None,
                  "max": max(prices) if prices else None},
        "trend_summary": trend,
    }


def run(data: dict, days: int) -> dict:
    products = data.get("products", [])
    reports  = [aggregate(p) for p in products]
    valid    = [r for r in reports if r["snapshot_count"] > 0
                                   and r["rank"].get("delta") is not None]
    focus    = max(valid, key=lambda r: abs(r["rank"]["delta"])) if valid else None

    return {
        "report_type":     "weekly" if days <= 7 else "monthly",
        "days":            days,
        "generated_at":    datetime.now(timezone.utc).isoformat(),
        "product_count":   len(products),
        "total_snapshots": sum(r["snapshot_count"] for r in reports),
        "focus_asin":      focus["asin"]  if focus else None,
        "focus_title":     focus["title"] if focus else None,
        "products":        reports,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=7)
    args = parser.parse_args()
    data = json.load(sys.stdin)
    print(json.dumps(run(data, args.days), ensure_ascii=False, default=str))
