from pathlib import Path

from streamlit.testing.v1 import AppTest

from outreach import config, db, llm

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
    at.text_input(key=f"reply_note_{mid}").input("Happy to talk next week")
    at.button(key=f"reply_{mid}").click().run()
    at.button(key=f"handled_{mid}").click().run()
    assert not at.exception

    row = conn.execute("SELECT * FROM messages WHERE id = ?", (mid,)).fetchone()
    assert (row["status"], row["channel"], row["reply_text"]) == ("sent", "manual", "Happy to talk next week")
    assert row["sent_at"] and row["replied_at"] and row["handled_at"]
    conn.close()


def _drafts(at: AppTest) -> AppTest:
    """Create a campaign, search the fake GitHub, score and draft (alex_builder and sarah_robotics get drafts)."""
    at.text_input(key="c_name").input("Robotics SEA")
    at.text_area(key="c_segment").input("People building robots in Southeast Asia")
    at.text_input(key="c_keywords").input("robotics, robot learning, machine learning")
    at.text_area(key="c_context").input("GenAI Fund backs early robotics founders in Southeast Asia.")
    at.button(key="c_create").click().run()
    at.button(key="search").click().run()
    at.button(key="score").click().run()
    return at.button(key="draft").click().run()


def _mid(conn, handle: str) -> int:
    return conn.execute("SELECT m.id FROM messages m JOIN prospects p ON p.id = m.prospect_id "
                        "WHERE p.x_username = ?", (handle,)).fetchone()["id"]


def test_do_not_contact_is_not_undone_by_another_tab(tmp_path, monkeypatch):
    a = _drafts(_app(tmp_path, monkeypatch).run())
    b = AppTest.from_file(APP, default_timeout=30).run()      # second browser tab, same database
    a.toggle[0].set_value(True).run()                          # tab A: first person (alex_builder) -> do not contact
    b.run()                                                    # tab B reruns with its old toggle state
    conn = db.connect(config.DB_PATH)
    assert conn.execute("SELECT do_not_contact FROM prospects WHERE x_username = 'alex_builder'").fetchone()[0] == 1
    conn.close()


def test_review_shows_untrusted_text_as_plain_text_and_no_x_link(tmp_path, monkeypatch):
    at = _app(tmp_path, monkeypatch).run()
    _drafts(at)
    conn = db.connect(config.DB_PATH)
    with conn:
        conn.execute("UPDATE prospects SET name = '![px](https://example.invalid/t.png)' "
                     "WHERE x_username = 'alex_builder'")
        conn.execute("UPDATE messages SET evidence = ? WHERE id = ?",
                     ('[{"source_id": "x](https://example.invalid/p", "quote": "q"}]', _mid(conn, "alex_builder")))
    conn.close()
    at.run()
    assert not at.exception
    shown = [m.value for m in at.markdown]
    assert not [m for m in shown if "x.com/" in m]            # no way to message anyone before Start reserves it
    assert not [m for m in shown if "example.invalid" in m]   # profile and model text never become links or images


def test_mark_replied_twice_does_not_mark_the_next_person(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "SEND_MODE", "live")   # manual channel: any approved person
    at = _drafts(_app(tmp_path, monkeypatch).run())
    conn = db.connect(config.DB_PATH)
    first, second = [r[0] for r in conn.execute("SELECT id FROM messages ORDER BY id LIMIT 2")]
    for mid in (first, second):
        at.button(key=f"approve_{mid}").click().run()
        at.button(key=f"start_{mid}").click().run()
        at.button(key=f"send_sent_{mid}").click().run()
    at.selectbox(key="reply_pick").select(first)
    at.text_input(key=f"reply_note_{first}").input("note for first")
    at.button(key=f"reply_{first}").click().run()
    assert not at.exception
    assert not [b for b in at.button if b.key == f"reply_{first}"]   # a second click has nothing to hit
    assert at.text_input(key=f"reply_note_{second}").value == ""
    assert conn.execute("SELECT replied_at FROM messages WHERE id = ?", (second,)).fetchone()[0] is None
    conn.close()


def test_draft_next_n_tries_each_person_once(tmp_path, monkeypatch):
    calls = []

    def drafter(ctx, prospect, sources, fit):   # paid or slow per call, so a failing person must not be retried
        calls.append(prospect["x_username"])
        if prospect["x_username"] == calls[0]:     # the first person always fails
            raise llm.LLMUnavailable("bad reply")
        return llm.template_draft(ctx, prospect, sources, fit)

    monkeypatch.setattr(llm, "get_drafter", lambda conn: drafter)
    at = _drafts(_app(tmp_path, monkeypatch).run())
    assert not at.exception
    assert sorted(calls) == sorted(set(calls))


def test_drafting_error_shows_no_success_message(tmp_path, monkeypatch):
    def down(*a):
        raise llm.LLMDown("Ollama is not running")

    monkeypatch.setattr(llm, "get_drafter", lambda conn: down)
    at = _drafts(_app(tmp_path, monkeypatch).run())
    assert [e.value for e in at.error] == ["Drafting stopped: Ollama is not running"]
    assert not at.success or all("draft" not in s.value.lower() for s in at.success)


def test_approved_message_can_be_rejected_in_send(tmp_path, monkeypatch):
    at = _drafts(_app(tmp_path, monkeypatch).run())
    conn = db.connect(config.DB_PATH)
    mid = _mid(conn, "alex_builder")
    at.button(key=f"approve_{mid}").click().run()
    at.button(key=f"send_reject_{mid}").click().run()
    assert conn.execute("SELECT status FROM messages WHERE id = ?", (mid,)).fetchone()[0] == "rejected"
    conn.close()
