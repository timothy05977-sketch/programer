#!/usr/bin/env python3
"""Validate and persist agent configuration."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[3]))
from shared import config as cfg


_CONFIG_KEYS = (
    "amazon_marketplace",
    "rainforest_api_key",
    "feishu_doc_token",
    "feishu_bitable_token",
    "feishu_bitable_table_id_products",
    "feishu_bitable_table_id_snapshots",
)


def save(args):
    updates = {k: v for k in _CONFIG_KEYS
               if (v := getattr(args, k, None))}
    cfg.save(updates)
    print(json.dumps({"status": "ok", "saved": list(updates.keys())}))


def test_rainforest():
    import requests
    key = cfg.get("rainforest_api_key")
    if not key:
        print(json.dumps({"status": "skipped", "reason": "no_api_key"}))
        return
    try:
        resp = requests.get(
            "https://api.rainforestapi.com/request",
            params={"api_key": key, "type": "product", "asin": "B08N5WRWNW",
                    "amazon_domain": cfg.amazon_domain()},
            timeout=15,
        )
        if resp.status_code == 200:
            print(json.dumps({"status": "ok", "source": "rainforest"}))
        elif resp.status_code == 401:
            print(json.dumps({"status": "error", "reason": "invalid_api_key"}))
        else:
            print(json.dumps({"status": "error", "code": resp.status_code}))
    except Exception as e:
        print(json.dumps({"status": "error", "reason": str(e)}))


def check():
    conf = cfg.load()
    missing = [k for k in cfg.REQUIRED_KEYS if not conf.get(k)]
    print(json.dumps({
        "initialized": len(missing) == 0,
        "missing": missing,
        "has_rainforest_key": bool(conf.get("rainforest_api_key")),
        "marketplace": conf.get("amazon_marketplace"),
    }))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")

    p_save = sub.add_parser("save")
    for k in _CONFIG_KEYS:
        p_save.add_argument(f"--{k.replace('_', '-')}", dest=k)

    sub.add_parser("test-rainforest")
    sub.add_parser("check")

    args = parser.parse_args()
    if args.cmd == "save":
        save(args)
    elif args.cmd == "test-rainforest":
        test_rainforest()
    else:
        check()
