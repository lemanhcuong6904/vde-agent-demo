"""Structured Chart Agent telemetry with deliberately non-sensitive fields."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Protocol


@dataclass(frozen=True)
class ChartEvent:
    name: str
    attributes: Mapping[str, str | int | bool]


class TelemetryPort(Protocol):
    def record(self, name: str, attributes: Mapping[str, str | int | bool]) -> None: ...


class InMemoryTelemetry:
    """Demo/test collector. Production adapters can forward the same safe envelope."""

    def __init__(self) -> None:
        self.events: list[ChartEvent] = []

    def record(self, name: str, attributes: Mapping[str, str | int | bool]) -> None:
        self.events.append(ChartEvent(name, dict(attributes)))
