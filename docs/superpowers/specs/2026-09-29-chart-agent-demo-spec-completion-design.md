# Chart Agent Demo Spec-Completion Design

## Goal

Bring the fixture-backed VDAgent Chart Agent demo into conformance with the
deterministic-core requirements of `docs/Chart_Agent_Master_Specification_Complete_v2.md`.
The result must accept a normalized task and pinned upstream artifacts, produce
an immutable semantic `chart-spec/2.0`, render it in the existing UI, and be
demonstrably safe without building the Orchestrator or other upstream agents.

## Scope and boundaries

This is a complete Chart Agent *demo core*, not a production multi-agent
deployment.

- Fixture artifacts remain the upstream Artifact Store implementation. They
  model exact, immutable outputs from Data, Compare, and Insight.
- `chart demo <scenario>` remains the user-facing entry point. A programmatic
  task API uses the same execution path for tests and future integration.
- The LLM remains GPT-4o-mini, optional and bounded to visual-language advice.
  It never reads raw artifacts, determines values, changes lineage, or bypasses
  deterministic validation/selection.
- No Orchestrator, upstream agents, external Artifact Store, external Policy
  Store, reporting workflow, dashboard/alert backend, or authentication-system
  redesign is included. Their required contracts are represented by ports and
  fixtures.

## Architecture

The execution pipeline has five deterministic stages:

1. **Input boundary.** Parse `ChartTaskInput` v2 into typed immutable DTOs.
   Validate schema/version, task identity, mode, intent, scope, pinned refs,
   idempotency, and optional auth/trace metadata before any reasoning.
2. **Resolution and context.** Resolve only exact artifact refs through
   `ArtifactStorePort`; normalize metric, evidence, comparison, and insight
   envelopes; construct `ResolvedChartContext` with a validation summary and
   an Evidence Map per visual target.
3. **Decision and dataset.** Determine compatible candidates from the pinned
   policy and the target's data profile. Assemble a chart-ready dataset using
   only validated values and explicit presentation transforms. Apply a recorded
   fallback or structured target error when compatibility is insufficient.
4. **Semantic output.** Build a `ChartSpecArtifact` with a semantic chart body
   (dataset, encoding, presentation, selection, scope, limitations, lineage,
   and validation). Validate this output before converting it to Vega-Lite.
5. **Persistence and rendering.** Persist the canonical semantic artifact with
   content-addressed idempotency. The renderer adapter consumes only this
   semantic spec; the frontend shows the chart plus audit metadata.

The existing `ChartAgentService` becomes the orchestration point for these
stages. Individual modules stay focused: contracts/schema, resolver/context,
evidence mapping, data profiling, selection, dataset assembly, semantic-spec
building, output validation, renderer adaptation, and persistence adapter.

## Contracts

### Chart task

`ChartTaskInput` supports the specification's fields while keeping fixture
compatibility:

- identity: schema version, run ID, task ID, mode, idempotency key;
- scope: project/area IDs, snapshot, time range, filters, population reference,
  and data grain;
- intent: purpose, business question, one-or-more visual targets, and
  presentation context;
- exact artifact refs: ID, integer version, expected content hash, required;
- pinned policy, requested-by/auth context, and trace context.

The parser rejects unknown or incompatible task schema data. Existing demo
JSON is migrated to the expanded shape without losing the simple command UX.

### Normalized artifacts and resolved context

Artifact normalization produces typed envelopes with common identity, status,
scope, quality/limitations, content hash, and source lineage fields.
Specialized payloads retain the minimum data required by metrics, evidence,
comparisons, and insights. `ResolvedChartContext` is the only object available
to later stages; raw fixture dictionaries do not cross this boundary.

An Evidence Map links each target to its metric, evidence, insight, and/or
comparison refs. Purpose/visual-question dependency rules are explicit. A
comparison-backed target-vs-peer chart may use comparison display records while
source metrics stay in lineage; it never joins incompatible observations.

### Semantic ChartSpec

The persisted chart is `chart-spec/2.0`, not merely a Vega-Lite object. It
contains identity/version/status, task and target IDs, purpose/question, scope,
typed dataset, encoding, presentation, selection decision, limitations,
exact-input lineage, governance versions, and validation summary. Vega-Lite is
derived by a `RendererPort` adapter and is stored/read as render output only.

The persistence model permits immutable revisions: same logical chart plus
identical canonical content returns the original revision; changed semantic
content receives a new version/revision identity and never overwrites history.

## Validation, selection, and fallback

Input validation checks exact dependency resolution, status, run/snapshot,
scope, time range, filters/population, unit, grain, and purpose-specific
completeness. It returns typed `ChartError` / `DependencyRequest` values rather
than exposing exception strings to users.

Selection uses a data profile and policy-based compatibility matrix. It records
the candidate set, preferred-chart result, selected type, and reason. Supported
demo renderers cover: KPI, line/area, bar/grouped/stacked bar, pie, histogram,
box plot, scatter, heatmap, map fallback, funnel, waterfall, treemap, bullet,
and table fallback. A chart type is selected only when its required encoding
and data-shape invariants hold.

Presentation transforms are limited to declared select/sort/rename/reshape,
policy-approved binning, and explicit truncation. The dataset retains nulls,
records `omitted_count` and `null_handling`, and never recalculates a business
metric. Output validation verifies schema, values, scope, unit/grain, chart
invariants, evidence/lineage, semantic wording, PII-safe fields, and renderer
compatibility.

Each visual target is isolated after common input readiness succeeds. A target
with an unsupported shape gets an explicit table/no-chart fallback and reason;
independent targets may still persist as validated outputs.

## LLM and safety

GPT-4o-mini receives only a minimized visual-question/policy candidate request.
It returns strict JSON, with timeout, response validation, no automatic retry
unless policy says so, and telemetry that omits prompts, records, and API keys.
Its suggestion is advisory: compatibility validation and deterministic policy
remain authoritative.

Labels, titles, tooltips, annotations, and narrative hints undergo causal,
HTML, PII, and prompt-injection boundary checks. Artifact text is data, never
instructions. The frontend receives only sanitized renderable fields.

## Observability and UI

The demo emits safe structured events for request receipt, dependency
resolution, validation, candidate selection, fallback, persistence, renderer
validation, and completion. Each event carries task/target, policy, validator,
and renderer contract versions where available, plus a trace ID if supplied.

The inspector renders Vega-Lite through the renderer output and adds collapsible
audit information: semantic chart type, input refs/hashes, validation checks,
selection/fallback reason, scope/snapshot, limitations, and safe error details.

## Testing and acceptance

Tests are layered:

- unit tests for parsers, invariants, data profiles, transforms, selection,
  semantic/presentation guards, and renderer adapters;
- contract tests for task/artifact/chart-spec JSON schemas and immutable
  persistence;
- golden fixtures for every demo chart and target-vs-peer comparison;
- negative/property tests for wrong versions/hashes, scope/unit/grain/time
  conflicts, missing evidence/comparison, malformed LLM output, PII, causal
  wording, duplicate observations, and unsupported data shapes;
- backend/frontend integration and E2E checks that persist, retrieve, and
  render every successful scenario.

The demo acceptance gate is: all standard scenarios produce a valid immutable
semantic ChartSpec and render it; `missing_dependency` produces only the
specified dependency request; every persisted output passes output validation;
no failure leaks an exception trace or causes another independent target to
fail.

## Delivery sequence

1. Contracts, schemas, fixture migration, and resolver/context.
2. Evidence map plus complete cross-artifact validation and error contracts.
3. Data profiling, dataset transforms, compatibility/selection, and fallbacks.
4. Semantic ChartSpec builder, output validator, and renderer adapter.
5. Persistence revisions, runtime state/idempotency, and safe observability.
6. Inspector audit UX, full test matrix, and CI-style demo ship gate.

## Non-goals

This work does not compute business metrics, select peer groups, create
insights, query the warehouse at chart runtime, use a latest artifact lookup,
or make the LLM a source of factual data.
