import sys
from pathlib import Path

# Ensure project root is in sys.path when running pytest directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import sqlite3
import pytest
from outreach.db import connect, init_db



@pytest.fixture
def conn():
    """In-memory SQLite connection with full schema initialized."""
    c = connect(":memory:")
    try:
        yield c
    finally:
        c.close()


@pytest.fixture
def file_db(tmp_path: Path):
    """Path to a temporary SQLite database file for multi-connection tests."""
    db_path = str(tmp_path / "test.db")
    return db_path


@pytest.fixture
def campaign_id(conn):
    """Seed a sample campaign to satisfy foreign key constraints in prospects."""
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO campaigns (name, segment, keywords, sender_context, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            "AI Builders SEA",
            "Founders and engineers building AI products in Southeast Asia",
            "ai,robotics,founder,engineer",
            "GenAI Fund looking to support early-stage founders",
            "2026-11-12T00:00:00+00:00",
        ),
    )
    conn.commit()
    return cur.lastrowid
