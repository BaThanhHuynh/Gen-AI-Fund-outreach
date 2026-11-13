from pathlib import Path

from streamlit.testing.v1 import AppTest

from outreach import config, db

APP = str(Path(__file__).resolve().parent.parent / "app.py")


def _app(tmp_path, monkeypatch) -> AppTest:
    monkeypatch.setattr(config, "DB_PATH", str(tmp_path / "app.db"))  # never touch data/fake.db
    return AppTest.from_file(APP, default_timeout=30)


def test_app_runs_in_fake_mode(tmp_path, monkeypatch):
    at = _app(tmp_path, monkeypatch).run()
    assert not at.exception
    assert len(at.tabs) == 4


def test_manual_flow_find_to_handled(tmp_path, monkeypatch):
    """6.3 as a test: find -> score -> draft -> approve -> Start -> I sent it -> Mark replied -> Mark handled."""
    monkeypatch.setattr(config, "SEND_ALLOWLIST", ["alex_builder"])
    at = _app(tmp_path, monkeypatch).run()

    at.text_input(key="c_name").input("Robotics SEA")
    at.text_area(key="c_segment").input("People building robots in Southeast Asia")
    at.text_input(key="c_keywords").input("robotics")
    at.text_area(key="c_context").input("GenAI Fund backs early robotics founders in Southeast Asia.")
    at.button(key="c_create").click().run()
    at.button(key="search").click().run()
    at.button(key="score").click().run()
    at.button(key="draft").click().run()
    assert not at.exception

    conn = db.connect(config.DB_PATH)
    mid = conn.execute("SELECT m.id FROM messages m JOIN prospects p ON p.id = m.prospect_id "
                       "WHERE p.x_username = 'alex_builder'").fetchone()["id"]
    at.button(key=f"approve_{mid}").click().run()
    at.button(key=f"start_{mid}").click().run()
    at.button(key=f"send_sent_{mid}").click().run()
    at.selectbox(key="reply_pick").select(mid)
    at.text_input(key="reply_note").input("Happy to talk next week")
    at.button(key="reply").click().run()
    at.button(key=f"handled_{mid}").click().run()
    assert not at.exception

    row = conn.execute("SELECT * FROM messages WHERE id = ?", (mid,)).fetchone()
    assert (row["status"], row["channel"], row["reply_text"]) == ("sent", "manual", "Happy to talk next week")
    assert row["sent_at"] and row["replied_at"] and row["handled_at"]
    conn.close()
