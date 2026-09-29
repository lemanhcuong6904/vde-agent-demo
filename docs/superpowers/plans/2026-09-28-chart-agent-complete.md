# Complete Chart Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver a complete, testable Chart Agent for VDAgent that fulfills the master specification while using fixture upstream artifacts instead of an Orchestrator and live upstream agents.

**Architecture:** Preserve the existing deterministic core and extend it behind explicit ports: immutable artifact storage, policy/version loading, renderer compatibility and telemetry. The plugin resolves only exact fixture refs, GPT-4o-mini returns bounded semantic suggestions, validators own final selection/output status, and the API/UI consume immutable ChartSpec artifacts.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy/SQLite, LiteLLM/OpenAI GPT-4o-mini, pytest, React/TypeScript, Vega-Lite.

**Spec:** `docs/Chart_Agent_Master_Specification_Complete_v2.md`

## Global Constraints

- Never query warehouse data, calculate business metrics, choose peer groups, or call upstream agents at Chart Agent runtime.
- Resolve only task-authorized `artifact_id + version + hash`; never use latest.
- Keep values, scope, snapshot, filter, unit, grain, limitations and lineage deterministic and auditable.
- LLM output is optional and may only suggest wording/candidates from the allowlist; deterministic policy and validators decide the result.
- Persist immutable ChartSpec artifacts only after validation; identical idempotency input reuses the existing semantic result.
- Renderer receives declarative data/encoding only and must not contain business logic.
- Do not silently truncate, impute, rebin, alter population, or strengthen a claim into causation.

## Review Focus

- Exact reference hash mismatch must reject before reasoning.
- Mixed units/grains, partial input and missing evidence must not produce a validated chart.
- User/LLM chart preference must not bypass compatibility or fallback rules.
- Renderer/API must preserve nulls, order, lineage and limitations from the immutable ChartSpec.
- Retry with one idempotency key must not create a divergent chart version.

---

### Task 1: Reconcile existing core contracts with complete master contract

**Files:** `agents/chart/vdagent_chart/{contracts.py,errors.py,policy.py,validation.py,dataset.py}`, tests under `agents/chart/vdagent_chart/tests/`.

- [ ] Write failing tests for full task/spec/result envelopes, target isolation, typed error object, partial status and all mandatory lineage fields.
- [ ] Run focused pytest and confirm RED.
- [ ] Implement explicit DTOs, validation summaries, dependency requests, status aggregation and limitation propagation.
- [ ] Run focused pytest and confirm GREEN; commit.

### Task 2: Complete deterministic selection, compatibility and fallback matrix

**Files:** `selection.py`, `dataset.py`, `vega.py`, policy JSON, golden/negative tests.

- [ ] Write failing parameterized tests for KPI, line, area, bar/grouped/stacked, pie, scatter, histogram, box plot, heatmap, map, funnel, waterfall, treemap, bullet and table fallback.
- [ ] Run focused pytest and confirm RED.
- [ ] Implement chart-type compatibility, policy limits, reason codes, presentation transforms and honest fallback matrix.
- [ ] Run focused pytest and confirm GREEN; commit.

### Task 3: Immutable chart artifact store and idempotency

**Files:** `backend/vdagent_backend/db/{schema.sql,artifacts.py}`, chart store adapter, backend tests.

- [ ] Write failing tests for user-scoped exact retrieval, immutable conflict, content/dataset hashes, versioning and idempotency reuse.
- [ ] Run focused pytest and confirm RED.
- [ ] Add `chart_artifacts` SQLite table, repository functions and Chart Agent store adapter.
- [ ] Run focused pytest and confirm GREEN; commit.

### Task 4: Service workflow, plugin adapter and structured telemetry

**Files:** `agents/chart/vdagent_chart/{service.py,agent.py,__init__.py,telemetry.py,llm.py}`, plugin tests.

- [ ] Write failing tests for 12-stage flow, missing dependency, semantic fallback, multi-target partial result, bounded LLM failure and emitted event names.
- [ ] Run focused pytest and confirm RED.
- [ ] Implement policy/store/renderer/telemetry ports, async plugin turn, GPT-4o-mini client injection and structured events without PII.
- [ ] Run focused pytest and confirm GREEN; commit.

### Task 5: REST API and frontend ChartSpec renderer

**Files:** backend REST/artifacts tests; `frontend/src/api/{types,client,queries,keys}.ts`; `ChartView.tsx`, artifact utilities/tests.

- [ ] Write failing backend/frontend tests for chart-artifact retrieval, lineage/limitations display, embedded Vega-Lite rendering and legacy chart compatibility.
- [ ] Run backend and frontend focused suites and confirm RED.
- [ ] Implement additive API/DTO/query/view paths and renderer compatibility check.
- [ ] Run focused suites and confirm GREEN; commit.

### Task 6: Fixture generator, complete demo matrix and documentation

**Files:** fixture generator/data/tasks, `agents/chart/README.md`, root README, tests.

- [ ] Write failing tests proving every supported scenario originates from VHop fixture data, including dependency/error/fallback scenarios.
- [ ] Run focused pytest and confirm RED.
- [ ] Generate sanitized exact-version fixtures, document `.env` with `gpt-4o-mini`, startup, task commands, lineage and limitations.
- [ ] Run focused pytest and confirm GREEN; commit.

### Task 7: Evaluation and release gate

**Files:** golden/property/E2E tests and CI documentation.

- [ ] Add golden, negative, property and API/UI E2E tests for spec invariants and contract compatibility.
- [ ] Run full Python suite, frontend tests and frontend build; inspect output.
- [ ] Fix only validated failures using RED-GREEN; record any deferred minor issues.
- [ ] Commit verified release gate evidence.

## Self-review

Tasks 1–7 cover all master-spec areas: contracts, policy/dependencies, workflow, guardrails, errors/fallback, evaluation and observability/integration. Each production task begins with a failing test and ends with focused verification; Task 7 provides the whole-system gate.
