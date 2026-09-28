from __future__ import annotations

from vdagent_sdk import InvocationContext, Message

from .fixtures import load_demo_task
from .service import ChartAgentService

NAME = "chart"
DESCRIPTION = "Builds validated, traceable chart specifications from pinned demo artifacts."


class ChartPluginAgent:
    def __init__(self, service: ChartAgentService) -> None:
        self._service = service

    async def invoke(self, ctx: InvocationContext) -> None:
        text = str(ctx.history[-1].get("content", "")).strip()
        if not text.startswith("chart demo "):
            await ctx.emit_assistant("Use `chart demo <scenario>`; e.g. `chart demo price_trend`.")
            return
        scenario = text.removeprefix("chart demo ").strip()
        try:
            result = self._service.execute(load_demo_task(scenario))
        except KeyError:
            await ctx.emit_assistant(f"Unknown chart demo scenario: {scenario}")
            return
        if result.chart_artifacts:
            await ctx.emit_assistant("Created chart artifact: " + ", ".join(result.chart_artifacts))
        elif result.dependency_requests:
            request = result.dependency_requests[0]
            await ctx.emit_assistant(f"Chart could not run: required artifact {request['artifact_id']}@{request['version']} is unavailable.")
        else:
            await ctx.emit_assistant("Chart task failed validation.")

    async def compact(self, previous_summary: str, messages: list[Message]) -> str:
        return previous_summary
