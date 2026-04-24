#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 xiao
"""Trend analysis — pure computation, no DB access.

Input via stdin JSON:
  --all : {"products": [{"asin":"..","title":"..","history":[<snapshot>,..]}, ...]}
  --asin: {"asin":"..","title":"..","history":[<snapshot>,...]}

Snapshot keys: sales_rank(int|null), price_value(float|null), price(str),
               fetched_at(ISO str), data_source(str)
History ordered newest → oldest.
"""
from __future__ import annotations
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[3]))
from shared import config as cfg

THRESHOLD = int(cfg.get("alert_threshold", 3))


def _label(rank_deltas: list[int]) -> str:
    if len(rank_deltas) < 2:
        return "— 数据不足"
    last = rank_deltas[0]
    if abs(last) > THRESHOLD:
        return "⚠ 异动"
    if all(d > 0 for d in rank_deltas[:2]):
        return "📈 上升"
    if all(d < 0 for d in rank_deltas[:2]):
        return "📉 下降"
    return "➡ 稳定"


def _summary(label: str, curr_rank, prev_rank, curr_price, prev_price) -> str:
    if curr_rank is None:
        return "当前排名数据获取失败，无法分析趋势。"
    if prev_rank is None:
        return f"首次快照，排名 #{curr_rank}，无历史对比基准。"
    delta = prev_rank - curr_rank
    up = delta > 0
    rank_desc = f"排名从 #{prev_rank} {'升' if up else '降'}至 #{curr_rank}，{'▲' if up else '▼'}{abs(delta)} 位。"
    price_desc = ""
    if prev_price and curr_price:
        try:
            pct = (curr_price - prev_price) / prev_price * 100
            if abs(pct) >= 0.5:
                price_desc = f" 价格{'下降' if pct < 0 else '上升'} {abs(pct):.1f}%。"
        except Exception:
            pass
    notes = {
        "⚠ 异动": "单次大幅跳升，建议持续关注。" if up else "单次大幅下滑，建议关注竞争压力。",
        "📈 上升": "连续上升趋势明显。",
        "📉 下降": "连续下降，需关注竞争变化。",
        "➡ 稳定": "数据稳定，无明显异动。",
    }
    return rank_desc + price_desc + " " + notes.get(label, "")


def analyze_product(p: dict) -> dict:
    asin    = p["asin"]
    history = p.get("history", [])

    if not history:
        return {"asin": asin, "title": p.get("title", ""),
                "label": "— 数据不足", "alert": False, "status": "no_data"}

    curr       = history[0]
    prev       = history[1] if len(history) > 1 else None
    curr_rank  = curr.get("sales_rank")
    prev_rank  = prev.get("sales_rank") if prev else None
    curr_price = curr.get("price_value")
    prev_price = prev.get("price_value") if prev else None
    rank_delta = (prev_rank - curr_rank) if (curr_rank and prev_rank) else None

    deltas = []
    for i in range(len(history) - 1):
        a, b = history[i].get("sales_rank"), history[i + 1].get("sales_rank")
        if a and b:
            deltas.append(b - a)

    label = _label(deltas)
    alert = rank_delta is not None and abs(rank_delta) > THRESHOLD

    return {
        "asin":             asin,
        "title":            p.get("title", curr.get("title", "")),
        "rank_curr":        curr_rank,
        "rank_prev":        prev_rank,
        "rank_delta":       rank_delta,
        "price_curr":       curr.get("price", "N/A"),
        "price_prev":       prev.get("price", "N/A") if prev else "N/A",
        "price_value_curr": curr_price,
        "price_value_prev": prev_price,
        "label":            label,
        "alert":            alert,
        "summary":          _summary(label, curr_rank, prev_rank, curr_price, prev_price),
        "data_source":      curr.get("data_source", "unknown"),
        "fetched_at":       curr.get("fetched_at"),
    }


def run_all(products: list[dict]) -> dict:
    results = [analyze_product(p) for p in products]
    valid = [r for r in results if r.get("rank_delta") is not None]
    # Focus: largest abs(rank_delta); tie → higher current rank (lower rank number).
    focus = max(valid, key=lambda r: (abs(r["rank_delta"]), -r["rank_curr"])) \
        if valid else (results[0] if results else None)
    return {
        "cycle_time": datetime.now(timezone.utc).isoformat(),
        "focus": focus,
        "products": results,
        "alerts": [r for r in results if r.get("alert")],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    grp = parser.add_mutually_exclusive_group(required=True)
    grp.add_argument("--all",  action="store_true")
    grp.add_argument("--asin", action="store_true")
    args = parser.parse_args()

    data = json.load(sys.stdin)
    if args.all:
        print(json.dumps(run_all(data["products"]), ensure_ascii=False, default=str))
    else:
        print(json.dumps(analyze_product(data), ensure_ascii=False, default=str))
