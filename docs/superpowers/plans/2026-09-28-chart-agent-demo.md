# Chart Agent Demo Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a standalone VDAgent Chart Agent demo that turns pinned VHop fixture artifacts into validated, immutable, frontend-renderable chart artifacts using GPT-4o-mini only for bounded visual-language reasoning.

**Architecture:** A new `agents/chart` plugin owns a framework-free deterministic service and ports.  Demo upstream JSON artifacts and a versioned policy are read exactly by id/version; the service validates, selects, assembles, hashes and persists ChartSpecs.  The Backend stores ChartSpec artifacts separately and serves their embedded Vega-Lite render spec to the existing frontend.

**Tech Stack:** Python 3.12, asyncio, LiteLLM/OpenAI-compatible GPT-4o-mini, FastAPI, SQLAlchemy/SQLite, pytest, React/TypeScript, Vega-Lite.

**Spec:** `docs/superpowers/specs/2026-09-28-chart-agent-demo-design.md`

## Global Constraints

- Do not build an Orchestrator or modify existing upstream agents; use generated, checked-in VHop fixture artifacts.
- The chart plugin must never query the warehouse, call Data/Insight/Compare, recalculate a business metric, or resolve `latest`.
- Deterministic code is authoritative for exact refs, scope, units, grain, compatibility, assembly, hashes, validation, fallback and persistence; GPT-4o-mini is bounded to presentation/selection suggestions.
- Read only task-authorized artifact versions and preserve limitations and exact lineage.
- Prohibit dual axes, imputation and silent truncation; unsafe data must fail or return an explicit table/no-chart fallback.
- Persist only validated/allowed partial ChartSpecs immutably; idempotent equivalent input returns the existing artifact.
- The existing legacy dataset-chart API and UI behavior must remain backward compatible.
- Tests must never call a live OpenAI endpoint; inject a scripted LLM.

## Review Focus

- Artifact id/version looks valid but hash differs: reject it before any LLM call (Task 2 test).
- A partial input carries a severe limitation: policy-controlled partial status and propagated limitation must reach output (Task 3 test).
- An LLM suggests an unsupported type or causal title: deterministic policy/text guards must override/reject it (Task 4 test).
- Two target results share an idempotency key: persist one immutable artifact, never a divergent revision (Task 5 test).
- The frontend receives a chart-spec artifact without `dataset_id`: it should render the embedded Vega-Lite spec and show artifact lineage, while legacy charts still render (Task 6 test).

---

## File structure

- `agents/chart/`: new plugin package, settings, LLM adapter, deterministic domain service, fixture adapters, policy/data, prompts, tests and README.
- `data/generate_chart_demo_fixtures.py`: reproducibly builds static upstream artifacts/tasks from `warehouse/vhop` exports.
- `backend/vdagent_backend/db/schema.sql`, `db/artifacts.py`, `api/rest.py`: isolated immutable ChartSpec storage and retrieval.
- `frontend/src/api/types.ts`, `components/inspector/ChartView.tsx`, `ui/artifacts.ts`: support chart-artifact DTOs, links and presentation without altering old chart records.
- Root workspace/config/Docker files: install and load the plugin; fixture docs explain manual GPT-4o-mini setup.

### Task 1: Scaffold plugin contracts, settings, and policy

**Files:**
- Create: `agents/chart/pyproject.toml`, `agents/chart/.env.example`, `agents/chart/README.md`
- Create: `agents/chart/vdagent_chart/{__init__.py,contracts.py,settings.py,policy.py,errors.py}`
- Create: `agents/chart/vdagent_chart/demo/chart-policy-demo-1.0.json`
- Test: `agents/chart/vdagent_chart/tests/test_settings.py`, `agents/chart/vdagent_chart/tests/test_policy.py`
- Modify: `pyproject.toml`

**Interfaces:**
- Produces: immutable `ArtifactRef`, `ChartTaskInput`, `VisualTarget`, `ChartSpecArtifact`, `ChartTaskResult`, `ChartError`, `ChartPolicy`; `load_settings(env)` and `load_policy(version)`.

- [ ] **Step 1: Write failing settings/policy tests** for required LLM settings, default `gpt-4o-mini`, requested `chart-policy/demo-1.0`, allowed types, and forbidden global transforms.
- [ ] **Step 2: Run** `uv run pytest agents/chart/vdagent_chart/tests/test_settings.py agents/chart/vdagent_chart/tests/test_policy.py -v` **and verify expected import/module failure.**
- [ ] **Step 3: Implement contracts, configuration validation, and immutable JSON policy** with exact schema/policy versions named in the spec.
- [ ] **Step 4: Re-run the focused tests** and verify PASS.
- [ ] **Step 5: Commit** `feat(chart): add contracts and demo policy`.

### Task 2: Build exact fixture artifact resolution and fixture generator

**Files:**
- Create: `agents/chart/vdagent_chart/{ports.py,fixture_store.py,fixtures.py}`
- Create: `agents/chart/vdagent_chart/demo/{artifacts.json,tasks.json}`
- Create: `data/generate_chart_demo_fixtures.py`
- Test: `agents/chart/vdagent_chart/tests/test_fixture_store.py`, `agents/chart/vdagent_chart/tests/test_fixture_generation.py`

**Interfaces:**
- Consumes: Task 1 `ArtifactRef`, `ChartTaskInput`, `ChartError`.
- Produces: `ArtifactStorePort.get_exact(ref)`, `FixtureArtifactStore`, `load_demo_task(name)`, deterministic fixture generator.

- [ ] **Step 1: Write failing tests** that resolve a pinned artifact, reject unpinned/missing version and hash mismatch, and assert generated fixtures include the required VHop scenarios.
- [ ] **Step 2: Run** `uv run pytest agents/chart/vdagent_chart/tests/test_fixture_store.py agents/chart/vdagent_chart/tests/test_fixture_generation.py -v` **and verify expected failure.**
- [ ] **Step 3: Implement the store and generator** using only `warehouse/vhop` source files at generation time; include metric/evidence/comparison/insight lineage and one deliberate missing dependency task.
- [ ] **Step 4: Re-run the focused tests** and verify PASS.
- [ ] **Step 5: Commit** `feat(chart): add pinned demo artifacts`.

### Task 3: Implement deterministic validation and dataset assembly

**Files:**
- Create: `agents/chart/vdagent_chart/{validation.py,dataset.py}`
- Test: `agents/chart/vdagent_chart/tests/test_validation.py`, `agents/chart/vdagent_chart/tests/test_dataset.py`

**Interfaces:**
- Consumes: Task 1 contracts/policy and Task 2 resolved artifact envelopes.
- Produces: `validate_input(task, artifacts, policy)`, `assemble_dataset(target, artifacts, decision)`, dataset hashes/transforms and typed validation summaries.

- [ ] **Step 1: Write failing tests** for run/scope/snapshot/unit/grain mismatch, incomplete evidence, limitation propagation from a permitted partial input, stable dataset hash, and no silent category drop/null-to-zero conversion.
- [ ] **Step 2: Run** `uv run pytest agents/chart/vdagent_chart/tests/test_validation.py agents/chart/vdagent_chart/tests/test_dataset.py -v` **and verify expected failure.**
- [ ] **Step 3: Implement validation and allowed presentation-only transforms** (`select`, `rename`, deterministic sort, reshape, display format, policy-gated top-N) with audit metadata.
- [ ] **Step 4: Re-run the focused tests** and verify PASS.
- [ ] **Step 5: Commit** `feat(chart): validate artifacts and assemble datasets`.

### Task 4: Implement bounded LLM reasoning, selection, and ChartSpec validation

**Files:**
- Create: `agents/chart/vdagent_chart/{llm.py,selection.py,presentation.py,vega.py}`
- Create: `agents/chart/vdagent_chart/prompts/system.md`
- Test: `agents/chart/vdagent_chart/tests/test_selection.py`, `agents/chart/vdagent_chart/tests/test_presentation.py`, `agents/chart/vdagent_chart/tests/test_vega.py`

**Interfaces:**
- Consumes: Task 3 validation/dataset result and `LLMClient.suggest_visual(...)`.
- Produces: `SelectionDecision`, sanitized `PresentationSpec`, `build_vega_spec(chart_spec)`, `validate_chart_spec(chart_spec, policy)`.

- [ ] **Step 1: Write failing tests** for deterministic selection of line/bar/pie/scatter/histogram/heatmap/funnel, table fallback for too many categories, policy override of an invalid LLM preference, causal wording rejection, and valid Vega-Lite output.
- [ ] **Step 2: Run** `uv run pytest agents/chart/vdagent_chart/tests/test_selection.py agents/chart/vdagent_chart/tests/test_presentation.py agents/chart/vdagent_chart/tests/test_vega.py -v` **and verify expected failure.**
- [ ] **Step 3: Implement the injected GPT-4o-mini client and constrained response model, then policy-first selection, text sanitization, type-specific checks, and declarative Vega-Lite translation.**
- [ ] **Step 4: Re-run the focused tests** and verify PASS.
- [ ] **Step 5: Commit** `feat(chart): select and validate chart specs`.

### Task 5: Compose the service, immutable persistence, and agent turn

**Files:**
- Create: `agents/chart/vdagent_chart/{service.py,agent.py}`
- Create: `agents/chart/vdagent_chart/tests/{test_service.py,test_agent.py}`
- Modify: `agents/chart/vdagent_chart/__init__.py`
- Modify: `backend/vdagent_backend/db/{schema.sql,artifacts.py}`
- Modify: `backend/vdagent_backend/api/rest.py`
- Test: `backend/tests/test_chart_artifacts.py`

**Interfaces:**
- Consumes: Tasks 1–4 services/ports.
- Produces: `ChartAgentService.execute(task) -> ChartTaskResult`, `insert_chart_artifact`, `get_chart_artifact`, `GET /api/chart-artifacts/{id}` and registered `chart` Agent.

- [ ] **Step 1: Write failing tests** for success, partial target isolation, structured dependency request, idempotent reuse, immutable conflict, agent `emit_assistant` final answer, and user-scoped API retrieval.
- [ ] **Step 2: Run** `uv run pytest agents/chart/vdagent_chart/tests/test_service.py agents/chart/vdagent_chart/tests/test_agent.py backend/tests/test_chart_artifacts.py -v` **and verify expected failure.**
- [ ] **Step 3: Implement the service orchestration, atomic immutable SQLite persistence, REST endpoint, and plugin adapter**; all task parsing uses supplied fixture task ids/full JSON and makes no MCP/peer/warehouse call.
- [ ] **Step 4: Re-run the focused tests** and verify PASS.
- [ ] **Step 5: Commit** `feat(chart): persist chart artifacts through chart agent`.

### Task 6: Integrate workspace, UI, and demo documentation

**Files:**
- Modify: `pyproject.toml`, `backend/config.yaml`, `backend/config.compose.yaml`, `Dockerfile.python`, `docker-compose.yml`, `README.md`
- Modify: `frontend/src/{api/types.ts,api/client.ts,api/queries.ts,api/keys.ts,ui/artifacts.ts,components/inspector/ChartView.tsx}`
- Test: `frontend/src/ui/artifacts.test.ts`, `frontend/src/components/inspector/ChartView.test.tsx`

**Interfaces:**
- Consumes: Task 5 chart-artifact API DTO: `{id, title, spec, chart_spec, lineage}`.
- Produces: `chart-artifact` detection/linking and renderer support; documented `chart demo <task-id>` invocation.

- [ ] **Step 1: Write failing frontend tests** for identifying a chart-artifact id, rendering an embedded spec without `dataset_id`, showing lineage, and retaining legacy `ch_…` rendering.
- [ ] **Step 2: Run** `cd frontend && npm test -- --run src/ui/artifacts.test.ts src/components/inspector/ChartView.test.tsx` **and verify expected failure.**
- [ ] **Step 3: Implement the additive DTO/client/query/view changes and register the chart plugin in Python/Docker workspace configuration; document `.env` setup, fixture generation, backend/UI launch and eight demo commands.**
- [ ] **Step 4: Re-run the focused frontend tests** and verify PASS.
- [ ] **Step 5: Commit** `feat(chart): expose chart agent demo in VDAgent UI`.

### Task 7: Run end-to-end regression and fixture smoke checks

**Files:**
- Modify: `agents/chart/README.md`
- Test: `agents/chart/vdagent_chart/tests/test_demo_e2e.py`

**Interfaces:**
- Consumes: all earlier task interfaces.
- Produces: a test-proven demo matrix and exact verification instructions.

- [ ] **Step 1: Write failing E2E tests** that run supplied task fixtures through the chart service and assert chart type, output status, fallback/dependency code, lineage and Vega-Lite render payload.
- [ ] **Step 2: Run** `uv run pytest agents/chart/vdagent_chart/tests/test_demo_e2e.py -v` **and verify expected failure.**
- [ ] **Step 3: Implement only any missing composition/wiring needed for the E2E cases; update README with observed outputs.**
- [ ] **Step 4: Run** `uv run pytest` **and** `cd frontend && npm test -- --run`; verify both suites pass and record the result.
- [ ] **Step 5: Commit** `test(chart): verify chart agent demo scenarios`.

## Self-review

Coverage: Tasks 1–7 cover the approved plugin, fixture, deterministic/LLM boundary, persistence, UI, documentation and test requirements.  The plan deliberately limits the demo to the policy’s eleven supported/fallback types rather than falsely claiming all optional master-spec types.  All later interfaces are named in earlier task interface blocks.  The review-focus cases are assigned to Tasks 2–6.  No production implementation step lacks a preceding failing-test and expected command.
