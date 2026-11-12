import inspect

import httpx
import pytest

from outreach import config
from outreach.github import (
    FakeGitHub,
    GitHubAuthError,
    GitHubClient,
    GitHubError,
    GitHubRateLimited,
)


@pytest.fixture(autouse=True)
def token(monkeypatch):
    monkeypatch.setattr(config, "GITHUB_TOKEN", "tok")


def client(handler):
    return GitHubClient(transport=httpx.MockTransport(handler))


USER = {"id": 7, "login": "al", "name": "Al", "bio": None, "location": None,
        "company": None, "followers": 3}


def test_search_users_paginates_and_caps():
    pages = []

    def handler(req):
        assert req.url.params["per_page"] == "100"
        page = int(req.url.params["page"])
        pages.append(page)
        return httpx.Response(200, json={"items": [{"login": f"u{page}_{i}"} for i in range(100)]})

    out = client(handler).search_users('"robotics" in:bio', limit=150)
    assert len(out) == 150
    assert pages == [1, 2]


def test_user_normalizes_x_handle():
    def handler(req):
        return httpx.Response(200, json={**USER, "twitter_username": " @Alice_X "})

    u = client(handler).user("al")
    assert u["x_username"] == "Alice_X"
    assert u["gh_id"] == 7


def test_user_falls_back_to_social_accounts():
    def handler(req):
        if req.url.path == "/users/al":
            return httpx.Response(200, json={**USER, "twitter_username": ""})
        if req.url.path == "/users/al/social_accounts":
            return httpx.Response(200, json=[
                {"provider": "generic", "url": "https://github.com/al"},
                {"provider": "generic", "url": "https://x.com/bob"},
            ])
        raise AssertionError(req.url.path)

    assert client(handler).user("al")["x_username"] == "bob"


def test_user_without_any_x_handle():
    def handler(req):
        if req.url.path == "/users/al":
            return httpx.Response(200, json={**USER, "twitter_username": None})
        return httpx.Response(200, json=[])

    assert client(handler).user("al")["x_username"] is None


def test_user_returns_none_on_404():
    assert client(lambda req: httpx.Response(404, json={})).user("nobody") is None


def test_repos_skips_forks_and_builds_source_ids():
    repos = [
        {"name": "a", "full_name": "bob/a", "fork": False, "description": "d",
         "topics": ["ml"], "stargazers_count": 5, "pushed_at": "2026-01-01T00:00:00Z",
         "html_url": "https://github.com/bob/a"},
        {"name": "f", "full_name": "bob/f", "fork": True, "description": None,
         "topics": [], "stargazers_count": 0, "pushed_at": None,
         "html_url": "https://github.com/bob/f"},
    ]
    out = client(lambda req: httpx.Response(200, json=repos)).repos("bob")
    assert len(out) == 1
    assert out[0]["source_id"] == "repo:bob/a"
    assert out[0]["stars"] == 5
    assert out[0]["topics"] == ["ml"]


@pytest.mark.parametrize("status", [403, 429])
def test_rate_limited_raises_with_reset(status):
    def handler(req):
        return httpx.Response(status, json={"message": "limit"},
                              headers={"x-ratelimit-remaining": "0",
                                       "x-ratelimit-reset": "1700000000"})

    with pytest.raises(GitHubRateLimited) as e:
        client(handler).user("bob")
    assert e.value.reset_at == 1700000000


def test_bad_token_raises_autherror():
    with pytest.raises(GitHubAuthError):
        client(lambda req: httpx.Response(401, json={"message": "Bad credentials"})).user("bob")


def test_server_error_is_plain_githuberror():
    with pytest.raises(GitHubError) as e:
        client(lambda req: httpx.Response(500, text="boom")).user("bob")
    assert not isinstance(e.value, (GitHubRateLimited, GitHubAuthError))


def test_token_sent_as_bearer_header():
    seen = {}

    def handler(req):
        seen["auth"] = req.headers["authorization"]
        seen["url"] = str(req.url)
        return httpx.Response(200, json=USER | {"twitter_username": "x"})

    client(handler).user("al")
    assert seen["auth"] == "Bearer tok"
    assert "tok" not in seen["url"]


def test_fake_github_has_same_methods():
    for name in ["search_users", "user", "repos", "following"]:
        assert str(inspect.signature(getattr(FakeGitHub, name))) == \
            str(inspect.signature(getattr(GitHubClient, name)))
