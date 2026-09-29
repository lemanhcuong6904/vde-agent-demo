from __future__ import annotations

import unittest

from vdagent_chart.vega import build_vega_spec


def test_renderer_projection_is_derived_from_semantic_spec():
    from vdagent_chart.vega import render_vega

    semantic_spec = {
        "schema_version": "chart-spec/2.0",
        "chart_type": "line",
        "dataset": {"records": [{"month": "2026-01", "value": 10}]},
        "presentation": {"title": "Monthly value"},
    }

    rendered = render_vega(semantic_spec)

    assert rendered["title"] == "Monthly value"
    assert rendered["data"]["values"] == [{"month": "2026-01", "value": 10}]
    assert rendered["mark"]["type"] == "line"


class VegaTests(unittest.TestCase):
    def test_builds_declarative_line_spec_without_business_logic(self) -> None:
        spec = build_vega_spec("line", [{"month": "2026-01", "price_m2": 68.0}], "Price trend")
        self.assertEqual(spec["mark"], {"type": "line", "tooltip": True})
        self.assertEqual(spec["encoding"]["x"]["field"], "month")

    def test_builds_centered_ordered_funnel_projection(self) -> None:
        spec = build_vega_spec(
            "funnel",
            [
                {"stage": "Visit", "order": 1, "count": 520},
                {"stage": "Booking", "order": 2, "count": 180},
                {"stage": "Deposit", "order": 3, "count": 104},
                {"stage": "Contract", "order": 4, "count": 82},
            ],
            "Sales funnel",
        )

        self.assertEqual(spec["mark"], {"type": "bar", "tooltip": True})
        self.assertEqual(spec["encoding"]["y"]["field"], "stage")
        self.assertEqual(spec["encoding"]["y"]["sort"], {"field": "order", "order": "ascending"})
        self.assertEqual(spec["encoding"]["x"]["field"], "center_offset")
        self.assertEqual(spec["encoding"]["x2"]["field"], "funnel_end")
        self.assertIn({"joinaggregate": [{"op": "max", "field": "count", "as": "max_count"}]}, spec["transform"])
        self.assertIn({"calculate": "(datum.max_count - datum.count) / 2", "as": "center_offset"}, spec["transform"])
