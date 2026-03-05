from app import match_glob


def test_negated_min_js():
    patterns = ["*.js", "!*.min.js"]
    assert match_glob("static/app.js", patterns)
    assert not match_glob("static/app.min.js", patterns)


def test_only_excludes_default_to_all():
    assert not match_glob("notes.tmp", ["!*.tmp"])
    assert match_glob("notes.md", ["!*.tmp"])
