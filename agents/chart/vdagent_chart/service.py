from __future__ import annotations

import hashlib
import json

from .contracts import ChartTaskInput, ChartTaskResult, TargetResult
from .dataset import assemble_dataset
from .errors import ChartError
from .fixture_store import FixtureArtifactStore
from .policy import load_policy
from .presentation import build_presentation
from .selection import select_chart
from .validation import validate_input
from .vega import build_vega_spec


class ChartAgentService:
    """Deterministic execution entry point for fixture-backed Chart Agent demos."""

    def __init__(self, store: FixtureArtifactStore) -> None:
        self._store = store
        self.artifacts: dict[str, dict] = {}

    def execute(self, task: ChartTaskInput) -> ChartTaskResult:
        try:
            resolved = [self._store.get_exact(ref) for ref in task.artifact_refs]
        except ChartError as exc:
            missing = next((ref for ref in task.artifact_refs if ref.artifact_id in str(exc)), task.artifact_refs[0])
            return ChartTaskResult("chart-result/2.0", task.run_id, task.task_id, "failed", dependency_requests=({"artifact_id": missing.artifact_id, "version": missing.version, "code": exc.code},))
        policy = load_policy(task.policy_ref)
        validate_input(task, resolved, policy)
        refs: list[str] = []
        targets: list[TargetResult] = []
        for target in task.visual_targets:
            decision = select_chart(target, policy)
            dataset = assemble_dataset(target, resolved, decision)
            title = f"{target.visual_question.replace('_', ' ').title()} — VHop"
            presentation = build_presentation(title, f"Snapshot {task.scope.snapshot_id or 'n/a'}")
            render_spec = build_vega_spec(decision["chart_type"], dataset["records"], presentation["title"])
            chart_id = f"chart_{task.task_id}_{target.target_id}"
            content = {"chart_type": decision["chart_type"], "dataset": dataset, "render_spec": render_spec, "lineage": [f"{a['artifact_id']}@{a['version']}" for a in resolved]}
            content_hash = "sha256:" + hashlib.sha256(json.dumps(content, sort_keys=True).encode()).hexdigest()
            self.artifacts[chart_id] = {"artifact_id": chart_id, "version": 1, "status": "validated", **content, "content_hash": content_hash, "selection": decision, "presentation": presentation}
            refs.append(f"{chart_id}@1")
            targets.append(TargetResult(target.target_id, "success", f"{chart_id}@1"))
        return ChartTaskResult("chart-result/2.0", task.run_id, task.task_id, "success", tuple(refs), tuple(targets))
