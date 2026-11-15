import sqlite3
from collections import defaultdict
from typing import Any

from outreach.db import now


def _counts() -> dict[str, int]:
    return {"new": 0, "existing": 0, "checked": 0}


def store_x_user(
    conn: sqlite3.Connection,
    u: dict[str, Any],
    campaign_id: int,
    source: str,
    posts: list[dict[str, Any]] | None = None,
) -> str:
    """Save one X user as a prospect with optional recent posts as evidence."""
    username = str(u.get("username") or "").strip().lstrip("@")
    if not username:
        return "existing"
    prospect_id = f"x:{u['id']}"

    known = conn.execute(
        "SELECT 1 FROM prospects WHERE id = ? OR x_username = ? COLLATE NOCASE",
        (prospect_id, username),
    ).fetchone()
    if known:
        return "existing"

    can_dm = 1 if u.get("receives_your_dm") else (0 if u.get("receives_your_dm") is False else None)

    try:
        with conn:
            conn.execute(
                """INSERT INTO prospects (id, github_login, x_username, x_user_id, name, bio, location,
                       company, followers, can_dm, campaign_id, source, fetched_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    prospect_id,
                    "",  # github_login is empty for X native prospects
                    username,
                    str(u["id"]),
                    u.get("name") or username,
                    u.get("description") or "",
                    u.get("location") or "",
                    "",  # company
                    u.get("followers", 0),
                    can_dm,
                    campaign_id,
                    source,
                    now(),
                ),
            )
            if posts:
                for p in posts:
                    conn.execute(
                        """INSERT OR IGNORE INTO repos (source_id, prospect_id, name, description, topics,
                               stars, pushed_at, url)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                        (
                            f"post:{p['id']}",
                            prospect_id,
                            f"post:{p['id']}",
                            p.get("text", ""),
                            "[]",
                            0,
                            p.get("created_at"),
                            f"https://x.com/{username}/status/{p['id']}",
                        ),
                    )
    except sqlite3.IntegrityError:
        return "existing"
    return "new"


def discover_by_x_search(
    conn: sqlite3.Connection,
    x,
    campaign_id: int,
    query: str,
    max_results: int = 10,
) -> dict[str, int]:
    """Search recent posts on X by query and store matching users and their posts."""
    counts = _counts()
    try:
        posts, users = x.search_recent(query=query, max_results=max_results)
    except Exception:
        raise

    posts_by_author: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for p in posts:
        posts_by_author[str(p.get("author_id"))].append(p)

    for u in users:
        counts["checked"] += 1
        author_id = str(u.get("id"))
        u_posts = posts_by_author.get(author_id)
        if not u_posts:
            try:
                u_posts = x.user_posts(author_id, max_results=3)
            except Exception:
                u_posts = []
        status = store_x_user(conn, u, campaign_id, f"x_search:{query}", u_posts)
        counts[status] += 1

    return counts


def discover_by_x_seeds(
    conn: sqlite3.Connection,
    x,
    campaign_id: int,
    seed_usernames: list[str],
    max_people: int = 20,
) -> dict[str, int]:
    """Discover people followed by seed accounts on X."""
    counts = _counts()
    cleaned = [s.strip().lstrip("@") for s in seed_usernames if s.strip()]
    if not cleaned:
        return counts

    seeds = x.users_by_usernames(cleaned)
    for s in seeds:
        seed_id = str(s["id"])
        seed_name = s.get("username", seed_id)
        try:
            following = x.following(seed_id, max_results=min(max_people * 2, 100))
        except Exception:
            continue

        for u in following:
            counts["checked"] += 1
            u_id = str(u.get("id"))
            try:
                posts = x.user_posts(u_id, max_results=2)
            except Exception:
                posts = []
            status = store_x_user(conn, u, campaign_id, f"x_seed:{seed_name}", posts)
            counts[status] += 1
            if counts["new"] >= max_people:
                break
        if counts["new"] >= max_people:
            break

    return counts


def import_x_usernames(
    conn: sqlite3.Connection,
    x,
    campaign_id: int,
    usernames: list[str],
) -> dict[str, int]:
    """Look up specific X users and store them as prospects."""
    counts = _counts()
    cleaned = [u.strip().lstrip("@") for u in usernames if u.strip()]
    if not cleaned:
        return counts

    users = x.users_by_usernames(cleaned)
    for u in users:
        counts["checked"] += 1
        u_id = str(u.get("id"))
        try:
            posts = x.user_posts(u_id, max_results=3)
        except Exception:
            posts = []
        status = store_x_user(conn, u, campaign_id, "x_import", posts)
        counts[status] += 1

    return counts
