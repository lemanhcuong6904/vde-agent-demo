"""VDAgent Chart Agent plugin package."""

from collections.abc import Mapping
from typing import Any

from vdagent_sdk import PluginAPI

from .agent import ChartPluginAgent, DESCRIPTION, NAME
from .fixture_store import FixtureArtifactStore
from .service import ChartAgentService


def setup(api: PluginAPI, opts: Mapping[str, Any]) -> None:
    api.register_agent(name=NAME, description=DESCRIPTION, agent=ChartPluginAgent(ChartAgentService(FixtureArtifactStore.demo())))
