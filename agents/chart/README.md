# Chart Agent demo

This plugin converts exact, version-pinned VHop demo artifacts into validated chart
specifications. It never queries the warehouse at runtime and never calls upstream
agents. Copy `.env.example` to `.env`, supply `OPENAI_API_KEY`, then set
`LLM_MODEL=gpt-4o-mini` (the default) to use OpenAI for bounded visual-language
suggestions.

The deterministic core remains authoritative for values, scope, validation, chart
compatibility, fallback, hashes and persistence.

## Run the demo

From the repository root, activate `.venv` and ensure `agents/chart/.env` contains
an OpenAI-compatible endpoint. The LLM is optional: if the key is absent or the
provider times out, the policy selects the same safe deterministic chart.

```powershell
$env:PYTHONPATH = "agents/chart"
.\.venv\Scripts\python.exe -m pytest agents\chart\vdagent_chart\tests -q
```

Start the backend with `make backend`, then select the **chart** agent and send one
of these messages:

| Command | Chart question | Source fixture |
| --- | --- | --- |
| `chart demo dom_peer` | target versus peer | inventory snapshot |
| `chart demo price_trend` | monthly trend | price history |
| `chart demo inventory_composition` | inventory composition | inventory snapshot |
| `chart demo dom_distribution` | DOM distribution | inventory snapshot |
| `chart demo price_dom_relationship` | price/DOM relationship | price history |
| `chart demo sales_funnel` | sales funnel | funnel daily export |
| `chart demo area_month_heatmap` | area/month matrix | inventory snapshot |
| `chart demo missing_dependency` | dependency failure | intentionally absent exact ref |

The committed fixtures declare snapshot `SNAP-20260630-01` and their three VHop
exports in `vdagent_chart/demo/artifacts.json`. Regenerate or validate source inputs
outside runtime with:

```powershell
.\.venv\Scripts\python.exe data\generate_chart_demo_fixtures.py
```

No demo command queries `warehouse/` at runtime. Each artifact reference is pinned
by ID, version and hash; a missing reference returns a structured dependency request.
