"""Tests for skills/amz-monitor/scripts/analyze.py"""
import json
import subprocess
import sys
from pathlib import Path

import analyze

SCRIPT = Path(__file__).resolve().parent.parent / "skills" / "amz-monitor" / "scripts" / "analyze.py"


def _snap(rank=None, price=None, price_raw="$10.00", source="rainforest",
          ts="2026-04-18T14:00:00"):
    return {
        "sales_rank": rank,
        "price_value": price,
        "price": price_raw,
        "fetched_at": ts,
        "data_source": source,
    }


class TestLabel:
    def test_single_point_insufficient(self):
        assert analyze._label([]) == "— 数据不足"
        assert analyze._label([5]) == "— 数据不足"

    def test_above_threshold_is_anomaly(self):
        # THRESHOLD default = 3, so a delta of 5 triggers it
        assert analyze._label([5, 1]) == "⚠ 异动"
        assert analyze._label([-5, 1]) == "⚠ 异动"

    def test_consecutive_up(self):
        # deltas = rank_older - rank_newer; positive means rank improved
        assert analyze._label([2, 2]) == "📈 上升"

    def test_consecutive_down(self):
        assert analyze._label([-2, -2]) == "📉 下降"

    def test_mixed_is_stable(self):
        assert analyze._label([2, -1]) == "➡ 稳定"


class TestAnalyzeProduct:
    def test_no_history_returns_no_data(self):
        out = analyze.analyze_product({"asin": "B00TEST0000", "history": []})
        assert out["status"] == "no_data"
        assert out["label"] == "— 数据不足"
        assert out["alert"] is False

    def test_single_snapshot_no_delta(self):
        out = analyze.analyze_product({
            "asin": "B00TEST0000",
            "history": [_snap(rank=18, price=24.99)],
        })
        assert out["rank_curr"] == 18
        assert out["rank_prev"] is None
        assert out["rank_delta"] is None
        assert out["alert"] is False

    def test_rank_improvement_within_threshold(self):
        # rank went from 20 → 18, delta = +2, below threshold
        out = analyze.analyze_product({
            "asin": "B00TEST0000",
            "history": [_snap(rank=18), _snap(rank=20)],
        })
        assert out["rank_curr"] == 18
        assert out["rank_prev"] == 20
        assert out["rank_delta"] == 2
        assert out["alert"] is False

    def test_rank_jump_triggers_alert(self):
        # rank went from 25 → 18, delta = +7, above threshold (3)
        out = analyze.analyze_product({
            "asin": "B00TEST0000",
            "history": [_snap(rank=18), _snap(rank=25)],
        })
        assert out["rank_delta"] == 7
        assert out["alert"] is True

    def test_rank_drop_triggers_alert(self):
        # rank went from 10 → 30, delta = -20, above threshold
        out = analyze.analyze_product({
            "asin": "B00TEST0000",
            "history": [_snap(rank=30), _snap(rank=10)],
        })
        assert out["rank_delta"] == -20
        assert out["alert"] is True

    def test_price_change_in_summary(self):
        out = analyze.analyze_product({
            "asin": "B00TEST0000",
            "history": [
                _snap(rank=18, price=22.00, price_raw="$22.00"),
                _snap(rank=20, price=24.99, price_raw="$24.99"),
            ],
        })
        # price dropped, summary should mention it
        assert "价格下降" in out["summary"]

    def test_title_fallback_from_snapshot(self):
        history = [{"sales_rank": 10, "fetched_at": "x", "title": "from-snap"}]
        out = analyze.analyze_product({"asin": "B00TEST0000", "history": history})
        assert out["title"] == "from-snap"


class TestRunAll:
    def test_focus_selects_largest_abs_delta(self):
        products = [
            {"asin": "A00000000A", "history": [_snap(rank=10), _snap(rank=12)]},  # delta +2
            {"asin": "B00000000B", "history": [_snap(rank=30), _snap(rank=10)]},  # delta -20
            {"asin": "C00000000C", "history": [_snap(rank=5),  _snap(rank=8)]},   # delta +3
        ]
        out = analyze.run_all(products)
        assert out["focus"]["asin"] == "B00000000B"
        assert len(out["products"]) == 3

    def test_alerts_only_includes_above_threshold(self):
        products = [
            {"asin": "A00000000A", "history": [_snap(rank=10), _snap(rank=12)]},  # no alert
            {"asin": "B00000000B", "history": [_snap(rank=30), _snap(rank=10)]},  # alert
        ]
        out = analyze.run_all(products)
        alert_asins = [a["asin"] for a in out["alerts"]]
        assert alert_asins == ["B00000000B"]

    def test_empty_products(self):
        out = analyze.run_all([])
        assert out["products"] == []
        assert out["alerts"] == []
        assert out["focus"] is None


class TestCLI:
    def _run(self, mode, payload):
        return subprocess.run(
            [sys.executable, str(SCRIPT), f"--{mode}"],
            input=json.dumps(payload), capture_output=True, text=True, check=True,
        )

    def test_all_mode(self):
        payload = {"products": [
            {"asin": "B00TEST0000", "history": [_snap(rank=10), _snap(rank=20)]},
        ]}
        out = json.loads(self._run("all", payload).stdout)
        assert out["focus"]["asin"] == "B00TEST0000"

    def test_asin_mode(self):
        payload = {"asin": "B00TEST0000", "history": [_snap(rank=10), _snap(rank=20)]}
        out = json.loads(self._run("asin", payload).stdout)
        assert out["asin"] == "B00TEST0000"
        assert out["rank_delta"] == 10
