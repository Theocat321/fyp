import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from app.main import to_iso_ts, iso_now


class TestToIsoTs:
    def test_none_returns_none(self):
        assert to_iso_ts(None) is None

    def test_epoch_ms_converted(self):
        # 1_700_000_000_000 ms → 2023
        result = to_iso_ts(1_700_000_000_000)
        assert result is not None
        assert "2023" in result

    def test_epoch_seconds(self):
        # 1_700_000_000 s → 2023
        result = to_iso_ts(1_700_000_000)
        assert result is not None
        assert "2023" in result

    def test_string_returned_as_is(self):
        assert to_iso_ts("2024-01-01T00:00:00Z") == "2024-01-01T00:00:00Z"

    def test_threshold_boundary(self):
        # Values > 1e12 treated as ms; the ms value should equal the same instant as that number / 1000
        ms_value = 1_600_000_000_000  # epoch ms → 2020
        s_value = 1_600_000_000       # epoch s  → 2020
        result_ms = to_iso_ts(ms_value)
        result_s = to_iso_ts(s_value)
        assert result_ms is not None
        assert result_s is not None
        # Both should land in the same second after dividing ms by 1000
        assert result_ms == result_s

    def test_invalid_type_returns_none(self):
        assert to_iso_ts({"not": "a timestamp"}) is None

    def test_float_epoch(self):
        result = to_iso_ts(1_700_000_000.5)
        assert result is not None


class TestIsoNow:
    def test_returns_string(self):
        result = iso_now()
        assert isinstance(result, str)

    def test_contains_utc_marker(self):
        result = iso_now()
        assert "+" in result or result.endswith("Z") or "+00:00" in result
