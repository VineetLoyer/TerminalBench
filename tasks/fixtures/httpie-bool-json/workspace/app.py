def encode_field(raw: str):
    """Split `name=value` (string) or `name:=value` (JSON scalar)."""
    if ":=" in raw:
        key, value = raw.split(":=", 1)
        return key, _parse_jsonish(value)
    key, value = raw.split("=", 1)
    return key, value


def _parse_jsonish(value: str):
    if value in {"true", "false"}:
        return value
    if value.isdigit():
        return int(value)
    return value
