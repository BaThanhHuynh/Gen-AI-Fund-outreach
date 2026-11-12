import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

def validate_choice(var_name: str, value: str, allowed: tuple[str, ...]) -> str:
    """Validate that value is in allowed choices, or raise ValueError."""
    cleaned = value.strip().lower()
    if cleaned not in allowed:
        allowed_str = ", ".join(f"'{a}'" for a in allowed)
        raise ValueError(
            f"Invalid value for {var_name}: expected one of [{allowed_str}], got '{cleaned}'"
        )
    return cleaned


def parse_float_env(var_name: str, value: str | None, default: float = 0.0) -> float:
    """Safely parse float environment variable, handling empty strings."""
    if value is None or not value.strip():
        return default
    try:
        return float(value.strip())
    except ValueError:
        raise ValueError(f"Invalid float value for {var_name}: '{value}'")


# Mode settings
X_MODE: str = validate_choice("X_MODE", os.getenv("X_MODE", "fake"), ("fake", "real"))
X_CLIENT_ID: str = os.getenv("X_CLIENT_ID", "")
X_CLIENT_SECRET: str = os.getenv("X_CLIENT_SECRET", "")
X_REDIRECT_URI: str = os.getenv("X_REDIRECT_URI", "http://127.0.0.1:8765/callback")

# GitHub settings
GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "").strip()

# Sending channel: manual ($0) or api (X API)
SEND_CHANNEL: str = validate_choice(
    "SEND_CHANNEL", os.getenv("SEND_CHANNEL", "manual"), ("manual", "api")
)

# LLM settings
LLM_PROVIDER: str = validate_choice(
    "LLM_PROVIDER", os.getenv("LLM_PROVIDER", "ollama"), ("ollama", "template", "anthropic")
)
OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "qwen3:4b").strip()
OLLAMA_URL: str = "http://127.0.0.1:11434"
ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
LLM_MODEL: str = os.getenv("LLM_MODEL", "claude-fable-5-2")
LLM_PRICE_IN: float = parse_float_env("LLM_PRICE_IN", os.getenv("LLM_PRICE_IN", "0"))
LLM_PRICE_OUT: float = parse_float_env("LLM_PRICE_OUT", os.getenv("LLM_PRICE_OUT", "0"))

# Scoring and target criteria
MIN_SCORE: int = 40
SEA_LOCATIONS: list[str] = [
    "Vietnam",
    "Viet Nam",
    "Ho Chi Minh",
    "Hanoi",
    "Singapore",
    "Thailand",
    "Bangkok",
    "Indonesia",
    "Jakarta",
    "Malaysia",
    "Kuala Lumpur",
    "Philippines",
    "Manila",
]

# Sending safety controls
SEND_MODE: str = validate_choice(
    "SEND_MODE", os.getenv("SEND_MODE", "allowlist"), ("allowlist", "live")
)
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
