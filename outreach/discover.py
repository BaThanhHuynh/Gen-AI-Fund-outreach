import json
import sqlite3
from collections import defaultdict

from outreach import config
from outreach.db import now


def search_queries(phrases: list[str], locations: list[str] = config.SEA_LOCATIONS) -> list[str]:
    """Build one GitHub user-search query per (phrase, location) pair."""
    out = []
    for phrase in phrases:
        for loc in locations:
            loc_q = f'"{loc}"' if " " in loc else loc
            out.append(f'"{phrase}" in:bio location:{loc_q}')
    return out


def _counts() -> dict[str, int]:
    return {"new": 0, "existing": 0, "no_x_handle": 0, "checked": 0}


def _store(conn: sqlite3.Connection, gh, campaign_id: int, login: str, source: str) -> str:
    """Save one GitHub user as a prospect. Returns 'new', 'existing' or 'no_x_handle'."""
    u = gh.user(login)
    if u is None or not u.get("x_username"):
        return "no_x_handle"
    prospect_id = f"gh:{u['gh_id']}"
    known = conn.execute(
        "SELECT 1 FROM prospects WHERE id = ? OR x_username = ? COLLATE NOCASE",
        (prospect_id, u["x_username"]),
    ).fetchone()
    if known:
        return "existing"
    repos = gh.repos(login, limit=5)
    try:
        with conn:
            conn.execute(
                """INSERT INTO prospects (id, github_login, x_username, name, bio, location,
                       company, followers, campaign_id, source, fetched_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (prospect_id, u["login"], u["x_username"], u["name"], u["bio"], u["location"],
                 u["company"], u["followers"], campaign_id, source, now()),
            )
            for r in repos:
                conn.execute(
                    """INSERT INTO repos (source_id, prospect_id, name, description, topics,
                           stars, pushed_at, url)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (r["source_id"], prospect_id, r["name"], r["description"],
                     json.dumps(r["topics"]), r["stars"], r["pushed_at"], r["url"]),
                )
    except sqlite3.IntegrityError:   # saved meanwhile by another run, or a repo owned by a renamed login
        return "existing"
    return "new"


def _run(conn, gh, campaign_id, logins, source, max_people) -> dict[str, int]:
    counts = _counts()
    seen: set[str] = set()
    for login in logins:
        if login in seen:
            continue
        seen.add(login)
        counts["checked"] += 1
        counts[_store(conn, gh, campaign_id, login, source)] += 1
        if counts["new"] >= max_people:
            break
    return counts


def discover_by_segment(conn, gh, campaign_id: int, phrases: list[str],
                        max_people: int = 30) -> dict[str, int]:
    counts = _counts()
    seen: set[str] = set()
    for query in search_queries(phrases):
        logins = [lg for lg in gh.search_users(query, limit=100) if lg not in seen]
        seen.update(logins)
        sub = _run(conn, gh, campaign_id, logins, f"segment:{query}",
                   max_people - counts["new"])
        for k in counts:
            counts[k] += sub[k]
        if counts["new"] >= max_people:
            break
    return counts


def import_logins(conn, gh, campaign_id: int, logins: list[str]) -> dict[str, int]:
    return _run(conn, gh, campaign_id, logins, "import", max_people=len(logins) or 1)


def seed_scores(following: dict[str, list[str]], min_seeds: int) -> list[tuple[str, float]]:
    """Rank candidates followed by the seeds: score = sum of 1/len(following[seed])."""
    seeds = set(following)
    score: dict[str, float] = defaultdict(float)
    hits: dict[str, int] = defaultdict(int)
    for seed, follows in following.items():
        if not follows:
            continue
        for cand in set(follows):
            if cand in seeds:
                continue
            score[cand] += 1 / len(follows)
            hits[cand] += 1
    ranked = [(c, s) for c, s in score.items() if hits[c] >= min_seeds]
    ranked.sort(key=lambda item: (-item[1], item[0]))
    return ranked


def discover_by_seeds(conn, gh, campaign_id: int, seed_logins: list[str],
                      min_seeds: int = 2, max_people: int = 30) -> dict[str, int]:
    if len(seed_logins) == 1:
        min_seeds = 1
    following = {s: gh.following(s, limit=500) for s in seed_logins}
    ranked = seed_scores(following, min_seeds)
    source = f"seed:{','.join(seed_logins)}"
    return _run(conn, gh, campaign_id, [c for c, _ in ranked], source, max_people)
