import os


def resolve_count(cli_value: int | None, default: int | None = 1) -> int:
    """Prefer the CLI flag, then APP_COUNT, then the default.

    Bug: the environment is only read when default is None, so a normal
    default hides APP_COUNT.
    """
    if cli_value is not None:
        return cli_value
    if default is None:
        raw = os.environ.get("APP_COUNT")
        if raw not in (None, ""):
            return int(raw)
        raise RuntimeError("count is required")
    return default
