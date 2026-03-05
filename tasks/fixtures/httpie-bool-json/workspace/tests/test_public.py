from app import encode_field


def test_integer_json():
    assert encode_field("n:=3") == ("n", 3)


def test_plain_string():
    assert encode_field("name=ada") == ("name", "ada")
