from __future__ import annotations

import unittest

from vdagent_chart.fixture_store import FixtureArtifactStore
from vdagent_chart.fixtures import load_demo_task
from vdagent_chart import make_reasoner
from vdagent_chart.llm import OpenAIVisualReasoner
from vdagent_chart.service import ChartAgentService
from vdagent_chart.telemetry import InMemoryTelemetry


def test_telemetry_removes_sensitive_keys_and_values():
    from vdagent_chart.telemetry import safe_attributes

    attributes = safe_attributes(
        {"status": "success", "prompt": "ignore this", "api_key": "sk-secret", "trace_id": "trace-1", "note": "a@b.com"}
    )

    assert attributes == {"status": "success", "trace_id": "trace-1"}


class FailingReasoner:
    async def suggest(self, visual_question: str, allowed_chart_types: tuple[str, ...]) -> str | None:
        raise TimeoutError("provider unavailable")


class AsyncRuntimeTests(unittest.IsolatedAsyncioTestCase):
    def test_reasoner_factory_uses_gpt_4o_mini_only_when_openai_is_configured(self) -> None:
        reasoner = make_reasoner(
            {
                "OPENAI_API_KEY": "test-key",
                "OPENAI_BASE_URL": "https://api.openai.com/v1",
                "LLM_MODEL": "gpt-4o-mini",
            }
        )

        self.assertIsInstance(reasoner, OpenAIVisualReasoner)
        self.assertIsNone(make_reasoner({}))

    async def test_llm_failure_keeps_deterministic_result_and_emits_safe_events(self) -> None:
        telemetry = InMemoryTelemetry()
        service = ChartAgentService(
            FixtureArtifactStore.demo(), reasoner=FailingReasoner(), telemetry=telemetry
        )

        result = await service.execute_async(load_demo_task("price_trend"))

        self.assertEqual(result.status, "success")
        self.assertEqual([event.name for event in telemetry.events], [
            "chart.started", "chart.llm.unavailable", "chart.completed"
        ])
        self.assertNotIn("visual_question", telemetry.events[1].attributes)
        self.assertNotIn("OPENAI_API_KEY", str(telemetry.events))
