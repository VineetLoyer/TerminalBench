from app import match_glob


def test_include_py():
    assert match_glob("pkg/a.py", ["*.py"])
    assert not match_glob("pkg/a.js", ["*.py"])
