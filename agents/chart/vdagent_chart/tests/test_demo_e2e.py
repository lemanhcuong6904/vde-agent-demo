"""Fixture-backed ship gate: every documented demo has a safe render artifact."""

import pytest

from vdagent_chart.fixture_store import FixtureArtifactStore
from vdagent_chart.fixtures import load_demo_task
from vdagent_chart.output_validation import validate_chart_spec
from vdagent_chart.service import ChartAgentService


@pytest.mark.parametrize(
    "scenario",
    [
        "dom_peer",
        "price_trend",
        "inventory_composition",
        "dom_distribution",
        "price_dom_relationship",
        "sales_funnel",
        "area_month_heatmap",
    ],
)
def test_documented_demo_scenario_produces_valid_semantic_spec_and_renderer_projection(scenario: str):
    service = ChartAgentService(FixtureArtifactStore.demo())

    result = service.execute(load_demo_task(scenario))

    assert result.status == "success"
    artifact_id = result.chart_artifacts[0].removesuffix("@1")
    artifact = service.artifacts[artifact_id]
    assert validate_chart_spec(artifact["semantic_spec"])["overall_result"] == "pass"
    assert artifact["semantic_spec"]["validation"]["checks"] == [
        "schema",
        "lineage",
        "dataset",
        "scope",
        "renderer",
        "presentation",
    ]
    assert artifact["render_spec"]["data"]["values"] == artifact["dataset"]["records"]


def test_documented_missing_dependency_returns_only_a_dependency_request():
    result = ChartAgentService(FixtureArtifactStore.demo()).execute(load_demo_task("missing_dependency"))

    assert result.status == "failed"
    assert result.chart_artifacts == ()
    assert result.dependency_requests == ({"artifact_id": "metric_not_ready", "version": 1, "code": "DEP-002"},)
