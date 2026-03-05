def render_row(cells: list[str], widths: list[int]) -> str:
    """Pad each cell and join columns with a single space.

    Bug: the joiner is three characters, so the line is wider than
    sum(widths) + len(cells) - 1.
    """
    parts = []
    for cell, width in zip(cells, widths):
        text = cell if len(cell) <= width else cell[: max(width - 1, 0)] + "…"
        parts.append(text.ljust(width)[:width])
    return " | ".join(parts)
