from app import render_row


def test_single_column_width():
    assert len(render_row(["hello"], [8])) == 8


def test_pads_short_cell():
    assert render_row(["ab"], [4]) == "ab  "
