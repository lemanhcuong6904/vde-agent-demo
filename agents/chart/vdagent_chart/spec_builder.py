"""Build the semantic artifact; renderers consume this contract, not business data."""
from __future__ import annotations
from typing import Any


def build_encoding(chart_type: str, records: list[dict[str, Any]]) -> dict[str, Any]:
    """Describe fields semantically; the Vega adapter only projects this mapping."""
    names = list(records[0]) if records else []
    x = next(
        (name for name in names if name in {"month", "label", "status", "stage", "bin_start", "area"}),
        names[0] if names else "label",
    )
    y = next(
        (
            name
            for name in names
            if name not in {x, "unit_id", "order", "bin_end"}
            and isinstance(records[0].get(name), (int, float))
        ),
        "value",
    )
    if chart_type == "pie":
        return {"theta": {"field": y, "type": "quantitative"}, "color": {"field": x, "type": "nominal"}}
    if chart_type == "heatmap":
        return {
            "x": {"field": "month", "type": "ordinal"},
            "y": {"field": "area", "type": "nominal"},
            "color": {"field": y, "type": "quantitative"},
        }
    if chart_type == "scatter":
        return {
            "x": {"field": "price_m2", "type": "quantitative"},
            "y": {"field": "dom", "type": "quantitative"},
        }
    return {
        "x": {"field": x, "type": "temporal" if x == "month" else "nominal"},
        "y": {"field": y, "type": "quantitative"},
    }


def build_semantic_spec(*, chart_id: str, task_id: str, target_id: str, chart_type: str, purpose: str,
                        visual_question: str, scope: dict[str, Any], dataset: dict[str, Any],
                        selection: dict[str, Any], presentation: dict[str, Any], lineage: dict[str, Any],
                        validation: dict[str, Any], limitations: list[str] | None = None) -> dict[str, Any]:
    return {"schema_version": "chart-spec/2.0", "chart_id": chart_id, "task_id": task_id,
            "visual_target_ids": [target_id], "status": "validated", "chart_type": chart_type,
            "purpose": purpose, "visual_question": visual_question, "scope": scope, "dataset": dataset,
            "encoding": build_encoding(chart_type, list(dataset.get("records", ()))), "selection": selection, "presentation": presentation, "lineage": lineage,
            "validation": validation, "limitations": limitations or [], "governance": {"validator_version": "demo/1"}}
