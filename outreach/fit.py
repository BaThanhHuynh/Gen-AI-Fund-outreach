import json
import re
import sqlite3
from datetime import date

from outreach import config
from outreach.db import now

BIO_POINTS, BIO_MAX = 20, 40
REPO_POINTS, REPO_MAX = 15, 45
ACTIVE_POINTS, ACTIVE_DAYS = 10, 90
STARS_POINTS, STARS_MIN = 5, 50
LOCATION_POINTS = 10

CATEGORIES = [
    ("founder", re.compile(r"\b(?:founder|co-?founder|ceo|cto)\b")),
    ("researcher", re.compile(r"\b(?:phd|researcher|professor|postdoc|research scientist)\b")),
]


def sources_for(prospect: dict, repos: list[dict]) -> dict[str, str]:
    """Texts a draft may quote, keyed by source_id. Empty sources are left out."""
    out = {"bio": prospect.get("bio") or "", "location": prospect.get("location") or ""}
    for r in repos:
        desc = (r.get("description") or "").strip()
        out[r["source_id"]] = f"{r['name']}: {desc}" if desc else r["name"]
    return {k: v for k, v in out.items() if v.strip()}


def keyword_hits(text: str | None, keywords: list[str]) -> list[str]:
    """Keywords found in text: case-insensitive, whole words only, any whitespace between words."""
    text = (text or "").casefold()
    hits = []
    for kw in keywords:
        words = kw.casefold().split()
        if words and re.search(r"\b" + r"\s+".join(map(re.escape, words)) + r"\b", text):
            hits.append(kw.strip())
    return hits


def _repo_text(r: dict) -> str:
    # names and topics are identifiers like "robot-arm" or "machine_learning"
    ident = " ".join([r["name"], *(r.get("topics") or [])]).replace("-", " ").replace("_", " ")
    return f"{ident} {r.get('description') or ''}"


def score_fit(prospect: dict, repos: list[dict], keywords: list[str], today: str) -> dict:
    """Rule-based fit score 0..100 with one reason per piece of evidence. No keyword hit means 0."""
    who = f"{prospect.get('bio') or ''} {prospect.get('company') or ''}".casefold()
    category = next((name for name, rx in CATEGORIES if rx.search(who)), "builder")

    reasons, score = [], 0
    bio_hits = keyword_hits(prospect.get("bio"), keywords)
    if bio_hits:
        score += min(BIO_POINTS * len(bio_hits), BIO_MAX)
        reasons.append({"claim": f"Bio mentions {', '.join(bio_hits)}", "source_id": "bio"})

    repo_points = 0
    for r in sorted(repos, key=lambda r: -(r.get("stars") or 0)):
        hits = keyword_hits(_repo_text(r), keywords)
        if hits:
            repo_points += REPO_POINTS
            reasons.append({"claim": f"Repo {r['name']} is about {', '.join(hits)}",
                            "source_id": r["source_id"]})
    if not reasons:
        return {"score": 0, "category": category, "reasons": []}
    score += min(repo_points, REPO_MAX)

    day = date.fromisoformat(today[:10])
    active = [r for r in repos if r.get("pushed_at")
              and (day - date.fromisoformat(r["pushed_at"][:10])).days <= ACTIVE_DAYS]
    if active:
        score += ACTIVE_POINTS
        reasons.append({"claim": f"Pushed code to {active[0]['name']} in the last {ACTIVE_DAYS} days",
                        "source_id": active[0]["source_id"]})

    top = max(repos, key=lambda r: r.get("stars") or 0, default=None)
    if top and (top.get("stars") or 0) >= STARS_MIN:
        score += STARS_POINTS
        reasons.append({"claim": f"{top['name']} has {top['stars']} stars", "source_id": top["source_id"]})

    loc = keyword_hits(prospect.get("location"), config.SEA_LOCATIONS)
    if loc:
        score += LOCATION_POINTS
        reasons.append({"claim": f"Based in {loc[0]}", "source_id": "location"})

    return {"score": min(score, 100), "category": category, "reasons": reasons}


def repos_of(conn: sqlite3.Connection, prospect_id: str) -> list[dict]:
    rows = conn.execute("SELECT * FROM repos WHERE prospect_id = ? ORDER BY source_id", (prospect_id,))
    return [{**dict(r), "topics": json.loads(r["topics"])} for r in rows]


def score_campaign(conn: sqlite3.Connection, campaign_id: int, today: str | None = None) -> int:
    """Score every prospect of the campaign; returns how many were scored."""
    today = today or now()[:10]
    row = conn.execute("SELECT keywords FROM campaigns WHERE id = ?", (campaign_id,)).fetchone()
    keywords = [k.strip() for k in row["keywords"].split(",") if k.strip()]
    prospects = conn.execute("SELECT * FROM prospects WHERE campaign_id = ?", (campaign_id,)).fetchall()
    with conn:
        for p in prospects:
            f = score_fit(dict(p), repos_of(conn, p["id"]), keywords, today)
            conn.execute("UPDATE prospects SET fit_score = ?, fit_category = ?, fit_reasons = ? WHERE id = ?",
                         (f["score"], f["category"], json.dumps(f["reasons"]), p["id"]))
    return len(prospects)
