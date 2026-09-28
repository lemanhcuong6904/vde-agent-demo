from __future__ import annotations

import unittest

from vdagent_chart.fixtures import load_demo_task, scenario_names


class FixtureGenerationTests(unittest.TestCase):
    def test_demo_scenarios_cover_required_vhop_visual_questions(self) -> None:
        scenarios = set(scenario_names())

        self.assertTrue(
            {"dom_peer", "price_trend", "inventory_composition", "dom_distribution", "price_dom_relationship", "sales_funnel", "area_month_heatmap"}
            <= scenarios
        )

    def test_missing_dependency_task_keeps_an_exact_missing_ref(self) -> None:
        task = load_demo_task("missing_dependency")

        self.assertEqual(task.task_id, "chart_task_missing_dependency")
        self.assertTrue(any(ref.artifact_id == "metric_not_ready" and ref.required for ref in task.artifact_refs))
