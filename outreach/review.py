import sqlite3

EDITABLE = ("draft", "rejected", "failed")
REJECTABLE = ("draft", "approved", "failed")


def _status(conn: sqlite3.Connection, message_id: int) -> sqlite3.Row:
    row = conn.execute("SELECT status, evidence_ok, edited FROM messages WHERE id = ?",
                       (message_id,)).fetchone()
    if row is None:
        raise ValueError(f"message {message_id} not found")
    return row


def _update_if(conn, message_id: int, allowed: tuple[str, ...], sql_set: str, params: tuple) -> int:
    """Change one message only while its status is still one of `allowed` (safe against a parallel click)."""
    marks = ",".join("?" * len(allowed))
    with conn:
        cur = conn.execute(f"UPDATE messages SET {sql_set} WHERE id = ? AND status IN ({marks})",
                           (*params, message_id, *allowed))
    return cur.rowcount


def set_text(conn: sqlite3.Connection, message_id: int, text: str) -> None:
    if not text.strip():
        raise ValueError("message text is empty")
    if _update_if(conn, message_id, EDITABLE, "text = ?, edited = 1", (text.strip(),)) != 1:
        raise ValueError(f"cannot edit a message with status {_status(conn, message_id)['status']}")


def approve(conn: sqlite3.Connection, message_id: int) -> str | None:
    """None when approved; otherwise the reason it was not."""
    row = _status(conn, message_id)
    if row["status"] not in EDITABLE:
        return f"cannot approve from status {row['status']}"
    if not row["evidence_ok"] and not row["edited"]:
        return "evidence not verified — edit the text first"
    if _update_if(conn, message_id, EDITABLE, "status = 'approved'", ()) != 1:
        return f"cannot approve from status {_status(conn, message_id)['status']}"
    return None


def reject(conn: sqlite3.Connection, message_id: int) -> None:
    if _update_if(conn, message_id, REJECTABLE, "status = 'rejected'", ()) != 1:
        raise ValueError(f"cannot reject a message with status {_status(conn, message_id)['status']}")
