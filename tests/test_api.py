"""Tests for the pure-Python PVL HTML parser."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest

MODULE_PATH = Path(__file__).parents[1] / "custom_components" / "pvl_reservoir" / "api.py"
SPEC = importlib.util.spec_from_file_location("pvl_api_under_test", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
api = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = api
SPEC.loader.exec_module(api)


def make_page(rows: str, timestamp: str = "18.11.2026 15:20") -> str:
    """Build a minimal page using PVL's verified table and timestamp IDs."""
    return f'<span id="casMereniLbl">{timestamp}</span><table id="AktualniHodnotyDV">{rows}</table>'


class ParseCurrentMeasurementsTests(unittest.TestCase):
    """Check successful parsing and safe handling of unavailable fields."""

    def test_parses_current_values_and_prague_timestamp(self) -> None:
        rows = "".join(f"<tr><td>{label}</td><td>{value}</td></tr>" for label, value in [
            ("Hladina vody v nádrži", "261,80 m n. m."),
            ("Objem", "177,83 mil. m³"),
            ("Přítok", "31,42 m³/s"),
            ("Odtok", "0,00 m³/s"),
            ("Srážky (24h)", "1,5 mm"),
            ("Teplota vzduchu", "10,8 °C"),
        ])
        # The parser receives numeric table cells without the display unit suffix.
        rows = rows.replace("261,80 m n. m.", "261,80").replace("177,83 mil. m³", "177,83").replace("31,42 m³/s", "31,42").replace("0,00 m³/s", "0,00").replace("1,5 mm", "1,5").replace("10,8 °C", "10,8")
        result = api.parse_current_measurements(make_page(rows))
        self.assertEqual(result.water_level_m, 261.8)
        self.assertEqual(result.volume_million_m3, 177.83)
        self.assertEqual(result.inflow_m3_s, 31.42)
        self.assertEqual(result.outflow_m3_s, 0.0)
        self.assertEqual(result.precipitation_24h_mm, 1.5)
        self.assertEqual(result.air_temperature_c, 10.8)
        self.assertEqual(result.measured_at.isoformat(), "2026-11-18T15:20:00+01:00")

    def test_blank_field_is_not_treated_as_zero(self) -> None:
        rows = "".join(f"<tr><td>{label}</td><td>{value}</td></tr>" for label, value in [
            ("Hladina vody v nádrži", "261,80"), ("Objem", "177,83"),
            ("Přítok", "31,42"), ("Odtok", "0,00"),
            ("Srážky (24h)", ""), ("Teplota vzduchu", "10,8"),
        ])
        self.assertIsNone(api.parse_current_measurements(make_page(rows)).precipitation_24h_mm)

    def test_malformed_nonempty_value_fails_safely(self) -> None:
        with self.assertRaises(api.PVLPageError):
            api._parse_number("not-a-number", "inflow")

    def test_missing_current_table_fails_safely(self) -> None:
        with self.assertRaises(api.PVLPageError):
            api.parse_current_measurements("<html><body>no measurements</body></html>")


if __name__ == "__main__":
    unittest.main()
