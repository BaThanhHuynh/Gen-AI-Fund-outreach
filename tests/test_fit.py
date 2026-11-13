import json

from outreach import fit
from outreach.db import now

TODAY = "2026-11-13"


def repo(name, description=None, topics=(), stars=0, pushed_at="2025-01-01T00:00:00Z"):
    return {"source_id": f"repo:dev/{name}", "name": name, "description": description,
            "topics": list(topics), "stars": stars, "pushed_at": pushed_at,
            "url": f"https://github.com/dev/{name}"}


def test_bio_keyword_scores_and_cites_bio():
    r = fit.score_fit({"bio": "I build Robotics systems", "location": "Paris"}, [], ["robotics"], TODAY)
    assert r["score"] == 20
    assert [x["source_id"] for x in r["reasons"]] == ["bio"]


def test_repo_keyword_cites_repo_source():
    repos = [repo("drones", "Machine learning for drones"), repo("dotfiles", "my config")]
    r = fit.score_fit({"bio": None, "location": None}, repos, ["machine learning"], TODAY)
    assert r["score"] == 15
    assert [x["source_id"] for x in r["reasons"]] == ["repo:dev/drones"]


def test_score_capped_at_100():
    prospect = {"bio": "robotics and machine learning, ai", "location": "Hanoi, Vietnam"}
    repos = [repo(f"r{i}", "robotics toolkit", stars=100, pushed_at="2026-11-01T00:00:00Z")
             for i in range(4)]
    r = fit.score_fit(prospect, repos, ["robotics", "machine learning", "ai"], TODAY)
    assert r["score"] == 100


def test_no_keyword_scores_zero():
    prospect = {"bio": "Web developer", "location": "Ho Chi Minh City, Vietnam"}
    repos = [repo("shop", "online store", stars=900, pushed_at="2026-11-10T00:00:00Z")]
    r = fit.score_fit(prospect, repos, ["robotics"], TODAY)
    assert r["score"] == 0


def test_category_founder_researcher_builder():
    def cat(bio, company=None):
        return fit.score_fit({"bio": bio, "company": company}, [], ["x"], TODAY)["category"]
    assert cat("Co-founder at RoboCo") == "founder"
    assert cat("PhD, founder of a lab spinout") == "founder"   # founder wins over researcher
    assert cat("Robot learning", company="CTO @ Acme") == "founder"
    assert cat("Research scientist in vision") == "researcher"
    assert cat("Director of engineering") == "builder"          # 'cto' inside 'director' must not match


def test_keyword_match_is_word_boundary():
    assert fit.keyword_hits("open-source maintainer", ["ai"]) == []
    assert fit.keyword_hits("she said so", ["ai"]) == []
    assert fit.keyword_hits("Building AI tools", ["ai"]) == ["ai"]
    # any whitespace between words; a blank keyword must not match everything
    assert fit.keyword_hits("Machine\n Learning", ["machine learning", " "]) == ["machine learning"]


def test_keyword_with_symbols_matches_whole_word():
    assert fit.keyword_hits("I write C++ and .NET services", ["c++", ".net", "c#"]) == ["c++", ".net"]
    assert fit.keyword_hits("abc++ tools", ["c++"]) == []


def test_score_campaign_writes_scores(conn, campaign_id):
    conn.execute("UPDATE campaigns SET keywords = 'robotics, ai' WHERE id = ?", (campaign_id,))
    conn.execute(
        "INSERT INTO prospects (id, github_login, x_username, bio, location, campaign_id, source, fetched_at) "
        "VALUES ('gh:1', 'a', 'a_x', 'Robotics founder', 'Hanoi', ?, 'import', ?)", (campaign_id, now()))
    conn.commit()

    assert fit.score_campaign(conn, campaign_id, today=TODAY) == 1

    row = conn.execute("SELECT fit_score, fit_category, fit_reasons FROM prospects").fetchone()
    assert row["fit_score"] == 30 and row["fit_category"] == "founder"
    assert {x["source_id"] for x in json.loads(row["fit_reasons"])} == {"bio", "location"}
