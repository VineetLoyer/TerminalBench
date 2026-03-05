from app import visible


def test_normal_path():
    assert visible("src/main.py", show_hidden=False)


def test_git_dir_stays_hidden():
    assert not visible(".git/config", show_hidden=False)
