"""Narrow GPT-4o-mini adapter; its suggestions never bypass deterministic policy."""

from __future__ import annotations

import asyncio
import json
from typing import Protocol

from .settings import Settings


class VisualReasoner(Protocol):
    async def suggest(self, visual_question: str, allowed_chart_types: tuple[str, ...]) -> str | None: ...


class OpenAIVisualReasoner:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def suggest(self, visual_question: str, allowed_chart_types: tuple[str, ...]) -> str | None:
        import litellm

        prompt = {"visual_question": visual_question, "allowed_chart_types": allowed_chart_types}
        async with asyncio.timeout(self._settings.llm_timeout_s):
            response = await litellm.acompletion(
                model=f"openai/{self._settings.llm_model}", api_base=self._settings.openai_base_url,
                api_key=self._settings.openai_api_key, temperature=0,
                messages=[{"role": "system", "content": "Return only JSON: {\\\"chart_type\\\": allowed value or null}."}, {"role": "user", "content": json.dumps(prompt)}],
            )
        try:
            value = json.loads(response.choices[0].message.content or "{}").get("chart_type")
        except json.JSONDecodeError:
            return None
        return value if value in allowed_chart_types else None
