from __future__ import annotations

import unittest

from vdagent_chart.vega import build_vega_spec


class VegaTests(unittest.TestCase):
    def test_builds_declarative_line_spec_without_business_logic(self) -> None:
        spec = build_vega_spec("line", [{"month": "2026-01", "price_m2": 68.0}], "Price trend")
        self.assertEqual(spec["mark"], {"type": "line", "tooltip": True})
        self.assertEqual(spec["encoding"]["x"]["field"], "month")
