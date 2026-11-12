import re
from typing import Any
from urllib.parse import urlparse

import httpx

from outreach import config

BASE = "https://api.github.com"
X_HANDLE_RE = re.compile(r"^[A-Za-z0-9_]{1,15}$")
X_HOSTS = {"x.com", "www.x.com", "twitter.com", "www.twitter.com"}


class GitHubError(Exception):
    def __init__(self, status: int, detail: str):
        super().__init__(f"GitHub {status}: {detail}")
        self.status = status
        self.detail = detail


class GitHubRateLimited(GitHubError):
    def __init__(self, status: int, detail: str, reset_at: int):
        super().__init__(status, detail)
        self.reset_at = reset_at


class GitHubAuthError(GitHubError):
    pass


def normalize_x_handle(raw: str | None) -> str | None:
    """Strip '@' and spaces; return the handle only if it is a valid X username (1-15 of A-Z, 0-9, _)."""
    if not raw:
        return None
    handle = "".join(raw.split()).lstrip("@")
    return handle if X_HANDLE_RE.match(handle) else None


def _x_from_social(accounts: list[dict[str, Any]]) -> str | None:
    for acc in accounts:
        parsed = urlparse(acc.get("url") or "")
        if parsed.netloc.lower() in X_HOSTS:
            handle = normalize_x_handle(parsed.path.strip("/").split("/")[0])
            if handle:
                return handle
    return None


class GitHubClient:
    def __init__(self, transport: httpx.BaseTransport | None = None):
        self.transport = transport

    def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        """GET one API path. Returns parsed JSON, or None on 404."""
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Authorization": f"Bearer {config.GITHUB_TOKEN}",
        }
        try:
            with httpx.Client(transport=self.transport, timeout=30.0) as client:
                r = client.get(f"{BASE}{path}", params=params, headers=headers)
        except httpx.HTTPError as e:
            raise GitHubError(0, f"lỗi mạng: {e}")
        if r.status_code == 404:
            return None
        if r.status_code == 401:
            raise GitHubAuthError(401, "token sai hoặc hết hạn")
        if r.status_code in (403, 429) and (
            r.headers.get("x-ratelimit-remaining") == "0" or "retry-after" in r.headers
        ):
            reset = int(r.headers.get("x-ratelimit-reset") or 0)
            raise GitHubRateLimited(r.status_code, "hết hạn mức", reset)
        if r.status_code >= 400:
            raise GitHubError(r.status_code, r.text[:200])
        return r.json()

    def rate_limit(self) -> dict[str, Any]:
        """GET /rate_limit (không tính vào hạn mức). Returns the core bucket."""
        return self._get("/rate_limit")["resources"]["core"]

    def search_users(self, query: str, limit: int = 100) -> list[str]:
        limit = min(limit, 1000)
        logins: list[str] = []
        page = 1
        while len(logins) < limit:
            data = self._get("/search/users", {"q": query, "per_page": 100, "page": page})
            items = (data or {}).get("items", [])
            logins.extend(item["login"] for item in items)
            if len(items) < 100:
                break
            page += 1
        return logins[:limit]

    def user(self, login: str) -> dict[str, Any] | None:
        data = self._get(f"/users/{login}")
        if data is None:
            return None
        x_username = normalize_x_handle(data.get("twitter_username"))
        if x_username is None:
            accounts = self._get(f"/users/{login}/social_accounts") or []
            x_username = _x_from_social(accounts)
        return {
            "gh_id": data["id"],
            "login": data["login"],
            "name": data.get("name"),
            "bio": data.get("bio"),
            "location": data.get("location"),
            "company": data.get("company"),
            "followers": data.get("followers"),
            "x_username": x_username,
        }

    def repos(self, login: str, limit: int = 5) -> list[dict[str, Any]]:
        data = self._get(f"/users/{login}/repos",
                         {"type": "owner", "sort": "pushed", "per_page": 30}) or []
        out = []
        for r in data:
            if r.get("fork"):
                continue
            out.append({
                "source_id": f"repo:{r['full_name']}",
                "name": r["name"],
                "description": r.get("description"),
                "topics": r.get("topics", []),
                "stars": r.get("stargazers_count", 0),
                "pushed_at": r.get("pushed_at"),
                "url": r["html_url"],
            })
            if len(out) == limit:
                break
        return out

    def following(self, login: str, limit: int = 500) -> list[str]:
        logins: list[str] = []
        page = 1
        while len(logins) < limit:
            items = self._get(f"/users/{login}/following", {"per_page": 100, "page": page}) or []
            logins.extend(item["login"] for item in items)
            if len(items) < 100:
                break
            page += 1
        return logins[:limit]


# Sample people for X_MODE=fake: 4 with an X name (2 match, 1 matches but repo doesn't
# describe it, 1 unrelated), 2 without one. search_users returns every sample login.
_SAMPLE_USERS: dict[str, dict[str, Any]] = {
    "fake_alex": {"gh_id": 9001, "name": "Alex Builder", "bio": "Robotics founder, ML",
                  "location": "Ho Chi Minh", "x_username": "alex_builder"},
    "fake_sarah": {"gh_id": 9002, "name": "Sarah Chen", "bio": "Robot learning researcher",
                   "location": "Hanoi", "x_username": "sarah_robotics"},
    "fake_minh": {"gh_id": 9003, "name": "Minh Tran", "bio": "Machine learning engineer",
                  "location": "Vietnam", "x_username": "minh_ml"},
    "fake_linh": {"gh_id": 9004, "name": "Linh Pham", "bio": "Frontend developer",
                  "location": "Vietnam", "x_username": "linh_front"},
    "fake_david": {"gh_id": 9005, "name": "David Kim", "bio": "Robotics hobbyist",
                   "location": "Singapore", "x_username": None},
    "fake_an": {"gh_id": 9006, "name": "An Nguyen", "bio": "Data analyst",
                "location": "Da Nang", "x_username": None},
}


class FakeGitHub:
    """Offline stand-in with the same methods as GitHubClient. Makes no network calls."""

    def __init__(self, users: dict[str, dict[str, Any]] | None = None):
        self.users = _SAMPLE_USERS if users is None else users

    def search_users(self, query: str, limit: int = 100) -> list[str]:
        return list(self.users)[:limit]

    def user(self, login: str) -> dict[str, Any] | None:
        p = self.users.get(login)
        if p is None:
            return None
        return {"gh_id": p["gh_id"], "login": login, "name": p.get("name"),
                "bio": p.get("bio"), "location": p.get("location"),
                "company": p.get("company"), "followers": p.get("followers", 10),
                "x_username": p.get("x_username")}

    def repos(self, login: str, limit: int = 5) -> list[dict[str, Any]]:
        return list(self.users.get(login, {}).get("repos", []))[:limit]

    def following(self, login: str, limit: int = 500) -> list[str]:
        return list(self.users.get(login, {}).get("following", []))[:limit]


def get_github() -> FakeGitHub | GitHubClient:
    return FakeGitHub() if config.X_MODE == "fake" else GitHubClient()
