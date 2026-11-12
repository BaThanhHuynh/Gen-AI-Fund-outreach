import sqlite3
import pytest
from outreach.db import (
    connect,
    init_db,
    kv_get,
    kv_set,
    record_usage,
    spend_since,
)


def test_init_db_is_idempotent(conn, campaign_id):
    """Calling init_db multiple times must preserve existing records."""
    init_db(conn)
    row = conn.execute("SELECT name FROM campaigns WHERE id = ?", (campaign_id,)).fetchone()
    assert row is not None
    assert row["name"] == "AI Builders SEA"


def test_one_message_per_person(conn, campaign_id):
    """Inserting a second message for the same prospect_id must raise IntegrityError."""
    conn.execute(
        """
        INSERT INTO prospects (id, github_login, x_username, campaign_id, source, fetched_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        ("gh:123", "alice_gh", "alice_ai", campaign_id, "segment:ai", "2026-11-12T00:00:00+00:00"),
    )
    conn.commit()

    conn.execute(
        """
        INSERT INTO messages (prospect_id, text, evidence, evidence_ok, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        ("gh:123", "Hello Alice", "[]", 1, "draft", "2026-11-12T00:00:00+00:00"),
    )
    conn.commit()

    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            """
            INSERT INTO messages (prospect_id, text, evidence, evidence_ok, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            ("gh:123", "Second message", "[]", 1, "draft", "2026-11-12T00:00:00+00:00"),
        )
        conn.commit()


def test_status_check_constraint(conn, campaign_id):
    """Invalid message status must violate CHECK constraint and raise IntegrityError."""
    conn.execute(
        """
        INSERT INTO prospects (id, github_login, x_username, campaign_id, source, fetched_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        ("gh:456", "bob_gh", "bob_robotics", campaign_id, "segment:robotics", "2026-11-12T00:00:00+00:00"),
    )
    conn.commit()

    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            """
            INSERT INTO messages (prospect_id, text, evidence, evidence_ok, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            ("gh:456", "Hello Bob", "[]", 1, "bogus", "2026-11-12T00:00:00+00:00"),
        )
        conn.commit()


def test_message_requires_existing_prospect(conn):
    """Inserting a message for a nonexistent prospect must fail foreign key check."""
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            """
            INSERT INTO messages (prospect_id, text, evidence, evidence_ok, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            ("gh:nonexistent", "Hello Stranger", "[]", 1, "draft", "2026-11-12T00:00:00+00:00"),
        )
        conn.commit()


def test_kv_roundtrip(conn):
    """kv_set and kv_get must roundtrip JSON dicts, returning None for unknown keys."""
    kv_set(conn, "test_key", {"count": 42, "enabled": True})
    assert kv_get(conn, "test_key") == {"count": 42, "enabled": True}
    assert kv_get(conn, "nonexistent_key") is None


def test_record_usage_cost(conn):
    """record_usage must record cost according to PRICES and calculate spend_since."""
    record_usage(conn, "post_read", 3)
    assert spend_since(conn, "1970-01-01T00:00:00+00:00") == pytest.approx(0.015)


def test_writes_are_visible_to_second_connection(file_db):
    """kv_set and record_usage committed on connection A must be readable from connection B."""
    conn_a = connect(file_db)
    kv_set(conn_a, "shared_state", {"synced": True})

    # Read kv_get on conn_b BEFORE record_usage is called on conn_a
    # This ensures conn.commit() in kv_set is strictly required and tested independently
    conn_b = connect(file_db)
    val = kv_get(conn_b, "shared_state")
    assert val == {"synced": True}

    # Now call record_usage on conn_a while conn_a is still open and verify visibility on conn_b
    record_usage(conn_a, "post_read", 2)
    spend = spend_since(conn_b, "1970-01-01T00:00:00+00:00")
    assert spend == pytest.approx(0.010)

    conn_a.close()
    conn_b.close()


def test_one_x_account_per_prospect(conn, campaign_id):
    """x_username must be UNIQUE COLLATE NOCASE across prospects."""
    conn.execute(
        """
        INSERT INTO prospects (id, github_login, x_username, campaign_id, source, fetched_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        ("gh:101", "alice_gh", "alice_x", campaign_id, "segment:ai", "2026-11-12T00:00:00+00:00"),
    )
    conn.commit()

    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            """
            INSERT INTO prospects (id, github_login, x_username, campaign_id, source, fetched_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            ("gh:102", "alice_other_gh", "ALICE_X", campaign_id, "segment:ai", "2026-11-12T00:00:00+00:00"),
        )
        conn.commit()

