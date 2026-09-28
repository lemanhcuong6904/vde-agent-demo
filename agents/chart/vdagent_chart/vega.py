from __future__ import annotations

from typing import Any

from .spec_builder import build_encoding

VEGA_SCHEMA = "https://vega.github.io/schema/vega-lite/v5.json"


def build_vega_spec(chart_type: str, records: list[dict[str, Any]], title: str) -> dict[str, Any]:
    mark = "bar" if chart_type in {"bar", "histogram", "funnel"} else chart_type
    if chart_type == "pie":
        mark = "arc"
    if chart_type == "heatmap":
        mark = "rect"
    if chart_type == "scatter":
        mark = "point"
    return {"$schema": VEGA_SCHEMA, "title": title, "data": {"values": records}, "mark": {"type": mark, "tooltip": True}, "encoding": build_encoding(chart_type, records)}


def render_vega(spec: dict[str, Any]) -> dict[str, Any]:
    """Project an already validated semantic spec to a Vega-Lite document."""
    dataset = spec.get("dataset", {})
    presentation = spec.get("presentation", {})
    rendered = build_vega_spec(str(spec["chart_type"]), list(dataset.get("records", ())), str(presentation.get("title", "")))
    rendered["encoding"] = dict(spec.get("encoding") or build_encoding(str(spec["chart_type"]), list(dataset.get("records", ()))))
    return rendered
