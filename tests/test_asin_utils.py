# SPDX-License-Identifier: MIT
# Copyright (c) 2026 xiao
"""Tests for skills/scavio-amazon/scripts/asin_utils.py"""
import json
import subprocess
import sys
from pathlib import Path

import asin_utils

SCRIPT = Path(__file__).resolve().parent.parent / "skills" / "scavio-amazon" / "scripts" / "asin_utils.py"


class TestValidate:
    def test_valid_asin(self):
        assert asin_utils.validate("B0CHWX8DFH") == {"asin": "B0CHWX8DFH", "valid": True}

    def test_lowercase_is_normalized(self):
        assert asin_utils.validate("b0chwx8dfh") == {"asin": "B0CHWX8DFH", "valid": True}

    def test_whitespace_stripped(self):
        assert asin_utils.validate("  B0CHWX8DFH  ") == {"asin": "B0CHWX8DFH", "valid": True}

    def test_too_short(self):
        assert asin_utils.validate("B0CHWX8DF")["valid"] is False

    def test_too_long(self):
        assert asin_utils.validate("B0CHWX8DFH1")["valid"] is False

    def test_lowercase_only_still_normalized_and_valid(self):
        assert asin_utils.validate("abcdefghij")["valid"] is True

    def test_contains_invalid_char(self):
        assert asin_utils.validate("B0CHWX8DF!")["valid"] is False

    def test_empty(self):
        assert asin_utils.validate("")["valid"] is False


class TestCLI:
    def _run(self, *args):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            capture_output=True, text=True, check=True,
        )
        return json.loads(result.stdout)

    def test_single_valid(self):
        out = self._run("B0CHWX8DFH")
        assert out["valid"] == ["B0CHWX8DFH"]
        assert out["invalid"] == []

    def test_mixed(self):
        out = self._run("B0CHWX8DFH", "bad!", "B09G9HD6PD")
        assert set(out["valid"]) == {"B0CHWX8DFH", "B09G9HD6PD"}
        assert out["invalid"] == ["BAD!"]
