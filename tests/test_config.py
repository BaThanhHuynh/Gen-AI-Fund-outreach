from pathlib import Path
from outreach import config


def test_db_path_is_absolute_and_anchored_to_project_root():
    """DB_PATH must be an absolute path anchored to project_root / 'data'."""
    db_path = Path(config.DB_PATH)
    assert db_path.is_absolute()
    project_root = Path(__file__).resolve().parent.parent
    assert db_path.parent == project_root / "data"
