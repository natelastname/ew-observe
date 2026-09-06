"""Queue-depth-oriented human presentation for EW decision traces."""

from __future__ import annotations

from collections.abc import Sequence

from .decision import CandidateAudit, DecisionTrace
from .incidence import IncidenceRow, IncidenceTable, render_text as render_incidence_text
from .queue_depth import exact_support_queue_depth


def _prime_exponents(value: int) -> tuple[tuple[int, int], ...]:
    if value < 1:
        raise ValueError("value must be positive")
    if value == 1:
        return ()

    remaining = value
    factors: list[tuple[int, int]] = []
    divisor = 2
    while divisor * divisor <= remaining:
        exponent = 0
        while remaining % divisor == 0:
            remaining //= divisor
            exponent += 1
        if exponent:
            factors.append((divisor, exponent))
        divisor = 3 if divisor == 2 else divisor + 2
    if remaining > 1:
        factors.append((remaining, 1))
    return tuple(factors)


def _incidence_coordinates(
    value: int,
    *,
    introduced: frozenset[int] = frozenset(),
    mark_roles: bool = False,
) -> tuple[tuple[int, str], ...]:
    cells: list[tuple[int, str]] = []
    for prime, exponent in _prime_exponents(value):
        label = str(exponent)
        if mark_roles and prime in introduced:
            label = "+" + label
        cells.append((prime, label))
    return tuple(cells)


def _human_primes(primes: frozenset[int]) -> str:
    return ",".join(str(prime) for prime in sorted(primes)) or "—"


def queue_depth_candidate_order(trace: DecisionTrace) -> tuple[CandidateAudit, ...]:
    """Return paid threats deepest-first, then by value, with winner last."""

    threats = sorted(
        trace.threats,
        key=lambda audit: (-exact_support_queue_depth(audit.value), audit.value),
    )
    return (*threats, trace.winner_audit)


def _candidate_row(trace: DecisionTrace, audit: CandidateAudit) -> IncidenceRow:
    is_winner = audit == trace.winner_audit
    return IncidenceRow(
        leading=(
            "W" if is_winner else "T",
            str(audit.value),
            str(exact_support_queue_depth(audit.value)),
        ),
        coordinates=_incidence_coordinates(
            audit.value,
            introduced=audit.introduced_primes,
            mark_roles=True,
        ),
    )


def _table(trace: DecisionTrace, candidates: Sequence[CandidateAudit]) -> IncidenceTable:
    rows = [
        IncidenceRow(
            leading=("B", str(trace.two_back), ""),
            coordinates=_incidence_coordinates(trace.two_back),
        ),
        IncidenceRow(
            leading=("A", str(trace.previous), ""),
            coordinates=_incidence_coordinates(trace.previous),
        ),
        *(_candidate_row(trace, audit) for audit in candidates),
    ]
    features = tuple(
        sorted(
            {
                prime
                for row in rows
                for prime, _cell in row.coordinates
            }
        )
    )
    return IncidenceTable(
        leading_headers=("role", "object", "depth"),
        features=features,
        rows=tuple(rows),
    )


def _table_width(table: IncidenceTable) -> int:
    rendered = render_incidence_text(table, max_width=0)
    return max((len(line) for line in rendered.splitlines()), default=0)


def _tables(
    trace: DecisionTrace,
    *,
    max_width: int,
    candidates_per_table: int,
) -> tuple[tuple[int, int, IncidenceTable], ...]:
    if max_width < 0:
        raise ValueError("max_width must be nonnegative")
    if candidates_per_table < 0:
        raise ValueError("candidates_per_table must be nonnegative")

    candidates = list(queue_depth_candidate_order(trace))
    groups: list[list[CandidateAudit]] = []
    current: list[CandidateAudit] = []

    for audit in candidates:
        split_for_count = (
            bool(current)
            and candidates_per_table > 0
            and len(current) >= candidates_per_table
        )
        split_for_width = False
        if current and not split_for_count and max_width > 0:
            split_for_width = _table_width(_table(trace, [*current, audit])) > max_width

        if split_for_count or split_for_width:
            groups.append(current)
            current = []
        current.append(audit)

    if current:
        groups.append(current)

    tables: list[tuple[int, int, IncidenceTable]] = []
    start = 1
    for group in groups:
        end = start + len(group) - 1
        tables.append((start, end, _table(trace, group)))
        start = end + 1
    return tuple(tables)


def render_queue_depth_decision_trace(
    trace: DecisionTrace,
    *,
    diagnostics: bool = False,
    max_width: int = 160,
    candidates_per_table: int = 0,
) -> str:
    """Render threats by descending exact-support queue depth."""

    tables = _tables(
        trace,
        max_width=max_width,
        candidates_per_table=candidates_per_table,
    )
    lines = [
        f"EW step {trace.n}: choose a_{trace.n} = {trace.winner}",
        f"least unused = {trace.least_unused}; legal carry primes = {_human_primes(trace.legal_carriers)}",
        "queue-depth mode: T rows sorted by descending depth, then ascending value; W stays last",
        "",
    ]

    for index, (start, end, table) in enumerate(tables, start=1):
        if len(tables) > 1:
            lines.append(f"candidate rows {start}–{end} ({index}/{len(tables)})")
        lines.append(render_incidence_text(table, max_width=0))
        lines.append("")

    if len(tables) > 1:
        lines.append("Each table repeats B and A; prime columns are local to the candidates shown.")
    lines.extend(
        (
            "depth = number of smaller values with exactly the same prime support (zero-based)",
            "role: B=two-back, A=previous, T=smaller admissible threat, W=winner",
            f"T/W cells: bare exponent = shared with a_{trace.n - 1}; +exponent = newly introduced prime",
            "B/A cells: ordinary prime exponents; blank cell = prime absent",
            "",
        )
    )

    if trace.threats:
        deepest = min(
            trace.threats,
            key=lambda audit: (-exact_support_queue_depth(audit.value), audit.value),
        )
        lines.append(
            f"All {trace.paid_threat_count} smaller locally admissible candidates were already used; "
            f"{trace.winner} wins."
        )
        lines.append(
            f"Deepest paid threat: {deepest.value} at queue depth "
            f"{exact_support_queue_depth(deepest.value)}."
        )
    else:
        lines.append(
            f"There are no smaller locally admissible candidates; {trace.winner} wins immediately."
        )

    if diagnostics:
        lines.extend(("", "Diagnostics (rejection counts overlap)"))
        lines.append(f"  values below winner : {trace.values_below_winner}")
        lines.append(f"  already used        : {trace.used_below_winner}")
        lines.append(f"  threats             : {len(trace.threats)}")
        for reason, count in trace.rejection_reason_counts:
            lines.append(f"  {reason.value:<22}: {count}")

    return "\n".join(lines) + "\n"
