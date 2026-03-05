from app import resolve_count


def test_env_overrides_default(monkeypatch):
    monkeypatch.setenv("APP_COUNT", "5")
    assert resolve_count(None, default=1) == 5


def test_flag_overrides_env(monkeypatch):
    monkeypatch.setenv("APP_COUNT", "5")
    assert resolve_count(2, default=1) == 2
