# report agent

Builds charts (`create_chart`) and a saved markdown report (`save_report`) from the findings and datasets it is given; replies with the report id.

A Backend plugin (see [`agents/_template`](../_template/README.md) and the `vdagent_sdk` docstring):
`vdagent_report/__init__.py` exports `setup(api, opts)`, which registers the agent. The brain is a thin
tool-calling loop over LiteLLM (`agent.py`, `llm.py`, `mcp_client.py`); its role prompt is
`vdagent_report/prompts/system.md`, the summariser prompt `prompts/compact.md`.

MCP tools granted by the Backend (`backend/vdagent_backend/mcp/tools.py`): `create_chart`, `save_report`, `describe_dataset`, `get_dataset_rows`;
plus `send_to_agent` to reach the other agents.

## Run

The Backend loads it at startup when `vdagent_report` is listed under `plugins:` in
`backend/config.yaml` (it is by default): `make backend` from the repo root. There is no separate
process.

Configure it in `agents/report/.env` (gitignored). The plugin reads the file itself with
`dotenv_values()`; its values win over the Backend's process environment. A missing required
variable makes the plugin fail to load: the Backend logs `plugin vdagent_report failed: …` and starts
without this agent.

| Variable | |
|---|---|
| `OPENAI_API_KEY`, `OPENAI_BASE_URL`, `LLM_MODEL` | Required. OpenAI-compatible endpoint with tool calling. |
| `LLM_TIMEOUT_S` | Per LLM call, default 120. |

## Test

```
uv run pytest agents/report
```
