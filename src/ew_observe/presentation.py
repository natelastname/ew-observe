"""Human-oriented terminal presentation for EW decision traces."""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from .decision import DecisionTrace


def _factorization(value: int) -> str:
    """Render a positive integer as a compact prime factorization."""

    if value < 1:
        raise ValueError("value must be positive")
    if value == 1:
        return "1"

    remaining = value
    pieces: list[str] = []
    divisor = 2
    while divisor * divisor <= remaining:
        exponent = 0
        while remaining % divisor == 0:
            remaining //= divisor
            exponent += 1
        if exponent:
            pieces.append(str(divisor) if exponent == 1 else f"{divisor}^{exponent}")
        divisor = 3 if divisor == 2 else divisor + 2
    if remaining > 1:
        pieces.append(str(remaining))
    return "·".join(pieces)


def _primes(primes: Iterable[int]) -> str:
    values = sorted(primes)
    return ", ".join(str(prime) for prime in values) if values else "—"


def _render_table(
    headers: Sequence[str],
    rows: Sequence[Sequence[str]],
    *,
    right_align: frozenset[int] = frozenset(),
) -> list[str]:
    """Render a small dependency-free box table for terminal output."""

    if any(len(row) != len(headers) for row in rows):
        raise ValueError("table rows must match header width")

    widths = [len(header) for header in headers]
    for row in rows:
        for index, cell in enumerate(row):
            widths[index] = max(widths[index], len(cell))

    def border(left: str, middle: str, right: str) -> str:
        return left + middle.join("─" * (width + 2) for width in widths) + right

    def render_row(row: Sequence[str]) -> str:
        cells: list[str] = []
        for index, (cell, width) in enumerate(zip(row, widths, strict=True)):
            cells.append(cell.rjust(width) if index in right_align else cell.ljust(width))
        return "│ " + " │ ".join(cells) + " │"

    output = [border("┌", "┬", "┐"), render_row(headers), border("├", "┼", "┤")]
    output.extend(render_row(row) for row in rows)
    output.append(border("└", "┴", "┘"))
    return output


def render_decision_trace(trace: DecisionTrace, *, diagnostics: bool = False) -> str:
    """Render one greedy choice as a human-readable explanation.

    The default view emphasizes the mathematical narrative: the incoming state,
    the locally admissible smaller threats, the historical occurrence that paid
    each threat, and the observed winner. Aggregate exhaustive-scan counters are
    available with ``diagnostics=True`` but are intentionally hidden by default.
    """

    previous_n = trace.n - 1
    two_back_n = trace.n - 2
    winner = trace.winner_audit

    lines = [
        f"EW step {trace.n}: choose a_{trace.n} = {trace.winner}",
        "",
        "Incoming state",
        f"  a_{two_back_n} (two back) : {trace.two_back} = {_factorization(trace.two_back)}",
        f"  a_{previous_n} (previous) : {trace.previous} = {_factorization(trace.previous)}",
        f"  carry primes available    : {_primes(trace.legal_carriers)}",
        f"  least unused integer      : {trace.least_unused}",
        "",
        f"Smaller admissible threats (< {trace.winner})",
        f"  Every row below satisfies the local EW rules and would beat {trace.winner} if it were unused.",
    ]

    threat_rows = [
        (
            str(threat.value),
            _factorization(threat.value),
            _primes(threat.retained_primes),
            _primes(threat.introduced_primes),
            f"a_{threat.used_at}" if threat.used_at is not None else "UNPAID",
        )
        for threat in trace.threats
    ]
    if threat_rows:
        lines.extend(
            _render_table(
                ("candidate", "factorization", "shared w/ prev", "new primes", "paid at"),
                threat_rows,
                right_align=frozenset({0}),
            )
        )
    else:
        lines.append("  none")

    lines.extend(
        (
            "",
            "Winner",
            f"  {winner.value} = {_factorization(winner.value)}",
            f"  shared with previous : {_primes(winner.retained_primes)}",
            f"  new primes            : {_primes(winner.introduced_primes)}",
            "",
        )
    )

    if trace.threats:
        lines.append(
            f"Conclusion: all {trace.paid_threat_count} smaller admissible threats were already used, "
            f"so {trace.winner} is the greedy winner."
        )
        last = trace.last_paid_threat
        if last is not None:
            lines.append(
                f"Last threat paid: {last.value} = {_factorization(last.value)} at a_{last.used_at}."
            )
    else:
        lines.append(
            f"Conclusion: there are no smaller locally admissible threats, so {trace.winner} wins immediately."
        )

    if diagnostics:
        lines.extend(
            (
                "",
                "Diagnostics (rejection counts overlap)",
                f"  values below winner : {trace.values_below_winner}",
                f"  already used        : {trace.used_below_winner}",
                f"  threats             : {len(trace.threats)}",
            )
        )
        for reason, count in trace.rejection_reason_counts:
            lines.append(f"  {reason.value:<22}: {count}")

    return "\n".join(lines)
