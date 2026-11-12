import argparse
import os
import sys
from typing import Any
import sqlite3

from outreach import config
from outreach.db import connect, kv_get
from outreach.xclient import AuthError, XClient, get_x


def run_doctor(args_list: list[str] | None = None, conn: sqlite3.Connection | None = None, x: Any | None = None) -> int:
    """Run system diagnostic checks and tests, returning 0 on success or 1 on failure."""
    parser = argparse.ArgumentParser(description="GenAI Fund Outreach Diagnostic Tool")
    parser.add_argument("--spend", action="store_true", help="Perform a 10-result search and report estimated cost")
    parser.add_argument("--dm-test", type=str, metavar="USERNAME", help="Send a test DM to an allowlisted user")
    parser.add_argument("--check-reply", type=str, metavar="USERNAME", help="Check DM history for replies from a user")
    args = parser.parse_args(args_list)

    if conn is None:
        conn = connect()
    if x is None:
        x = get_x(conn)

    print("=== GenAI Fund Outreach Doctor ===\n")
    has_failure = False

    # 1. Environment variables check
    print("[1] Checking environment configuration...")
    required_keys = ["X_MODE", "SEND_MODE", "DAILY_SEND_CAP"]
    if config.X_MODE == "real":
        required_keys.extend(["X_CLIENT_ID", "X_CLIENT_SECRET", "ANTHROPIC_API_KEY"])

    env_path = config.PROJECT_ROOT / ".env"
    if not env_path.exists():
        print("  WARN: Local .env file does not exist yet (falling back to default config)")

    missing = [k for k in required_keys if os.getenv(k) is None and getattr(config, k, None) is None]
    if missing:
        print(f"  FAIL: Missing required configuration keys: {', '.join(missing)}")
        has_failure = True
    else:
        print("  PASS: Core environment variables are configured (secrets kept hidden)")

    # 2. Check connection and user identity
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

    # 4. Optional --spend check
    if args.spend:
        print("\n[4] Running spend estimation search (--spend)...")
        try:
            posts, users = x.search_recent("AI", max_results=10)
            cost = len(posts) * config.PRICES["post_read"] + len(users) * config.PRICES["user_read"]
            print(f"  PASS: Search retrieved {len(posts)} posts and {len(users)} users.")
            print(f"  Estimated cost for this call: ${cost:.4f}")
        except Exception as e:
            print(f"  FAIL: Search failed: {e}")
            has_failure = True

    # 5. Optional --dm-test check
    if args.dm_test:
        raw_user = args.dm_test.strip()
        clean_user = raw_user.lstrip("@").lower()
        print(f"\n[5] Executing test DM to @{clean_user} (--dm-test)...")

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

    # 6. Optional --check-reply check
    if args.check_reply:
        raw_user = args.check_reply.strip()
        clean_user = raw_user.lstrip("@").lower()
        print(f"\n[6] Checking conversation history for replies from @{clean_user} (--check-reply)...")
        try:
            users = x.users_by_usernames([clean_user])
            if not users:
                print(f"  FAIL: User @{clean_user} not found.")
                return 1

            user_id = users[0]["id"]
            events = x.dm_events_with(user_id, max_results=20)
            replies = [e for e in events if e.get("sender_id") == user_id]
            if replies:
                latest = replies[0]
                print(f"  PASS: Found reply from @{clean_user}: \"{latest.get('text')}\" (at {latest.get('created_at')})")
            else:
                print(f"  INFO: No reply found yet from @{clean_user} (inspected {len(events)} events).")
        except Exception as e:
            print(f"  FAIL: Error checking replies: {e}")
            return 1

    print("\nDiagnostic complete.")
    return 1 if has_failure else 0


if __name__ == "__main__":
    sys.exit(run_doctor())
