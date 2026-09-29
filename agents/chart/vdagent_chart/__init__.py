"""VDAgent Chart Agent plugin package."""

from collections.abc import Mapping
from typing import Any

from vdagent_sdk import PluginAPI

from .agent import ChartPluginAgent, DESCRIPTION, NAME
from .fixture_store import FixtureArtifactStore
from .llm import OpenAIVisualReasoner, VisualReasoner
from .service import ChartAgentService
from .settings import load_settings, read_env
from .errors import ChartError


def make_reasoner(env: Mapping[str, str]) -> VisualReasoner | None:
    """Enable the optional GPT advisor only with a complete local config."""
    try:
        return OpenAIVisualReasoner(load_settings(env))
    except ChartError:
        return None


def setup(api: PluginAPI, opts: Mapping[str, Any]) -> None:
    reasoner = make_reasoner(read_env())
    service = ChartAgentService(FixtureArtifactStore.demo(), reasoner=reasoner)
    api.register_agent(name=NAME, description=DESCRIPTION, agent=ChartPluginAgent(service, upstream_reasoner=reasoner))
