"""Persistence contract for immutable ChartSpec artifacts."""

from __future__ import annotations

import sqlite3

import pytest

from vdagent_backend.db import artifacts
from vdagent_backend.db.database import apply_schema

from conftest import ALICE, BOB


def test_schema_upgrades_legacy_chart_specs_with_audit_metadata(tmp_path) -> None:
    path = tmp_path / "legacy.db"
    with sqlite3.connect(path) as conn:
        conn.execute(
            "CREATE TABLE chart_specs (id TEXT PRIMARY KEY, user_id TEXT NOT NULL, invocation_id TEXT NOT NULL,"
            " idempotency_key TEXT NOT NULL, version INTEGER NOT NULL, status TEXT NOT NULL, title TEXT NOT NULL,"
            " chart_spec_json TEXT NOT NULL, dataset_hash TEXT NOT NULL, content_hash TEXT NOT NULL, created_at TEXT NOT NULL)"
        )

    apply_schema(str(path))

    with sqlite3.connect(path) as conn:
        columns = {row[1] for row in conn.execute("PRAGMA table_info(chart_specs)")}
    assert {"lineage_json", "validation_json", "limitations_json"} <= columns


def test_migrated_chart_specs_keep_created_at_default(tmp_path) -> None:
    path = tmp_path / "version_one.db"
    with sqlite3.connect(path) as conn:
        conn.execute(
            "CREATE TABLE chart_specs (id TEXT PRIMARY KEY, user_id TEXT NOT NULL, invocation_id TEXT NOT NULL,"
            " idempotency_key TEXT NOT NULL, version INTEGER NOT NULL CHECK (version = 1),"
            " status TEXT NOT NULL, title TEXT NOT NULL, chart_spec_json TEXT NOT NULL, dataset_hash TEXT NOT NULL,"
            " lineage_json TEXT NOT NULL DEFAULT '{}', validation_json TEXT NOT NULL DEFAULT '{}',"
            " limitations_json TEXT NOT NULL DEFAULT '[]', content_hash TEXT NOT NULL,"
            " created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')))"
        )

    apply_schema(str(path))

    with sqlite3.connect(path) as conn:
        created_at = next(row for row in conn.execute("PRAGMA table_info(chart_specs)") if row[1] == "created_at")
        alias_sql = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'chart_spec_idempotency_keys'"
        ).fetchone()[0]
    assert "strftime" in str(created_at[4]).lower()
    assert "references chart_specs(" in alias_sql.lower()


def test_schema_repairs_already_migrated_chart_specs_missing_timestamp_default(tmp_path) -> None:
    path = tmp_path / "broken_migration.db"
    with sqlite3.connect(path) as conn:
        conn.execute(
            "CREATE TABLE chart_specs (id TEXT PRIMARY KEY, user_id TEXT NOT NULL, invocation_id TEXT NOT NULL,"
            " idempotency_key TEXT NOT NULL, logical_chart_id TEXT NOT NULL,"
            " version INTEGER NOT NULL CHECK (version >= 1), status TEXT NOT NULL, title TEXT NOT NULL,"
            " chart_spec_json TEXT NOT NULL, dataset_hash TEXT NOT NULL, lineage_json TEXT NOT NULL DEFAULT '{}',"
            " validation_json TEXT NOT NULL DEFAULT '{}', limitations_json TEXT NOT NULL DEFAULT '[]',"
            " content_hash TEXT NOT NULL, created_at TEXT NOT NULL)"
        )

    apply_schema(str(path))

    with sqlite3.connect(path) as conn:
        created_at = next(row for row in conn.execute("PRAGMA table_info(chart_specs)") if row[1] == "created_at")
    assert "strftime" in str(created_at[4]).lower()


def test_schema_repairs_idempotency_aliases_that_reference_legacy_table(tmp_path) -> None:
    path = tmp_path / "legacy_alias.db"
    with sqlite3.connect(path) as conn:
        conn.execute(
            "CREATE TABLE chart_specs (id TEXT PRIMARY KEY, user_id TEXT NOT NULL, invocation_id TEXT NOT NULL,"
            " idempotency_key TEXT NOT NULL, logical_chart_id TEXT NOT NULL,"
            " version INTEGER NOT NULL DEFAULT 1 CHECK (version >= 1), status TEXT NOT NULL,"
            " title TEXT NOT NULL, chart_spec_json TEXT NOT NULL, dataset_hash TEXT NOT NULL,"
            " lineage_json TEXT NOT NULL DEFAULT '{}', validation_json TEXT NOT NULL DEFAULT '{}',"
            " limitations_json TEXT NOT NULL DEFAULT '[]', content_hash TEXT NOT NULL,"
            " created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')))"
        )
        conn.execute(
            "CREATE TABLE chart_spec_idempotency_keys ("
            "user_id TEXT NOT NULL, idempotency_key TEXT NOT NULL,"
            " chart_spec_id TEXT NOT NULL REFERENCES chart_specs_legacy(id),"
            " content_hash TEXT NOT NULL, PRIMARY KEY (user_id, idempotency_key))"
        )

    apply_schema(str(path))

    with sqlite3.connect(path) as conn:
        fk_targets = {
            row[2]
            for row in conn.execute("PRAGMA foreign_key_list(chart_spec_idempotency_keys)")
            if row[3] == "chart_spec_id"
        }
    assert fk_targets == {"chart_specs"}


@pytest.mark.asyncio
async def test_chart_spec_is_user_scoped_immutable_and_idempotent(harness) -> None:
    task_id = await harness.post("data", "prepare a chart")
    await harness.wait_task(task_id, "completed")
    invocation_id = (await harness.invocations(task_id))[0]["id"]
    spec = {"$schema": "https://vega.github.io/schema/vega-lite/v5.json", "mark": "line"}
    lineage = {"input_artifact_refs": [{"artifact_id": "metric_price", "version": 2, "content_hash": "sha256:metric"}]}
    validation = {"overall_result": "pass", "validator_version": "chart-validator/1.0"}
    limitations = ["No causal interpretation"]

    first = await artifacts.insert_chart_spec(
        harness.db,
        user_id=ALICE,
        invocation_id=invocation_id,
        title="Price trend",
        chart_spec=spec,
        idempotency_key="task-price-trend:target-1",
        dataset_hash="dataset-sha256",
        lineage=lineage,
        validation=validation,
        limitations=limitations,
    )
    repeated = await artifacts.insert_chart_spec(
        harness.db,
        user_id=ALICE,
        invocation_id=invocation_id,
        title="Price trend",
        chart_spec=spec,
        idempotency_key="task-price-trend:target-1",
        dataset_hash="dataset-sha256",
        lineage=lineage,
        validation=validation,
        limitations=limitations,
    )

    assert repeated["id"] == first["id"]
    assert repeated["version"] == 1
    assert await artifacts.get_chart_spec(harness.db, BOB, first["id"]) is None
    assert (await artifacts.get_chart_spec(harness.db, ALICE, first["id"]))["chart_spec"] == spec
    assert first["lineage"] == lineage
    assert first["validation"] == validation
    assert first["limitations"] == limitations

    with pytest.raises(ValueError, match="idempotency key"):
        await artifacts.insert_chart_spec(
            harness.db,
            user_id=ALICE,
            invocation_id=invocation_id,
            title="Changed chart",
            chart_spec={**spec, "mark": "bar"},
            idempotency_key="task-price-trend:target-1",
            dataset_hash="dataset-sha256",
            lineage=lineage,
            validation=validation,
            limitations=limitations,
        )


@pytest.mark.asyncio
async def test_invocation_artifact_store_persists_chart_spec_for_its_owner(harness) -> None:
    task_id = await harness.post("data", "prepare a chart")
    await harness.wait_task(task_id, "completed")
    invocation_id = (await harness.invocations(task_id))[0]["id"]

    stored = await artifacts.InvocationArtifactStore(harness.db, ALICE, invocation_id).save_chart_spec(
        title="Trend",
        chart_spec={"mark": "line"},
        idempotency_key="chart-target-1",
        dataset_hash="sha256:dataset",
    )

    assert stored["id"].startswith("csp_")
    assert await artifacts.get_chart_spec(harness.db, BOB, stored["id"]) is None


@pytest.mark.asyncio
async def test_changed_semantic_content_creates_immutable_revision(harness) -> None:
    task_id = await harness.post("data", "prepare a chart")
    await harness.wait_task(task_id, "completed")
    invocation_id = (await harness.invocations(task_id))[0]["id"]
    common = {
        "user_id": ALICE,
        "invocation_id": invocation_id,
        "title": "Price trend",
        "dataset_hash": "sha256:dataset",
        "logical_chart_id": "chart_price_trend_target",
    }

    first = await artifacts.insert_chart_spec(
        harness.db,
        **common,
        chart_spec={"schema_version": "chart-spec/2.0", "chart_type": "line"},
        idempotency_key="price-trend:attempt-1",
    )
    revised = await artifacts.insert_chart_spec(
        harness.db,
        **common,
        chart_spec={"schema_version": "chart-spec/2.0", "chart_type": "area"},
        idempotency_key="price-trend:attempt-2",
    )

    assert first["id"] != revised["id"]
    assert first["version"] == 1
    assert revised["version"] == 2
    assert revised["logical_chart_id"] == "chart_price_trend_target"
    assert (await artifacts.get_chart_spec(harness.db, ALICE, first["id"]))["chart_spec"]["chart_type"] == "line"


@pytest.mark.asyncio
async def test_content_deduplicated_retry_key_remains_reserved(harness) -> None:
    task_id = await harness.post("data", "prepare a chart")
    await harness.wait_task(task_id, "completed")
    invocation_id = (await harness.invocations(task_id))[0]["id"]
    common = {
        "user_id": ALICE,
        "invocation_id": invocation_id,
        "title": "Price trend",
        "dataset_hash": "sha256:dataset",
        "logical_chart_id": "chart_price_trend_target",
    }
    first = await artifacts.insert_chart_spec(
        harness.db, **common, chart_spec={"chart_type": "line"}, idempotency_key="original"
    )
    repeated = await artifacts.insert_chart_spec(
        harness.db, **common, chart_spec={"chart_type": "line"}, idempotency_key="alias"
    )

    assert repeated["id"] == first["id"]
    with pytest.raises(ValueError, match="idempotency key"):
        await artifacts.insert_chart_spec(
            harness.db, **common, chart_spec={"chart_type": "area"}, idempotency_key="alias"
        )
