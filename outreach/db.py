import json
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from typing import Any

from outreach import config


def now() -> str:
    """Return current UTC timestamp in ISO-8601 format."""
    return datetime.now(timezone.utc).isoformat()


def init_db(conn: sqlite3.Connection) -> None:
    """Initialize database tables and constraints if they do not exist."""
    cur = conn.cursor()
    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS kv (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS campaigns (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            segment TEXT NOT NULL,
            keywords TEXT NOT NULL,
            sender_context TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS prospects (
            id TEXT PRIMARY KEY,
            github_login TEXT NOT NULL,
            x_username TEXT NOT NULL UNIQUE COLLATE NOCASE,
            x_user_id TEXT,
            name TEXT,
            bio TEXT,
            location TEXT,
            company TEXT,
            followers INTEGER,
            can_dm INTEGER,
            campaign_id INTEGER NOT NULL REFERENCES campaigns(id),
            source TEXT NOT NULL,
            fit_score INTEGER,
            fit_category TEXT,
            fit_reasons TEXT,
            do_not_contact INTEGER NOT NULL DEFAULT 0,
            fetched_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS repos (
            source_id TEXT PRIMARY KEY,
            prospect_id TEXT NOT NULL REFERENCES prospects(id),
            name TEXT NOT NULL,
            description TEXT,
            topics TEXT NOT NULL DEFAULT '[]',
            stars INTEGER NOT NULL DEFAULT 0,
            pushed_at TEXT,
            url TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY,
            prospect_id TEXT NOT NULL UNIQUE REFERENCES prospects(id),
            text TEXT NOT NULL,
            evidence TEXT NOT NULL,
            evidence_ok INTEGER NOT NULL,
            edited INTEGER NOT NULL DEFAULT 0,
            status TEXT NOT NULL CHECK (status IN
                ('draft','approved','rejected','sending','sent','failed','blocked','unknown')),
            channel TEXT CHECK (channel IN ('manual','api')),
            error TEXT,
            dm_event_id TEXT,
            dm_conversation_id TEXT,
            claimed_at TEXT,
            sent_at TEXT,
            reply_text TEXT,
            replied_at TEXT,
            handled_at TEXT,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS usage (
            ts TEXT NOT NULL,
            kind TEXT NOT NULL,
            units INTEGER NOT NULL,
            cost_usd REAL NOT NULL
        );
        """
    )
    conn.commit()


def connect(path: str | None = None) -> sqlite3.Connection:
    """
    Connect to SQLite database with Row factory, foreign keys, and WAL journal mode.
    Automatically creates the parent directory if path is a file, and calls init_db.
    """
    db_path = config.DB_PATH if path is None else path

    if db_path != ":memory:":
        parent_dir = Path(db_path).resolve().parent
        parent_dir.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    if db_path != ":memory:":
        conn.execute("PRAGMA journal_mode = WAL;")

    init_db(conn)
    return conn


def kv_get(conn: sqlite3.Connection, key: str) -> dict[str, Any] | None:
    """Retrieve JSON-deserialized value from the kv table, or None if missing."""
    row = conn.execute("SELECT value FROM kv WHERE key = ?", (key,)).fetchone()
    if row is None:
        return None
    return json.loads(row["value"])


def kv_set(conn: sqlite3.Connection, key: str, value: dict[str, Any]) -> None:
    """
    Insert or update a JSON-serialized value in the kv table.
    Commits immediately before returning.
    """
    json_val = json.dumps(value)
    conn.execute(
        """
        INSERT INTO kv (key, value)
        VALUES (?, ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value
        """,
        (key, json_val),
    )
    conn.commit()


def record_usage(conn: sqlite3.Connection, kind: str, units: int) -> None:
    """
    Record API usage units and calculated USD cost into the usage table.
    Supported kinds: post_read, user_read, dm_read, dm_send, llm_in, llm_out.
    Commits immediately before returning.
    """
    if kind in config.PRICES:
        cost = units * config.PRICES[kind]
    elif kind == "llm_in":
        cost = units * (config.LLM_PRICE_IN / 1_000_000.0)
    elif kind == "llm_out":
        cost = units * (config.LLM_PRICE_OUT / 1_000_000.0)
    else:
        raise ValueError(f"Unknown usage kind: {kind}")

    conn.execute(
        """
        INSERT INTO usage (ts, kind, units, cost_usd)
        VALUES (?, ?, ?, ?)
        """,
        (now(), kind, units, cost),
    )
    conn.commit()


def spend_since(conn: sqlite3.Connection, iso_ts: str) -> float:
    """Calculate total USD cost accumulated in the usage table since iso_ts."""
    row = conn.execute(
        "SELECT COALESCE(SUM(cost_usd), 0.0) AS total_cost FROM usage WHERE ts >= ?",
        (iso_ts,),
    ).fetchone()
    return float(row["total_cost"])
