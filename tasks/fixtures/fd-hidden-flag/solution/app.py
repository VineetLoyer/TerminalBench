def visible(path: str, show_hidden: bool) -> bool:
    if show_hidden:
        return True
    for part in path.split("/"):
        if part.startswith(".") and part not in {".", ".."}:
            return False
    return True
