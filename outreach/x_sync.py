import sqlite3
from typing import Any

from outreach import sender


def sync_x_replies(conn: sqlite3.Connection, x) -> dict[str, Any]:
    """Fetch recent DM events from X API and match incoming replies against sent messages.

    Automatically marks replied messages and moves them to needs_attention.
    Returns: {'checked_events': int, 'new_replies': int, 'replied_users': list[str]}.
    """
    try:
        me = x.me()
        my_id = str(me.get("id"))
    except Exception:
        my_id = ""

    # Find sent messages that haven't been marked as replied yet
    sent_messages = conn.execute(
        """SELECT m.id, m.prospect_id, m.dm_conversation_id, p.x_user_id, p.x_username
           FROM messages m
           JOIN prospects p ON p.id = m.prospect_id
           WHERE m.status = 'sent' AND m.replied_at IS NULL"""
    ).fetchall()

    if not sent_messages:
        return {"checked_events": 0, "new_replies": 0, "replied_users": []}

    by_user_id = {str(m["x_user_id"]): m for m in sent_messages if m["x_user_id"]}
    by_conv_id = {str(m["dm_conversation_id"]): m for m in sent_messages if m["dm_conversation_id"]}

    try:
        events = x.dm_events()
    except Exception as e:
        return {"checked_events": 0, "new_replies": 0, "replied_users": [], "error": str(e)}

    new_replies = 0
    replied_users = []

    for ev in events:
        sender_id = str(ev.get("sender_id"))
        if my_id and sender_id == my_id:
            continue  # Outgoing message from us

        conv_id = str(ev.get("dm_conversation_id") or "")
        match = by_user_id.get(sender_id) or (by_conv_id.get(conv_id) if conv_id else None)
        if match:
            mid = match["id"]
            username = match["x_username"]
            reply_text = str(ev.get("text") or "Replied on X")
            try:
                sender.mark_replied(conn, mid, reply_text)
                new_replies += 1
                replied_users.append(username)
                # Remove from lookup so multiple events for same user don't double count
                if str(match["x_user_id"]) in by_user_id:
                    del by_user_id[str(match["x_user_id"])]
                if conv_id and conv_id in by_conv_id:
                    del by_conv_id[conv_id]
            except Exception:
                pass

    return {
        "checked_events": len(events),
        "new_replies": new_replies,
        "replied_users": replied_users,
    }
