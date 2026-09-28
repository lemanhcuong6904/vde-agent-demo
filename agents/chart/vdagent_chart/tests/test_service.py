from __future__ import annotations

import unittest

from vdagent_chart.fixture_store import FixtureArtifactStore
from vdagent_chart.fixtures import load_demo_task
from vdagent_chart.service import ChartAgentService


class ServiceTests(unittest.TestCase):
    def test_creates_a_validated_chart_spec_for_a_demo_task(self) -> None:
        result = ChartAgentService(FixtureArtifactStore.demo()).execute(load_demo_task("price_trend"))
        self.assertEqual(result.status, "success")
        self.assertEqual(len(result.chart_artifacts), 1)

    def test_returns_structured_dependency_request_without_hallucinating(self) -> None:
        result = ChartAgentService(FixtureArtifactStore.demo()).execute(load_demo_task("missing_dependency"))
        self.assertEqual(result.status, "failed")
        self.assertEqual(result.dependency_requests[0]["artifact_id"], "metric_not_ready")
