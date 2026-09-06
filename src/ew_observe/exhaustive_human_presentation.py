"""Human-only expanded threat presentation with fixed B/A/W context."""

from __future__ import annotations

from collections.abc import Sequence

from .decision import CandidateAudit, DecisionTrace
from .human_sort import prime_exponents, prime_lex_key
from .incidence import IncidenceRow, IncidenceTable, render_text as render_incidence_text
from .presentation import OutputFormat
from .queue_depth import exact_support_queue_depth
from .queue_frontier_presentation import HUMAN_SORT_ORDERS


def _coordinates(
    value: int,
    *,
    introduced: frozenset[int] = frozenset(),
    mark_roles: bool = False,
) -> tuple[tuple[int, str], ...]:
    cells: list[tuple[int, str]] = []
    for prime, exponent in prime_exponents(value):
        label = str(exponent)
        if mark_roles and prime in introduced:
            label = "+" + label
        cells.append((prime, label))
    return tuple(cells)


def _ordered_threats(trace: DecisionTrace, *, sort_order: str) -> tuple[CandidateAudit, ...]:
    if sort_order not in HUMAN_SORT_ORDERS:
        raise ValueError(
            f"unknown human sort order {sort_order!r}; choose one of {', '.join(HUMAN_SORT_ORDERS)}"
        )
    threats = list(trace.threats)
    if sort_order == "value":
        threats.sort(key=lambda audit: audit.value)
    elif sort_order == "depth":
        threats.sort(key=lambda audit: (-exact_support_queue_depth(audit.value), audit.value))
    elif sort_order == "prime-lex":
        threats.sort(key=lambda audit: (prime_lex_key(audit.value), audit.value))
    else:
        threats.sort(
            key=lambda audit: (
                min(audit.retained_primes, default=float("inf")),
                audit.value,
            )
        )
    return tuple(threats)


def _winner_row(trace: DecisionTrace) -> IncidenceRow:
    winner = trace.winner_audit
    return IncidenceRow(
        leading=("W", str(winner.value), f"a_{trace.n}"),
        coordinates=_coordinates(
            winner.value,
            introduced=winner.introduced_primes,
            mark_roles=True,
        ),
    )


def _threat_row(audit: CandidateAudit) -> IncidenceRow:
    return IncidenceRow(
        leading=(
            "T",
            str(audit.value),
            f"a_{audit.used_at}" if audit.used_at is not None else "UNPAID",
        ),
        coordinates=_coordinates(
            audit.value,
            introduced=audit.introduced_primes,
            mark_roles=True,
        ),
    )


def _table(trace: DecisionTrace, threats: Sequence[CandidateAudit]) -> IncidenceTable:
    rows = [
        IncidenceRow(
            leading=("B", str(trace.two_back), f"a_{trace.n - 2}"),
            coordinates=_coordinates(trace.two_back),
        ),
        IncidenceRow(
            leading=("A", str(trace.previous), f"a_{trace.n - 1}"),
            coordinates=_coordinates(trace.previous),
        ),
        _winner_row(trace),
        *(_threat_row(threat) for threat in threats),
    ]
    features = tuple(sorted({p for row in rows for p, _ in row.coordinates}))
    return IncidenceTable(
        leading_headers=("role", "object", "occurrence"),
        features=features,
        rows=tuple(rows),
    )


def _width(table: IncidenceTable) -> int:
    return max(
        (len(line) for line in render_incidence_text(table, max_width=0).splitlines()),
        default=0,
    )


def _groups(
    trace: DecisionTrace,
    *,
    max_width: int,
    candidates_per_table: int,
    sort_order: str,
) -> tuple[tuple[CandidateAudit, ...], ...]:
    if max_width < 0:
        raise ValueError("max_width must be nonnegative")
    if candidates_per_table < 0:
        raise ValueError("candidates_per_table must be nonnegative")

    threats = _ordered_threats(trace, sort_order=sort_order)
    if not threats:
        return ((),)

    groups: list[list[CandidateAudit]] = []
    current: list[CandidateAudit] = []
    for threat in threats:
        split_for_count = (
            bool(current)
            and candidates_per_table > 0
            and len(current) >= candidates_per_table
        )
        split_for_width = False
        if current and not split_for_count and max_width > 0:
            split_for_width = _width(_table(trace, [*current, threat])) > max_width
        if split_for_count or split_for_width:
            groups.append(current)
            current = []
        current.append(threat)
    if current:
        groups.append(current)
    return tuple(tuple(group) for group in groups)


def _render_text(
    trace: DecisionTrace,
    *,
    max_width: int,
    candidates_per_table: int,
    sort_order: str,
    diagnostics: bool,
) -> str:
    groups = _groups(
        trace,
        max_width=max_width,
        candidates_per_table=candidates_per_table,
        sort_order=sort_order,
    )
    lines = [
        f"EW step {trace.n}: choose a_{trace.n} = {trace.winner}",
        f"expanded threat view; human sort={sort_order}",
        "",
    ]
    start = 1
    for index, group in enumerate(groups, start=1):
        end = start + len(group) - 1
        if len(groups) > 1:
            lines.append(f"threat rows {start}–{end} ({index}/{len(groups)})")
        lines.append(render_incidence_text(_table(trace, group), max_width=0))
        lines.append("")
        start = end + 1
    if len(groups) > 1:
        lines.append("Each table repeats B, A, and W; prime columns are local to the threats shown.")
    lines.extend(
        (
            "role: B=two-back, A=previous, W=winner, T=already-used smaller admissible threat",
            f"T/W cells: bare exponent = shared with a_{trace.n - 1}; +exponent = newly introduced prime",
        )
    )
    if diagnostics:
        lines.extend(("", "Diagnostics (rejection counts overlap)"))
        for reason, count in trace.rejection_reason_counts:
            lines.append(f"  {reason.value:<22}: {count}")
    return "\n".join(lines) + "\n"


def _markdown_table(trace: DecisionTrace, threats: Sequence[CandidateAudit]) -> list[str]:
    lines = [
        "| role | object | occurrence | support |",
        "| --- | ---: | --- | --- |",
        f"| B | {trace.two_back} | a_{trace.n - 2} | `{','.join(map(str, sorted(trace.two_back_support)))}` |",
        f"| A | {trace.previous} | a_{trace.n - 1} | `{','.join(map(str, sorted(trace.previous_support)))}` |",
        f"| W | {trace.winner} | a_{trace.n} | `{','.join(map(str, sorted(trace.winner_support)))}` |",
    ]
    for threat in threats:
        lines.append(
            f"| T | {threat.value} | a_{threat.used_at} | `{','.join(map(str, sorted(threat.support)))}` |"
        )
    return lines


def _render_markdown(
    trace: DecisionTrace,
    *,
    max_width: int,
    candidates_per_table: int,
    sort_order: str,
) -> str:
    groups = _groups(
        trace,
        max_width=max_width,
        candidates_per_table=candidates_per_table,
        sort_order=sort_order,
    )
    lines = [
        f"## EW step {trace.n}: expanded threat view",
        "",
        f"Human sort: `{sort_order}`.",
        "",
    ]
    for index, group in enumerate(groups, start=1):
        if len(groups) > 1:
            lines.extend((f"### Threat table {index}/{len(groups)}", ""))
        lines.extend(_markdown_table(trace, group))
        lines.append("")
    return "\n".join(lines)


def render_exhaustive_human_trace(
    trace: DecisionTrace,
    *,
    output_format: OutputFormat | str = OutputFormat.TEXT,
    diagnostics: bool = False,
    max_width: int = 160,
    candidates_per_table: int = 0,
    sort_order: str = "value",
) -> str:
    """Render the expanded ledger. This module intentionally has no machine formats."""

    format_ = OutputFormat(output_format)
    if format_ is OutputFormat.TEXT:
        return _render_text(
            trace,
            max_width=max_width,
            candidates_per_table=candidates_per_table,
            sort_order=sort_order,
            diagnostics=diagnostics,
        )
    if format_ is OutputFormat.MARKDOWN:
        return _render_markdown(
            trace,
            max_width=max_width,
            candidates_per_table=candidates_per_table,
            sort_order=sort_order,
        )
    raise ValueError("expanded human presentation accepts only text or markdown")
