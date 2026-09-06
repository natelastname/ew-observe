"""Small sparse incidence-table primitives for ew-observe.

The project deliberately owns this tiny renderer instead of depending on the
lex-earliest-seqs presentation layer. It is intended for prime-coordinate
microscope views and later event chronologies.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class IncidenceRow:
    """One row with fixed leading cells and sparse feature cells."""

    leading: tuple[str, ...]
    coordinates: tuple[tuple[int, str], ...]

    def cell(self, feature: int) -> str:
        for current, value in self.coordinates:
            if current == feature:
                return value
        return ""


@dataclass(frozen=True, slots=True)
class IncidenceTable:
    """A sparse integer-feature table with ordinary leading columns."""

    leading_headers: tuple[str, ...]
    features: tuple[int, ...]
    rows: tuple[IncidenceRow, ...]


def _cells(
    table: IncidenceTable,
    features: tuple[int, ...],
) -> tuple[tuple[str, ...], tuple[tuple[str, ...], ...]]:
    headers = (*table.leading_headers, *(str(feature) for feature in features))
    rows = tuple(
        (*row.leading, *(row.cell(feature) for feature in features))
        for row in table.rows
    )
    return headers, rows


def _widths(
    headers: tuple[str, ...],
    rows: tuple[tuple[str, ...], ...],
) -> tuple[int, ...]:
    widths = [len(header) for header in headers]
    for row in rows:
        for index, cell in enumerate(row):
            widths[index] = max(widths[index], len(cell))
    return tuple(widths)


def _render_grid(
    headers: tuple[str, ...],
    rows: tuple[tuple[str, ...], ...],
) -> str:
    widths = _widths(headers, rows)

    def render_row(row: tuple[str, ...]) -> str:
        return " ".join(
            cell.rjust(width)
            for cell, width in zip(row, widths, strict=True)
        ).rstrip()

    divider = " ".join("-" * width for width in widths).rstrip()
    return "\n".join((render_row(headers), divider, *(render_row(row) for row in rows)))


def _rendered_width(table: IncidenceTable, features: tuple[int, ...]) -> int:
    headers, rows = _cells(table, features)
    return max((len(line) for line in _render_grid(headers, rows).splitlines()), default=0)


def _feature_panels(
    table: IncidenceTable,
    *,
    max_width: int,
) -> tuple[tuple[int, ...], ...]:
    if not table.features:
        return ((),)
    if max_width <= 0:
        return (table.features,)

    panels: list[tuple[int, ...]] = []
    current: list[int] = []
    for feature in table.features:
        trial = (*current, feature)
        if current and _rendered_width(table, trial) > max_width:
            panels.append(tuple(current))
            current = [feature]
        else:
            current.append(feature)
    panels.append(tuple(current))
    return tuple(panels)


def render_text(table: IncidenceTable, *, max_width: int = 0) -> str:
    """Render a compact aligned sparse table.

    The default ``max_width=0`` means unlimited width and preserves all feature
    columns in one table. A positive width explicitly enables feature paneling.
    """

    panels = _feature_panels(table, max_width=max_width)
    rendered: list[str] = []
    for index, features in enumerate(panels, start=1):
        headers, rows = _cells(table, features)
        body = _render_grid(headers, rows)
        if len(panels) > 1:
            if features:
                title = f"prime columns {features[0]}–{features[-1]} ({index}/{len(panels)})"
            else:
                title = f"object columns ({index}/{len(panels)})"
            body = f"{title}\n{body}"
        rendered.append(body)
    return "\n\n".join(rendered)
