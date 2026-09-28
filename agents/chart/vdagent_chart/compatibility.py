"""Deterministic data-shape checks before a chart type may be selected."""

from __future__ import annotations

from .errors import ChartError
from .profile import DataProfile


def compatibility_errors(chart_type: str, profile: DataProfile) -> tuple[ChartError, ...]:
    errors: list[ChartError] = []
    if chart_type in {"line", "area"} and (not profile.has_time or profile.row_count < 2):
        errors.append(ChartError("DAT-002", f"{chart_type} requires an ordered time series with at least two records", "data"))
    if chart_type == "scatter" and len(profile.metric_fields) < 2:
        errors.append(ChartError("DAT-008", "scatter requires two numeric metrics", "data"))
    if chart_type in {"bar", "pie", "funnel", "heatmap", "histogram"} and profile.row_count == 0:
        errors.append(ChartError("DAT-002", f"{chart_type} requires at least one record", "data"))
    return tuple(errors)
