"""Base Feishu API client — token management and low-level HTTP calls."""
from __future__ import annotations
import time
import requests
from shared import config as cfg

_token_cache: dict = {"token": None, "expires_at": 0}
_BASE = "https://open.feishu.cn/open-apis"


def _tenant_token() -> str:
    """Fetch or return cached tenant_access_token."""
    now = time.time()
    if _token_cache["token"] and now < _token_cache["expires_at"] - 60:
        return _token_cache["token"]

    conf = cfg.load()
    resp = requests.post(
        f"{_BASE}/auth/v3/tenant_access_token/internal",
        json={
            "app_id": conf["feishu_app_id"],
            "app_secret": conf["feishu_app_secret"],
        },
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    _token_cache["token"] = data["tenant_access_token"]
    _token_cache["expires_at"] = now + data["expire"]
    return _token_cache["token"]


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {_tenant_token()}",
        "Content-Type": "application/json",
    }


def get(path: str, **kwargs) -> dict:
    r = requests.get(f"{_BASE}{path}", headers=_headers(), timeout=15, **kwargs)
    r.raise_for_status()
    return r.json()


def post(path: str, body: dict) -> dict:
    r = requests.post(f"{_BASE}{path}", headers=_headers(), json=body, timeout=15)
    r.raise_for_status()
    return r.json()


def patch(path: str, body: dict) -> dict:
    r = requests.patch(f"{_BASE}{path}", headers=_headers(), json=body, timeout=15)
    r.raise_for_status()
    return r.json()


def upload_image(image_bytes: bytes, mime: str = "image/png") -> str:
    """Upload image to Feishu and return image_key."""
    token = _tenant_token()
    r = requests.post(
        f"{_BASE}/im/v1/images",
        headers={"Authorization": f"Bearer {token}"},
        data={"image_type": "message"},
        files={"image": ("chart.png", image_bytes, mime)},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["data"]["image_key"]
