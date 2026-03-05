from app import encode_field


def test_true_is_bool():
    key, value = encode_field("ok:=true")
    assert key == "ok"
    assert value is True


def test_false_is_bool():
    assert encode_field("ok:=false")[1] is False
