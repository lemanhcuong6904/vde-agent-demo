from __future__ import annotations

import unittest

from vdagent_chart.contracts import VisualTarget
from vdagent_chart.policy import load_policy
from vdagent_chart.selection import select_chart


class SelectionTests(unittest.TestCase):
    def test_maps_visual_questions_to_policy_compatible_chart_types(self) -> None:
        policy = load_policy("chart-policy/demo-1.0")
        self.assertEqual(select_chart(VisualTarget("a", "trend"), policy)["chart_type"], "line")
        self.assertEqual(select_chart(VisualTarget("b", "relationship"), policy)["chart_type"], "scatter")
        self.assertEqual(select_chart(VisualTarget("c", "matrix"), policy)["chart_type"], "heatmap")

    def test_invalid_llm_or_user_preference_falls_back_to_safe_type(self) -> None:
        policy = load_policy("chart-policy/demo-1.0")
        decision = select_chart(VisualTarget("a", "trend", preferred_chart_type="pie"), policy, llm_suggestion="waterfall")
        self.assertEqual(decision["chart_type"], "line")
        self.assertEqual(decision["reason_code"], "SEL_POLICY_VISUAL_QUESTION")

    def test_supports_the_complete_visual_question_catalog(self) -> None:
        policy = load_policy("chart-policy/demo-1.0")
        cases = {
            "current_value": "kpi_card", "comparison": "bar", "distribution_comparison": "box_plot",
            "geospatial": "map", "additive_change": "waterfall", "hierarchy": "treemap", "actual_vs_target": "bullet",
        }
        for question, expected in cases.items():
            with self.subTest(question=question):
                self.assertEqual(select_chart(VisualTarget(question, question), policy)["chart_type"], expected)
