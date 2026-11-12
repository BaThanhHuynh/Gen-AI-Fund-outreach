import base64
import hashlib
from http.server import BaseHTTPRequestHandler, HTTPServer
import secrets
import sqlite3
import time
from urllib.parse import parse_qs, urlencode, urlparse
import webbrowser
import httpx

from outreach import config
from outreach.db import kv_get, kv_set
from outreach.xclient import AuthError, XClient


def generate_pkce_pair() -> tuple[str, str]:
    """Generate (code_verifier, code_challenge) using SHA-256 and Base64URL encoding without padding."""
    verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
    return verifier, challenge


def build_authorize_url(state: str, code_challenge: str) -> str:
    """Construct official X OAuth 2.0 PKCE authorize URL."""
    params = {
        "response_type": "code",
        "client_id": config.X_CLIENT_ID,
        "redirect_uri": config.X_REDIRECT_URI,
        "scope": config.SCOPES,
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }
    return f"https://x.com/i/oauth2/authorize?{urlencode(params)}"


def handle_callback(
    conn: sqlite3.Connection,
    query_params: dict[str, Any],
    transport: httpx.BaseTransport | None = None,
) -> dict[str, Any]:
    """
    Process OAuth callback parameters, verify state to prevent CSRF,
    and exchange authorization code for access and refresh tokens.
    """
    received_state = query_params.get("state")
    if isinstance(received_state, list):
        received_state = received_state[0] if received_state else None

    expected_pkce = kv_get(conn, "pkce")
    if not expected_pkce or expected_pkce.get("state") != received_state:
        raise AuthError(f"State mismatch: expected '{expected_pkce.get('state') if expected_pkce else None}'")

    code = query_params.get("code")
    if isinstance(code, list):
        code = code[0] if code else None
    if not code:
        raise AuthError("No authorization code provided in callback")

    client_id = config.X_CLIENT_ID
    client_secret = config.X_CLIENT_SECRET
    basic_creds = base64.b64encode(f"{client_id}:{client_secret}".encode("utf-8")).decode("ascii")

    headers = {
        "Authorization": f"Basic {basic_creds}",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": config.X_REDIRECT_URI,
        "code_verifier": expected_pkce["code_verifier"],
    }

    try:
        with httpx.Client(transport=transport, timeout=30.0) as client:
            resp = client.post("https://api.x.com/2/oauth2/token", headers=headers, data=data)
    except Exception as e:
        raise AuthError(f"Failed to connect to token endpoint: {e}")

    if resp.status_code != 200:
        raise AuthError(f"Token exchange rejected ({resp.status_code}): {resp.text}")

    body = resp.json()
    expires_in = int(body.get("expires_in", 7200))
    tokens = {
        "access_token": body["access_token"],
        "refresh_token": body.get("refresh_token", ""),
        "expires_at": time.time() + expires_in,
        "scope": body.get("scope", config.SCOPES),
    }

    kv_set(conn, "oauth", tokens)
    return tokens


def login(conn: sqlite3.Connection, timeout_s: int = 120) -> dict[str, str]:
    """
    Interactive OAuth 2.0 PKCE login via local browser.
    Listens only on 127.0.0.1 and suppresses request logging to avoid leaking auth code.
    """
    state = secrets.token_urlsafe(32)
    verifier, challenge = generate_pkce_pair()
    kv_set(conn, "pkce", {"state": state, "code_verifier": verifier})

    callback_params: dict[str, list[str]] = {}

    class CallbackHandler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: Any) -> None:
            # Overridden to prevent printing authorization code query string to stdout/stderr
            pass

        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path == urlparse(config.X_REDIRECT_URI).path:
                qs = parse_qs(parsed.query)
                callback_params.update(qs)
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(b"<h1>Authentication successful!</h1><p>You can return to the application.</p>")
            else:
                self.send_response(404)
                self.end_headers()

    # Bind strictly to 127.0.0.1 on port 8765
    server_address = ("127.0.0.1", 8765)
    server = HTTPServer(server_address, CallbackHandler)
    server.timeout = timeout_s

    auth_url = build_authorize_url(state, challenge)
    print(f"\nOpening browser for X authentication:\n{auth_url}\n")
    webbrowser.open(auth_url)

    # Handle single callback request
    server.handle_request()
    server.server_close()

    if not callback_params:
        raise AuthError("Authentication timed out or received no response")

    # Format params dictionary
    flat_params = {k: v[0] if isinstance(v, list) and v else v for k, v in callback_params.items()}
    handle_callback(conn, flat_params)
    me_data = kv_get(conn, "me")
    if not me_data:
        raise AuthError("Failed to fetch user profile after authentication")
    return me_data
