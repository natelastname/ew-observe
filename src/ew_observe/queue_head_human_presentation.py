"""Human-only current-head view with B/A/W fixed in every table."""

from __future__ import annotations

from collections.abc import Sequence

from .decision import Support
from .human_sort import prime_exponents, prime_lex_key
from .incidence import IncidenceRow, IncidenceTable, render_text as render_incidence_text
from .presentation import OutputFormat
from .queue_frontier_presentation import HUMAN_SORT_ORDERS
from .queue_heads import ExactQueueHead, QueueHeadTrace


def _coords(
    value: int,
    *,
    introduced: Support = frozenset(),
    mark_roles: bool = False,
) -> tuple[tuple[int, str], ...]:
    cells: list[tuple[int, str]] = []
    for prime, exponent in prime_exponents(value):
        label = str(exponent)
        if mark_roles and prime in introduced:
            label = "+" + label
        cells.append((prime, label))
    return tuple(cells)


def _ordered(trace: QueueHeadTrace, sort_order: str) -> tuple[ExactQueueHead, ...]:
    if sort_order not in HUMAN_SORT_ORDERS:
        raise ValueError(f"unknown human sort order {sort_order!r}")
    queues = list(trace.competitor_heads)
    if sort_order == "value":
        queues.sort(key=lambda q: q.value)
    elif sort_order == "depth":
        queues.sort(key=lambda q: (-q.depth, q.value))
    elif sort_order == "prime-lex":
        queues.sort(key=lambda q: (prime_lex_key(q.value), q.value))
    else:
        queues.sort(
            key=lambda q: (
                min(q.support & trace.decision.previous_support, default=float("inf")),
                q.value,
            )
        )
    return tuple(queues)


def _table(trace: QueueHeadTrace, queues: Sequence[ExactQueueHead]) -> IncidenceTable:
    d = trace.decision
    w = trace.winner_head
    rows = [
        IncidenceRow(("B", str(d.two_back), ""), _coords(d.two_back)),
        IncidenceRow(("A", str(d.previous), ""), _coords(d.previous)),
        IncidenceRow(
            ("W", str(d.winner), str(w.depth)),
            _coords(d.winner, introduced=w.support - d.previous_support, mark_roles=True),
        ),
    ]
    for q in queues:
        rows.append(
            IncidenceRow(
                ("H", str(q.value), str(q.depth)),
                _coords(q.value, introduced=q.support - d.previous_support, mark_roles=True),
            )
        )
    features = tuple(sorted({p for row in rows for p, _ in row.coordinates}))
    return IncidenceTable(("role", "object", "depth"), features, tuple(rows))


def _width(table: IncidenceTable) -> int:
    return max(
        (len(line) for line in render_incidence_text(table, max_width=0).splitlines()),
        default=0,
    )


def _groups(
    trace: QueueHeadTrace,
    *,
    max_width: int,
    candidates_per_table: int,
    sort_order: str,
) -> tuple[tuple[ExactQueueHead, ...], ...]:
    if max_width < 0:
        raise ValueError("max_width must be nonnegative")
    if candidates_per_table < 0:
        raise ValueError("candidates_per_table must be nonnegative")

    queues = _ordered(trace, sort_order)
    if not queues:
        return ((),)
    groups: list[list[ExactQueueHead]] = []
    current: list[ExactQueueHead] = []
    for q in queues:
        split_count = (
            bool(current)
            and candidates_per_table > 0
            and len(current) >= candidates_per_table
        )
        split_width = False
        if current and not split_count and max_width > 0:
            split_width = _width(_table(trace, [*current, q])) > max_width
        if split_count or split_width:
            groups.append(current)
            current = []
        current.append(q)
    if current:
        groups.append(current)
    return tuple(tuple(group) for group in groups)


def render_queue_head_human_trace(
    trace: QueueHeadTrace,
    *,
    output_format: OutputFormat | str = OutputFormat.TEXT,
    diagnostics: bool = False,
    max_width: int = 160,
    candidates_per_table: int = 0,
    sort_order: str = "value",
) -> str:
    format_ = OutputFormat(output_format)
    groups = _groups(
        trace,
        max_width=max_width,
        candidates_per_table=candidates_per_table,
        sort_order=sort_order,
    )
    if format_ is OutputFormat.TEXT:
        lines = [
            f"EW step {trace.decision.n}: current-head view; human sort={sort_order}",
            "",
        ]
        start = 1
        for i, group in enumerate(groups, start=1):
            end = start + len(group) - 1
            if len(groups) > 1:
                lines.append(f"head rows {start}–{end} ({i}/{len(groups)})")
            lines.append(render_incidence_text(_table(trace, group), max_width=0))
            lines.append("")
            start = end + 1
        if len(groups) > 1:
            lines.append("Each table repeats B, A, and W.")
        lines.append("role: H=current nonwinning exact-support queue head; W=actual winner")
        if diagnostics:
            lines.extend(("", f"represented queues: {len(trace.heads)}"))
        return "\n".join(lines) + "\n"
    if format_ is OutputFormat.MARKDOWN:
        lines = [
            f"## EW step {trace.decision.n}: current-head view",
            "",
            f"Human sort: `{sort_order}`.",
            "",
        ]
        for i, group in enumerate(groups, start=1):
            if len(groups) > 1:
                lines.extend((f"### Head table {i}/{len(groups)}", ""))
            lines.extend(
                (
                    "| role | object | depth | support |",
                    "| --- | ---: | ---: | --- |",
                    f"| B | {trace.decision.two_back} |  | `{','.join(map(str, sorted(trace.decision.two_back_support)))}` |",
                    f"| A | {trace.decision.previous} |  | `{','.join(map(str, sorted(trace.decision.previous_support)))}` |",
                    f"| W | {trace.decision.winner} | {trace.winner_head.depth} | `{','.join(map(str, sorted(trace.winner_head.support)))}` |",
                )
            )
            for q in group:
                lines.append(
                    f"| H | {q.value} | {q.depth} | `{','.join(map(str, sorted(q.support)))}` |"
                )
            lines.append("")
        return "\n".join(lines)
    raise ValueError("queue-head human presentation accepts only text or markdown")
