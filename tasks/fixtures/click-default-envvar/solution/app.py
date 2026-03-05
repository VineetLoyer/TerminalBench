import os


def resolve_count(cli_value: int | None, default: int | None = 1) -> int:
    if cli_value is not None:
        return cli_value
    raw = os.environ.get("APP_COUNT")
    if raw not in (None, ""):
        return int(raw)
    if default is None:
        raise RuntimeError("count is required")
    return default
