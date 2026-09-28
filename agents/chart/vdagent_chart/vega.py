from __future__ import annotations

from typing import Any

VEGA_SCHEMA = "https://vega.github.io/schema/vega-lite/v5.json"


def _fields(records: list[dict[str, Any]]) -> tuple[str, str]:
    names = list(records[0]) if records else []
    x = next((name for name in names if name in {"month", "label", "status", "stage", "bin_start", "area"}), names[0] if names else "label")
    y = next((name for name in names if name not in {x, "unit_id", "order", "bin_end"} and isinstance(records[0].get(name), (int, float))), "value")
    return x, y


def build_vega_spec(chart_type: str, records: list[dict[str, Any]], title: str) -> dict[str, Any]:
    x, y = _fields(records)
    mark = "bar" if chart_type in {"bar", "histogram", "funnel"} else chart_type
    if chart_type == "pie":
        encoding = {"theta": {"field": y, "type": "quantitative"}, "color": {"field": x, "type": "nominal"}}
        mark = "arc"
    elif chart_type == "heatmap":
        encoding = {"x": {"field": "month", "type": "ordinal"}, "y": {"field": "area", "type": "nominal"}, "color": {"field": y, "type": "quantitative"}}
        mark = "rect"
    elif chart_type == "scatter":
        encoding = {"x": {"field": "price_m2", "type": "quantitative"}, "y": {"field": "dom", "type": "quantitative"}}
        mark = "point"
    else:
        encoding = {"x": {"field": x, "type": "temporal" if x == "month" else "nominal"}, "y": {"field": y, "type": "quantitative"}}
    return {"$schema": VEGA_SCHEMA, "title": title, "data": {"values": records}, "mark": {"type": mark, "tooltip": True}, "encoding": encoding}
