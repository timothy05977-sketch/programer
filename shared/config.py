"""Agent configuration — loaded from env vars or written by init-tracker."""
from __future__ import annotations
import json
import os
from pathlib import Path

_CONFIG_FILE = Path(__file__).parent.parent / ".tracker_config.json"

_DEFAULTS = {
    "amazon_marketplace": "US",
    "alert_threshold": 3,
    "interval_minutes": 20,
    "report_language": "zh-CN",
    "timezone_offset": 8,
}

_MARKETPLACE_DOMAINS = {
    "US": "amazon.com",
    "JP": "amazon.co.jp",
    "UK": "amazon.co.uk",
    "DE": "amazon.de",
    "CA": "amazon.ca",
}


def load() -> dict:
    cfg = dict(_DEFAULTS)
    if _CONFIG_FILE.exists():
        cfg.update(json.loads(_CONFIG_FILE.read_text()))
    for key in ("RAINFOREST_API_KEY", "FEISHU_DOC_TOKEN", "FEISHU_BITABLE_TOKEN",
                "FEISHU_BITABLE_TABLE_ID_PRODUCTS",
                "FEISHU_BITABLE_TABLE_ID_SNAPSHOTS"):
        val = os.environ.get(key)
        if val:
            cfg[key.lower()] = val
    return cfg


def save(updates: dict) -> None:
    cfg = load()
    cfg.update(updates)
    _CONFIG_FILE.write_text(json.dumps(cfg, ensure_ascii=False, indent=2))


def get(key: str, default=None):
    return load().get(key, default)


def amazon_domain() -> str:
    market = get("amazon_marketplace", "US")
    return _MARKETPLACE_DOMAINS.get(market, "amazon.com")


def is_initialized() -> bool:
    required = ["rainforest_api_key", "feishu_doc_token", "amazon_marketplace"]
    cfg = load()
    return all(cfg.get(k) for k in required)
