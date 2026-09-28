"""Deterministic, safe minimum validator for semantic ChartSpec artifacts."""

from __future__ import annotations
from typing import Any
import re

_UNSAFE_PRESENTATION = re.compile(r"\b(causes?|caused|because|therefore)\b|[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", re.I)


def validate_chart_spec(spec: dict[str, Any]) -> dict[str, Any]:
    checks = []
    valid_schema = spec.get("schema_version") == "chart-spec/2.0"
    checks.append("schema")
    lineage = spec.get("lineage", {})
    valid_lineage = isinstance(lineage, dict) and bool(
        lineage.get("input_artifact_refs")
    )
    checks.append("lineage")
    dataset = spec.get("dataset", {})
    valid_dataset = (
        isinstance(dataset, dict) and "records" in dataset and "dataset_hash" in dataset
    )
    checks.append("dataset")
    title = str(spec.get("presentation", {}).get("title", ""))
    valid_presentation = not _UNSAFE_PRESENTATION.search(title)
    checks.append("presentation")
    failures = [
        name
        for name, valid in (
            ("schema", valid_schema),
            ("lineage", valid_lineage),
            ("dataset", valid_dataset),
            ("presentation", valid_presentation),
        )
        if not valid
    ]
    return {
        "overall_result": "pass" if not failures else "fail",
        "checks": checks,
        "failures": failures,
    }
