from app import render_row


def test_three_columns_use_single_space():
    line = render_row(["aa", "bbb", "c"], [4, 4, 2])
    assert line == "aa   bbb  c "
    assert len(line) == 4 + 4 + 2 + 2
