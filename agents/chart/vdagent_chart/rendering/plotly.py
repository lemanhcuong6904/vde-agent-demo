from __future__ import annotations

from typing import Any, Mapping

from .theme import resolve_theme

FIELD_LABELS = {
    "area": "Area",
    "area_m2": "$S\\;(m^2)$",
    "available": "Available units",
    "bin_start": "DOM bucket",
    "count": "Count",
    "dom": "DOM (days)",
    "label": "Label",
    "month": "Month",
    "price_m2": "$P\\;(\\mathrm{million\\ VND}/m^2)$",
    "stage": "Stage",
}


def _text(value: Any, fallback: str = "") -> str:
    if isinstance(value, Mapping):
        return str(value.get("value") or fallback)
    return str(value or fallback)


def _field(encoding: Mapping[str, Any], channel: str, fallback: str) -> str:
    value = encoding.get(channel)
    if isinstance(value, Mapping) and isinstance(value.get("field"), str):
        return str(value["field"])
    return fallback


def _axis_title(presentation: Mapping[str, Any], axis: str, fallback: str) -> str:
    spec = presentation.get(f"{axis}_axis")
    if isinstance(spec, Mapping):
        return _text(spec.get("title"), fallback)
    return FIELD_LABELS.get(fallback, fallback)


def _layout(title: str, presentation: Mapping[str, Any]) -> dict[str, Any]:
    theme = resolve_theme(str(presentation.get("theme_ref") or "dashboard/default"))
    return {
        "title": {"text": title, "font": {"size": theme["title_size"]}},
        "font": {"family": theme["font_family"], "size": theme["font_size"]},
        "paper_bgcolor": theme["paper_bgcolor"],
        "plot_bgcolor": theme["plot_bgcolor"],
        "margin": {"l": 64, "r": 24, "t": 56, "b": 56},
        "hovermode": "closest",
    }


def _xy_trace(chart_type: str, records: list[dict[str, Any]], encoding: Mapping[str, Any]) -> dict[str, Any]:
    x_field = _field(encoding, "x", "label")
    y_field = _field(encoding, "y", "value")
    trace_type = "scatter" if chart_type in {"line", "area", "scatter"} else "bar"
    trace: dict[str, Any] = {
        "type": trace_type,
        "x": [record.get(x_field) for record in records],
        "y": [record.get(y_field) for record in records],
        "name": y_field,
        "hovertemplate": f"{x_field}: %{{x}}<br>{y_field}: %{{y}}<extra></extra>",
    }
    if chart_type == "line":
        trace["mode"] = "lines+markers"
    elif chart_type == "area":
        trace["mode"] = "lines"
        trace["fill"] = "tozeroy"
    elif chart_type == "scatter":
        trace["mode"] = "markers"
        detail = encoding.get("detail")
        if isinstance(detail, Mapping) and isinstance(detail.get("field"), str):
            trace["text"] = [record.get(str(detail["field"])) for record in records]
            trace["hovertemplate"] = f"{detail['field']}: %{{text}}<br>{x_field}: %{{x}}<br>{y_field}: %{{y}}<extra></extra>"
    return trace


def _heatmap_trace(records: list[dict[str, Any]], encoding: Mapping[str, Any]) -> dict[str, Any]:
    x_field = _field(encoding, "x", "x")
    y_field = _field(encoding, "y", "y")
    color_field = _field(encoding, "color", "value")
    x_values = list(dict.fromkeys(record.get(x_field) for record in records))
    y_values = list(dict.fromkeys(record.get(y_field) for record in records))
    lookup = {(record.get(x_field), record.get(y_field)): record.get(color_field) for record in records}
    return {
        "type": "heatmap",
        "x": x_values,
        "y": y_values,
        "z": [[lookup.get((x_value, y_value)) for x_value in x_values] for y_value in y_values],
        "colorscale": "Blues",
        "colorbar": {"title": {"text": FIELD_LABELS.get(color_field, color_field)}},
        "hovertemplate": (
            f"{FIELD_LABELS.get(x_field, x_field)}: %{{x}}<br>"
            f"{FIELD_LABELS.get(y_field, y_field)}: %{{y}}<br>"
            f"{FIELD_LABELS.get(color_field, color_field)}: %{{z}}<extra></extra>"
        ),
    }


def _pie_trace(records: list[dict[str, Any]], encoding: Mapping[str, Any]) -> dict[str, Any]:
    label_field = _field(encoding, "color", "label")
    value_field = _field(encoding, "theta", "value")
    return {
        "type": "pie",
        "labels": [record.get(label_field) for record in records],
        "values": [record.get(value_field) for record in records],
        "hole": 0.35,
        "textinfo": "label+percent",
    }


def _funnel_trace(records: list[dict[str, Any]]) -> dict[str, Any]:
    ordered = sorted(records, key=lambda item: item.get("order", 0))
    return {
        "type": "funnel",
        "y": [record.get("stage") for record in ordered],
        "x": [record.get("count") for record in ordered],
        "textinfo": "value+percent initial",
        "hovertemplate": "stage: %{y}<br>count: %{x}<extra></extra>",
    }


def render_plotly(spec: dict[str, Any]) -> dict[str, Any]:
    dataset = spec.get("dataset", {})
    records = list(dataset.get("records", ())) if isinstance(dataset, Mapping) else []
    encoding = spec.get("encoding", {})
    encoding = encoding if isinstance(encoding, Mapping) else {}
    presentation = spec.get("presentation", {})
    presentation = presentation if isinstance(presentation, Mapping) else {}
    title = _text(presentation.get("title_spec"), str(presentation.get("title", "")))
    chart_type = str(spec.get("chart_type") or "bar")
    if chart_type == "funnel":
        data = [_funnel_trace(records)]
    elif chart_type == "pie":
        data = [_pie_trace(records, encoding)]
    elif chart_type == "heatmap":
        data = [_heatmap_trace(records, encoding)]
    else:
        data = [_xy_trace(chart_type, records, encoding)]
    layout = _layout(title, presentation)
    if chart_type not in {"pie", "funnel"}:
        layout["xaxis"] = {"title": {"text": _axis_title(presentation, "x", _field(encoding, "x", ""))}}
        layout["yaxis"] = {"title": {"text": _axis_title(presentation, "y", _field(encoding, "y", ""))}, "gridcolor": "#e5e7eb"}
    return {
        "renderer": "plotly",
        "data": data,
        "layout": layout,
        "config": {"responsive": True, "displaylogo": False, "typesetMath": True},
    }
