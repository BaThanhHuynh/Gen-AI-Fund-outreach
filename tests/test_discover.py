import pytest

from outreach import discover
from outreach.db import now
from outreach.github import FakeGitHub


@pytest.fixture
def cid(conn):
    conn.execute(
        "INSERT INTO campaigns (name, segment, keywords, sender_context, created_at) "
        "VALUES ('c', 'seg', 'robotics', 'ctx', ?)",
        (now(),),
    )
    conn.commit()
    return conn.execute("SELECT id FROM campaigns").fetchone()[0]


def person(gh_id, x=None, bio="robotics", following=(), with_repo=False):
    login = f"user{gh_id}"
    repos = []
    if with_repo:
        repos = [{"source_id": f"repo:{login}/robo", "name": "robo", "description": "d",
                  "topics": [], "stars": 1, "pushed_at": None,
                  "url": f"https://github.com/{login}/robo"}]
    return {"gh_id": gh_id, "login": login, "name": login.title(), "bio": bio,
            "location": "Vietnam", "company": None, "followers": 10, "x_username": x,
            "repos": repos, "following": list(following)}


def fake(users):
    """FakeGitHub keyed by login; the dict key is the login."""
    return FakeGitHub(users={login: p for login, p in users.items()})


def test_search_queries_quote_multiword():
    qs = discover.search_queries(["machine learning"], ["Ho Chi Minh", "Vietnam"])
    assert qs == [
        '"machine learning" in:bio location:"Ho Chi Minh"',
        '"machine learning" in:bio location:Vietnam',
    ]


def test_people_without_x_handle_are_skipped_and_counted(conn, cid):
    gh = fake({"a": person(1), "b": person(2, x="bee")})
    res = discover.discover_by_segment(conn, gh, cid, ["robotics"])
    assert res["checked"] == 2
    assert res["no_x_handle"] == 1
    assert res["new"] == 1


def test_segment_saves_prospect_with_repos(conn, cid):
    gh = fake({"alex": person(1, x="alex_builder", with_repo=True)})
    discover.discover_by_segment(conn, gh, cid, ["robotics"])
    row = conn.execute("SELECT id, x_username, source, can_dm FROM prospects").fetchone()
    assert row["id"] == "gh:1"
    assert row["x_username"] == "alex_builder"
    assert row["source"].startswith("segment:")
    assert row["can_dm"] is None
    assert conn.execute("SELECT COUNT(*) FROM repos").fetchone()[0] == 1


def test_known_prospect_not_overwritten(conn, cid):
    users = {"alex": person(1, x="alex_builder")}
    gh = fake(users)
    discover.discover_by_segment(conn, gh, cid, ["robotics"])
    conn.execute("UPDATE prospects SET do_not_contact = 1")
    conn.commit()

    users["alex"]["name"] = "Changed Name"
    res = discover.discover_by_segment(conn, FakeGitHub(users={"alex": users["alex"]}),
                                       cid, ["robotics"])
    row = conn.execute("SELECT name, do_not_contact FROM prospects").fetchone()
    assert res["new"] == 0
    assert res["existing"] == 1
    assert row["do_not_contact"] == 1
    assert row["name"] == "User1"


def test_same_x_handle_from_two_github_accounts_is_one_prospect(conn, cid):
    gh = fake({"alt1": person(1, x="Same_X"), "alt2": person(2, x="same_x")})
    res = discover.discover_by_segment(conn, gh, cid, ["robotics"])
    assert res["new"] == 1
    assert res["existing"] == 1
    assert conn.execute("SELECT COUNT(*) FROM prospects").fetchone()[0] == 1


def test_import_logins_adds_exact_accounts(conn, cid):
    gh = fake({"a": person(1, x="aa"), "b": person(2, x="bb")})
    res = discover.import_logins(conn, gh, cid, ["a"])
    assert res["new"] == 1
    assert res["checked"] == 1
    row = conn.execute("SELECT source, x_username FROM prospects").fetchone()
    assert row["source"] == "import"
    assert row["x_username"] == "aa"


def test_seed_scores_degree_normalized():
    scores = discover.seed_scores({"s1": ["a", "b"], "s2": ["a", "c", "d", "e"]}, min_seeds=2)
    assert scores == [("a", 0.75)]


def test_discover_by_seeds_uses_following(conn, cid):
    gh = fake({
        "s1": person(1, following=["a", "b"]),
        "s2": person(2, following=["a", "c"]),
        "a": person(3, x="ax"),
        "b": person(4, x="bx"),
        "c": person(5, x="cx"),
    })
    res = discover.discover_by_seeds(conn, gh, cid, ["s1", "s2"], min_seeds=2)
    assert res["new"] == 1
    row = conn.execute("SELECT x_username, source FROM prospects").fetchone()
    assert row["x_username"] == "ax"
    assert row["source"].startswith("seed:")


def test_discovery_stops_at_max_people(conn, cid):
    gh = fake({f"u{i}": person(i, x=f"x{i}") for i in range(1, 8)})
    res = discover.discover_by_segment(conn, gh, cid, ["robotics"], max_people=3)
    assert res["new"] == 3
    assert conn.execute("SELECT COUNT(*) FROM prospects").fetchone()[0] == 3


def test_rate_limit_mid_run_keeps_saved_people(conn, cid):
    from outreach.github import GitHubRateLimited

    class LimitedAfterTwo(FakeGitHub):
        calls = 0

        def user(self, login):
            self.calls += 1
            if self.calls == 3:
                raise GitHubRateLimited(403, "rate limited", 1700000000)
            return super().user(login)

    gh = LimitedAfterTwo(users={f"user{i}": person(i, x=f"x{i}", with_repo=True) for i in (1, 2, 3)})
    with pytest.raises(GitHubRateLimited):
        discover.discover_by_segment(conn, gh, cid, ["robotics"])
    assert conn.execute("SELECT COUNT(*) FROM prospects").fetchone()[0] == 2
    assert conn.execute("SELECT COUNT(*) FROM repos").fetchone()[0] == 2


def test_repo_already_saved_for_someone_else_counts_existing(conn, cid):
    """A clash on repos.source_id (renamed login, or two runs at once) must not abort the run."""
    a, b, c = person(1, x="xa", with_repo=True), person(2, x="xb", with_repo=True), person(3, x="xc")
    b["repos"] = [dict(a["repos"][0])]          # same source_id as a's repo
    gh = fake({"user1": a, "user2": b, "user3": c})
    res = discover.discover_by_segment(conn, gh, cid, ["robotics"])
    assert res == {"new": 2, "existing": 1, "no_x_handle": 0, "checked": 3}
    assert {r[0] for r in conn.execute("SELECT id FROM prospects")} == {"gh:1", "gh:3"}
