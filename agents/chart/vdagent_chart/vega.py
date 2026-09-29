from __future__ import annotations

from typing import Any

from .spec_builder import build_encoding

VEGA_SCHEMA = "https://vega.github.io/schema/vega-lite/v5.json"


def build_vega_spec(chart_type: str, records: list[dict[str, Any]], title: str) -> dict[str, Any]:
    if chart_type == "funnel":
        return {
            "$schema": VEGA_SCHEMA,
            "title": title,
            "data": {"values": records},
            "transform": [
                {"joinaggregate": [{"op": "max", "field": "count", "as": "max_count"}]},
                {"calculate": "(datum.max_count - datum.count) / 2", "as": "center_offset"},
                {"calculate": "datum.center_offset + datum.count", "as": "funnel_end"},
            ],
            "mark": {"type": "bar", "tooltip": True},
            "encoding": {
                "y": {
                    "field": "stage",
                    "type": "nominal",
                    "sort": {"field": "order", "order": "ascending"},
                    "title": "stage",
                },
                "x": {"field": "center_offset", "type": "quantitative", "axis": None},
                "x2": {"field": "funnel_end"},
                "color": {"field": "stage", "type": "nominal", "legend": None},
                "tooltip": [
                    {"field": "stage", "type": "nominal"},
                    {"field": "count", "type": "quantitative"},
                ],
            },
        }
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
    chart_type = str(spec["chart_type"])
    rendered = build_vega_spec(chart_type, list(dataset.get("records", ())), str(presentation.get("title", "")))
    if chart_type != "funnel":
        rendered["encoding"] = dict(spec.get("encoding") or build_encoding(chart_type, list(dataset.get("records", ()))))
    return rendered
