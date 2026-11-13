from datetime import datetime, timedelta, timezone

import pytest

from outreach import config, sender
from outreach.db import connect, now
from outreach.fake_x import FakeXClient
from outreach.sender import SendBlocked
from outreach.xclient import Ambiguous, AuthError, Forbidden, RateLimited, XError


def _ago(**kw) -> str:
    return (datetime.now(timezone.utc) - timedelta(**kw)).isoformat()


@pytest.fixture(autouse=True)
def safe_config(monkeypatch):
    monkeypatch.setattr(config, "SEND_MODE", "allowlist")
    monkeypatch.setattr(config, "SEND_ALLOWLIST", ["alex_builder", "sarah_robotics", "coffee_memes"])
    monkeypatch.setattr(config, "DAILY_SEND_CAP", 20)


def add(conn, campaign_id, username="alex_builder", status="approved", n=None, **cols):
    """Insert one prospect and its message; return the message id."""
    pid = f"gh:{username}"
    conn.execute(
        "INSERT INTO prospects (id, github_login, x_username, campaign_id, source, fetched_at, can_dm, do_not_contact)"
        " VALUES (?,?,?,?,?,?,?,?)",
        (pid, username, username, campaign_id, "import", now(), cols.pop("can_dm", None),
         cols.pop("do_not_contact", 0)))
    cols.setdefault("channel", None)
    cur = conn.execute(
        "INSERT INTO messages (prospect_id, text, evidence, evidence_ok, status, created_at, channel, claimed_at,"
        " replied_at, handled_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (pid, "hello", "[]", 1, status, now(), cols["channel"], cols.get("claimed_at"),
         cols.get("replied_at"), cols.get("handled_at")))
    conn.commit()
    return cur.lastrowid


def row(conn, mid):
    return conn.execute("SELECT * FROM messages WHERE id = ?", (mid,)).fetchone()


def test_unapproved_is_never_opened_or_sent(conn, campaign_id):
    x = FakeXClient(conn)
    for i, st in enumerate(("draft", "rejected")):
        mid = add(conn, campaign_id, "alex_builder" if i == 0 else "sarah_robotics", st)
        with pytest.raises(SendBlocked):
            sender.open_manual(conn, mid)
        with pytest.raises(SendBlocked):
            sender.send_api(conn, x, mid)
        assert row(conn, mid)["status"] == st
    assert len(x.sent) == 0


def test_open_manual_claims_and_returns_profile_url_and_text(conn, campaign_id):
    mid = add(conn, campaign_id)
    out = sender.open_manual(conn, mid)
    assert out == {"url": "https://x.com/alex_builder", "text": "hello"}
    r = row(conn, mid)
    assert (r["status"], r["channel"]) == ("sending", "manual") and r["claimed_at"]


def test_open_twice_second_is_blocked(conn, campaign_id):
    mid = add(conn, campaign_id)
    sender.open_manual(conn, mid)
    with pytest.raises(SendBlocked, match="not approved"):
        sender.open_manual(conn, mid)


def test_claim_is_atomic(file_db, campaign_id):
    a, b = connect(file_db), connect(file_db)
    a.execute("INSERT INTO campaigns (id, name, segment, keywords, sender_context, created_at)"
              " VALUES (1,'c','s','k','x',?)", (now(),))
    a.commit()
    mid = add(a, 1)
    results = [sender.claim(a, mid, "manual"), sender.claim(b, mid, "manual")]
    assert sorted(results) == [False, True]
    a.close(), b.close()


def test_confirm_sent_counts_toward_cap(conn, campaign_id):
    mid = add(conn, campaign_id)
    sender.open_manual(conn, mid)
    assert sender.confirm_manual(conn, mid, "sent") == "sent"
    assert row(conn, mid)["sent_at"]
    assert sender.sends_in_last_24h(conn) == 1


def test_confirm_not_sent_returns_to_approved_and_frees_cap(conn, campaign_id):
    mid = add(conn, campaign_id)
    sender.open_manual(conn, mid)
    assert sender.sends_in_last_24h(conn) == 1
    assert sender.confirm_manual(conn, mid, "not_sent") == "approved"
    r = row(conn, mid)
    assert r["claimed_at"] is None and r["channel"] is None
    assert sender.sends_in_last_24h(conn) == 0


def test_confirm_existing_conversation_blocks(conn, campaign_id):
    mid = add(conn, campaign_id)
    sender.open_manual(conn, mid)
    assert sender.confirm_manual(conn, mid, "existing") == "blocked"
    assert row(conn, mid)["error"] == "existing conversation"


def test_confirm_requires_manual_sending_state(conn, campaign_id):
    m1 = add(conn, campaign_id, "alex_builder", "approved")
    m2 = add(conn, campaign_id, "sarah_robotics", "sending", channel="api", claimed_at=now())
    for mid in (m1, m2):
        with pytest.raises(ValueError):
            sender.confirm_manual(conn, mid, "sent")
    assert row(conn, m1)["status"] == "approved" and row(conn, m2)["status"] == "sending"


def test_daily_cap_blocks(conn, campaign_id, monkeypatch):
    monkeypatch.setattr(config, "DAILY_SEND_CAP", 2)
    add(conn, campaign_id, "sarah_robotics", "sent", claimed_at=_ago(hours=1))
    add(conn, campaign_id, "coffee_memes", "unknown", claimed_at=_ago(hours=23))
    add(conn, campaign_id, "old_one", "sent", claimed_at=_ago(hours=25))
    mid = add(conn, campaign_id)
    assert "daily cap" in sender.check_can_send(conn, mid)
    assert sender.check_can_send(conn, mid) == "daily cap reached (2/2)"
    with pytest.raises(SendBlocked, match="daily cap"):
        sender.open_manual(conn, mid)


def test_allowlist_blocks_strangers_case_insensitive(conn, campaign_id, monkeypatch):
    monkeypatch.setattr(config, "SEND_ALLOWLIST", ["Alex_Builder"])
    x = FakeXClient(conn)
    ok = add(conn, campaign_id, "ALEX_builder")
    stranger = add(conn, campaign_id, "david_closed")
    assert sender.check_can_send(conn, ok) is None
    assert sender.check_can_send(conn, stranger) == "not on SEND_ALLOWLIST (safety mode)"
    with pytest.raises(SendBlocked, match="SEND_ALLOWLIST"):
        sender.open_manual(conn, stranger)
    with pytest.raises(SendBlocked, match="SEND_ALLOWLIST"):
        sender.send_api(conn, x, stranger)
    assert sender.send_api(conn, x, ok) == "sent"


def test_api_channel_requires_allowlist_even_when_live(conn, campaign_id, monkeypatch):
    monkeypatch.setattr(config, "SEND_MODE", "live")
    x = FakeXClient(conn)
    mid = add(conn, campaign_id, "david_closed")
    with pytest.raises(SendBlocked, match="api channel"):
        sender.send_api(conn, x, mid)
    assert len(x.sent) == 0 and row(conn, mid)["status"] == "approved"
    assert sender.open_manual(conn, mid)["url"] == "https://x.com/david_closed"


def test_do_not_contact_blocks(conn, campaign_id):
    mid = add(conn, campaign_id)
    sender.set_do_not_contact(conn, "gh:alex_builder", True)
    assert sender.check_can_send(conn, mid) == "marked do-not-contact"
    with pytest.raises(SendBlocked):
        sender.open_manual(conn, mid)
    sender.set_do_not_contact(conn, "gh:alex_builder", False)
    assert sender.check_can_send(conn, mid) is None


def test_api_send_happy_path(conn, campaign_id):
    x = FakeXClient(conn)
    mid = add(conn, campaign_id)
    assert sender.send_api(conn, x, mid) == "sent"
    r = row(conn, mid)
    p = conn.execute("SELECT x_user_id, can_dm FROM prospects").fetchone()
    assert (p["x_user_id"], p["can_dm"]) == ("1001", 1)
    assert r["dm_event_id"] and r["dm_conversation_id"] and r["sent_at"] and r["channel"] == "api"
    assert x.sent == [("1001", "hello")]


def test_api_prior_conversation_blocks(conn, campaign_id):
    x = FakeXClient(conn)
    x.inbox.append({"id": "e1", "sender_id": "1001", "recipient_id": "999999"})
    mid = add(conn, campaign_id)
    assert sender.send_api(conn, x, mid) == "blocked"
    assert row(conn, mid)["error"] == "existing conversation"
    assert len(x.sent) == 0


def test_api_ambiguous_becomes_unknown_and_is_never_resent(conn, campaign_id):
    x = FakeXClient(conn)
    mid = add(conn, campaign_id)
    real = x.send_dm

    def boom(uid, text):
        raise Ambiguous("timeout")
    x.send_dm = boom
    assert sender.send_api(conn, x, mid) == "unknown"
    x.send_dm = real
    with pytest.raises(SendBlocked):
        sender.send_api(conn, x, mid)
    assert len(x.sent) == 0


def test_api_403_blocked_400_failed_429_back_to_approved(conn, campaign_id):
    x = FakeXClient(conn)
    cases = [(Forbidden("no"), "blocked"), (XError(400, "bad"), "failed"),
             (AuthError("expired"), "failed"), (RateLimited(reset_at=1), "approved")]
    for i, (exc, expected) in enumerate(cases):
        mid = add(conn, campaign_id, f"user{i}")
        config.SEND_ALLOWLIST.append(f"user{i}")
        x.users_by_usernames = lambda names, n=f"user{i}": [
            {"id": f"id_{n}", "username": n, "receives_your_dm": True}]

        def boom(uid, text, exc=exc):
            raise exc
        x.send_dm = boom
        assert sender.send_api(conn, x, mid) == expected
        r = row(conn, mid)
        assert r["status"] == expected
        if expected == "approved":
            assert r["claimed_at"] is None and r["channel"] is None
        else:
            assert r["error"]


def test_api_closed_dm_blocks(conn, campaign_id, monkeypatch):
    monkeypatch.setattr(config, "SEND_ALLOWLIST", ["david_closed", "ghost_user"])
    x = FakeXClient(conn)
    closed = add(conn, campaign_id, "david_closed")
    missing = add(conn, campaign_id, "ghost_user")
    assert sender.send_api(conn, x, closed) == "blocked"
    assert sender.send_api(conn, x, missing) == "blocked"
    assert len(x.sent) == 0


def test_recover_stuck_only_touches_api_channel(conn, campaign_id):
    old_api = add(conn, campaign_id, "alex_builder", "sending", channel="api", claimed_at=_ago(minutes=10))
    new_api = add(conn, campaign_id, "sarah_robotics", "sending", channel="api", claimed_at=_ago(minutes=1))
    old_manual = add(conn, campaign_id, "coffee_memes", "sending", channel="manual", claimed_at=_ago(minutes=10))
    assert sender.recover_stuck(conn) == 1
    assert row(conn, old_api)["status"] == "unknown"
    assert row(conn, new_api)["status"] == "sending"
    assert row(conn, old_manual)["status"] == "sending"


def test_resolve_unknown(conn, campaign_id):
    a = add(conn, campaign_id, "alex_builder", "unknown", channel="api", claimed_at=now())
    b = add(conn, campaign_id, "sarah_robotics", "unknown", channel="api", claimed_at=now())
    assert sender.resolve_unknown(conn, a, True) == "sent"
    assert row(conn, a)["sent_at"]
    assert sender.resolve_unknown(conn, b, False) == "failed"
    with pytest.raises(ValueError):
        sender.resolve_unknown(conn, a, False)


def test_mark_replied_and_handled(conn, campaign_id):
    sent = add(conn, campaign_id, "alex_builder", "sent")
    approved = add(conn, campaign_id, "sarah_robotics", "approved")
    sender.mark_replied(conn, sent, "interested")
    r = row(conn, sent)
    assert r["reply_text"] == "interested" and r["replied_at"]
    with pytest.raises(ValueError):
        sender.mark_replied(conn, approved, "x")
    sender.mark_handled(conn, sent)
    assert row(conn, sent)["handled_at"]


def test_needs_attention_contents(conn, campaign_id):
    ids = {
        "manual_sending": add(conn, campaign_id, "u1", "sending", channel="manual", claimed_at=_ago(days=3)),
        "unknown": add(conn, campaign_id, "u2", "unknown", channel="api", claimed_at=now()),
        "failed": add(conn, campaign_id, "u3", "failed"),
        "blocked": add(conn, campaign_id, "u4", "blocked"),
        "replied": add(conn, campaign_id, "u5", "sent", replied_at=now()),
    }
    add(conn, campaign_id, "u6", "blocked", handled_at=now())
    add(conn, campaign_id, "u7", "sent")
    add(conn, campaign_id, "u8", "sending", channel="api", claimed_at=now())
    add(conn, campaign_id, "u9", "approved")
    assert {r["id"] for r in sender.needs_attention(conn)} == set(ids.values())
    for name, mid in ids.items():
        sender.mark_handled(conn, mid)
        listed = mid in {r["id"] for r in sender.needs_attention(conn)}
        assert listed == (name in ("unknown", "manual_sending"))  # these only leave by the user's choice


def test_new_attempt_after_handled_failure_shows_again(conn, campaign_id):
    """failed -> handled -> approved again -> fails again: the new failure must not stay hidden."""
    x = FakeXClient(conn)
    mid = add(conn, campaign_id)
    x.send_dm = lambda uid, text: (_ for _ in ()).throw(XError(400, "bad"))
    assert sender.send_api(conn, x, mid) == "failed"
    sender.mark_handled(conn, mid)
    assert mid not in {r["id"] for r in sender.needs_attention(conn)}
    conn.execute("UPDATE messages SET status = 'approved' WHERE id = ?", (mid,))
    conn.commit()
    assert sender.send_api(conn, x, mid) == "failed"
    assert mid in {r["id"] for r in sender.needs_attention(conn)}
