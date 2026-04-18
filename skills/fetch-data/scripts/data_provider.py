#!/usr/bin/env python3
"""Unified data provider: Rainforest API → scraper fallback."""
from __future__ import annotations
import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[3]))
from shared import config as cfg, db

import rainforest
import scraper


def _fetch_product(asin: str) -> dict:
    key = cfg.get("rainforest_api_key")
    errors = []

    if key:
        for attempt in range(2):
            try:
                snap = rainforest.get_product(asin)
                db.save_snapshot(snap)
                return {"asin": asin, "status": "ok", "source": "rainforest",
                        "data": snap.__dict__}
            except Exception as e:
                errors.append(f"rainforest: {e}")
                if "429" in str(e):
                    time.sleep(60)

    try:
        snap = scraper.get_product(asin)
        db.save_snapshot(snap)
        return {"asin": asin, "status": "ok", "source": "scraper", "data": snap.__dict__}
    except Exception as e:
        errors.append(f"scraper: {e}")

    return {"asin": asin, "status": "failed", "errors": errors}


def cmd_fetch(args):
    db.init()
    results = [_fetch_product(a) for a in args.asin]
    failed = [r["asin"] for r in results if r["status"] == "failed"]
    scraper_used = [r["asin"] for r in results if r.get("source") == "scraper"]
    print(json.dumps({
        "results": results,
        "summary": {
            "total": len(results),
            "ok": len([r for r in results if r["status"] == "ok"]),
            "failed": failed,
            "scraper_fallback": scraper_used,
        }
    }, default=str))


def cmd_bestsellers(args):
    key = cfg.get("rainforest_api_key")
    try:
        if key:
            items = rainforest.get_bestsellers(args.category, args.top)
            source = "rainforest"
        else:
            raise ValueError("no key")
    except Exception:
        items = scraper.get_bestsellers(args.category, args.top)
        source = "scraper"
    print(json.dumps({"source": source, "category": args.category,
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
