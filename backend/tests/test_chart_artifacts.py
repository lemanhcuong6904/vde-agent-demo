"""Persistence contract for immutable ChartSpec artifacts."""

from __future__ import annotations

import pytest

from vdagent_backend.db import artifacts

from conftest import ALICE, BOB


@pytest.mark.asyncio
async def test_chart_spec_is_user_scoped_immutable_and_idempotent(harness) -> None:
    task_id = await harness.post("data", "prepare a chart")
    await harness.wait_task(task_id, "completed")
    invocation_id = (await harness.invocations(task_id))[0]["id"]
    spec = {"$schema": "https://vega.github.io/schema/vega-lite/v5.json", "mark": "line"}

    first = await artifacts.insert_chart_spec(
        harness.db,
        user_id=ALICE,
        invocation_id=invocation_id,
        title="Price trend",
        chart_spec=spec,
        idempotency_key="task-price-trend:target-1",
        dataset_hash="dataset-sha256",
    )
    repeated = await artifacts.insert_chart_spec(
        harness.db,
        user_id=ALICE,
        invocation_id=invocation_id,
        title="Price trend",
        chart_spec=spec,
        idempotency_key="task-price-trend:target-1",
        dataset_hash="dataset-sha256",
    )

    assert repeated["id"] == first["id"]
    assert repeated["version"] == 1
    assert await artifacts.get_chart_spec(harness.db, BOB, first["id"]) is None
    assert (await artifacts.get_chart_spec(harness.db, ALICE, first["id"]))["chart_spec"] == spec

    with pytest.raises(ValueError, match="idempotency key"):
        await artifacts.insert_chart_spec(
            harness.db,
            user_id=ALICE,
            invocation_id=invocation_id,
            title="Changed chart",
            chart_spec={**spec, "mark": "bar"},
            idempotency_key="task-price-trend:target-1",
            dataset_hash="dataset-sha256",
        )
