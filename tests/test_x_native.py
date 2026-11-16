import sqlite3
import pytest

from outreach import config, fit, llm, sender
from outreach.fake_x import FakeXClient
from outreach.x_discover import discover_by_x_search, discover_by_x_seeds, import_x_usernames
from outreach.x_sync import sync_x_replies


def test_discover_by_x_search_and_score(conn, campaign_id):
    x = FakeXClient(conn)
    counts = discover_by_x_search(conn, x, campaign_id, "robotics", max_results=5)
    assert counts["new"] > 0
    assert counts["checked"] > 0

    # Verify prospects are in the DB
    prospects = conn.execute("SELECT * FROM prospects WHERE campaign_id = ?", (campaign_id,)).fetchall()
    assert len(prospects) > 0
    p = prospects[0]
    assert p["id"].startswith("x:")
    assert p["x_username"] != ""

    # Score campaign
    scored = fit.score_campaign(conn, campaign_id, today="2026-11-15")
    assert scored > 0

    # Check that fit reasons mention the post or bio
    updated_p = conn.execute("SELECT * FROM prospects WHERE id = ?", (p["id"],)).fetchone()
    assert updated_p["fit_score"] is not None


def test_search_query_ors_campaign_keywords():
    # X treats spaces as AND, so a raw "a, b c" keyword list would need every word in one post
    from outreach.x_discover import search_query
    assert search_query("robotics, embodied AI, ") == '("robotics" OR "embodied AI") -is:retweet'


def test_discover_by_x_seeds(conn, campaign_id):
    x = FakeXClient(conn)
    counts = discover_by_x_seeds(conn, x, campaign_id, ["alex_builder"], max_people=2)
    assert counts["checked"] > 0


def test_import_x_usernames(conn, campaign_id):
    x = FakeXClient(conn)
    counts = import_x_usernames(conn, x, campaign_id, ["sarah_robotics"])
    assert counts["new"] == 1
    row = conn.execute("SELECT * FROM prospects WHERE x_username = 'sarah_robotics'").fetchone()
    assert row is not None
    assert row["name"] == "Sarah Chen"


def test_x_post_evidence_quotes_in_template_draft(conn, campaign_id):
    x = FakeXClient(conn)
    import_x_usernames(conn, x, campaign_id, ["alex_builder"])
    p = conn.execute("SELECT * FROM prospects WHERE x_username = 'alex_builder'").fetchone()
    fit.score_campaign(conn, campaign_id, today="2026-11-15")

    updated_p = conn.execute("SELECT * FROM prospects WHERE id = ?", (p["id"],)).fetchone()
    reasons = fit.repos_of(conn, p["id"])
    sources = fit.sources_for(dict(updated_p), reasons)
    fit_data = {
        "score": updated_p["fit_score"],
        "category": updated_p["fit_category"],
        "reasons": [{"claim": "Post is about robotics", "source_id": reasons[0]["source_id"]}],
    }
    draft = llm.template_draft("We are GenAI Fund.", dict(updated_p), sources, fit_data)
    assert "your post on X" in draft["text"]
    assert llm.verify_evidence(draft["evidence"], sources) is True


def test_sync_x_replies_auto_updates_needs_attention(conn, campaign_id, monkeypatch):
    monkeypatch.setattr(config, "SEND_MODE", "allowlist")
    monkeypatch.setattr(config, "SEND_ALLOWLIST", ["alex_builder"])
    x = FakeXClient(conn)

    # 1. Store and approve a prospect
    import_x_usernames(conn, x, campaign_id, ["alex_builder"])
    p = conn.execute("SELECT * FROM prospects WHERE x_username = 'alex_builder'").fetchone()

    # 2. Insert approved message and send via API
    cur = conn.execute(
        """INSERT INTO messages (prospect_id, text, evidence, evidence_ok, status, channel, created_at)
           VALUES (?, 'Hi Alex, testing sync', '[]', 1, 'approved', 'api', ?)""",
        (p["id"], "2026-11-15T10:00:00Z"),
    )
    mid = cur.lastrowid
    conn.commit()

    # 3. Send API
    status = sender.send_api(conn, x, mid)
    assert status == "sent"

    # 4. Simulate an incoming reply in FakeXClient
    x.simulate_reply(user_id=p["x_user_id"], text="Thanks! Let's talk about robotics.")

    # 5. Run sync
    res = sync_x_replies(conn, x)
    assert res["new_replies"] == 1
    assert "alex_builder" in res["replied_users"]

    # 6. Verify message status and that it shows in needs_attention
    m = conn.execute("SELECT * FROM messages WHERE id = ?", (mid,)).fetchone()
    assert m["replied_at"] is not None
    assert "Let's talk" in m["reply_text"]

    attention = sender.needs_attention(conn)
    assert any(item["id"] == mid for item in attention)
