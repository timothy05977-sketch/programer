"""Tests for skills/amz-agent/scripts/weekly_report.py"""
import json
import subprocess
import sys
from pathlib import Path

import weekly_report

SCRIPT = Path(__file__).resolve().parent.parent / "skills" / "amz-agent" / "scripts" / "weekly_report.py"


def _snap(rank=None, price=None, ts="2026-04-18T14:00:00"):
    return {"sales_rank": rank, "price_value": price, "fetched_at": ts}


class TestAggregate:
    def test_empty_snapshots(self):
        out = weekly_report.aggregate({"asin": "A", "title": "t", "snapshots": []})
        assert out["snapshot_count"] == 0
        assert out["trend_summary"] == "数据不足"

    def test_single_snapshot(self):
        out = weekly_report.aggregate({
            "asin": "A", "title": "t",
            "snapshots": [_snap(rank=10, price=20)],
        })
        assert out["snapshot_count"] == 1
        assert out["rank"]["min"] == 10
        assert out["rank"]["delta"] is None
        assert out["trend_summary"] == "数据不足"

    def test_sorts_by_fetched_at(self):
        snaps = [
            _snap(rank=15, ts="2026-04-10T00:00:00"),
            _snap(rank=10, ts="2026-04-18T00:00:00"),
            _snap(rank=20, ts="2026-04-05T00:00:00"),
        ]
        out = weekly_report.aggregate({"asin": "A", "snapshots": snaps})
        # period_start = oldest (4/5), period_end = newest (4/18)
        assert out["period_start"] == "2026-04-05T00:00:00"
        assert out["period_end"] == "2026-04-18T00:00:00"
        # delta = first - last = 20 - 10 = 10
        assert out["rank"]["delta"] == 10

    def test_two_snapshots_stable(self):
        out = weekly_report.aggregate({
            "asin": "A",
            "snapshots": [
                _snap(rank=10, ts="2026-04-01T00:00:00"),
                _snap(rank=12, ts="2026-04-10T00:00:00"),
            ],
        })
        assert out["trend_summary"] == "稳定"

    def test_two_snapshots_fluctuation(self):
        out = weekly_report.aggregate({
            "asin": "A",
            "snapshots": [
                _snap(rank=10, ts="2026-04-01T00:00:00"),
                _snap(rank=50, ts="2026-04-10T00:00:00"),
            ],
        })
        assert out["trend_summary"] == "波动"

    def test_five_plus_snapshots_trend_up(self):
        # ranks improving from 100 → 5, recent 5 all below overall mean (35.7)
        snaps = [_snap(rank=r, ts=f"2026-04-{i+1:02d}T00:00:00")
                 for i, r in enumerate([100, 50, 30, 25, 20, 15, 10])]
        out = weekly_report.aggregate({"asin": "A", "snapshots": snaps})
        assert out["trend_summary"] == "持续上升"

    def test_five_plus_snapshots_trend_down(self):
        # ranks worsening from 1 → 100, recent 5 all above overall mean (~57)
        snaps = [_snap(rank=r, ts=f"2026-04-{i+1:02d}T00:00:00")
                 for i, r in enumerate([1, 2, 60, 70, 80, 90, 100])]
        out = weekly_report.aggregate({"asin": "A", "snapshots": snaps})
        assert out["trend_summary"] == "持续下降"

    def test_five_plus_volatile_is_fluctuation(self):
        # High variance without monotonic trend
        snaps = [_snap(rank=r, ts=f"2026-04-{i+1:02d}T00:00:00")
                 for i, r in enumerate([10, 80, 20, 90, 30, 70, 40])]
        out = weekly_report.aggregate({"asin": "A", "snapshots": snaps})
        assert out["trend_summary"] == "波动"

    def test_five_plus_stable_low_variance(self):
        # Low variance, no clear trend
        snaps = [_snap(rank=r, ts=f"2026-04-{i+1:02d}T00:00:00")
                 for i, r in enumerate([50, 51, 49, 50, 52, 48, 50])]
        out = weekly_report.aggregate({"asin": "A", "snapshots": snaps})
        assert out["trend_summary"] == "稳定"

    def test_price_range(self):
        snaps = [_snap(rank=5, price=p, ts=f"2026-04-{i+1:02d}T00:00:00")
                 for i, p in enumerate([20.0, 22.0, 18.0])]
        out = weekly_report.aggregate({"asin": "A", "snapshots": snaps})
        assert out["price"]["min"] == 18.0
        assert out["price"]["max"] == 22.0


class TestRun:
    def test_report_type_weekly(self):
        out = weekly_report.run({"products": []}, days=7)
        assert out["report_type"] == "weekly"
        assert out["days"] == 7

    def test_report_type_monthly(self):
        out = weekly_report.run({"products": []}, days=30)
        assert out["report_type"] == "monthly"

    def test_focus_is_largest_delta(self):
        data = {"products": [
            {"asin": "A", "snapshots": [_snap(rank=10), _snap(rank=12, ts="2026-04-20T00:00:00")]},
            {"asin": "B", "snapshots": [_snap(rank=50), _snap(rank=10, ts="2026-04-20T00:00:00")]},
        ]}
        out = weekly_report.run(data, days=7)
        assert out["focus_asin"] == "B"

    def test_totals(self):
        data = {"products": [
            {"asin": "A", "snapshots": [_snap(rank=10), _snap(rank=12)]},
            {"asin": "B", "snapshots": [_snap(rank=5)]},
        ]}
        out = weekly_report.run(data, days=7)
        assert out["product_count"] == 2
        assert out["total_snapshots"] == 3


class TestCLI:
    def _run(self, payload, days=7):
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--days", str(days)],
            input=json.dumps(payload), capture_output=True, text=True, check=True,
        )

    def test_stdin_stdout(self):
        payload = {"products": [{
            "asin": "A", "title": "t",
            "snapshots": [_snap(rank=10, price=20), _snap(rank=12, price=22, ts="2026-04-20")],
        }]}
        out = json.loads(self._run(payload).stdout)
        assert out["product_count"] == 1
        assert out["products"][0]["asin"] == "A"
