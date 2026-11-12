import pytest

from outreach import review
from outreach.db import now


def _message(conn, campaign_id, status="draft", evidence_ok=1):
    conn.execute(
        "INSERT INTO prospects (id, github_login, x_username, campaign_id, source, fetched_at) "
        "VALUES ('gh:1', 'u1', 'x1', ?, 'import', ?)", (campaign_id, now()))
    cur = conn.execute(
        "INSERT INTO messages (prospect_id, text, evidence, evidence_ok, status, created_at) "
        "VALUES ('gh:1', 'draft text', '[]', ?, ?, ?)", (evidence_ok, status, now()))
    conn.commit()
    return cur.lastrowid


def _row(conn, mid):
    return conn.execute("SELECT * FROM messages WHERE id = ?", (mid,)).fetchone()


def test_approve_requires_verified_evidence(conn, campaign_id):
    mid = _message(conn, campaign_id, evidence_ok=0)
    assert review.approve(conn, mid) == "evidence not verified — edit the text first"
    assert _row(conn, mid)["status"] == "draft"

    conn.execute("UPDATE messages SET evidence_ok = 1 WHERE id = ?", (mid,))
    assert review.approve(conn, mid) is None
    assert _row(conn, mid)["status"] == "approved"
    assert review.approve(conn, mid) == "cannot approve from status approved"


def test_edit_then_approve(conn, campaign_id):
    mid = _message(conn, campaign_id, evidence_ok=0)
    with pytest.raises(ValueError):
        review.set_text(conn, mid, "   ")             # blank text is refused
    review.set_text(conn, mid, "Hi, a better text written by a person.")
    row = _row(conn, mid)
    assert row["text"] == "Hi, a better text written by a person." and row["edited"] == 1
    assert review.approve(conn, mid) is None
    assert _row(conn, mid)["status"] == "approved"


def test_cannot_edit_after_sent(conn, campaign_id):
    mid = _message(conn, campaign_id, status="sent")
    with pytest.raises(ValueError):
        review.set_text(conn, mid, "changed")
    assert _row(conn, mid)["text"] == "draft text"


def test_reject(conn, campaign_id):
    mid = _message(conn, campaign_id)
    review.reject(conn, mid)
    assert _row(conn, mid)["status"] == "rejected"
    assert review.approve(conn, mid) is None          # a rejected draft can be approved again

    conn.execute("UPDATE messages SET status = 'sent' WHERE id = ?", (mid,))
    with pytest.raises(ValueError):
        review.reject(conn, mid)
    assert _row(conn, mid)["status"] == "sent"
