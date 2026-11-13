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


def test_doctor_env_check_fails_on_empty_keys(conn, monkeypatch, capsys):
    """X_MODE=real requires non-empty GITHUB_TOKEN; empty string must be treated as missing."""
    monkeypatch.setattr(config, "X_MODE", "real")
    monkeypatch.setattr(config, "GITHUB_TOKEN", "")
    monkeypatch.setenv("GITHUB_TOKEN", "")

    class NoCallGitHub:
        def rate_limit(self):
            raise RuntimeError("GitHub must not be called without a token")

    exit_code = doctor.run_doctor([], conn=conn, gh=NoCallGitHub())

    captured = capsys.readouterr()
    assert exit_code != 0
    assert "FAIL" in captured.out
    assert "GITHUB_TOKEN" in captured.out


def test_doctor_manual_channel_skips_x_check(conn, monkeypatch, capsys):
    """When SEND_CHANNEL=manual, doctor skips calling x.me() and passes without X credentials."""
    monkeypatch.setattr(config, "SEND_CHANNEL", "manual")

    class BombClient:
        def me(self):
            raise RuntimeError("x.me() must not be called when SEND_CHANNEL=manual")

    exit_code = doctor.run_doctor([], conn=conn, x=BombClient())

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Manual send channel (no X API credentials required)" in captured.out




def test_doctor_fails_on_bad_github_token(conn, monkeypatch, capsys):
    """In X_MODE=real, doctor must report a rejected GitHub token as FAIL and return non-zero."""
    from outreach.github import GitHubAuthError
    monkeypatch.setattr(config, "X_MODE", "real")
    monkeypatch.setattr(config, "GITHUB_TOKEN", "bad")
    monkeypatch.setenv("GITHUB_TOKEN", "bad")   # so the env check passes and only the GitHub step can fail

    class BadGitHub:
        def rate_limit(self):
            raise GitHubAuthError(401, "Bad credentials")

    exit_code = doctor.run_doctor([], conn=conn, x=FakeXClient(conn), gh=BadGitHub())

    out = capsys.readouterr().out
    assert exit_code == 1
    assert "FAIL: GitHub rejected GITHUB_TOKEN" in out
    assert "github.com/settings/tokens" in out


def test_doctor_fails_when_ollama_model_missing(conn, monkeypatch, capsys):
    """LLM_PROVIDER=ollama: a running Ollama without OLLAMA_MODEL is FAIL with the pull command."""
    import httpx
    monkeypatch.setattr(config, "X_MODE", "real")
    monkeypatch.setattr(config, "LLM_PROVIDER", "ollama")
    monkeypatch.setattr(config, "OLLAMA_MODEL", "qwen3:4b")

    def handler(request):
        assert request.url.path == "/api/tags"
        return httpx.Response(200, json={"models": [{"name": "llama3:8b", "model": "llama3:8b"}]})

    exit_code = doctor.run_doctor([], conn=conn, x=FakeXClient(conn),
                                  ollama_transport=httpx.MockTransport(handler))

    out = capsys.readouterr().out
    assert exit_code == 1
    assert "FAIL" in out
    assert "FAIL: Model qwen3:4b is not installed" in out
    assert "ollama pull qwen3:4b" in out


def test_doctor_skips_ollama_in_fake_mode(conn, monkeypatch, capsys):
    """X_MODE=fake always drafts with template, so a missing Ollama must not make doctor fail."""
    import httpx
    monkeypatch.setattr(config, "LLM_PROVIDER", "ollama")

    def handler(request):
        raise AssertionError("fake mode must not call Ollama")

    exit_code = doctor.run_doctor([], conn=conn, x=FakeXClient(conn),
                                  ollama_transport=httpx.MockTransport(handler))

    assert "[Ollama]" not in capsys.readouterr().out
    assert exit_code == 0
