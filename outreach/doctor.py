import argparse
import os
import sys
from typing import Any
import sqlite3

import httpx

from outreach import config
from outreach.db import connect, kv_get
from outreach.xclient import AuthError, XClient, get_x
from outreach.github import GitHubAuthError, GitHubClient, GitHubError


def run_doctor(args_list: list[str] | None = None, conn: sqlite3.Connection | None = None, x: Any | None = None, gh: Any | None = None,
               ollama_transport: httpx.BaseTransport | None = None) -> int:
    """Run system diagnostic checks and tests, returning 0 on success or 1 on failure."""
    parser = argparse.ArgumentParser(description="GenAI Fund Outreach Diagnostic Tool")
    parser.add_argument("--dm-test", type=str, metavar="USERNAME", help="Send a test DM to an allowlisted user")
    args = parser.parse_args(args_list)

    if conn is None:
        conn = connect()
    if x is None:
        x = get_x(conn)

    print("=== GenAI Fund Outreach Doctor ===\n")
    has_failure = False

    # 1. Environment variables check
    print("[1] Checking environment configuration...")
    required_keys = ["X_MODE", "SEND_MODE", "DAILY_SEND_CAP", "SEND_CHANNEL", "LLM_PROVIDER"]
    if config.X_MODE == "real":
        required_keys.append("GITHUB_TOKEN")
    if config.SEND_CHANNEL == "api":
        required_keys.extend(["X_CLIENT_ID", "X_CLIENT_SECRET"])
    if config.LLM_PROVIDER == "anthropic":
        required_keys.append("ANTHROPIC_API_KEY")

    env_path = config.PROJECT_ROOT / ".env"
    if not env_path.exists():
        print("  WARN: Local .env file does not exist yet (falling back to default config)")

    missing = []
    for k in required_keys:
        env_val = os.getenv(k)
        cfg_val = getattr(config, k, None)
        val = env_val if env_val is not None else cfg_val
        if val is None or not str(val).strip():
            missing.append(k)

    if missing:
        print(f"  FAIL: Missing required configuration keys: {', '.join(missing)}")
        has_failure = True
    else:
        print("  PASS: Core environment variables are configured (secrets kept hidden)")

    # 2. Check X connection and credentials
    if config.SEND_CHANNEL == "api":
        print("\n[2] Checking X connection and credentials...")
        try:
            me = x.me()
            print(f"  PASS: Connected as @{me['username']} (ID: {me['id']})")
        except AuthError as e:
            print(f"  FAIL: Authentication failed: {e}")
            print("  Advice: Run 'python -m outreach.auth' to log in via browser.")
            return 1
        except Exception as e:
            print(f"  FAIL: Error connecting to X: {e}")
            return 1

        # 3. Check OAuth scopes
        print("\n[3] Checking OAuth token permissions...")
        oauth = kv_get(conn, "oauth")
        if oauth and "scope" in oauth:
            scopes = oauth["scope"]
            has_dm_read = "dm.read" in scopes
            has_dm_write = "dm.write" in scopes
            if has_dm_read and has_dm_write:
                print("  PASS: Token has dm.read and dm.write permissions")
            else:
                print(f"  WARN: Missing DM scopes in token (active scopes: {scopes})")
        else:
            if config.X_MODE == "fake":
                print("  PASS: Running in fake mode with simulated scopes")
            else:
                print("  WARN: No stored scope metadata found in kv['oauth']")
    else:
        print("\n[2] Checking X connection...")
        print("  PASS: Manual send channel (no X API credentials required)")

    # GitHub token (real mode only; /rate_limit does not count against quota)
    if config.X_MODE == "real" and config.GITHUB_TOKEN:   # an empty token already failed step [1]
        print("\n[GitHub] Checking GITHUB_TOKEN...")
        try:
            core = (gh or GitHubClient()).rate_limit()
            print(f"  PASS: GitHub token accepted ({core['remaining']}/{core['limit']} requests left)")
        except GitHubAuthError as e:
            print(f"  FAIL: GitHub rejected GITHUB_TOKEN: {e}")
            print("  Advice: create a new token at github.com/settings/tokens and set GITHUB_TOKEN in .env")
            has_failure = True
        except GitHubError as e:
            print(f"  FAIL: Could not reach GitHub: {e}")
            has_failure = True

    # Local model (only when drafting with Ollama)
    if config.LLM_PROVIDER == "ollama":
        print(f"\n[Ollama] Checking {config.OLLAMA_URL} for model {config.OLLAMA_MODEL}...")
        try:
            with httpx.Client(transport=ollama_transport, timeout=10) as client:
                models = client.get(f"{config.OLLAMA_URL}/api/tags").json().get("models", [])
            names = {m.get("name") for m in models} | {m.get("model") for m in models}
            if config.OLLAMA_MODEL in names or f"{config.OLLAMA_MODEL}:latest" in names:
                print("  PASS: Ollama is running and the model is installed")
            else:
                print(f"  FAIL: Model {config.OLLAMA_MODEL} is not installed in Ollama")
                print(f"  Advice: run 'ollama pull {config.OLLAMA_MODEL}', or set LLM_PROVIDER=template in .env")
                has_failure = True
        except (httpx.HTTPError, ValueError) as e:
            print(f"  FAIL: Ollama is not reachable at {config.OLLAMA_URL} ({type(e).__name__})")
            print("  Advice: start Ollama, or set LLM_PROVIDER=template in .env")
            has_failure = True

    # 4. Optional --dm-test check
    if args.dm_test:
        raw_user = args.dm_test.strip()
        clean_user = raw_user.lstrip("@").lower()
        print(f"\n[4] Executing test DM to @{clean_user} (--dm-test)...")

        allowed = [u.lstrip("@").lower() for u in config.SEND_ALLOWLIST]
        if clean_user not in allowed:
            print(f"  FAIL: Recipient @{raw_user} is not in SEND_ALLOWLIST (safety mode).")
            print(f"  Current allowlist: {config.SEND_ALLOWLIST}")
            return 1

        try:
            users = x.users_by_usernames([clean_user])
            if not users:
                print(f"  FAIL: Recipient @{clean_user} not found on X.")
                return 1

            recipient = users[0]
            can_dm = recipient.get("receives_your_dm")
            print(f"  INFO: Profile receives_your_dm = {can_dm}")
            if can_dm is False:
                print(f"  WARN: User @{clean_user} has DMs closed for stranger accounts.")

            res = x.send_dm(recipient["id"], "Test message from GenAI Fund doctor tool")
            print(f"  PASS: Successfully sent test DM to @{clean_user}. Event ID: {res['dm_event_id']}")
        except Exception as e:
            print(f"  FAIL: Could not send test DM: {e}")
            return 1

    print("\nDiagnostic complete.")
    return 1 if has_failure else 0


if __name__ == "__main__":
    sys.exit(run_doctor())
