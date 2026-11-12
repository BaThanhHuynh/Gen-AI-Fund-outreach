import pytest
from outreach import config
from outreach.fake_x import FakeXClient
from outreach import doctor


def test_doctor_dm_test_blocks_stranger_and_does_not_send(conn, monkeypatch, capsys):
    """doctor --dm-test must reject usernames not in SEND_ALLOWLIST, send nothing, and return non-zero code."""
    monkeypatch.setattr(config, "SEND_ALLOWLIST", ["allowed_user"])
    fake_x = FakeXClient(conn)

    exit_code = doctor.run_doctor(["--dm-test", "unauthorized_stranger"], conn=conn, x=fake_x)

    captured = capsys.readouterr()
    assert exit_code != 0
    assert "SEND_ALLOWLIST" in captured.out or "SEND_ALLOWLIST" in captured.err
    assert len(fake_x.sent) == 0


def test_doctor_dm_test_allows_user_case_insensitive_and_strips_at(conn, monkeypatch, capsys):
    """doctor --dm-test matches allowlist case-insensitively and strips leading @."""
    monkeypatch.setattr(config, "SEND_ALLOWLIST", ["alex_builder"])
    fake_x = FakeXClient(conn)

    exit_code = doctor.run_doctor(["--dm-test", "@ALEX_BUILDER"], conn=conn, x=fake_x)

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "PASS" in captured.out
    assert len(fake_x.sent) == 1
    assert fake_x.sent[0][0] == "1001"  # alex_builder user ID in FakeXClient

