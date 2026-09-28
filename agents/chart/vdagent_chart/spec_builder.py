"""Build the semantic artifact; renderers consume this contract, not business data."""
from __future__ import annotations
from typing import Any


def build_semantic_spec(*, chart_id: str, task_id: str, target_id: str, chart_type: str, purpose: str,
                        visual_question: str, scope: dict[str, Any], dataset: dict[str, Any],
                        selection: dict[str, Any], presentation: dict[str, Any], lineage: dict[str, Any],
                        validation: dict[str, Any], limitations: list[str] | None = None) -> dict[str, Any]:
    return {"schema_version": "chart-spec/2.0", "chart_id": chart_id, "task_id": task_id,
            "visual_target_ids": [target_id], "status": "validated", "chart_type": chart_type,
            "purpose": purpose, "visual_question": visual_question, "scope": scope, "dataset": dataset,
            "encoding": {}, "selection": selection, "presentation": presentation, "lineage": lineage,
            "validation": validation, "limitations": limitations or [], "governance": {"validator_version": "demo/1"}}
