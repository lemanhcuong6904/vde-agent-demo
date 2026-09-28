# Chart Agent Demo Spec-Completion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver a fixture-backed Chart Agent demo whose deterministic core produces, persists, validates, and renders semantic `chart-spec/2.0` artifacts according to the master specification.

**Architecture:** Expand the existing plugin around typed task/artifact contracts and a `ResolvedChartContext`, then move selection, dataset construction, semantic output validation, and Vega rendering behind focused modules. Fixture stores remain the upstream boundary; the backend persists canonical semantic specs while the frontend renders only the renderer projection plus audit data.

**Tech Stack:** Python 3.12, dataclasses, pytest, FastAPI/SQLAlchemy/SQLite, React/TypeScript, TanStack Query, Vega-Lite/vega-embed.

**Spec:** `docs/superpowers/specs/2026-09-29-chart-agent-demo-spec-completion-design.md`; source requirements: `docs/Chart_Agent_Master_Specification_Complete_v2.md`.

## Global Constraints

- Do not query `warehouse/` or invoke upstream agents at chart runtime; only exact fixture artifact refs are allowed in this demo.
- Use GPT-4o-mini only for bounded, strict-JSON visual advice; values, scope, lineage, validation, and fallback remain deterministic.
- Never recompute business metrics, silently impute/truncate data, look up `latest`, mutate validated artifacts, or let the renderer contain business logic.
- Keep the current user-facing `chart demo <scenario>` command and preserve `missing_dependency` as an intentional dependency failure.
- Implement all behavior test-first; preserve unrelated worktree changes.
- Do not use subagents; execute natively in this workspace.

## Review Focus

- Cross-grain target-vs-peer input must render only comparison display records while retaining source metrics solely in lineage (Task 3).
- A changed semantic body with a repeated logical chart must create an immutable new revision rather than overwrite the original (Task 6).
- A malformed LLM response, timeout, or request-like text in an artifact label must not alter deterministic output or execute instructions (Task 7).
- Every renderer projection must be derivable from a valid semantic spec, including table fallback and null values (Task 5).
- A target-level incompatibility in a multi-target task must produce a structured fallback/error without hiding independent validated outputs (Task 4).

---

## File structure

- `agents/chart/vdagent_chart/contracts.py`: immutable typed input, normalized artifact, context, semantic output, and error DTOs.
- `agents/chart/vdagent_chart/schema.py`: JSON-compatible parse/serialize and schema boundary checks.
- `agents/chart/vdagent_chart/resolution.py`: exact-ref normalization and `ResolvedChartContext` construction.
- `agents/chart/vdagent_chart/evidence.py`: target dependency matrix and Evidence Map.
- `agents/chart/vdagent_chart/profile.py`: chart data-shape profiling and compatibility facts.
- `agents/chart/vdagent_chart/dataset.py`: explicit chart-ready dataset assembly/transforms.
- `agents/chart/vdagent_chart/selection.py`: candidates, selection metadata, and policy fallback.
- `agents/chart/vdagent_chart/spec_builder.py`: semantic `chart-spec/2.0` construction.
- `agents/chart/vdagent_chart/output_validation.py`: deterministic output pipeline.
- `agents/chart/vdagent_chart/vega.py`: semantic-spec to Vega-Lite adapter only.
- `agents/chart/vdagent_chart/service.py`: staged state machine, target isolation, retries, and telemetry.
- `agents/chart/vdagent_chart/agent.py`, `backend/vdagent_backend/db/artifacts.py`, `frontend/src/...`: persistence, API DTO, and audit inspector integration.

### Task 1: Typed contracts and task/artifact schema boundary

**Files:**
- Modify: `agents/chart/vdagent_chart/contracts.py`, `agents/chart/vdagent_chart/fixtures.py`, `agents/chart/vdagent_chart/errors.py`
- Create: `agents/chart/vdagent_chart/schema.py`, `agents/chart/vdagent_chart/tests/test_schema.py`
- Modify: `agents/chart/vdagent_chart/tests/test_contracts.py`, `agents/chart/vdagent_chart/demo/tasks.json`, `agents/chart/vdagent_chart/demo/artifacts.json`

**Interfaces:**
- Produces `parse_chart_task(raw: Mapping[str, Any]) -> ChartTaskInput` and `normalize_artifact(raw: Mapping[str, Any]) -> NormalizedArtifact`.
- `ChartTaskInput` exposes typed `intent`, expanded `scope`, auth/trace, and pinned refs; later tasks consume only these DTOs.

- [ ] Write failing schema tests for valid expanded fixture tasks and rejection of unsupported mode, unknown schema field, missing snapshot, non-integer version, and malformed time range.
- [ ] Run `pytest agents/chart/vdagent_chart/tests/test_schema.py -q`; verify the parser symbols/tests fail before implementation.
- [ ] Implement immutable DTOs and parser/normalizer; migrate fixtures to include purpose, presentation context, scope filters/population where demo-relevant, and normalized envelope fields.
- [ ] Run the schema and contracts tests; verify they pass.
- [ ] Commit `feat(chart): add typed task and artifact contracts`.

### Task 2: Resolution, dependency rules, and Evidence Map

**Files:**
- Create: `agents/chart/vdagent_chart/resolution.py`, `agents/chart/vdagent_chart/evidence.py`, `agents/chart/vdagent_chart/tests/test_resolution.py`, `agents/chart/vdagent_chart/tests/test_evidence.py`
- Modify: `agents/chart/vdagent_chart/ports.py`, `agents/chart/vdagent_chart/fixture_store.py`, `agents/chart/vdagent_chart/validation.py`, `agents/chart/vdagent_chart/errors.py`

**Interfaces:**
- Consumes `ChartTaskInput`, `NormalizedArtifact`, and `ArtifactStorePort.get_exact` from Task 1.
- Produces `resolve_context(task, store, policy) -> ResolvedChartContext` and `build_evidence_map(context) -> Mapping[str, EvidenceBinding]`.

- [ ] Write failing tests for exact hash/version resolution, required metric/evidence/comparison rules by target purpose, and structured dependency requests for absent artifacts.
- [ ] Run focused resolution/evidence tests; verify they fail for missing context/evidence-map behavior.
- [ ] Implement only-exact resolver, common cross-artifact checks (run, status, scope, snapshot, time, filters, population, unit, grain), and target bindings. Preserve the comparison-backed grain exception only when render records come from the validated comparison artifact.
- [ ] Run focused tests and full chart tests; verify they pass.
- [ ] Commit `feat(chart): resolve typed context and evidence map`.

### Task 3: Data profiles and chart-ready dataset contracts

**Files:**
- Create: `agents/chart/vdagent_chart/profile.py`, `agents/chart/vdagent_chart/tests/test_profile.py`
- Modify: `agents/chart/vdagent_chart/dataset.py`, `agents/chart/vdagent_chart/tests/test_dataset.py`, `agents/chart/vdagent_chart/demo/artifacts.json`

**Interfaces:**
- Consumes `EvidenceBinding` and `NormalizedArtifact` from Task 2.
- Produces `profile_target(binding) -> DataProfile` and `assemble_dataset(binding, decision) -> ChartDataset` with schema, records/data-ref mode, hash, transforms, null handling, and omitted count.

- [ ] Write failing tests for target-vs-peer comparison display records, null preservation, explicit sorting/renaming, rejected silent top-N, histogram bins, and shape facts for time series/scatter/funnel/heatmap.
- [ ] Run profile/dataset tests; verify new shape and transform cases fail.
- [ ] Implement typed profile and explicit transform records; retain direct upstream values, prohibit business filtering/imputation, and require chart-ready bins/statistics where relevant.
- [ ] Run focused tests and fixture generation tests; verify they pass.
- [ ] Commit `feat(chart): add chart-ready datasets and data profiles`.

### Task 4: Compatibility, candidates, selection, and target fallback

**Files:**
- Modify: `agents/chart/vdagent_chart/policy.py`, `agents/chart/vdagent_chart/selection.py`, `agents/chart/vdagent_chart/service.py`, `agents/chart/vdagent_chart/tests/test_selection.py`, `agents/chart/vdagent_chart/tests/test_service.py`
- Create: `agents/chart/vdagent_chart/compatibility.py`, `agents/chart/vdagent_chart/tests/test_compatibility.py`

**Interfaces:**
- Consumes `DataProfile`, policy, and visual target from Tasks 1–3.
- Produces `select_chart(...) -> SelectionDecision` and `compatibility_errors(chart_type, profile, policy) -> tuple[ChartError, ...]`.

- [ ] Write failing tests covering required encodings/invariants for the supported chart catalog and explicit table fallback for incompatible shapes.
- [ ] Run selection/compatibility tests; verify candidate metadata and fallbacks are absent/failing.
- [ ] Implement policy-versioned candidate matrix, preference result, reason/fallback metadata, and per-target service isolation. Do not select a chart type merely because it is allowlisted.
- [ ] Run focused tests plus all standard demo scenarios; verify all standard scenarios remain successful and the intentional missing dependency remains failed.
- [ ] Commit `feat(chart): enforce chart compatibility and fallback`.

### Task 5: Semantic ChartSpec, output validation, and renderer adapter

**Files:**
- Create: `agents/chart/vdagent_chart/spec_builder.py`, `agents/chart/vdagent_chart/output_validation.py`, `agents/chart/vdagent_chart/tests/test_spec_builder.py`, `agents/chart/vdagent_chart/tests/test_output_validation.py`
- Modify: `agents/chart/vdagent_chart/contracts.py`, `agents/chart/vdagent_chart/presentation.py`, `agents/chart/vdagent_chart/vega.py`, `agents/chart/vdagent_chart/tests/test_vega.py`

**Interfaces:**
- Consumes `ResolvedChartContext`, `EvidenceBinding`, `ChartDataset`, and `SelectionDecision`.
- Produces `build_chart_spec(...) -> SemanticChartSpec` and `render_vega(spec: SemanticChartSpec) -> dict[str, Any]`.

- [ ] Write failing tests asserting `chart-spec/2.0` includes scope, target/purpose/question, typed dataset, encoding, presentation, selection, limitations, exact input refs, governance versions, and output validation checks.
- [ ] Run semantic/output/renderer tests; verify the current Vega-only output cannot satisfy them.
- [ ] Implement semantic builder and output validation pipeline (schema, values, scope, unit/grain, evidence/lineage, causal/PII text, chart invariant, renderer compatibility). Make `vega.py` a pure adapter.
- [ ] Run focused tests and frontend renderer contract tests; verify semantic and Vega output stay consistent.
- [ ] Commit `feat(chart): build validated semantic chart specs`.

### Task 6: Immutable revisions, runtime state, and idempotency

**Files:**
- Modify: `agents/chart/vdagent_chart/service.py`, `agents/chart/vdagent_chart/agent.py`, `agents/chart/vdagent_chart/ports.py`, `backend/vdagent_backend/db/schema.sql`, `backend/vdagent_backend/db/database.py`, `backend/vdagent_backend/db/artifacts.py`, `backend/tests/test_artifacts.py`
- Create: `agents/chart/vdagent_chart/runtime.py`, `agents/chart/vdagent_chart/tests/test_runtime.py`

**Interfaces:**
- Consumes semantic specs from Task 5.
- Produces `ChartRunState`, canonical idempotency material, and `save_chart_spec(semantic_spec, render_spec, ...) -> PersistedChartSpec`.

- [ ] Write failing tests for identical retry reuse, conflicting idempotency content rejection, changed semantic content revision creation, and a multi-target partial result that persists independent successes.
- [ ] Run runtime/artifact tests; verify existing persistence is version-one-only.
- [ ] Implement state transitions, canonical input hash, per-key in-process single-flight, immutable revision storage, structured result/error persistence, and a retry policy limited to transient renderer/LLM failures.
- [ ] Run focused tests plus backend E2E persistence tests; verify pass.
- [ ] Commit `feat(chart): add immutable revisions and runtime state`.

### Task 7: Safety boundary and structured observability

**Files:**
- Modify: `agents/chart/vdagent_chart/llm.py`, `agents/chart/vdagent_chart/telemetry.py`, `agents/chart/vdagent_chart/presentation.py`, `agents/chart/vdagent_chart/service.py`, `agents/chart/vdagent_chart/tests/test_async_runtime.py`, `agents/chart/vdagent_chart/tests/test_presentation.py`
- Create: `agents/chart/vdagent_chart/safety.py`, `agents/chart/vdagent_chart/tests/test_safety.py`

**Interfaces:**
- Produces `sanitize_presentation_text(text) -> str`, `validate_safe_text(...)`, and structured `ChartEvent` envelopes with trace/version tags.

- [ ] Write failing tests for PII-like labels/tooltips, instruction-like artifact text, malformed LLM JSON, timeout, and event fields that must not contain prompt/data/API-key values.
- [ ] Run safety/runtime tests; verify missing guards fail.
- [ ] Implement deterministic sanitization/validation, minimized LLM request/response schema, bounded failure fallback, safe event names, trace IDs, and governance version tags.
- [ ] Run focused and complete backend/chart suites; verify pass.
- [ ] Commit `feat(chart): add safety boundary and observability`.

### Task 8: Inspector audit UI, scenario E2E, and demo ship gate

**Files:**
- Modify: `frontend/src/api/types.ts`, `frontend/src/api/client.ts`, `frontend/src/api/queries.ts`, `frontend/src/components/inspector/ChartView.tsx`, `frontend/src/components/inspector/ChartView.test.ts`, `backend/vdagent_backend/api/rest.py`, `backend/tests/test_api.py`, `agents/chart/README.md`
- Create: `frontend/src/components/inspector/ChartAudit.tsx`, `frontend/src/components/inspector/ChartAudit.test.ts`, `agents/chart/vdagent_chart/tests/test_demo_e2e.py`

**Interfaces:**
- Consumes `PersistedChartSpec` from Task 6 and its semantic/audit fields.
- Produces an inspector with rendered chart plus safe scope, lineage, validation, selection/fallback, and limitation views.

- [ ] Write failing frontend/API tests for reading all semantic/audit fields and E2E tests for each successful scenario plus the intentional dependency response.
- [ ] Run focused frontend and backend tests; verify audit data is not exposed/rendered yet.
- [ ] Implement versioned DTO/API response, audit panel, scenario E2E fixture runner, and one documented Windows PowerShell run path without Make/uv requirements.
- [ ] Run `pytest backend/tests agents/chart/vdagent_chart/tests -q`, `npm.cmd test`, and `npm.cmd run build`; verify all pass.
- [ ] Commit `feat(chart): ship auditable chart demo gate`.

## Plan self-review

- Contracts, dependencies, workflow, guardrails, output, storage, renderer, tests, observability, and UI requirements map to Tasks 1–8.
- Production-only external Orchestrator/Artifact Store/Report Agent integrations remain explicit non-goals; ports and fixture-backed contract tests cover their demo boundary.
- Each task consumes only prior named interfaces and ends with a complete test gate.
- The Review Focus cases are assigned to Tasks 3–7 and will be added as tests there.
