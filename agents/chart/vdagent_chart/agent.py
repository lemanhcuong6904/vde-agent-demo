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
        if text.startswith("[from:") and "] " in text:
            text = text.split("] ", 1)[1]
        if not text.startswith("chart demo "):
            await ctx.emit_assistant("Use `chart demo <scenario>`; e.g. `chart demo price_trend`.")
            return
        scenario = text.removeprefix("chart demo ").strip()
        try:
            task = load_demo_task(scenario)
            result = await self._service.execute_async(task)
        except KeyError:
            await ctx.emit_assistant(f"Unknown chart demo scenario: {scenario}")
            return
        if result.chart_artifacts:
            refs = list(result.chart_artifacts)
            store = getattr(ctx, "artifacts", None)
            if store is not None:
                refs = []
                for local_ref in result.chart_artifacts:
                    local = self._service.artifacts[local_ref.removesuffix("@1")]
                    persisted_spec = {**local["semantic_spec"], **local["render_spec"]}
                    saved = await store.save_chart_spec(
                        title=local["presentation"]["title"],
                        chart_spec=persisted_spec,
                        idempotency_key=f"{task.idempotency_key}:{local_ref}",
                        logical_chart_id=local["semantic_spec"]["chart_id"],
                        dataset_hash=local["dataset"]["dataset_hash"],
                        lineage={"input_artifact_refs": local["lineage"]},
                        validation={"overall_result": "pass"},
                        limitations=list(local.get("limitations", ())),
                    )
                    refs.append(f"{saved['id']}@{saved['version']}")
            await ctx.emit_assistant("Created chart artifact: " + ", ".join(refs))
        elif result.dependency_requests:
            request = result.dependency_requests[0]
            await ctx.emit_assistant(f"Chart could not run: required artifact {request['artifact_id']}@{request['version']} is unavailable.")
        else:
            await ctx.emit_assistant("Chart task failed validation.")

    async def compact(self, previous_summary: str, messages: list[Message]) -> str:
        return previous_summary
