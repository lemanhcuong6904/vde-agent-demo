"""Narrow GPT-4o-mini adapter; its suggestions never bypass deterministic policy."""

from __future__ import annotations

import asyncio
import json
from typing import Any, Protocol

from .settings import Settings


class VisualReasoner(Protocol):
    async def decide(self, payload: dict[str, Any], allowed_chart_types: tuple[str, ...]) -> dict[str, Any] | None: ...
    async def suggest(self, visual_question: str, allowed_chart_types: tuple[str, ...]) -> str | None: ...


class OpenAIVisualReasoner:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def decide(self, payload: dict[str, Any], allowed_chart_types: tuple[str, ...]) -> dict[str, Any] | None:
        import litellm

        prompt = {**payload, "allowed_chart_types": allowed_chart_types}
        async with asyncio.timeout(self._settings.llm_timeout_s):
            response = await litellm.acompletion(
                model=f"openai/{self._settings.llm_model}", api_base=self._settings.openai_base_url,
                api_key=self._settings.openai_api_key, temperature=0,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Return only JSON with keys: visual_question, candidates, selected_chart_type, "
                            "encoding, presentation. selected_chart_type must be one allowed value or null. "
                            "Encoding fields must come from the provided data_profile fields. Do not invent or change data values."
                        ),
                    },
                    {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
                ],
            )
        try:
            value = json.loads(response.choices[0].message.content or "{}")
        except json.JSONDecodeError:
            return None
        if not isinstance(value, dict):
            return None
        selected = value.get("selected_chart_type") or value.get("chart_type")
        if selected not in allowed_chart_types:
            value["selected_chart_type"] = None
        else:
            value["selected_chart_type"] = selected
        return value

    async def suggest(self, visual_question: str, allowed_chart_types: tuple[str, ...]) -> str | None:
        decision = await self.decide({"visual_question": visual_question}, allowed_chart_types)
        selected = None if decision is None else decision.get("selected_chart_type")
        return selected if isinstance(selected, str) and selected in allowed_chart_types else None
