#!/usr/bin/env python3
"""Trend analysis: compute rank/price changes, assign labels, identify focus product."""
from __future__ import annotations
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[3]))
from shared import config as cfg, db

THRESHOLD = cfg.get("alert_threshold", 3)


def _label(deltas: list[int]) -> str:
    if len(deltas) < 2:
        return "— 数据不足"
    recent = deltas[:2]
    last_delta = deltas[0]
    if abs(last_delta) > THRESHOLD:
        return "⚠ 异动"
    rising = all(d > 0 for d in recent)
    falling = all(d < 0 for d in recent)
    if rising:
        return "📈 上升"
    if falling:
        return "📉 下降"
    return "➡ 稳定"


def _summary(asin: str, label: str, curr_rank, prev_rank, curr_price, prev_price) -> str:
    if prev_rank is None or curr_rank is None:
        return "首次快照，无对比基准。"
    delta = prev_rank - curr_rank  # positive = rank improved (smaller number)
    direction = "▲" if delta > 0 else "▼"
    rank_desc = f"排名从 #{prev_rank} {'升' if delta > 0 else '降'}至 #{curr_rank}，{direction}{abs(delta)} 位。"
    price_desc = ""
    if prev_price and curr_price and prev_price != curr_price:
        try:
            pct = (curr_price - prev_price) / prev_price * 100
            price_desc = f" 价格{'下降' if pct < 0 else '上升'} {abs(pct):.1f}%。"
        except Exception:
            pass
    if label == "⚠ 异动":
        note = "单次大幅跳升，建议持续关注。" if delta > 0 else "单次大幅下滑，建议关注原因。"
    elif label == "📈 上升":
        note = "连续上升趋势明显。"
    elif label == "📉 下降":
        note = "连续下降趋势，需关注竞争压力。"
    else:
        note = "数据稳定，无明显异动。"
    return rank_desc + price_desc + " " + note


def analyze_asin(asin: str) -> dict:
    history = db.get_recent_snapshots(asin, limit=6)
    if not history:
        return {"asin": asin, "status": "no_data"}

    curr = history[0]
    prev = history[1] if len(history) > 1 else None

    curr_rank = curr.get("sales_rank")
    prev_rank = prev.get("sales_rank") if prev else None
    curr_price = curr.get("price_value")
    prev_price = prev.get("price_value") if prev else None

    rank_delta = None
    if curr_rank is not None and prev_rank is not None:
        rank_delta = prev_rank - curr_rank  # positive = improved

    deltas = []
    for i in range(len(history) - 1):
        a = history[i].get("sales_rank")
        b = history[i + 1].get("sales_rank")
        if a is not None and b is not None:
            deltas.append(b - a)  # positive = rank got worse (larger number)

    label = _label(deltas)
    alert = rank_delta is not None and abs(rank_delta) > THRESHOLD

    summary = _summary(asin, label, curr_rank, prev_rank, curr_price, prev_price)

    return {
        "asin": asin,
        "title": curr.get("title", "N/A"),
        "rank_curr": curr_rank,
        "rank_prev": prev_rank,
        "rank_delta": rank_delta,
        "price_curr": curr.get("price", "N/A"),
        "price_prev": prev.get("price", "N/A") if prev else "N/A",
        "price_value_curr": curr_price,
        "price_value_prev": prev_price,
        "label": label,
        "alert": alert,
        "summary": summary,
        "data_source": curr.get("data_source", "unknown"),
        "fetched_at": curr.get("fetched_at"),
    }


def run_all() -> dict:
    db.init()
    products = db.list_products()
    results = [analyze_asin(p.asin) for p in products]
    valid = [r for r in results if r.get("rank_delta") is not None]

    focus = max(valid, key=lambda r: abs(r["rank_delta"])) if valid else (results[0] if results else None)

    return {
        "cycle_time": datetime.now(timezone.utc).isoformat(),
        "focus": focus,
        "products": results,
        "alerts": [r for r in results if r.get("alert")],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    grp = parser.add_mutually_exclusive_group(required=True)
    grp.add_argument("--all", action="store_true")
    grp.add_argument("--asin")
    args = parser.parse_args()

    if args.all:
        print(json.dumps(run_all(), ensure_ascii=False, default=str))
    else:
        db.init()
        print(json.dumps(analyze_asin(args.asin), ensure_ascii=False, default=str))
