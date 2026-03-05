def encode_field(raw: str):
    if ":=" in raw:
        key, value = raw.split(":=", 1)
        return key, _parse_jsonish(value)
    key, value = raw.split("=", 1)
    return key, value


def _parse_jsonish(value: str):
    if value == "true":
        return True
    if value == "false":
        return False
    if value.isdigit():
        return int(value)
    return value
