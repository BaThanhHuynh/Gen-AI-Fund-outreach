import os
from pathlib import Path
import subprocess
import sys
import pytest
from outreach import config
from outreach.config import validate_choice


def test_db_path_is_absolute_and_anchored_to_project_root():
    """DB_PATH must be an absolute path anchored to project_root / 'data'."""
    db_path = Path(config.DB_PATH)
    assert db_path.is_absolute()
    project_root = Path(__file__).resolve().parent.parent
    assert db_path.parent == project_root / "data"


def test_invalid_x_mode_raises_value_error():
    """Invalid X_MODE value must raise ValueError naming the variable and valid choices."""
    with pytest.raises(ValueError, match=r"X_MODE.*\[.*fake.*real.*\]"):
        validate_choice("X_MODE", "fak", ("fake", "real"))


def test_invalid_send_mode_raises_value_error():
    """Invalid SEND_MODE value must raise ValueError naming the variable and valid choices."""
    with pytest.raises(ValueError, match=r"SEND_MODE.*\[.*allowlist.*live.*\]"):
        validate_choice("SEND_MODE", "allowlst", ("allowlist", "live"))


def test_module_load_fails_on_invalid_x_mode():
    """Importing outreach.config with invalid X_MODE must exit non-zero with stderr naming X_MODE."""
    env = os.environ.copy()
    env["X_MODE"] = "fak"
    res = subprocess.run(
        [sys.executable, "-c", "import outreach.config"],
        env=env,
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).resolve().parent.parent),
    )
    assert res.returncode != 0
    assert "X_MODE" in res.stderr
    assert "fake" in res.stderr
    assert "real" in res.stderr


def test_module_load_fails_on_invalid_send_mode():
    """Importing outreach.config with invalid SEND_MODE must exit non-zero with stderr naming SEND_MODE."""
    env = os.environ.copy()
    env["SEND_MODE"] = "allowlst"
    res = subprocess.run(
        [sys.executable, "-c", "import outreach.config"],
        env=env,
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).resolve().parent.parent),
    )
    assert res.returncode != 0
    assert "SEND_MODE" in res.stderr
    assert "allowlist" in res.stderr


def test_module_load_fails_on_invalid_send_channel():
    """Importing outreach.config with invalid SEND_CHANNEL must exit non-zero with stderr naming SEND_CHANNEL."""
    env = os.environ.copy()
    env["SEND_CHANNEL"] = "invalid_channel"
    res = subprocess.run(
        [sys.executable, "-c", "import outreach.config"],
        env=env,
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).resolve().parent.parent),
    )
    assert res.returncode != 0
    assert "SEND_CHANNEL" in res.stderr
    assert "manual" in res.stderr
    assert "api" in res.stderr


def test_module_load_fails_on_invalid_llm_provider():
    """Importing outreach.config with invalid LLM_PROVIDER must exit non-zero with stderr naming LLM_PROVIDER."""
    env = os.environ.copy()
    env["LLM_PROVIDER"] = "invalid_provider"
    res = subprocess.run(
        [sys.executable, "-c", "import outreach.config"],
        env=env,
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).resolve().parent.parent),
    )
    assert res.returncode != 0
    assert "LLM_PROVIDER" in res.stderr
    assert "ollama" in res.stderr
    assert "template" in res.stderr
    assert "anthropic" in res.stderr
