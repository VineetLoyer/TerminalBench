def render_row(cells: list[str], widths: list[int]) -> str:
    parts = []
    for cell, width in zip(cells, widths):
        text = cell if len(cell) <= width else cell[: max(width - 1, 0)] + "…"
        parts.append(text.ljust(width)[:width])
    return " ".join(parts)
