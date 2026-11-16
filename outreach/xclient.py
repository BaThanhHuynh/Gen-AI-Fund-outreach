import base64
import time
from typing import Any
import httpx
import sqlite3

from outreach import config
from outreach.db import kv_get, kv_set, record_usage


class XError(Exception):
    """Base exception for all X API errors."""

    def __init__(self, status: int, detail: str = ""):
        super().__init__(f"X API error {status}: {detail}")
        self.status = status
        self.detail = detail


class RateLimited(XError):
    """Raised when X returns HTTP 429 Too Many Requests."""

    def __init__(self, reset_at: int, detail: str = "Rate limit exceeded"):
        super().__init__(429, detail)
        self.reset_at = reset_at


class AuthError(XError):
    """Raised when authentication fails (HTTP 401, missing credentials, or refresh failure)."""

    def __init__(self, detail: str = "Authentication error"):
        super().__init__(401, detail)


class Forbidden(XError):
    """Raised when access is forbidden (HTTP 403, e.g. account suspended or blocked)."""

    def __init__(self, detail: str = "Forbidden"):
        super().__init__(403, detail)


class Ambiguous(XError):
    """Raised when network drops, timeout occurs, or server returns 5xx (execution status uncertain)."""

    def __init__(self, detail: str = "Ambiguous error", status: int = 0):
        super().__init__(status, detail)


class XClient:
    """Official X API v2 client with automatic PKCE token rotation and strict error handling."""

    def __init__(self, conn: sqlite3.Connection, transport: httpx.BaseTransport | None = None):
        self.conn = conn
        self.transport = transport

    def _get_valid_token(self) -> str:
        """Read token directly from kv on every call (no in-memory caching) and rotate if expired."""
        oauth = kv_get(self.conn, "oauth")
        if not oauth or not oauth.get("access_token"):
            raise AuthError("Not connected to X: no credentials found in kv['oauth']")

        expires_at = float(oauth.get("expires_at", 0))
        # Refresh if expired or expiring within 60 seconds
        if time.time() >= expires_at - 60:
            self._refresh_token(oauth.get("refresh_token"))
            oauth = kv_get(self.conn, "oauth")
            if not oauth or not oauth.get("access_token"):
                raise AuthError("Token refresh failed to store new credentials")

        return str(oauth["access_token"])

    def _refresh_token(self, refresh_token: str | None) -> None:
        """Call token endpoint with Basic auth header, and persist new rotated tokens BEFORE next request."""
        if not refresh_token:
            raise AuthError("Token refresh failed: missing refresh_token")

        client_id = config.X_CLIENT_ID
        client_secret = config.X_CLIENT_SECRET
        basic_creds = base64.b64encode(f"{client_id}:{client_secret}".encode("utf-8")).decode("ascii")

        headers = {
            "Authorization": f"Basic {basic_creds}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        }

        try:
            with httpx.Client(transport=self.transport, timeout=30.0) as client:
                resp = client.post("https://api.x.com/2/oauth2/token", headers=headers, data=data)
        except Exception as e:
            raise AuthError(f"Token refresh failed due to connection error: {e}")

        if resp.status_code != 200:
            raise AuthError(f"Token refresh failed ({resp.status_code}): {resp.text}")

        new_data = resp.json()
        expires_in = int(new_data.get("expires_in", 7200))
        persisted = {
            "access_token": new_data["access_token"],
            "refresh_token": new_data.get("refresh_token", refresh_token),
            "expires_at": time.time() + expires_in,
            "scope": new_data.get("scope", config.SCOPES),
        }
        # CRUCIAL: Persist rotated token to SQLite immediately before any subsequent API call
        kv_set(self.conn, "oauth", persisted)

    def _request(self, method: str, url: str, **kwargs) -> httpx.Response:
        """Execute HTTP request without automatic retry, strictly classifying responses."""
        token = self._get_valid_token()
        headers = dict(kwargs.pop("headers", {}))
        headers["Authorization"] = f"Bearer {token}"

        try:
            with httpx.Client(transport=self.transport, timeout=30.0) as client:
                resp = client.request(method, url, headers=headers, **kwargs)
        except (httpx.TimeoutException, httpx.NetworkError) as e:
            raise Ambiguous(f"Network error during request to {url}: {e}")
        except Exception as e:
            raise Ambiguous(f"Unexpected error during request to {url}: {e}")

        if resp.status_code == 401:
            raise AuthError(resp.text)
        elif resp.status_code == 403:
            raise Forbidden(resp.text)
        elif resp.status_code == 429:
            reset_header = resp.headers.get("x-rate-limit-reset", "0")
            try:
                reset_at = int(reset_header)
            except ValueError:
                reset_at = int(time.time() + 900)
            raise RateLimited(reset_at=reset_at, detail=resp.text)
        elif 400 <= resp.status_code < 500:
            raise XError(status=resp.status_code, detail=resp.text)
        elif resp.status_code >= 500:
            raise Ambiguous(detail=resp.text, status=resp.status_code)

        return resp

    def me(self) -> dict[str, str]:
        """Fetch authenticated user profile {id, username} and persist into kv['me']."""
        resp = self._request("GET", "https://api.x.com/2/users/me")
        data = resp.json().get("data", {})
        result = {"id": str(data["id"]), "username": str(data["username"])}
        kv_set(self.conn, "me", result)
        return result

    def search_recent(self, query: str, max_results: int = 10) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Search recent tweets (min 10, max 100) and return normalized (posts, users)."""
        params = {
            "query": query,
            "max_results": str(max_results),
            "expansions": "author_id",
            "tweet.fields": "id,author_id,text,created_at",
            "user.fields": "id,name,username,description,location,public_metrics,protected,receives_your_dm",
        }
        resp = self._request("GET", "https://api.x.com/2/tweets/search/recent", params=params)
        body = resp.json()

        raw_posts = body.get("data", [])
        raw_users = body.get("includes", {}).get("users", [])

        normalized_posts = [
            {
                "id": str(p["id"]),
                "author_id": str(p["author_id"]),
                "text": str(p["text"]),
                "created_at": p.get("created_at"),
            }
            for p in raw_posts
        ]

        normalized_users = [
            {
                "id": str(u["id"]),
                "username": str(u["username"]),
                "name": u.get("name"),
                "description": u.get("description"),
                "location": u.get("location"),
                "followers": u.get("public_metrics", {}).get("followers_count", 0)
                if isinstance(u.get("public_metrics"), dict)
                else 0,
                "protected": 1 if u.get("protected") else 0,
                "receives_your_dm": u.get("receives_your_dm"),
            }
            for u in raw_users
        ]

        record_usage(self.conn, "post_read", len(normalized_posts))
        record_usage(self.conn, "user_read", len(normalized_users))
        return normalized_posts, normalized_users

    def users_by_usernames(self, usernames: list[str]) -> list[dict[str, Any]]:
        """Look up user profiles by list of usernames (up to 100)."""
        cleaned = [u.lstrip("@") for u in usernames if u.strip()]
        if not cleaned:
            return []

        params = {
            "usernames": ",".join(cleaned),
            "user.fields": "id,name,username,description,location,public_metrics,protected,receives_your_dm",
        }
        resp = self._request("GET", "https://api.x.com/2/users/by", params=params)
        body = resp.json()
        raw_users = body.get("data", [])

        normalized_users = [
            {
                "id": str(u["id"]),
                "username": str(u["username"]),
                "name": u.get("name"),
                "description": u.get("description"),
                "location": u.get("location"),
                "followers": u.get("public_metrics", {}).get("followers_count", 0)
                if isinstance(u.get("public_metrics"), dict)
                else 0,
                "protected": 1 if u.get("protected") else 0,
                "receives_your_dm": u.get("receives_your_dm"),
            }
            for u in raw_users
        ]

        record_usage(self.conn, "user_read", len(normalized_users))
        return normalized_users

    def following(self, user_id: str, max_results: int = 100) -> list[dict[str, Any]]:
        """Get accounts that user_id is following (min 1, max 1000)."""
        params = {
            "max_results": str(max_results),
            "user.fields": "id,name,username,description,location,public_metrics,protected,receives_your_dm",
        }
        resp = self._request("GET", f"https://api.x.com/2/users/{user_id}/following", params=params)
        body = resp.json()
        raw_users = body.get("data", [])

        normalized_users = [
            {
                "id": str(u["id"]),
                "username": str(u["username"]),
                "name": u.get("name"),
                "description": u.get("description"),
                "location": u.get("location"),
                "followers": u.get("public_metrics", {}).get("followers_count", 0)
                if isinstance(u.get("public_metrics"), dict)
                else 0,
                "protected": 1 if u.get("protected") else 0,
                "receives_your_dm": u.get("receives_your_dm"),
            }
            for u in raw_users
        ]

        record_usage(self.conn, "user_read", len(normalized_users))
        return normalized_users

    def user_posts(self, user_id: str, max_results: int = 5) -> list[dict[str, Any]]:
        """Get recent original posts from a user, excluding retweets and replies (min 5, max 100)."""
        params = {
            "max_results": str(max(5, max_results)),  # X answers 400 below 5
            "exclude": "retweets,replies",
            "tweet.fields": "id,author_id,text,created_at",
        }
        resp = self._request("GET", f"https://api.x.com/2/users/{user_id}/tweets", params=params)
        body = resp.json()
        raw_posts = body.get("data", [])

        normalized_posts = [
            {
                "id": str(p["id"]),
                "author_id": str(p["author_id"]),
                "text": str(p["text"]),
                "created_at": p.get("created_at"),
            }
            for p in raw_posts
        ]

        record_usage(self.conn, "post_read", len(normalized_posts))
        return normalized_posts

    def send_dm(self, user_id: str, text: str) -> dict[str, str]:
        """Send Direct Message to participant and return {dm_event_id, dm_conversation_id}."""
        payload = {"text": text}
        resp = self._request(
            "POST",
            f"https://api.x.com/2/dm_conversations/with/{user_id}/messages",
            json=payload,
        )
        body = resp.json().get("data", {})
        result = {
            "dm_event_id": str(body.get("dm_event_id")),
            "dm_conversation_id": str(body.get("dm_conversation_id")),
        }
        record_usage(self.conn, "dm_send", 1)
        return result

    def dm_events_with(self, user_id: str, max_results: int = 100) -> list[dict[str, Any]]:
        """Get DM conversation events with a specific user (min 1, max 100)."""
        params = {
            "max_results": str(max_results),
            "dm_event.fields": "id,sender_id,text,created_at,dm_conversation_id",
        }
        resp = self._request(
            "GET",
            f"https://api.x.com/2/dm_conversations/with/{user_id}/dm_events",
            params=params,
        )
        body = resp.json()
        raw_events = body.get("data", [])

        normalized_events = [
            {
                "id": str(e["id"]),
                "sender_id": str(e["sender_id"]),
                "text": str(e.get("text", "")),
                "created_at": e.get("created_at"),
                "dm_conversation_id": e.get("dm_conversation_id"),
            }
            for e in raw_events
        ]

        record_usage(self.conn, "dm_read", len(normalized_events))
        return normalized_events

    def dm_events(self, stop_at_id: str | None = None) -> list[dict[str, Any]]:
        """
        Fetch newest DM events.
        If stop_at_id is None, fetch exactly 1 page to minimize read cost ($0.010/event).
        If stop_at_id is provided, paginate up to 3 pages maximum, stopping immediately upon seeing stop_at_id.
        """
        max_pages = 1 if stop_at_id is None else 3
        current_page = 0
        pagination_token: str | None = None
        all_events: list[dict[str, Any]] = []

        while current_page < max_pages:
            current_page += 1
            params: dict[str, str] = {
                "max_results": "100",
                "dm_event.fields": "id,sender_id,text,created_at,dm_conversation_id",
            }
            if pagination_token:
                params["pagination_token"] = pagination_token

            resp = self._request("GET", "https://api.x.com/2/dm_events", params=params)
            body = resp.json()
            raw_events = body.get("data", [])

            stopped = False
            for e in raw_events:
                event_id = str(e["id"])
                if stop_at_id and event_id == stop_at_id:
                    stopped = True
                    break
                all_events.append(
                    {
                        "id": event_id,
                        "sender_id": str(e["sender_id"]),
                        "text": str(e.get("text", "")),
                        "created_at": e.get("created_at"),
                        "dm_conversation_id": e.get("dm_conversation_id"),
                    }
                )

            if stopped:
                break

            meta = body.get("meta", {})
            pagination_token = meta.get("next_token")
            if not pagination_token:
                break

        record_usage(self.conn, "dm_read", len(all_events))
        return all_events


def get_x(conn: sqlite3.Connection) -> Any:
    """Return FakeXClient when X_MODE=fake, otherwise return XClient."""
    if config.X_MODE == "fake":
        from outreach.fake_x import FakeXClient

        return FakeXClient(conn)
    return XClient(conn)
