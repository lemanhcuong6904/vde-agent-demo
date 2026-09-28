from __future__ import annotations

import re

from .errors import ChartError

_HTML = re.compile(r"<[^>]*>")
_CAUSAL = re.compile(r"\b(causes?|caused|because|therefore|dẫn đến|nguyên nhân)\b", re.IGNORECASE)


def build_presentation(title: str, subtitle: str | None = None) -> dict[str, str]:
    if _CAUSAL.search(title) or (subtitle and _CAUSAL.search(subtitle)):
        raise ChartError("SEM-001", "causal wording is not allowed without causal evidence", "semantic")
    clean_title = _HTML.sub("", title).strip()
    if not clean_title:
        raise ChartError("SEM-002", "chart title must not be empty", "semantic")
    return {"title": clean_title, "subtitle": _HTML.sub("", subtitle or "").strip(), "language": "vi-VN"}
