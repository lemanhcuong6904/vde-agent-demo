from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import replace

from .contracts import ChartTaskInput, ChartTaskResult, ResolvedChartContext, TargetResult
from .evidence import build_evidence_map
from .dataset import assemble_dataset
from .errors import ChartError
from .fixture_store import FixtureArtifactStore
from .llm import VisualReasoner
from .policy import load_policy
from .profile import profile_target
from .schema import normalize_artifact
from .presentation import build_presentation
from .selection import select_chart
from .telemetry import TelemetryPort
from .validation import validate_input
from .vega import build_vega_spec


class ChartAgentService:
    """Deterministic execution entry point for fixture-backed Chart Agent demos."""

    def __init__(
        self,
        store: FixtureArtifactStore,
        *,
        reasoner: VisualReasoner | None = None,
        telemetry: TelemetryPort | None = None,
    ) -> None:
        self._store = store
        self._reasoner = reasoner
        self._telemetry = telemetry
        self.artifacts: dict[str, dict] = {}

    def execute(
        self, task: ChartTaskInput, llm_suggestions: Mapping[str, str | None] | None = None
    ) -> ChartTaskResult:
        try:
            resolved = [self._store.get_exact(ref) for ref in task.artifact_refs]
        except ChartError as exc:
            missing = next((ref for ref in task.artifact_refs if ref.artifact_id in str(exc)), task.artifact_refs[0])
            return ChartTaskResult("chart-result/2.0", task.run_id, task.task_id, "failed", dependency_requests=({"artifact_id": missing.artifact_id, "version": missing.version, "code": exc.code},))
        policy = load_policy(task.policy_ref)
        validate_input(task, resolved, policy)
        context = ResolvedChartContext(
            task, policy, tuple(normalize_artifact(artifact) for artifact in resolved),
            {"overall_result": "pass"},
        )
        refs: list[str] = []
        targets: list[TargetResult] = []
        errors: list[dict[str, str]] = []
        for target in task.visual_targets:
            try:
                target_context = replace(context, task=replace(task, visual_targets=(target,)))
                binding = build_evidence_map(target_context)[target.target_id]
                decision = select_chart(
                    target,
                    policy,
                    (llm_suggestions or {}).get(target.target_id),
                    profile_target(target_context, binding),
                )
                dataset = assemble_dataset(target, resolved, decision)
            except ChartError as exc:
                targets.append(TargetResult(target.target_id, "failed", reason_code=exc.code))
                errors.append({"target_id": target.target_id, "code": exc.code, "message": exc.message})
                continue
            title = f"{target.visual_question.replace('_', ' ').title()} — VHop"
            presentation = build_presentation(title, f"Snapshot {task.scope.snapshot_id or 'n/a'}")
            render_spec = build_vega_spec(decision["chart_type"], dataset["records"], presentation["title"])
            chart_id = f"chart_{task.task_id}_{target.target_id}"
            content = {"chart_type": decision["chart_type"], "dataset": dataset, "render_spec": render_spec, "lineage": [f"{a['artifact_id']}@{a['version']}" for a in resolved]}
            content_hash = "sha256:" + hashlib.sha256(json.dumps(content, sort_keys=True).encode()).hexdigest()
            self.artifacts[chart_id] = {"artifact_id": chart_id, "version": 1, "status": "validated", **content, "content_hash": content_hash, "selection": decision, "presentation": presentation}
            refs.append(f"{chart_id}@1")
            targets.append(TargetResult(target.target_id, "success", f"{chart_id}@1"))
        status = "success" if not errors else "partial" if refs else "failed"
        return ChartTaskResult(
            "chart-result/2.0",
            task.run_id,
            task.task_id,
            status,
            tuple(refs),
            tuple(targets),
            errors=tuple(errors),
        )

    async def execute_async(self, task: ChartTaskInput) -> ChartTaskResult:
        """Run optional bounded LLM advice, then the deterministic workflow."""
        self._record("chart.started", {"target_count": len(task.visual_targets)})
        suggestions: dict[str, str | None] = {}
        if self._reasoner is not None:
            policy = load_policy(task.policy_ref)
            for target in task.visual_targets:
                try:
                    suggestions[target.target_id] = await self._reasoner.suggest(
                        target.visual_question, policy.allowed_chart_types
                    )
                except Exception:
                    suggestions[target.target_id] = None
                    self._record("chart.llm.unavailable", {"target_count": 1})
        result = self.execute(task, suggestions)
        self._record(
            "chart.completed",
            {"status": result.status, "artifact_count": len(result.chart_artifacts)},
        )
        return result

    def _record(self, name: str, attributes: Mapping[str, str | int | bool]) -> None:
        if self._telemetry is not None:
            self._telemetry.record(name, attributes)
