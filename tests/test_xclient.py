import base64
import inspect
import io
import json
import time
from urllib.parse import parse_qs, urlparse
import httpx
import pytest

from outreach import config
from outreach.db import kv_get, kv_set, spend_since
from outreach.xclient import (
    Ambiguous,
    AuthError,
    Forbidden,
    RateLimited,
    XClient,
    XError,
    get_x,
)
from outreach.fake_x import FakeXClient
from outreach.auth import build_authorize_url, handle_callback, login


def test_authorize_url_has_pkce_and_scopes():
    """Authorize URL must include PKCE S256 parameters, state, and required scopes."""
    url = build_authorize_url(state="test_state_123", code_challenge="test_challenge_abc")
    parsed = urlparse(url)
    assert parsed.scheme == "https"
    assert parsed.netloc == "x.com"
    assert parsed.path == "/i/oauth2/authorize"

    qs = parse_qs(parsed.query)
    assert qs["response_type"] == ["code"]
    assert qs["code_challenge_method"] == ["S256"]
    assert qs["code_challenge"] == ["test_challenge_abc"]
    assert qs["state"] == ["test_state_123"]
    assert "dm.write" in qs["scope"][0]
    assert "dm.read" in qs["scope"][0]
    assert "offline.access" in qs["scope"][0]


def test_auth_callback_rejects_mismatched_state(conn):
    """Callback with mismatched or missing state must raise AuthError without exchanging token."""
    kv_set(conn, "pkce", {"state": "valid_state", "code_verifier": "valid_verifier"})

    with pytest.raises(AuthError, match="State mismatch"):
        handle_callback(conn, {"state": "wrong_state", "code": "some_code"})

    with pytest.raises(AuthError, match="State mismatch"):
        handle_callback(conn, {"code": "some_code"})


def test_auth_callback_exchanges_code_for_tokens(conn, monkeypatch):
    """Valid callback exchanges authorization code for tokens using Basic auth."""
    monkeypatch.setattr(config, "X_CLIENT_ID", "client123")
    monkeypatch.setattr(config, "X_CLIENT_SECRET", "secret456")

    kv_set(conn, "pkce", {"state": "state_xyz", "code_verifier": "verifier_xyz"})

    def mock_handler(request: httpx.Request) -> httpx.Response:
        assert request.url == "https://api.x.com/2/oauth2/token"
        assert request.method == "POST"

        # Check Basic Auth header
        auth_header = request.headers.get("authorization", "")
        expected_basic = base64.b64encode(b"client123:secret456").decode("ascii")
        assert auth_header == f"Basic {expected_basic}"

        # Check request body
        body = parse_qs(request.content.decode("utf-8"))
        assert body["grant_type"] == ["authorization_code"]
        assert body["code"] == ["code_abc"]
        assert body["code_verifier"] == ["verifier_xyz"]

        return httpx.Response(
            200,
            json={
                "access_token": "acc_token_1",
                "refresh_token": "ref_token_1",
                "expires_in": 7200,
                "scope": config.SCOPES,
            },
        )

    transport = httpx.MockTransport(mock_handler)
    res = handle_callback(conn, {"state": "state_xyz", "code": "code_abc"}, transport=transport)

    assert res["access_token"] == "acc_token_1"
    saved = kv_get(conn, "oauth")
    assert saved is not None
    assert saved["access_token"] == "acc_token_1"
    assert saved["refresh_token"] == "ref_token_1"


def test_login_fetches_and_returns_me(conn, monkeypatch):
    """login() must exchange tokens, fetch me profile using transport, and persist me to kv."""
    monkeypatch.setattr(config, "X_MODE", "real")
    monkeypatch.setattr(config, "X_CLIENT_ID", "client_real")
    monkeypatch.setattr(config, "X_CLIENT_SECRET", "secret_real")

    # Monkeypatch webbrowser.open to ensure no browser is opened
    browser_opened = []
    monkeypatch.setattr("webbrowser.open", lambda url: browser_opened.append(url))

    # Mock socket for BaseHTTPRequestHandler
    class DummySocket:
        def __init__(self, req_bytes: bytes):
            self.r = io.BytesIO(req_bytes)
            self.w = io.BytesIO()

        def makefile(self, mode: str, *args, **kwargs):
            return self.r if "b" in mode and "r" in mode else self.w

        def sendall(self, data: bytes):
            self.w.write(data)

    # Mock HTTPServer to prevent binding port 8765
    class MockHTTPServer:
        def __init__(self, server_address, RequestHandlerClass):
            self.server_address = server_address
            self.RequestHandlerClass = RequestHandlerClass
            self.timeout = 120

        def handle_request(self):
            pkce = kv_get(conn, "pkce")
            state = pkce["state"]
            raw = f"GET /callback?code=code_123&state={state} HTTP/1.1\r\nHost: 127.0.0.1:8765\r\n\r\n".encode("utf-8")
            sock = DummySocket(raw)
            self.RequestHandlerClass(sock, ("127.0.0.1", 54321), self)

        def server_close(self):
            pass

    monkeypatch.setattr("outreach.auth.HTTPServer", MockHTTPServer)

    def mock_handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/2/oauth2/token":
            return httpx.Response(
                200,
                json={
                    "access_token": "acc_tok_99",
                    "refresh_token": "ref_tok_99",
                    "expires_in": 7200,
                    "scope": config.SCOPES,
                },
            )
        elif request.url.path == "/2/users/me":
            return httpx.Response(
                200,
                json={"data": {"id": "42", "username": "alice"}},
            )
        return httpx.Response(404)

    transport = httpx.MockTransport(mock_handler)
    res = login(conn, transport=transport)

    assert res == {"id": "42", "username": "alice"}
    assert kv_get(conn, "me") == {"id": "42", "username": "alice"}
    oauth = kv_get(conn, "oauth")
    assert oauth["access_token"] == "acc_tok_99"
    assert len(browser_opened) == 1


def test_login_without_client_id_fails_before_opening_x(conn, monkeypatch):
    """An empty X_CLIENT_ID makes X show 'You weren't able to give access to the App'; say why instead."""
    monkeypatch.setattr(config, "X_MODE", "real")
    monkeypatch.setattr(config, "X_CLIENT_ID", "")
    opened = []
    monkeypatch.setattr("webbrowser.open", lambda url: opened.append(url))
    with pytest.raises(AuthError, match="X_CLIENT_ID"):
        login(conn)
    assert opened == []


def test_missing_oauth_token_raises_autherror(conn):
    """Calling XClient when not logged in (kv['oauth'] is empty) must raise AuthError."""
    client = XClient(conn)
    with pytest.raises(AuthError, match="Not connected to X"):
        client.me()


def test_failed_token_refresh_raises_autherror(conn, monkeypatch):
    """When token refresh is rejected with 4xx, XClient must raise AuthError."""
    monkeypatch.setattr(config, "X_CLIENT_ID", "cid")
    monkeypatch.setattr(config, "X_CLIENT_SECRET", "csec")

    # Set expired token
    kv_set(
        conn,
        "oauth",
        {
            "access_token": "expired_tok",
            "refresh_token": "revoked_ref_tok",
            "expires_at": time.time() - 100,
        },
    )

    def mock_handler(request: httpx.Request) -> httpx.Response:
        if request.url == "https://api.x.com/2/oauth2/token":
            return httpx.Response(400, json={"error": "invalid_grant", "error_description": "Token revoked"})
        return httpx.Response(200, json={})

    transport = httpx.MockTransport(mock_handler)
    client = XClient(conn, transport=transport)

    with pytest.raises(AuthError, match="Token refresh failed"):
        client.me()


def test_refresh_persists_rotated_token(conn, monkeypatch):
    """
    When token expires, XClient refreshes it.
    kv['oauth'] must contain the new tokens INSIDE the transport handler before API request executes,
    and the API request must use the new Bearer token.
    """
    monkeypatch.setattr(config, "X_CLIENT_ID", "cid")
    monkeypatch.setattr(config, "X_CLIENT_SECRET", "csec")

    kv_set(
        conn,
        "oauth",
        {
            "access_token": "old_acc",
            "refresh_token": "old_ref",
            "expires_at": time.time() - 100,
        },
    )

    api_called = False

    def mock_handler(request: httpx.Request) -> httpx.Response:
        nonlocal api_called
        if request.url == "https://api.x.com/2/oauth2/token":
            # Verify Basic Auth on token refresh endpoint
            auth_header = request.headers.get("authorization", "")
            expected_basic = base64.b64encode(b"cid:csec").decode("ascii")
            assert auth_header == f"Basic {expected_basic}"

            body = parse_qs(request.content.decode("utf-8"))
            assert body["grant_type"] == ["refresh_token"]
            assert body["refresh_token"] == ["old_ref"]

            return httpx.Response(
                200,
                json={
                    "access_token": "new_acc_123",
                    "refresh_token": "new_ref_456",
                    "expires_in": 7200,
                },
            )
        elif request.url == "https://api.x.com/2/users/me":
            api_called = True
            # CRITICAL CHECK: In-flight verification that kv was persisted BEFORE API call went out
            oauth_data = kv_get(conn, "oauth")
            assert oauth_data["access_token"] == "new_acc_123"
            assert oauth_data["refresh_token"] == "new_ref_456"

            # Check that outgoing request uses the new bearer token
            assert request.headers.get("authorization") == "Bearer new_acc_123"
            return httpx.Response(200, json={"data": {"id": "42", "username": "alice"}})

        raise RuntimeError(f"Unexpected request: {request.url}")

    transport = httpx.MockTransport(mock_handler)
    client = XClient(conn, transport=transport)
    me = client.me()

    assert api_called is True
    assert me == {"id": "42", "username": "alice"}
    assert kv_get(conn, "me") == {"id": "42", "username": "alice"}


def test_token_read_from_kv_on_each_call(conn):
    """XClient must re-read token from kv on each call and not cache it in-memory."""
    kv_set(
        conn,
        "oauth",
        {
            "access_token": "initial_tok",
            "refresh_token": "initial_ref",
            "expires_at": time.time() + 3600,
        },
    )

    recorded_tokens = []

    def mock_handler(request: httpx.Request) -> httpx.Response:
        auth = request.headers.get("authorization", "")
        recorded_tokens.append(auth)
        return httpx.Response(200, json={"data": {"id": "42", "username": "alice"}})

    transport = httpx.MockTransport(mock_handler)
    client = XClient(conn, transport=transport)

    client.me()
    assert recorded_tokens[-1] == "Bearer initial_tok"

    # Simulate another tab / process updating the token in CSDL
    kv_set(
        conn,
        "oauth",
        {
            "access_token": "updated_by_another_tab",
            "refresh_token": "ref_tab",
            "expires_at": time.time() + 3600,
        },
    )

    client.me()
    assert recorded_tokens[-1] == "Bearer updated_by_another_tab"


def test_send_dm_posts_to_participant_endpoint(conn):
    """send_dm must POST to /2/dm_conversations/with/{user_id}/messages and record usage."""
    kv_set(conn, "oauth", {"access_token": "tok", "refresh_token": "ref", "expires_at": time.time() + 3600})

    def mock_handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == "https://api.x.com/2/dm_conversations/with/42/messages"
        assert request.method == "POST"
        payload = json.loads(request.content.decode("utf-8"))
        assert payload == {"text": "hi"}
        return httpx.Response(
            201,
            json={"data": {"dm_event_id": "e1", "dm_conversation_id": "c1"}},
        )

    transport = httpx.MockTransport(mock_handler)
    client = XClient(conn, transport=transport)
    res = client.send_dm("42", "hi")

    assert res == {"dm_event_id": "e1", "dm_conversation_id": "c1"}
    assert spend_since(conn, "1970-01-01T00:00:00+00:00") == pytest.approx(0.015)


def test_search_recent_joins_authors(conn):
    """search_recent must request author expansions, fields, and normalize joined posts and users."""
    kv_set(conn, "oauth", {"access_token": "tok", "refresh_token": "ref", "expires_at": time.time() + 3600})

    def mock_handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/2/tweets/search/recent"
        assert request.url.params["query"] == "robotics lang:en"
        assert request.url.params["max_results"] == "10"
        assert "author_id" in request.url.params["expansions"]
        assert "receives_your_dm" in request.url.params["user.fields"]
        assert "created_at" in request.url.params["tweet.fields"]

        return httpx.Response(
            200,
            json={
                "data": [
                    {
                        "id": "p1",
                        "author_id": "u1",
                        "text": "building robots",
                        "created_at": "2026-11-12T01:00:00Z",
                    }
                ],
                "includes": {
                    "users": [
                        {
                            "id": "u1",
                            "username": "robodev",
                            "name": "Robo Dev",
                            "description": "Founder building AI robots",
                            "location": "Singapore",
                            "public_metrics": {"followers_count": 1250},
                            "protected": False,
                            "receives_your_dm": True,
                        }
                    ]
                },
            },
        )

    transport = httpx.MockTransport(mock_handler)
    client = XClient(conn, transport=transport)
    posts, users = client.search_recent("robotics lang:en", max_results=10)

    assert len(posts) == 1
    assert posts[0] == {
        "id": "p1",
        "author_id": "u1",
        "text": "building robots",
        "created_at": "2026-11-12T01:00:00Z",
    }

    assert len(users) == 1
    assert users[0] == {
        "id": "u1",
        "username": "robodev",
        "name": "Robo Dev",
        "description": "Founder building AI robots",
        "location": "Singapore",
        "followers": 1250,
        "protected": 0,
        "receives_your_dm": True,
    }

    # Usage recorded: 1 post_read (0.005) + 1 user_read (0.010) = 0.015
    assert spend_since(conn, "1970-01-01T00:00:00+00:00") == pytest.approx(0.015)


def test_users_by_usernames(conn):
    """users_by_usernames must query /2/users/by and normalize user objects."""
    kv_set(conn, "oauth", {"access_token": "tok", "refresh_token": "ref", "expires_at": time.time() + 3600})

    def mock_handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/2/users/by"
        assert request.url.params["usernames"] == "alice,bob"
        return httpx.Response(
            200,
            json={
                "data": [
                    {
                        "id": "u1",
                        "username": "alice",
                        "name": "Alice",
                        "description": "AI researcher",
                        "location": "Vietnam",
                        "public_metrics": {"followers_count": 500},
                        "protected": False,
                        "receives_your_dm": True,
                    },
                    {
                        "id": "u2",
                        "username": "bob",
                        "name": "Bob",
                        "description": "Robotics engineer",
                        "location": None,
                        "public_metrics": {"followers_count": 300},
                        "protected": True,
                        "receives_your_dm": False,
                    },
                ]
            },
        )

    transport = httpx.MockTransport(mock_handler)
    client = XClient(conn, transport=transport)
    users = client.users_by_usernames(["alice", "bob"])

    assert len(users) == 2
    assert users[0]["username"] == "alice"
    assert users[0]["protected"] == 0
    assert users[1]["username"] == "bob"
    assert users[1]["protected"] == 1
    assert spend_since(conn, "1970-01-01T00:00:00+00:00") == pytest.approx(0.020)


def test_following_endpoint(conn):
    """following must query /2/users/{id}/following and normalize users."""
    kv_set(conn, "oauth", {"access_token": "tok", "refresh_token": "ref", "expires_at": time.time() + 3600})

    def mock_handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/2/users/u10/following"
        assert request.url.params["max_results"] == "50"
        return httpx.Response(
            200,
            json={
                "data": [
                    {
                        "id": "u20",
                        "username": "carol",
                        "name": "Carol",
                        "description": "LLM Dev",
                        "location": "Bangkok",
                        "public_metrics": {"followers_count": 100},
                        "protected": False,
                        "receives_your_dm": True,
                    }
                ]
            },
        )

    transport = httpx.MockTransport(mock_handler)
    client = XClient(conn, transport=transport)
    users = client.following("u10", max_results=50)

    assert len(users) == 1
    assert users[0]["username"] == "carol"
    assert spend_since(conn, "1970-01-01T00:00:00+00:00") == pytest.approx(0.010)


def test_user_posts_excludes_replies_and_retweets(conn):
    """user_posts must exclude replies and retweets and normalize posts."""
    kv_set(conn, "oauth", {"access_token": "tok", "refresh_token": "ref", "expires_at": time.time() + 3600})

    def mock_handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/2/users/u10/tweets"
        assert request.url.params["max_results"] == "5"
        assert request.url.params["exclude"] == "retweets,replies"
        return httpx.Response(
            200,
            json={
                "data": [
                    {
                        "id": "p101",
                        "author_id": "u10",
                        "text": "Shipping our new agent model!",
                        "created_at": "2026-11-12T02:00:00Z",
                    }
                ]
            },
        )

    transport = httpx.MockTransport(mock_handler)
    client = XClient(conn, transport=transport)
    posts = client.user_posts("u10", max_results=5)

    assert len(posts) == 1
    assert posts[0]["id"] == "p101"
    assert spend_since(conn, "1970-01-01T00:00:00+00:00") == pytest.approx(0.005)


def test_user_posts_asks_at_least_x_minimum_of_5(conn):
    """X rejects max_results < 5 on /users/:id/tweets with 400; callers asking for fewer must still get posts."""
    kv_set(conn, "oauth", {"access_token": "tok", "refresh_token": "ref", "expires_at": time.time() + 3600})

    def mock_handler(request: httpx.Request) -> httpx.Response:
        if int(request.url.params["max_results"]) < 5:
            return httpx.Response(400, json={"detail": "max_results must be between 5 and 100"})
        return httpx.Response(200, json={"data": []})

    client = XClient(conn, transport=httpx.MockTransport(mock_handler))
    assert client.user_posts("u10", max_results=2) == []


def test_dm_events_with_endpoint(conn):
    """dm_events_with must retrieve conversation events with a participant."""
    kv_set(conn, "oauth", {"access_token": "tok", "refresh_token": "ref", "expires_at": time.time() + 3600})

    def mock_handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/2/dm_conversations/with/u10/dm_events"
        return httpx.Response(
            200,
            json={
                "data": [
                    {
                        "id": "e50",
                        "sender_id": "u10",
                        "text": "Thanks for reaching out!",
                        "created_at": "2026-11-12T03:00:00Z",
                        "dm_conversation_id": "conv_10",
                    }
                ]
            },
        )

    transport = httpx.MockTransport(mock_handler)
    client = XClient(conn, transport=transport)
    events = client.dm_events_with("u10", max_results=10)

    assert len(events) == 1
    assert events[0] == {
        "id": "e50",
        "sender_id": "u10",
        "text": "Thanks for reaching out!",
        "created_at": "2026-11-12T03:00:00Z",
        "dm_conversation_id": "conv_10",
    }
    assert spend_since(conn, "1970-01-01T00:00:00+00:00") == pytest.approx(0.010)


def test_dm_events_stops_at_known_id(conn):
    """dm_events must stop pagination when encountering stop_at_id."""
    kv_set(conn, "oauth", {"access_token": "tok", "refresh_token": "ref", "expires_at": time.time() + 3600})

    pages_requested = 0

    def mock_handler(request: httpx.Request) -> httpx.Response:
        nonlocal pages_requested
        pages_requested += 1
        cursor = request.url.params.get("pagination_token")

        if cursor is None:
            return httpx.Response(
                200,
                json={
                    "data": [
                        {"id": "e3", "sender_id": "u1", "text": "three", "created_at": "t3", "dm_conversation_id": "c"},
                        {"id": "e2", "sender_id": "u1", "text": "two", "created_at": "t2", "dm_conversation_id": "c"},
                    ],
                    "meta": {"next_token": "page2_cursor"},
                },
            )
        elif cursor == "page2_cursor":
            return httpx.Response(
                200,
                json={
                    "data": [
                        {"id": "e1", "sender_id": "u1", "text": "one", "created_at": "t1", "dm_conversation_id": "c"},
                    ],
                },
            )
        raise RuntimeError(f"Unexpected cursor: {cursor}")

    transport = httpx.MockTransport(mock_handler)
    client = XClient(conn, transport=transport)

    events = client.dm_events(stop_at_id="e2")
    assert [e["id"] for e in events] == ["e3"]
    assert pages_requested == 1  # Stopped at e2, did not fetch page 2


def test_dm_events_single_page_when_no_stop_id(conn):
    """dm_events without stop_at_id must read only a single page to avoid unbounded cost."""
    kv_set(conn, "oauth", {"access_token": "tok", "refresh_token": "ref", "expires_at": time.time() + 3600})

    pages_requested = 0

    def mock_handler(request: httpx.Request) -> httpx.Response:
        nonlocal pages_requested
        pages_requested += 1
        return httpx.Response(
            200,
            json={
                "data": [
                    {"id": "e99", "sender_id": "u1", "text": "hello", "created_at": "t99", "dm_conversation_id": "c"}
                ],
                "meta": {"next_token": "next_page_token"},
            },
        )

    transport = httpx.MockTransport(mock_handler)
    client = XClient(conn, transport=transport)

    events = client.dm_events(stop_at_id=None)
    assert len(events) == 1
    assert pages_requested == 1


def test_dm_events_caps_pages_with_stop_id(conn):
    """dm_events with stop_at_id caps pagination at 3 pages if stop_at_id is not encountered."""
    kv_set(conn, "oauth", {"access_token": "tok", "refresh_token": "ref", "expires_at": time.time() + 3600})

    pages_requested = 0

    def mock_handler(request: httpx.Request) -> httpx.Response:
        nonlocal pages_requested
        pages_requested += 1
        return httpx.Response(
            200,
            json={
                "data": [
                    {"id": f"e_p{pages_requested}", "sender_id": "u1", "text": "msg", "created_at": "t", "dm_conversation_id": "c"}
                ],
                "meta": {"next_token": f"page_{pages_requested + 1}"},
            },
        )

    transport = httpx.MockTransport(mock_handler)
    client = XClient(conn, transport=transport)

    events = client.dm_events(stop_at_id="nonexistent_id")
    assert pages_requested == 3
    assert len(events) == 3


def test_429_raises_ratelimited_with_reset(conn):
    """HTTP 429 response must raise RateLimited with reset_at epoch seconds from header."""
    kv_set(conn, "oauth", {"access_token": "tok", "refresh_token": "ref", "expires_at": time.time() + 3600})

    def mock_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            429,
            headers={"x-rate-limit-reset": "1700000000"},
            json={"title": "Too Many Requests", "detail": "Rate limit exceeded"},
        )

    transport = httpx.MockTransport(mock_handler)
    client = XClient(conn, transport=transport)

    with pytest.raises(RateLimited) as exc_info:
        client.me()

    assert exc_info.value.reset_at == 1700000000
    assert exc_info.value.status == 429


def test_401_raises_autherror(conn):
    """HTTP 401 response from API must raise AuthError."""
    kv_set(conn, "oauth", {"access_token": "tok", "refresh_token": "ref", "expires_at": time.time() + 3600})

    def mock_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"title": "Unauthorized", "detail": "Invalid token"})

    transport = httpx.MockTransport(mock_handler)
    client = XClient(conn, transport=transport)

    with pytest.raises(AuthError):
        client.me()


def test_403_raises_forbidden(conn):
    """HTTP 403 response must raise Forbidden."""
    kv_set(conn, "oauth", {"access_token": "tok", "refresh_token": "ref", "expires_at": time.time() + 3600})

    def mock_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(403, json={"title": "Forbidden", "detail": "Account locked"})

    transport = httpx.MockTransport(mock_handler)
    client = XClient(conn, transport=transport)

    with pytest.raises(Forbidden):
        client.me()


def test_other_4xx_raises_xerror(conn):
    """Other HTTP 4xx responses (such as 400 or 404) must raise XError with status and detail."""
    kv_set(conn, "oauth", {"access_token": "tok", "refresh_token": "ref", "expires_at": time.time() + 3600})

    def mock_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, json={"title": "Bad Request", "detail": "Invalid parameter"})

    transport = httpx.MockTransport(mock_handler)
    client = XClient(conn, transport=transport)

    with pytest.raises(XError) as exc_info:
        client.me()

    assert exc_info.value.status == 400
    assert "Invalid parameter" in exc_info.value.detail


def test_timeout_and_5xx_raise_ambiguous(conn):
    """Timeouts, connection errors, and 5xx responses must raise Ambiguous."""
    kv_set(conn, "oauth", {"access_token": "tok", "refresh_token": "ref", "expires_at": time.time() + 3600})

    def mock_handler_500(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="Internal Server Error")

    transport_500 = httpx.MockTransport(mock_handler_500)
    client_500 = XClient(conn, transport=transport_500)
    with pytest.raises(Ambiguous):
        client_500.me()

    def mock_handler_timeout(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("Request timed out")

    transport_timeout = httpx.MockTransport(mock_handler_timeout)
    client_timeout = XClient(conn, transport=transport_timeout)
    with pytest.raises(Ambiguous):
        client_timeout.me()


def test_get_x_factory(conn, monkeypatch):
    """get_x returns FakeXClient when X_MODE=fake and XClient when X_MODE=real."""
    monkeypatch.setattr(config, "X_MODE", "fake")
    client_fake = get_x(conn)
    assert isinstance(client_fake, FakeXClient)

    monkeypatch.setattr(config, "X_MODE", "real")
    client_real = get_x(conn)
    assert isinstance(client_real, XClient)


def test_fake_client_has_same_methods_and_signatures():
    """FakeXClient must have the exact same 8 public API methods and signatures as XClient."""
    methods = [
        "me",
        "search_recent",
        "users_by_usernames",
        "following",
        "user_posts",
        "send_dm",
        "dm_events_with",
        "dm_events",
    ]

    for m_name in methods:
        assert hasattr(XClient, m_name), f"XClient missing {m_name}"
        assert hasattr(FakeXClient, m_name), f"FakeXClient missing {m_name}"

        sig_real = inspect.signature(getattr(XClient, m_name))
        sig_fake = inspect.signature(getattr(FakeXClient, m_name))
        assert sig_real == sig_fake, f"Signature mismatch for method {m_name}: {sig_real} != {sig_fake}"


def test_fake_client_simulates_operations(conn):
    """FakeXClient sample data has 6 profiles, tracks sent DMs, and respects fail_next."""
    fake = FakeXClient(conn)

    me = fake.me()
    assert me["username"] == "genaifund_test"
    assert kv_get(conn, "me") == me

    posts, users = fake.search_recent("AI", max_results=10)
    assert len(users) == 6
    assert any(u["receives_your_dm"] is True for u in users)
    assert any(u["receives_your_dm"] is False for u in users)
    assert any(u["protected"] == 1 for u in users)

    res = fake.send_dm("u1", "hello fake")
    assert res["dm_event_id"].startswith("fake_dm_")
    assert len(fake.sent) == 1
    assert fake.sent[0] == ("u1", "hello fake")

    # Test fail_next
    fake.fail_next = Ambiguous("Simulated timeout", status=0)
    with pytest.raises(Ambiguous):
        fake.send_dm("u1", "will fail")
    assert fake.fail_next is None


def test_fake_inbox_starts_empty(conn):
    """FakeXClient inbox must start empty to prevent false positive existing conversation."""
    fake = FakeXClient(conn)
    assert fake.inbox == []
    assert fake.dm_events_with("1001", 1) == []

