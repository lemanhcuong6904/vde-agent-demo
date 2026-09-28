"""End-to-end Chart Agent release gate through the real invocation engine."""

from __future__ import annotations

import re

import pytest

from conftest import ALICE
from vdagent_backend.db import artifacts
from vdagent_backend.plugins import RegisteredAgent
from vdagent_chart.agent import ChartPluginAgent
from vdagent_chart.fixture_store import FixtureArtifactStore
from vdagent_chart.service import ChartAgentService


@pytest.mark.asyncio
async def test_chart_plugin_persists_an_owner_scoped_chart_spec_through_the_engine(harness) -> None:
    harness.registry._agents["chart"] = RegisteredAgent(  # type: ignore[attr-defined]
        "chart", "chart agent", ChartPluginAgent(ChartAgentService(FixtureArtifactStore.demo())), "tests"
    )

    task_id = await harness.post("chart", "chart demo price_trend")
    await harness.wait_task(task_id, "completed")
    transcript = await harness.stack("chart")
    chart_id = re.search(r"(csp_[0-9a-f]{12})@1", transcript[-1]["content"])

    assert chart_id is not None, [(row["role"], row["content"]) for row in transcript]
    stored = await artifacts.get_chart_spec(harness.db, ALICE, chart_id.group(1))
    assert stored is not None
    assert stored["chart_spec"]["$schema"].endswith("vega-lite/v5.json")
    assert stored["lineage"]["input_artifact_refs"] == ["metric_price_trend@1"]
