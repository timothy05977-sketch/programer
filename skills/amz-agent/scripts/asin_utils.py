#!/usr/bin/env python3
"""ASIN validation utility — no DB access.

Usage:
  python asin_utils.py B0CHWX8DFH [B09G9HD6PD ...]
Output JSON: {"results":[{"asin":"..","valid":bool}],"valid":[..],"invalid":[..]}
"""
import argparse
import json
import re
import sys

_ASIN_RE = re.compile(r'^[A-Z0-9]{10}$')


def validate(raw: str) -> dict:
    a = raw.strip().upper()
    return {"asin": a, "valid": bool(_ASIN_RE.match(a))}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("asins", nargs="+")
    args = parser.parse_args()

    results = [validate(a) for a in args.asins]
    print(json.dumps({
        "results": results,
        "valid":   [r["asin"] for r in results if r["valid"]],
        "invalid": [r["asin"] for r in results if not r["valid"]],
    }))
