#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 xiao
"""Fetch Amazon product snapshots. Outputs JSON only — no DB writes.
Agent persists results to Feishu Bitable via the OpenClaw plugin."""
from __future__ import annotations
import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[3]))
from shared import config as cfg

import rainforest
import scraper


def _snap_to_dict(snap) -> dict:
    return {
        "asin":          snap.asin,
        "title":         snap.title,
        "price":         snap.price,
        "price_value":   snap.price_value,
        "rating":        snap.rating,
        "review_count":  snap.review_count,
        "availability":  snap.availability,
        "sales_rank":    snap.sales_rank,
        "rank_category": snap.rank_category,
        "data_source":   snap.data_source,
        "fetched_at":    snap.fetched_at,
    }


def _fetch_one(asin: str) -> dict:
    key = cfg.get("rainforest_api_key")
    errors = []

    if key:
        for attempt in range(2):
            try:
                snap = rainforest.get_product(asin)
                return {"asin": asin, "status": "ok", "source": "rainforest",
                        "snapshot": _snap_to_dict(snap)}
            except Exception as e:
                errors.append(f"rainforest[{attempt}]: {e}")
                if "429" in str(e):
                    time.sleep(60)

    try:
        snap = scraper.get_product(asin)
        return {"asin": asin, "status": "ok", "source": "scraper",
                "snapshot": _snap_to_dict(snap)}
    except Exception as e:
        errors.append(f"scraper: {e}")

    return {"asin": asin, "status": "failed", "errors": errors}


def cmd_fetch(args):
    results = [_fetch_one(a) for a in args.asin]
    failed = [r["asin"] for r in results if r["status"] == "failed"]
    scraper_used = [r["asin"] for r in results if r.get("source") == "scraper"]
    print(json.dumps({
        "results": results,
        "summary": {
            "total": len(results),
            "ok": sum(1 for r in results if r["status"] == "ok"),
            "failed": failed,
            "scraper_fallback": scraper_used,
        },
    }, default=str))


def cmd_bestsellers(args):
    key = cfg.get("rainforest_api_key")
    errors = []
    items = None
    source = None

    if key:
        try:
            items = rainforest.get_bestsellers(args.category, args.top)
            source = "rainforest"
        except Exception as e:
            errors.append(f"rainforest: {e}")

    if items is None:
        try:
            items = scraper.get_bestsellers(args.category, args.top)
            source = "scraper"
        except Exception as e:
            errors.append(f"scraper: {e}")

    if items is None:
        print(json.dumps({"status": "failed", "category": args.category,
                          "errors": errors}))
        return

    print(json.dumps({"status": "ok", "source": source, "category": args.category,
                      "count": len(items), "items": items}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_fetch = sub.add_parser("fetch")
    p_fetch.add_argument("--asin", action="append", required=True)

    p_best = sub.add_parser("bestsellers")
    p_best.add_argument("--category", default="all")
    p_best.add_argument("--top", type=int, default=20)

    args = parser.parse_args()
    {"fetch": cmd_fetch, "bestsellers": cmd_bestsellers}[args.cmd](args)
