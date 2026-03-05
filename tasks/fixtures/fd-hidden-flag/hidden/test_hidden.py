from app import visible


def test_hidden_flag_reveals_dotfiles():
    assert visible(".env", show_hidden=True)
    assert visible("src/.secret", show_hidden=True)


def test_hidden_flag_off_still_skips():
    assert not visible(".env", show_hidden=False)
    assert not visible("src/.secret", show_hidden=False)
