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
    "US": "https://www.amazon.com",
    "JP": "https://www.amazon.co.jp",
    "UK": "https://www.amazon.co.uk",
    "DE": "https://www.amazon.de",
    "CA": "https://www.amazon.ca",
}


def load() -> dict:
    cfg = dict(_DEFAULTS)
    if _CONFIG_FILE.exists():
        cfg.update(json.loads(_CONFIG_FILE.read_text()))
    # Env vars override file (useful for CI / secrets)
    for key in ("RAINFOREST_API_KEY", "FEISHU_DOC_TOKEN",
                 "FEISHU_BITABLE_TOKEN", "FEISHU_BITABLE_TABLE_ID"):
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


def amazon_base_url() -> str:
    market = get("amazon_marketplace", "US")
    return _MARKETPLACE_DOMAINS.get(market, _MARKETPLACE_DOMAINS["US"])


def is_initialized() -> bool:
    required = ["rainforest_api_key", "feishu_doc_token", "amazon_marketplace"]
    cfg = load()
    return all(cfg.get(k) for k in required)
