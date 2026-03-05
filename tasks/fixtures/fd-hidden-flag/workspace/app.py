def visible(path: str, show_hidden: bool) -> bool:
    """Return whether a walk should yield `path`.

    Bug: `show_hidden` is ignored, so every dot segment is dropped.
    """
    for part in path.split("/"):
        if part.startswith(".") and part not in {".", ".."}:
            return False
    return True
