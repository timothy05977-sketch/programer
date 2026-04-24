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


_ENV_OVERRIDABLE_KEYS = (
    "amazon_marketplace",
    "rainforest_api_key",
    "feishu_doc_token",
    "feishu_bitable_token",
    "feishu_bitable_table_id_products",
    "feishu_bitable_table_id_snapshots",
    "alert_threshold",
    "interval_minutes",
    "report_language",
    "timezone_offset",
)


def load() -> dict:
    cfg = dict(_DEFAULTS)
    if _CONFIG_FILE.exists():
        cfg.update(json.loads(_CONFIG_FILE.read_text()))
    for key in _ENV_OVERRIDABLE_KEYS:
        val = os.environ.get(key.upper())
        if val is not None and val != "":
            cfg[key] = val
    return cfg


def save(updates: dict) -> None:
    # Persist only explicit user values so _DEFAULTS stay centralized in code.
    existing = {}
    if _CONFIG_FILE.exists():
        existing = json.loads(_CONFIG_FILE.read_text())
    existing.update(updates)
    _CONFIG_FILE.write_text(json.dumps(existing, ensure_ascii=False, indent=2))


def get(key: str, default=None):
    return load().get(key, default)


def amazon_domain() -> str:
    market = get("amazon_marketplace", "US")
    return _MARKETPLACE_DOMAINS.get(market, "amazon.com")


REQUIRED_KEYS = (
    "amazon_marketplace",
    "feishu_doc_token",
    "feishu_bitable_token",
    "feishu_bitable_table_id_products",
    "feishu_bitable_table_id_snapshots",
)


def is_initialized() -> bool:
    cfg = load()
    return all(cfg.get(k) for k in REQUIRED_KEYS)
