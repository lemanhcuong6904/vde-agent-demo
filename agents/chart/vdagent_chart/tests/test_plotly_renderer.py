from __future__ import annotations

from vdagent_chart.rendering.plotly import render_plotly


def test_plotly_renderer_uses_presentation_math_text_and_theme() -> None:
    spec = {
        "chart_type": "scatter",
        "dataset": {
            "records": [{"unit_id": "U01", "area_m2": 72.0, "price_m2": 68.5}],
        },
        "encoding": {
            "x": {"field": "area_m2", "type": "quantitative"},
            "y": {"field": "price_m2", "type": "quantitative"},
            "detail": {"field": "unit_id", "type": "nominal"},
        },
        "presentation": {
            "title_spec": {"format": "plain", "value": "Price by area"},
            "x_axis": {"field": "area_m2", "title": {"format": "math", "value": "$S\\;(m^2)$"}},
            "y_axis": {"field": "price_m2", "title": {"format": "math", "value": "$P\\;(\\mathrm{triệu\\ VND}/m^2)$"}},
            "theme_ref": "dashboard/default",
        },
    }

    rendered = render_plotly(spec)

    assert rendered["renderer"] == "plotly"
    assert rendered["data"][0]["type"] == "scatter"
    assert rendered["data"][0]["mode"] == "markers"
    assert rendered["layout"]["title"]["text"] == "Price by area"
    assert rendered["layout"]["xaxis"]["title"]["text"] == "$S\\;(m^2)$"
    assert rendered["layout"]["yaxis"]["title"]["text"] == "$P\\;(\\mathrm{triệu\\ VND}/m^2)$"
    assert rendered["layout"]["font"]["family"] == "Inter, system-ui, sans-serif"
    assert rendered["config"]["responsive"] is True
    assert rendered["config"]["typesetMath"] is True


def test_plotly_renderer_preserves_funnel_order_and_values() -> None:
    rendered = render_plotly(
        {
            "chart_type": "funnel",
            "dataset": {
                "records": [
                    {"stage": "Visit", "order": 1, "count": 520},
                    {"stage": "Booking", "order": 2, "count": 180},
                ],
            },
            "encoding": {"x": {"field": "stage"}, "y": {"field": "count"}},
            "presentation": {"title_spec": {"format": "plain", "value": "Sales funnel"}},
        }
    )

    assert rendered["data"][0]["type"] == "funnel"
    assert rendered["data"][0]["y"] == ["Visit", "Booking"]
    assert rendered["data"][0]["x"] == [520, 180]


def test_plotly_renderer_projects_heatmap_matrix() -> None:
    rendered = render_plotly(
        {
            "chart_type": "heatmap",
            "dataset": {
                "records": [
                    {"area": "A01", "month": "2026-01", "available": 12},
                    {"area": "A01", "month": "2026-02", "available": 10},
                    {"area": "A02", "month": "2026-01", "available": 8},
                    {"area": "A02", "month": "2026-02", "available": 7},
                ],
            },
            "encoding": {
                "x": {"field": "month", "type": "ordinal"},
                "y": {"field": "area", "type": "nominal"},
                "color": {"field": "available", "type": "quantitative"},
            },
            "presentation": {"title_spec": {"format": "plain", "value": "Inventory heatmap"}},
        }
    )

    assert rendered["data"][0]["type"] == "heatmap"
    assert rendered["data"][0]["x"] == ["2026-01", "2026-02"]
    assert rendered["data"][0]["y"] == ["A01", "A02"]
    assert rendered["data"][0]["z"] == [[12, 10], [8, 7]]
