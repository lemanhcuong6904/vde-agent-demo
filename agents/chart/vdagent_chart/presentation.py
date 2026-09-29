from __future__ import annotations

from typing import Any
import re

from .errors import ChartError
from .safety import sanitize_text

_HTML = re.compile(r"<[^>]*>")
_CAUSAL = re.compile(
    r"\b(causes?|caused|because|therefore|dẫn đến|nguyên nhân)\b", re.IGNORECASE
)


def build_presentation(
    title: str,
    subtitle: str | None = None,
    annotations: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if _CAUSAL.search(title) or (subtitle and _CAUSAL.search(subtitle)):
        raise ChartError(
            "SEM-001",
            "causal wording is not allowed without causal evidence",
            "semantic",
        )
    clean_title = sanitize_text(_HTML.sub("", title))
    if not clean_title:
        raise ChartError("SEM-002", "chart title must not be empty", "semantic")
    presentation: dict[str, Any] = {
        "title": clean_title,
        "subtitle": sanitize_text(_HTML.sub("", subtitle or "")),
        "language": "vi-VN",
    }
    if annotations:
        presentation["annotations"] = [
            {
                key: sanitize_text(_HTML.sub("", str(value))) if isinstance(value, str) else value
                for key, value in annotation.items()
            }
            for annotation in annotations
            if isinstance(annotation, dict)
        ]
    return presentation
