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
