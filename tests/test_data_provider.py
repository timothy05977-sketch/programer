# SPDX-License-Identifier: MIT
# Copyright (c) 2026 xiao
"""L2 tests for skills/scavio-amazon/scripts/data_provider.py — fallback chain."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

from shared import config as cfg
from shared.models import Snapshot
import data_provider

SCRIPT = Path(__file__).resolve().parent.parent / "skills" / "scavio-amazon" / "scripts" / "data_provider.py"


def _make_snap(asin, source):
    return Snapshot(asin=asin, title=f"title-{asin}", price="$10.00",
                    price_value=10.0, sales_rank=5, data_source=source,
                    fetched_at="2026-04-18T00:00:00")


@pytest.fixture(autouse=True)
def _isolate_cfg(monkeypatch, tmp_path):
    monkeypatch.setattr(cfg, "_CONFIG_FILE", tmp_path / "noexist.json")


class TestFetchOne:
    def test_scavio_ok(self, monkeypatch):
        monkeypatch.setenv("SCAVIO_API_KEY", "k")
        monkeypatch.setattr(data_provider.scavio, "get_product",
                            lambda a: _make_snap(a, "scavio"))
        out = data_provider._fetch_one("B0TEST00001")
        assert out["status"] == "ok"
        assert out["source"] == "scavio"
        assert out["snapshot"]["asin"] == "B0TEST00001"

    def test_scavio_fails_scraper_succeeds(self, monkeypatch):
        monkeypatch.setenv("SCAVIO_API_KEY", "k")
        monkeypatch.setattr(data_provider.time, "sleep", lambda _: None)

        def _raise(asin):
            raise RuntimeError("scavio down")

        monkeypatch.setattr(data_provider.scavio, "get_product", _raise)
        monkeypatch.setattr(data_provider.scraper, "get_product",
                            lambda a: _make_snap(a, "scraper"))

        out = data_provider._fetch_one("B0TEST00001")
        assert out["status"] == "ok"
        assert out["source"] == "scraper"

    def test_no_key_skips_scavio_uses_scraper(self, monkeypatch):
        monkeypatch.delenv("SCAVIO_API_KEY", raising=False)

        scavio_called = {"v": False}

        def _sc(asin):
            scavio_called["v"] = True
            return _make_snap(asin, "scavio")

        monkeypatch.setattr(data_provider.scavio, "get_product", _sc)
        monkeypatch.setattr(data_provider.scraper, "get_product",
                            lambda a: _make_snap(a, "scraper"))

        out = data_provider._fetch_one("B0TEST00001")
        assert out["source"] == "scraper"
        assert scavio_called["v"] is False

    def test_both_fail_returns_failed(self, monkeypatch):
        monkeypatch.setenv("SCAVIO_API_KEY", "k")
        monkeypatch.setattr(data_provider.time, "sleep", lambda _: None)

        def _bad(asin):
            raise RuntimeError("boom")

        monkeypatch.setattr(data_provider.scavio, "get_product", _bad)
        monkeypatch.setattr(data_provider.scraper, "get_product", _bad)

        out = data_provider._fetch_one("B0TEST00001")
        assert out["status"] == "failed"
        assert len(out["errors"]) >= 2

    def test_429_triggers_backoff_then_fallback(self, monkeypatch):
        monkeypatch.setenv("SCAVIO_API_KEY", "k")
        sleeps = []
        monkeypatch.setattr(data_provider.time, "sleep", lambda s: sleeps.append(s))

        def _rate_limited(asin):
            raise RuntimeError("HTTP 429 Too Many Requests")

        monkeypatch.setattr(data_provider.scavio, "get_product", _rate_limited)
        monkeypatch.setattr(data_provider.scraper, "get_product",
                            lambda a: _make_snap(a, "scraper"))

        out = data_provider._fetch_one("B0TEST00001")
        assert out["source"] == "scraper"
        assert 60 in sleeps


class TestBestsellers:
    def test_ok_prefers_scavio(self, monkeypatch):
        monkeypatch.setenv("SCAVIO_API_KEY", "k")
        monkeypatch.setattr(data_provider.scavio, "get_bestsellers",
                            lambda c, n: [{"rank": 1, "asin": "A"}])
        monkeypatch.setattr(data_provider.scraper, "get_bestsellers",
                            lambda c, n: [{"rank": 1, "asin": "FROM_SCRAPER"}])

        import argparse
        captured = {}
        monkeypatch.setattr("builtins.print", lambda s: captured.update(json.loads(s)))
        data_provider.cmd_bestsellers(argparse.Namespace(category="books", top=10))
        assert captured["status"] == "ok"
        assert captured["source"] == "scavio"

    def test_scavio_fails_falls_back_to_scraper(self, monkeypatch):
        monkeypatch.setenv("SCAVIO_API_KEY", "k")

        def _boom(c, n):
            raise RuntimeError("scavio down")

        monkeypatch.setattr(data_provider.scavio, "get_bestsellers", _boom)
        monkeypatch.setattr(data_provider.scraper, "get_bestsellers",
                            lambda c, n: [{"rank": 1, "asin": "S"}])

        import argparse
        captured = {}
        monkeypatch.setattr("builtins.print", lambda s: captured.update(json.loads(s)))
        data_provider.cmd_bestsellers(argparse.Namespace(category="books", top=10))
        assert captured["status"] == "ok"
        assert captured["source"] == "scraper"

    def test_both_fail_returns_json_error(self, monkeypatch):
        monkeypatch.setenv("SCAVIO_API_KEY", "k")

        def _boom(c, n):
            raise RuntimeError("boom")

        monkeypatch.setattr(data_provider.scavio, "get_bestsellers", _boom)
        monkeypatch.setattr(data_provider.scraper, "get_bestsellers", _boom)

        import argparse
        captured = {}
        monkeypatch.setattr("builtins.print", lambda s: captured.update(json.loads(s)))
        data_provider.cmd_bestsellers(argparse.Namespace(category="books", top=10))
        assert captured["status"] == "failed"
        assert len(captured["errors"]) == 2


class TestCLI:
    def _run(self, subcmd, *extra):
        return subprocess.run(
            [sys.executable, str(SCRIPT), subcmd, *extra],
            capture_output=True, text=True, check=True,
        )

    def test_fetch_command_json_shape(self, monkeypatch, tmp_path):
        stub_dir = tmp_path / "stubs"
        stub_dir.mkdir()
        (stub_dir / "scavio.py").write_text(
            "from shared.models import Snapshot\n"
            "def get_product(asin):\n"
            "    return Snapshot(asin=asin, title='t', price='$1', price_value=1.0,\n"
            "                    sales_rank=1, data_source='scavio',\n"
            "                    fetched_at='2026-04-18T00:00:00')\n"
            "def get_bestsellers(c, n): return []\n"
        )
        (stub_dir / "scraper.py").write_text(
            "from shared.models import Snapshot\n"
            "def get_product(asin):\n"
            "    return Snapshot(asin=asin, title='t', data_source='scraper',\n"
            "                    fetched_at='2026-04-18T00:00:00')\n"
            "def get_bestsellers(c, n): return []\n"
        )

        env = {
            **__import__("os").environ,
            "PYTHONPATH": f"{stub_dir}:{Path(__file__).resolve().parent.parent}",
            "SCAVIO_API_KEY": "k",
        }
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "fetch", "--asin", "B0TEST00001"],
            capture_output=True, text=True, env=env, check=True,
        )
        out = json.loads(result.stdout)
        assert "results" in out
        assert "summary" in out
        assert out["summary"]["total"] == 1
