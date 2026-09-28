from __future__ import annotations

import json
from pathlib import Path

from .contracts import ArtifactRef, ChartTaskInput, Scope, VisualTarget

TASKS_FILE = Path(__file__).parent / "demo" / "tasks.json"


def _task(raw: dict) -> ChartTaskInput:
    scope = raw["scope"]
    return ChartTaskInput(
        schema_version=raw["schema_version"], run_id=raw["run_id"], task_id=raw["task_id"], mode=raw["mode"],
        scope=Scope(tuple(scope.get("project_ids", [])), tuple(scope.get("area_ids", [])), scope.get("snapshot_id"),
                    tuple(scope["time_range"]) if scope.get("time_range") else None, scope.get("data_grain")),
        visual_targets=tuple(VisualTarget(t["target_id"], t["visual_question"], t.get("purpose", "direct_visualization"),
                                           t.get("preferred_chart_type"), tuple(t.get("artifact_ids", []))) for t in raw["visual_targets"]),
        artifact_refs=tuple(ArtifactRef(r["artifact_id"], r["version"], r.get("expected_hash"), r.get("required", True)) for r in raw["artifact_refs"]),
        policy_ref=raw["policy_ref"], idempotency_key=raw["idempotency_key"],
    )


def _raw_tasks() -> list[dict]:
    return json.loads(TASKS_FILE.read_text(encoding="utf-8"))["tasks"]


def scenario_names() -> tuple[str, ...]:
    return tuple(task["name"] for task in _raw_tasks())


def load_demo_task(name: str) -> ChartTaskInput:
    for task in _raw_tasks():
        if task["name"] == name:
            return _task(task)
    raise KeyError(f"unknown chart demo task {name!r}")
