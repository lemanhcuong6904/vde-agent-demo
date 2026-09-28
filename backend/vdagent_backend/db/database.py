"""backend.db access: async SQLAlchemy Core engine over aiosqlite (§8).

`create_db(path)` applies `schema.sql` (idempotent) and returns an `AsyncEngine` whose connections
carry the required pragmas and the `sqlite-vec` extension (vector search over agent memory). Query
functions live in `repo.py` (engine/core tables), `artifacts.py` (datasets / charts / reports) and
`memory.py` (agent memory).
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import sqlite_vec
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"


def apply_schema(path: str) -> None:
    """Create tables if missing (sync; startup / seed scripts only)."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.executescript(SCHEMA_PATH.read_text())
        _upgrade_chart_specs(conn)


def _upgrade_chart_specs(conn: sqlite3.Connection) -> None:
    """Upgrade immutable ChartSpec storage without discarding existing revisions."""
    existing = {row[1] for row in conn.execute("PRAGMA table_info(chart_specs)")}
    additions = {
        "lineage_json": "TEXT NOT NULL DEFAULT '{}'",
        "validation_json": "TEXT NOT NULL DEFAULT '{}'",
        "limitations_json": "TEXT NOT NULL DEFAULT '[]'",
        "logical_chart_id": "TEXT",
    }
    for name, definition in additions.items():
        if name not in existing:
            conn.execute(f"ALTER TABLE chart_specs ADD COLUMN {name} {definition}")
    conn.execute(
        "UPDATE chart_specs SET logical_chart_id = idempotency_key "
        "WHERE logical_chart_id IS NULL OR logical_chart_id = ''"
    )
    table_sql = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'chart_specs'"
    ).fetchone()[0].lower()
    if "version = 1" not in table_sql:
        conn.execute(
            "CREATE INDEX IF NOT EXISTS ix_chart_specs_logical "
            "ON chart_specs(user_id, logical_chart_id, version)"
        )
        return

    conn.execute("ALTER TABLE chart_specs RENAME TO chart_specs_legacy")
    conn.execute(
        "CREATE TABLE chart_specs ("
        "id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id), "
        "invocation_id TEXT NOT NULL REFERENCES invocations(id), idempotency_key TEXT NOT NULL, "
        "logical_chart_id TEXT NOT NULL, version INTEGER NOT NULL DEFAULT 1 CHECK (version >= 1), "
        "status TEXT NOT NULL DEFAULT 'ready' CHECK (status IN ('ready','failed')), title TEXT NOT NULL, "
        "chart_spec_json TEXT NOT NULL, dataset_hash TEXT NOT NULL, lineage_json TEXT NOT NULL DEFAULT '{}', "
        "validation_json TEXT NOT NULL DEFAULT '{}', limitations_json TEXT NOT NULL DEFAULT '[]', "
        "content_hash TEXT NOT NULL, created_at TEXT NOT NULL)"
    )
    conn.execute(
        "INSERT INTO chart_specs (id, user_id, invocation_id, idempotency_key, logical_chart_id, version, "
        "status, title, chart_spec_json, dataset_hash, lineage_json, validation_json, limitations_json, "
        "content_hash, created_at) "
        "SELECT id, user_id, invocation_id, idempotency_key, logical_chart_id, version, status, title, "
        "chart_spec_json, dataset_hash, lineage_json, validation_json, limitations_json, content_hash, created_at "
        "FROM chart_specs_legacy"
    )
    conn.execute("DROP TABLE chart_specs_legacy")
    conn.execute("CREATE INDEX IF NOT EXISTS ix_chart_specs_user ON chart_specs(user_id, created_at)")
    conn.execute(
        "CREATE INDEX IF NOT EXISTS ix_chart_specs_logical "
        "ON chart_specs(user_id, logical_chart_id, version)"
    )


def _set_pragmas(dbapi_conn, _record) -> None:  # noqa: ANN001
    cur = dbapi_conn.cursor()
    cur.execute("PRAGMA journal_mode=WAL")
    cur.execute("PRAGMA foreign_keys=ON")
    cur.execute("PRAGMA busy_timeout=5000")
    cur.close()
    dbapi_conn.run_async(_load_sqlite_vec)


async def _load_sqlite_vec(conn) -> None:  # noqa: ANN001  (aiosqlite.Connection)
    await conn.enable_load_extension(True)
    await conn.load_extension(sqlite_vec.loadable_path())
    await conn.enable_load_extension(False)


def create_db(path: str) -> AsyncEngine:
    apply_schema(path)
    engine = create_async_engine(f"sqlite+aiosqlite:///{path}")
    event.listen(engine.sync_engine, "connect", _set_pragmas)
    return engine
