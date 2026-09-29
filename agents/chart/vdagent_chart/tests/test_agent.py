from __future__ import annotations

import unittest

from vdagent_chart.agent import ChartPluginAgent
from vdagent_chart.fixture_store import FixtureArtifactStore
from vdagent_chart.service import ChartAgentService


class AgentTests(unittest.IsolatedAsyncioTestCase):
    async def test_fixture_command_emits_chart_reference(self) -> None:
        class Ctx:
            history = [{"role": "user", "content": "chart demo price_trend"}]
            emitted: list[str] = []
            async def emit_assistant(self, content, tool_calls=()): self.emitted.append(content)
        ctx = Ctx()
        await ChartPluginAgent(ChartAgentService(FixtureArtifactStore.demo())).invoke(ctx)
        self.assertIn("chart_chart_task_price_trend_vt_price_trend@1", ctx.emitted[-1])

    async def test_plugin_persists_to_context_artifact_store_when_available(self) -> None:
        class Store:
            async def save_chart_spec(self, **kwargs):
                self.kwargs = kwargs
                return {"id": "csp_0123456789ab", "version": 1}
        class Ctx:
            history = [{"role": "user", "content": "chart demo price_trend"}]
            emitted: list[str] = []
            artifacts = Store()
            async def emit_assistant(self, content, tool_calls=()): self.emitted.append(content)
        ctx = Ctx()

        await ChartPluginAgent(ChartAgentService(FixtureArtifactStore.demo())).invoke(ctx)

        self.assertIn("csp_0123456789ab@1", ctx.emitted[-1])

    async def test_persisted_demo_idempotency_key_is_scoped_to_chart_content(self) -> None:
        class Store:
            def __init__(self) -> None:
                self.idempotency_key = ""

            async def save_chart_spec(self, **kwargs):
                self.idempotency_key = kwargs["idempotency_key"]
                return {"id": "csp_0123456789ab", "version": 1}

        class Ctx:
            history = [{"role": "user", "content": "chart demo price_trend"}]
            emitted: list[str] = []
            artifacts = Store()

            async def emit_assistant(self, content, tool_calls=()):
                self.emitted.append(content)

        ctx = Ctx()

        await ChartPluginAgent(ChartAgentService(FixtureArtifactStore.demo())).invoke(ctx)

        self.assertRegex(
            ctx.artifacts.idempotency_key,
            r"^price-trend-v1:chart_chart_task_price_trend_vt_price_trend@1:sha256:[0-9a-f]{64}$",
        )
