import sqlite3
from datetime import datetime, timedelta, timezone

from outreach import config
from outreach.db import now
from outreach.xclient import Ambiguous, Forbidden, RateLimited, XError

class SendBlocked(Exception):
    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


def _ts(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def _ago(seconds: int) -> datetime:
    return datetime.now(timezone.utc) - timedelta(seconds=seconds)


def _get(conn, message_id: int) -> sqlite3.Row:
    row = conn.execute(
        "SELECT m.*, p.x_username, p.x_user_id, p.can_dm, p.do_not_contact FROM messages m "
        "JOIN prospects p ON p.id = m.prospect_id WHERE m.id = ?", (message_id,)).fetchone()
    if row is None:
        raise ValueError(f"message {message_id} not found")
    return row


def _move(conn, message_id: int, where: str, sql_set: str, params: tuple = ()) -> bool:
    """Guarded single UPDATE: changes the message only while `where` still holds. True when it did."""
    with conn:
        cur = conn.execute(f"UPDATE messages SET {sql_set} WHERE id = ? AND {where}", (*params, message_id))
    return cur.rowcount == 1


def _allowed(username: str) -> bool:
    return username.casefold() in {a.casefold() for a in config.SEND_ALLOWLIST}


def sends_in_last_24h(conn) -> int:
    cutoff = _ago(24 * 3600)
    rows = conn.execute("SELECT claimed_at FROM messages WHERE status IN ('sending','sent','unknown') "
                        "AND claimed_at IS NOT NULL").fetchall()
    return sum(1 for r in rows if _ts(r["claimed_at"]) >= cutoff)


def check_can_send(conn, message_id: int) -> str | None:
    """None when the message may be sent; otherwise the first reason it may not."""
    m = _get(conn, message_id)
    if m["status"] != "approved":
        return "not approved"
    if m["do_not_contact"]:
        return "marked do-not-contact"
    if m["can_dm"] == 0:
        return "recipient does not accept DMs from this account"
    if config.SEND_MODE == "allowlist" and not _allowed(m["x_username"]):
        return "not on SEND_ALLOWLIST (safety mode)"
    n = sends_in_last_24h(conn)
    if n >= config.DAILY_SEND_CAP:
        return f"daily cap reached ({n}/{config.DAILY_SEND_CAP})"
    return None


def claim(conn, message_id: int, channel: str) -> bool:
    """approved -> sending in one UPDATE, committed before the caller does anything else.
    A new attempt clears handled_at so its outcome shows up in needs_attention again."""
    return _move(conn, message_id, "status = 'approved'",
                 "status = 'sending', channel = ?, claimed_at = ?, handled_at = NULL", (channel, now()))


def open_manual(conn, message_id: int) -> dict:
    reason = check_can_send(conn, message_id)
    if reason:
        raise SendBlocked(reason)
    if not claim(conn, message_id, "manual"):
        raise SendBlocked("not approved")  # lost a race with another click
    m = _get(conn, message_id)
    return {"url": f"https://x.com/{m['x_username']}", "text": m["text"]}


def confirm_manual(conn, message_id: int, outcome: str) -> str:
    changes = {
        "sent": ("sent", "status = 'sent', sent_at = ?", (now(),)),
        "not_sent": ("approved", "status = 'approved', claimed_at = NULL, channel = NULL", ()),
        "existing": ("blocked", "status = 'blocked', error = 'existing conversation'", ()),
    }
    if outcome not in changes:
        raise ValueError(f"unknown outcome {outcome!r}")
    status, sql_set, params = changes[outcome]
    if not _move(conn, message_id, "status = 'sending' AND channel = 'manual'", sql_set, params):
        raise ValueError("message is not a manual send waiting for confirmation")
    return status


def _finish(conn, message_id: int, status: str, error: str | None = None, **extra) -> str:
    cols = {"status": status, "error": error, **extra}
    _move(conn, message_id, "status = 'sending'", ", ".join(f"{k} = ?" for k in cols), tuple(cols.values()))
    return status


def _release(conn, message_id: int) -> None:
    _move(conn, message_id, "status = 'sending'", "status = 'approved', claimed_at = NULL, channel = NULL")


def send_api(conn, x, message_id: int) -> str:
    m = _get(conn, message_id)
    if not _allowed(m["x_username"]):
        raise SendBlocked("api channel is limited to SEND_ALLOWLIST (X automation rules)")
    reason = check_can_send(conn, message_id)
    if reason:
        raise SendBlocked(reason)
    if not claim(conn, message_id, "api"):
        raise SendBlocked("not approved")
    m = _get(conn, message_id)  # send exactly the text that was claimed

    user_id = m["x_user_id"]
    try:
        if not user_id:
            found = x.users_by_usernames([m["x_username"]])
            if not found:
                return _finish(conn, message_id, "blocked", "X account not found")
            can_dm = found[0].get("receives_your_dm")
            user_id = found[0]["id"]
            with conn:
                conn.execute("UPDATE prospects SET x_user_id = ?, can_dm = ? WHERE id = ?",
                             (user_id, None if can_dm is None else int(bool(can_dm)), m["prospect_id"]))
            if can_dm is not None and not can_dm:
                return _finish(conn, message_id, "blocked", "recipient does not accept DMs from this account")
        if x.dm_events_with(user_id, 1):
            return _finish(conn, message_id, "blocked", "existing conversation")
    except Exception:
        _release(conn, message_id)  # nothing was sent: safe to retry later
        raise

    try:
        res = x.send_dm(user_id, m["text"])
    except Forbidden as e:
        return _finish(conn, message_id, "blocked", str(e))
    except RateLimited:
        _release(conn, message_id)
        return "approved"
    except Ambiguous as e:
        return _finish(conn, message_id, "unknown", str(e))
    except XError as e:  # 400, 401 (AuthError) and other client errors: certainly not sent
        return _finish(conn, message_id, "failed", str(e))
    return _finish(conn, message_id, "sent", None, dm_event_id=res["dm_event_id"],
                   dm_conversation_id=res["dm_conversation_id"], sent_at=now())


def recover_stuck(conn, older_than_s: int = 300) -> int:
    cutoff = _ago(older_than_s)
    rows = conn.execute("SELECT id, claimed_at FROM messages WHERE status = 'sending' AND channel = 'api'").fetchall()
    return sum(_move(conn, r["id"], "status = 'sending' AND channel = 'api'",
                     "status = 'unknown', error = 'no answer from X; check your X inbox'")
               for r in rows if r["claimed_at"] and _ts(r["claimed_at"]) < cutoff)


def resolve_unknown(conn, message_id: int, was_sent: bool) -> str:
    status = "sent" if was_sent else "failed"
    sql_set = "status = 'sent', sent_at = ?" if was_sent else "status = 'failed', error = 'user confirmed not sent'"
    if not _move(conn, message_id, "status = 'unknown'", sql_set, (now(),) if was_sent else ()):
        raise ValueError("message is not in status unknown")
    return status


def mark_replied(conn, message_id: int, note: str) -> None:
    if not _move(conn, message_id, "status = 'sent'", "reply_text = ?, replied_at = ?", (note, now())):
        raise ValueError("only a sent message can be marked replied")


def mark_handled(conn, message_id: int) -> None:
    if not _move(conn, message_id, "1 = 1", "handled_at = ?", (now(),)):
        raise ValueError(f"message {message_id} not found")


def set_do_not_contact(conn, prospect_id: str, value: bool) -> None:
    with conn:
        conn.execute("UPDATE prospects SET do_not_contact = ? WHERE id = ?", (int(value), prospect_id))


def needs_attention(conn) -> list[sqlite3.Row]:
    """Manual sends awaiting confirmation and unknown outcomes always; failed, blocked and replied until handled."""
    return conn.execute(
        "SELECT * FROM messages WHERE (status = 'sending' AND channel = 'manual') OR status = 'unknown' "
        "OR (status IN ('failed','blocked') AND handled_at IS NULL) "
        "OR (replied_at IS NOT NULL AND handled_at IS NULL) ORDER BY id").fetchall()
