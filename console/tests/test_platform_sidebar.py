from pathlib import Path

from components.platform_sidebar import _load_token_from_env_or_file, init_platform_session_state


class _FakeSessionState(dict):
    def __getattr__(self, name: str) -> object:
        return self[name]

    def __setattr__(self, name: str, value: object) -> None:
        self[name] = value


def test_load_token_from_env(monkeypatch) -> None:
    monkeypatch.setenv("EDD_BEARER_TOKEN", "env-token")
    monkeypatch.delenv("EDD_TOKEN_FILE", raising=False)
    assert _load_token_from_env_or_file() == "env-token"


def test_load_token_from_file(monkeypatch, tmp_path: Path) -> None:
    token_file = tmp_path / "edd-api.token"
    token_file.write_text("file-token\n", encoding="utf-8")
    monkeypatch.delenv("EDD_BEARER_TOKEN", raising=False)
    monkeypatch.setenv("EDD_TOKEN_FILE", str(token_file))
    assert _load_token_from_env_or_file() == "file-token"


def test_init_platform_session_state_sets_defaults_once(monkeypatch) -> None:
    fake_state = _FakeSessionState()
    monkeypatch.setattr("components.platform_sidebar.st.session_state", fake_state)
    monkeypatch.setattr("components.platform_sidebar.get_api_base_url", lambda: "http://localhost:8000")
    monkeypatch.setattr("components.platform_sidebar._load_token_from_env_or_file", lambda: "seed-token")

    init_platform_session_state()
    assert fake_state["api_base_url"] == "http://localhost:8000"
    assert fake_state["bearer_token"] == "seed-token"
    assert fake_state["tenant_id"] == "tenant-a"

    fake_state["bearer_token"] = "updated-token"
    init_platform_session_state()
    assert fake_state["bearer_token"] == "updated-token"
