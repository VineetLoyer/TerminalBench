from app import resolve_count


def test_explicit_flag_wins():
    assert resolve_count(3) == 3


def test_default_when_unset(monkeypatch):
    monkeypatch.delenv("APP_COUNT", raising=False)
    assert resolve_count(None, default=1) == 1
