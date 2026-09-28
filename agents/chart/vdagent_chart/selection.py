from __future__ import annotations

from .contracts import ChartPolicy, VisualTarget

QUESTION_DEFAULTS = {
    "current_value": "kpi_card", "trend": "line", "comparison": "bar", "target_vs_peer": "bar",
    "composition": "pie", "distribution": "histogram", "distribution_comparison": "box_plot",
    "relationship": "scatter", "matrix": "heatmap", "geospatial": "map", "funnel": "funnel",
    "additive_change": "waterfall", "hierarchy": "treemap", "actual_vs_target": "bullet",
}


def select_chart(target: VisualTarget, policy: ChartPolicy, llm_suggestion: str | None = None) -> dict[str, str]:
    preferred = target.preferred_chart_type or llm_suggestion
    expected = QUESTION_DEFAULTS.get(target.visual_question, policy.fallback_chart_type)
    if preferred == expected and preferred in policy.allowed_chart_types:
        return {"chart_type": preferred, "reason_code": "SEL_PREFERENCE_ACCEPTED"}
    return {"chart_type": expected if expected in policy.allowed_chart_types else policy.fallback_chart_type, "reason_code": "SEL_POLICY_VISUAL_QUESTION"}
