from pathlib import Path
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

