# Chart Agent Demo Design

## Purpose

Build a self-contained VDAgent Chart Agent demo for the VHop warehouse.  It converts
pre-built, version-pinned upstream artifacts into immutable, chart-ready artifacts,
without an Orchestrator or live Data/Insight/Compare agents.  It must use
`gpt-4o-mini` for bounded visual-language reasoning while deterministic code remains
the authority for data, scope, compatibility, validation, hashing, and persistence.

The demo is successful when a user can start VDAgent, send a supplied chart task to
the new `chart` agent, inspect a rendered chart in the existing UI, and trace every
displayed value to the input demo artifacts.

## Scope

### Included

- A new VDAgent plugin at `agents/chart`, registered as `chart`.
- A deterministic Chart Agent core with ports for artifact storage, policy, rendering
  compatibility, and telemetry.
- Versioned fixture artifacts generated from `warehouse/vhop`; they stand in for
  Data, Insight, and Compare Agent outputs.
- A versioned demo policy, typed task/result/spec contracts, immutable chart-spec
  persistence, and a chart API/rendering path compatible with the current Vega-Lite UI.
- `gpt-4o-mini` configuration and a narrow LLM adapter, injected for tests.
- Demo tasks for KPI, trend, peer comparison, composition, distribution, relationship,
  funnel, heatmap, fallback-to-table, and missing-dependency handling.
- Tests for contracts, deterministic guardrails, service integration, and the plugin.

### Excluded

- Building an Orchestrator or changing existing upstream agents to produce these
  artifacts at runtime.
- Warehouse access from the Chart Agent.
- Recalculation of business metrics, peer groups, gaps, or insights.
- A generic production artifact platform or a full implementation of every optional
  chart type in the master specification.

## Architecture

```text
ChartTaskInput (fixture / user message)
  -> ChartAgentService
       -> ArtifactStorePort.get_exact(ref)
       -> ChartPolicyPort.load(version)
       -> deterministic input + cross-artifact validation
       -> per-target evidence map
       -> GPT-4o-mini semantic suggestion (bounded, optional)
       -> deterministic selection and dataset assembly
       -> deterministic output validation
       -> ArtifactStorePort.put_immutable(ChartSpecArtifact)
  -> ChartTaskResult
  -> existing chart API / Vega-Lite renderer
```

The plugin follows the VDAgent `setup(api, opts)` and `Agent.invoke(ctx)` contract
shown in `docs/agent-design.html`.  Its state remains per invocation.  It reports its
turn through `ctx.emit_assistant`; it does not call peer agents and it does not use MCP
tools to read the warehouse.

## Responsibilities and boundaries

The chart plugin owns visual reasoning and declarative ChartSpec construction.  It
reads only exact, task-authorized artifact versions and only creates presentation
transforms: select, rename, deterministic sort, reshape, formatting, and policy-gated
top-N.  It never creates numeric truth.

The fixture producer owns the numeric truth.  It derives static demo artifact JSON
from the supplied warehouse data before the demo is run.  At run time these files are
read-only upstream inputs, not a back door to the warehouse.

The deterministic core is the final decision-maker.  The LLM can return a constrained
suggestion for visual question, candidate preference, title, subtitle, and accessible
summary.  The core discards suggestions outside the task taxonomy or policy and rejects
unsafe wording.  If the LLM is unavailable, the policy selection and deterministic
presentation templates still produce a valid chart.

## Contracts and persistence

`ChartTaskInput` includes schema version, run/task ids, mode, scope, intent with visual
targets, exact `artifact_refs`, a pinned policy version, and idempotency key.  A target
names its visual question and purpose, and may supply a compatible preferred chart type.

Fixture upstream artifacts use an envelope with `artifact_id`, `version`,
`artifact_type`, `run_id`, `status`, `scope`, `content_hash`, and typed payload.
Metric/evidence payloads expose ready-to-display records plus unit, observation grain,
calculation and source lineage.  Insight and comparison artifacts reference their
supporting metric/evidence artifacts.

The output `ChartSpecArtifact` includes its immutable identity/version/content hash;
selection reason; dataset schema, records, row count, hash and transform list;
encoding; sanitized presentation; limitations; exact upstream refs; validation results;
and a Vega-Lite spec that the current frontend can render without any business logic.
An idempotency hit returns the existing semantically equivalent output rather than
creating a new version.

For the demo, backend storage gains one explicit, isolated `chart_artifacts` table and
a read endpoint adapted to the frontend's existing `ChartView`.
The legacy `create_chart` flow stays intact.  The chart frontend understands the
artifact payload and supplies it directly to Vega-Lite.

## Policy and supported demo chart types

`chart-policy/demo-1.0` is immutable fixture data.  It allows the demo's chart types:
`kpi_card`, `line`, `bar`, `grouped_bar`, `stacked_bar`, `pie`, `scatter`, `histogram`,
`heatmap`, `funnel`, and `table` fallback.  It sets explicit category, series, and
point limits; forbids dual axes, imputation, and silent truncation; and maps invalid
data shapes to an honest fallback.

Each selected type has deterministic compatibility checks.  Examples: a line needs an
ordered time field and two points; scatter requires numeric X/Y with common observation
keys; pie/stacked bar requires additive parts; funnel needs explicit stage order; and
bar rejects category counts above policy limits unless a recorded policy transform is
valid.

## Guardrails and failures

Validation occurs before LLM reasoning and again before persistence.  It rejects
unsupported schemas, unpinned/missing refs, artifact hash mismatch, mismatched run,
scope, snapshot, unit or grain, missing evidence, non-validated inputs where policy
forbids them, incompatible chart encodings, PII labels, and causal overclaims.

All errors have stable code/category/retryability fields.  Missing upstream input yields
a structured dependency request.  A chart-incompatible but otherwise meaningful target
falls back to a table with a reason.  Targets execute in isolation: valid targets persist
even when others fail, and the task result becomes `partial`.

## Demo fixtures

A repeatable fixture-generation script reads VHop data and writes checked-in, sanitized
JSON artifacts under the chart agent's demo data directory.  It does not run during a
user chart task.  The fixture set covers DOM target-versus-peer, price/DOM trend,
inventory status composition, DOM distribution, price-per-m2 versus DOM relationship,
sales-funnel stages, and area-by-month heatmap data.  Tasks reference those exact
versions; one intentionally references a missing artifact to demonstrate a dependency
request, and one exceeds the bar category limit to demonstrate table fallback.

## Plugin configuration and invocation

`agents/chart/.env.example` exposes `OPENAI_API_KEY`, `OPENAI_BASE_URL`,
`LLM_MODEL=gpt-4o-mini`, and `LLM_TIMEOUT_S`.  `setup()` reads only that local file,
validates the settings, constructs the service/adapters, and registers `chart`.

Inbound text accepts a concise command with a fixture task id, and optionally the full
`ChartTaskInput` JSON.  The agent selects no external tools.  It emits an answer that
identifies created chart artifacts and embeds their display references so existing
chat/report artifact linking can open the rendered chart.

## Testing and acceptance

Tests are written first and use fake artifact store, policy, renderer, telemetry and
LLM ports.  They cover:

- contract parsing and exact-version resolution;
- deterministic chart selection and each supported compatibility rule;
- preservation of values, scope, unit, grain, limitations, transforms and lineage;
- idempotency and immutable-version behavior;
- missing dependency, scope/unit conflict, fallback, PII and causal-wording failures;
- plugin turn reporting with a scripted LLM and no live OpenAI call;
- chart artifact API response and frontend-compatible Vega-Lite output;
- a fixture smoke test generated from the VHop warehouse.

The whole Python suite and frontend test suite must pass.  A manual smoke run with an
actual `gpt-4o-mini` key is documented but not part of automated tests.

## Implementation choices

The service uses simple dataclasses/Pydantic-free typed dictionaries consistent with the
repository's current style, avoiding a broad dependency addition.  A purpose-built
OpenAI-compatible client can reuse the tested LiteLLM adapter pattern already used by
the data agent.  The core stays framework-free so LLM output can never bypass a
validator.

The existing chart database/API remains backward compatible.  New ChartSpec fields are
added in an isolated path instead of changing semantics of legacy dataset charts.
