#!/usr/bin/env python3
"""CLI for managing the monitored products list."""
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[3]))
from shared import db

_ASIN_RE = re.compile(r'^[A-Z0-9]{10}$')


def _validate_asin(asin: str) -> str:
    a = asin.strip().upper()
    if not _ASIN_RE.match(a):
        print(json.dumps({"status": "error", "reason": f"invalid_asin: {asin}"}))
        sys.exit(1)
    return a


def cmd_add(args):
    db.init()
    asin = _validate_asin(args.asin)
    existing = [p.asin for p in db.list_products()]
    if asin in existing:
        print(json.dumps({"status": "skipped", "reason": "already_monitored", "asin": asin}))
        return
    db.add_product(asin, label=args.label or "", category=args.category or "")
    print(json.dumps({"status": "ok", "action": "added", "asin": asin, "label": args.label}))


def cmd_remove(args):
    db.init()
    asin = _validate_asin(args.asin)
    removed = db.remove_product(asin)
    print(json.dumps({"status": "ok" if removed else "not_found",
                      "action": "removed", "asin": asin}))


def cmd_list(_args):
    db.init()
    products = db.list_products()
    print(json.dumps({
        "status": "ok",
        "count": len(products),
        "products": [{"asin": p.asin, "label": p.label,
                      "category": p.category, "added_at": p.added_at}
                     for p in products],
    }))


def cmd_label(args):
    db.init()
    asin = _validate_asin(args.asin)
    db.update_product_label(asin, args.label)
    print(json.dumps({"status": "ok", "action": "labeled", "asin": asin, "label": args.label}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_add = sub.add_parser("add")
    p_add.add_argument("asin")
    p_add.add_argument("--label", default="")
    p_add.add_argument("--category", default="")

    p_rm = sub.add_parser("remove")
    p_rm.add_argument("asin")

    sub.add_parser("list")

    p_lbl = sub.add_parser("label")
    p_lbl.add_argument("asin")
    p_lbl.add_argument("label")

    args = parser.parse_args()
    {"add": cmd_add, "remove": cmd_remove, "list": cmd_list, "label": cmd_label}[args.cmd](args)
