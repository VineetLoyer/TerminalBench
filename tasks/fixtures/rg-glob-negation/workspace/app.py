import fnmatch


def match_glob(path: str, patterns: list[str]) -> bool:
    """Include if any include matches and no exclude matches.

    Bug: the leading '!' stays on the pattern, so excludes never match.
    """
    name = path.split("/")[-1]
    includes = [item for item in patterns if not item.startswith("!")] or ["*"]
    excludes = [item[1:] for item in patterns if item.startswith("!")]
    included = any(fnmatch.fnmatch(name, pattern) for pattern in includes)
    excluded = any(fnmatch.fnmatch(name, "!" + pattern) for pattern in excludes)
    return included and not excluded
