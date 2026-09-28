"""Datasets, charts and reports in backend.db (§3, §8).

Every read is scoped by the owning user (I4): another user's id reads exactly like an unknown id
(`None`). Writes take the owner and creating invocation from the MCP caller identity.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from vdagent_backend.ids import new_id


class InvocationArtifactStore:
    """Chart persistence capability bound to one authenticated invocation."""

    def __init__(self, db: AsyncEngine, user_id: str, invocation_id: str) -> None:
        self._db = db
        self._user_id = user_id
        self._invocation_id = invocation_id

    async def save_chart_spec(
        self,
        *,
        title: str,
        chart_spec: dict[str, Any],
        idempotency_key: str,
        dataset_hash: str,
        lineage: dict[str, Any] | None = None,
        validation: dict[str, Any] | None = None,
        limitations: list[str] | None = None,
    ) -> dict[str, Any]:
        return await insert_chart_spec(
            self._db,
            user_id=self._user_id,
            invocation_id=self._invocation_id,
            title=title,
            chart_spec=chart_spec,
            idempotency_key=idempotency_key,
            dataset_hash=dataset_hash,
            lineage=lineage,
            validation=validation,
            limitations=limitations,
        )


def _canonical_chart_spec(
    chart_spec: dict[str, Any],
    dataset_hash: str,
    title: str,
    lineage: dict[str, Any],
    validation: dict[str, Any],
    limitations: list[str],
) -> tuple[str, str]:
    """Return the stable JSON payload and its content address."""
    spec_json = json.dumps(chart_spec, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    material = json.dumps(
        {
            "chart_spec": chart_spec,
            "dataset_hash": dataset_hash,
            "title": title,
            "lineage": lineage,
            "validation": validation,
            "limitations": limitations,
        },
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return spec_json, hashlib.sha256(material.encode("utf-8")).hexdigest()


def _chart_spec_row(row: Any) -> dict[str, Any]:
    return {
        "id": row.id,
        "version": row.version,
        "status": row.status,
        "title": row.title,
        "chart_spec": json.loads(row.chart_spec_json),
        "dataset_hash": row.dataset_hash,
        "lineage": json.loads(row.lineage_json),
        "validation": json.loads(row.validation_json),
        "limitations": json.loads(row.limitations_json),
        "content_hash": row.content_hash,
        "created_at": row.created_at,
    }


async def insert_chart_spec(
    db: AsyncEngine,
    *,
    user_id: str,
    invocation_id: str,
    title: str,
    chart_spec: dict[str, Any],
    idempotency_key: str,
    dataset_hash: str,
    lineage: dict[str, Any] | None = None,
    validation: dict[str, Any] | None = None,
    limitations: list[str] | None = None,
) -> dict[str, Any]:
    """Persist one immutable ChartSpec, returning a previous exact retry.

    `idempotency_key` is scoped to an owner.  Reusing it for different content
    fails instead of silently replacing a previously rendered chart.
    """
    if not idempotency_key.strip():
        raise ValueError("idempotency key must not be empty")
    lineage = lineage or {}
    validation = validation or {}
    limitations = limitations or []
    spec_json, content_hash = _canonical_chart_spec(
        chart_spec, dataset_hash, title, lineage, validation, limitations
    )
    async with db.begin() as conn:
        existing = (
            await conn.execute(
                text(
                    "SELECT id, version, status, title, chart_spec_json, dataset_hash, lineage_json, validation_json,"
                    " limitations_json, content_hash, created_at"
                    " FROM chart_specs WHERE user_id = :user_id AND idempotency_key = :idempotency_key"
                ),
                {"user_id": user_id, "idempotency_key": idempotency_key},
            )
        ).first()
        if existing is not None:
            if existing.content_hash != content_hash:
                raise ValueError("idempotency key already belongs to different chart content")
            return _chart_spec_row(existing)

        chart_spec_id = new_id("csp")
        await conn.execute(
            text(
                "INSERT INTO chart_specs (id, user_id, invocation_id, idempotency_key, title, chart_spec_json,"
                " dataset_hash, lineage_json, validation_json, limitations_json, content_hash)"
                " VALUES (:id, :user_id, :invocation_id, :idempotency_key, :title, :chart_spec_json,"
                " :dataset_hash, :lineage_json, :validation_json, :limitations_json, :content_hash)"
            ),
            {
                "id": chart_spec_id,
                "user_id": user_id,
                "invocation_id": invocation_id,
                "idempotency_key": idempotency_key,
                "title": title,
                "chart_spec_json": spec_json,
                "dataset_hash": dataset_hash,
                "lineage_json": json.dumps(lineage, sort_keys=True, separators=(",", ":"), ensure_ascii=False),
                "validation_json": json.dumps(validation, sort_keys=True, separators=(",", ":"), ensure_ascii=False),
                "limitations_json": json.dumps(limitations, ensure_ascii=False, separators=(",", ":")),
                "content_hash": content_hash,
            },
        )
    saved = await get_chart_spec(db, user_id, chart_spec_id)
    assert saved is not None
    return saved


async def get_chart_spec(db: AsyncEngine, user_id: str, chart_spec_id: str) -> dict[str, Any] | None:
    """Read an immutable chart spec only when it belongs to `user_id`."""
    async with db.connect() as conn:
        row = (
            await conn.execute(
                text(
                    "SELECT id, version, status, title, chart_spec_json, dataset_hash, lineage_json, validation_json,"
                    " limitations_json, content_hash, created_at"
                    " FROM chart_specs WHERE id = :id AND user_id = :user_id"
                ),
                {"id": chart_spec_id, "user_id": user_id},
            )
        ).first()
    return None if row is None else _chart_spec_row(row)


async def insert_dataset(
    db: AsyncEngine,
    *,
    user_id: str,
    invocation_id: str,
    name: str | None,
    source_sql: str,
    columns: list[dict[str, str]],
    rows: list[list[Any]],
    truncated: bool,
) -> str:
    dataset_id = new_id("ds")
    async with db.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO datasets (id, user_id, invocation_id, name, source_sql, columns_json, rows_json,"
                " row_count, truncated) VALUES (:id, :user_id, :invocation_id, :name, :source_sql,"
                " :columns_json, :rows_json, :row_count, :truncated)"
            ),
            {
                "id": dataset_id,
                "user_id": user_id,
                "invocation_id": invocation_id,
                "name": name,
                "source_sql": source_sql,
                "columns_json": json.dumps(columns),
                "rows_json": json.dumps(rows),
                "row_count": len(rows),
                "truncated": int(truncated),
            },
        )
    return dataset_id


async def get_dataset(db: AsyncEngine, user_id: str, dataset_id: str) -> dict[str, Any] | None:
    async with db.connect() as conn:
        row = (
            await conn.execute(
                text(
                    "SELECT id, name, columns_json, rows_json, row_count, truncated, source_sql, created_at"
                    " FROM datasets WHERE id = :id AND user_id = :user_id"
                ),
                {"id": dataset_id, "user_id": user_id},
            )
        ).first()
    if row is None:
        return None
    return {
        "id": row.id,
        "name": row.name,
        "columns": json.loads(row.columns_json),
        "row_count": row.row_count,
        "truncated": bool(row.truncated),
        "source_sql": row.source_sql,
        "rows": json.loads(row.rows_json),
        "created_at": row.created_at,
    }


async def insert_chart(
    db: AsyncEngine,
    *,
    user_id: str,
    invocation_id: str,
    dataset_id: str,
    title: str,
    spec: dict[str, Any],
) -> str:
    chart_id = new_id("ch")
    async with db.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO charts (id, user_id, invocation_id, dataset_id, title, spec_json)"
                " VALUES (:id, :user_id, :invocation_id, :dataset_id, :title, :spec_json)"
            ),
            {
                "id": chart_id,
                "user_id": user_id,
                "invocation_id": invocation_id,
                "dataset_id": dataset_id,
                "title": title,
                "spec_json": json.dumps(spec),
            },
        )
    return chart_id


async def get_chart(db: AsyncEngine, user_id: str, chart_id: str) -> dict[str, Any] | None:
    async with db.connect() as conn:
        row = (
            await conn.execute(
                text("SELECT id, title, dataset_id, spec_json FROM charts WHERE id = :id AND user_id = :user_id"),
                {"id": chart_id, "user_id": user_id},
            )
        ).first()
    if row is None:
        return None
    return {"id": row.id, "title": row.title, "dataset_id": row.dataset_id, "spec": json.loads(row.spec_json)}


async def insert_report(db: AsyncEngine, *, user_id: str, invocation_id: str, title: str, markdown: str) -> str:
    report_id = new_id("rp")
    async with db.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO reports (id, user_id, invocation_id, title, markdown)"
                " VALUES (:id, :user_id, :invocation_id, :title, :markdown)"
            ),
            {
                "id": report_id,
                "user_id": user_id,
                "invocation_id": invocation_id,
                "title": title,
                "markdown": markdown,
            },
        )
    return report_id


async def list_reports(db: AsyncEngine, user_id: str) -> list[dict[str, Any]]:
    async with db.connect() as conn:
        rows = (
            await conn.execute(
                text(
                    "SELECT id, title, created_at FROM reports WHERE user_id = :user_id"
                    " ORDER BY created_at DESC, rowid DESC"
                ),
                {"user_id": user_id},
            )
        ).all()
    return [{"id": r.id, "title": r.title, "created_at": r.created_at} for r in rows]


async def get_report(db: AsyncEngine, user_id: str, report_id: str) -> dict[str, Any] | None:
    async with db.connect() as conn:
        row = (
            await conn.execute(
                text("SELECT id, title, markdown, created_at FROM reports WHERE id = :id AND user_id = :user_id"),
                {"id": report_id, "user_id": user_id},
            )
        ).first()
    if row is None:
        return None
    return {"id": row.id, "title": row.title, "markdown": row.markdown, "created_at": row.created_at}


async def existing_artifact_ids(db: AsyncEngine, user_id: str, table: str, ids: set[str]) -> set[str]:
    """The subset of `ids` in `table` (`datasets` | `charts`) owned by `user_id`."""
    if table not in ("datasets", "charts"):
        raise ValueError(f"not an artifact table: {table}")
    if not ids:
        return set()
    params = {f"id{i}": v for i, v in enumerate(sorted(ids))}
    placeholders = ", ".join(f":{k}" for k in params)
    async with db.connect() as conn:
        rows = (
            await conn.execute(
                text(f"SELECT id FROM {table} WHERE user_id = :user_id AND id IN ({placeholders})"),
                {"user_id": user_id, **params},
            )
        ).all()
    return {r.id for r in rows}
