import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

# Mode settings
X_MODE: str = os.getenv("X_MODE", "fake").strip().lower()
X_CLIENT_ID: str = os.getenv("X_CLIENT_ID", "")
X_CLIENT_SECRET: str = os.getenv("X_CLIENT_SECRET", "")
X_REDIRECT_URI: str = os.getenv("X_REDIRECT_URI", "http://127.0.0.1:8765/callback")

# LLM settings
ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
LLM_MODEL: str = os.getenv("LLM_MODEL", "claude-fable-5-2")
LLM_PRICE_IN: float = float(os.getenv("LLM_PRICE_IN", "0"))
LLM_PRICE_OUT: float = float(os.getenv("LLM_PRICE_OUT", "0"))

# Sending safety controls
SEND_MODE: str = os.getenv("SEND_MODE", "allowlist").strip().lower()
_allowlist_raw = os.getenv("SEND_ALLOWLIST", "")
SEND_ALLOWLIST: list[str] = [
    item.strip().lstrip("@") for item in _allowlist_raw.split(",") if item.strip()
]
DAILY_SEND_CAP: int = int(os.getenv("DAILY_SEND_CAP", "20"))

# X API pricing in USD per unit
# Official documentation: https://docs.x.com/x-api/getting-started/pricing (verified on 2026-11-12)
PRICES: dict[str, float] = {
    "post_read": 0.005,
    "user_read": 0.010,
    "dm_read": 0.010,
    "dm_send": 0.015,
}

# Message and quotation limits
MAX_DM_CHARS: int = 500
MIN_QUOTE_CHARS: int = 15

# OAuth 2.0 scopes
SCOPES: str = "tweet.read users.read follows.read dm.read dm.write offline.access"

# Project root directory
PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent

# SQLite database file path based on X_MODE, anchored to project root
_db_filename = "fake.db" if X_MODE == "fake" else "outreach.db"
DB_PATH: str = str(PROJECT_ROOT / "data" / _db_filename)

