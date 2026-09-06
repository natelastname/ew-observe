"""Human- and machine-oriented presentation for EW decision traces."""

from __future__ import annotations

import csv
import io
import json
from collections.abc import Iterable, Sequence
from enum import StrEnum

from .decision import CandidateAudit, DecisionTrace
from .incidence import IncidenceRow, IncidenceTable, render_text as render_incidence_text


class OutputFormat(StrEnum):
    """Supported microscope output formats."""

    TEXT = "text"
    MARKDOWN = "markdown"
    JSON = "json"
    TSV = "tsv"
    CSV = "csv"


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


def _factor_piece(prime: int, exponent: int) -> str:
    return str(prime) if exponent == 1 else f"{prime}^{exponent}"


def _factorization(value: int) -> str:
    """Render a positive integer as a compact prime factorization."""

    factors = _prime_exponents(value)
    if not factors:
        return "1"
    return "·".join(_factor_piece(prime, exponent) for prime, exponent in factors)


def _role_factorization(audit: CandidateAudit) -> str:
    """Render factors with ``+`` marking primes introduced over the predecessor."""

    factors = _prime_exponents(audit.value)
    if not factors:
        return "1"
    pieces: list[str] = []
    for prime, exponent in factors:
        prefix = "+" if prime in audit.introduced_primes else ""
        pieces.append(prefix + _factor_piece(prime, exponent))
    return "·".join(pieces)


def _primes(primes: Iterable[int]) -> str:
    values = sorted(primes)
    return ",".join(str(prime) for prime in values) if values else ""


def _human_primes(primes: Iterable[int]) -> str:
    label = _primes(primes)
    return label if label else "—"


def _render_grid(
    headers: Sequence[str],
    rows: Sequence[Sequence[str]],
    *,
    right_align: frozenset[int] = frozenset(),
) -> str:
    """Render a compact whitespace grid."""

    if any(len(row) != len(headers) for row in rows):
        raise ValueError("table rows must match header width")
    widths = [len(header) for header in headers]
    for row in rows:
        for index, cell in enumerate(row):
            widths[index] = max(widths[index], len(cell))

    def render_row(row: Sequence[str]) -> str:
        cells: list[str] = []
        for index, (cell, width) in enumerate(zip(row, widths, strict=True)):
            cells.append(cell.rjust(width) if index in right_align else cell.ljust(width))
        return "  ".join(cells).rstrip()

    divider = "  ".join("-" * width for width in widths).rstrip()
    return "\n".join((render_row(headers), divider, *(render_row(row) for row in rows)))


def _audit_payload(audit: CandidateAudit) -> dict[str, object]:
    return {
        "value": audit.value,
        "factorization": _factorization(audit.value),
        "role_factorization": _role_factorization(audit),
        "support": sorted(audit.support),
        "used_at": audit.used_at,
        "predecessor_overlap": sorted(audit.predecessor_overlap),
        "two_back_overlap": sorted(audit.two_back_overlap),
        "retained_primes": sorted(audit.retained_primes),
        "introduced_primes": sorted(audit.introduced_primes),
        "rejection_reasons": [reason.value for reason in audit.rejection_reasons],
        "structurally_admissible": audit.structurally_admissible,
        "globally_admissible": audit.globally_admissible,
    }


def _trace_payload(trace: DecisionTrace) -> dict[str, object]:
    return {
        "type": "ew-decision-trace",
        "n": trace.n,
        "state": {
            "two_back": {
                "n": trace.n - 2,
                "value": trace.two_back,
                "support": sorted(trace.two_back_support),
            },
            "previous": {
                "n": trace.n - 1,
                "value": trace.previous,
                "support": sorted(trace.previous_support),
            },
        },
        "legal_carriers": sorted(trace.legal_carriers),
        "least_unused": trace.least_unused,
        "threats": [_audit_payload(threat) for threat in trace.threats],
        "winner": _audit_payload(trace.winner_audit),
        "summary": {
            "values_below_winner": trace.values_below_winner,
            "used_below_winner": trace.used_below_winner,
            "threat_count": len(trace.threats),
            "paid_threat_count": trace.paid_threat_count,
            "unpaid_threat_count": trace.unpaid_threat_count,
            "last_paid_threat": (
                {
                    "value": trace.last_paid_threat.value,
                    "used_at": trace.last_paid_threat.used_at,
                }
                if trace.last_paid_threat is not None
                else None
            ),
        },
        "rejection_counts": {
            reason.value: count for reason, count in trace.rejection_reason_counts
        },
    }


def _trace_rows(trace: DecisionTrace) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for kind, audit in [
        *(("threat", threat) for threat in trace.threats),
        ("winner", trace.winner_audit),
    ]:
        rows.append(
            {
                "n": trace.n,
                "two_back": trace.two_back,
                "previous": trace.previous,
                "winner": trace.winner,
                "legal_carriers": _primes(trace.legal_carriers),
                "least_unused": trace.least_unused,
                "kind": kind,
                "value": audit.value,
                "factorization": _factorization(audit.value),
                "role_factorization": _role_factorization(audit),
                "support": _primes(audit.support),
                "shared_with_previous": _primes(audit.retained_primes),
                "new_primes": _primes(audit.introduced_primes),
                "used_at": audit.used_at if audit.used_at is not None else "",
                "status": "winner" if kind == "winner" else "paid",
            }
        )
    return rows


def _render_delimited(rows: Sequence[dict[str, object]], delimiter: str) -> str:
    output = io.StringIO()
    if not rows:
        return ""
    writer = csv.DictWriter(
        output,
        fieldnames=list(rows[0]),
        delimiter=delimiter,
        lineterminator="\n",
    )
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def _incidence_coordinates(
    value: int,
    *,
    introduced: frozenset[int] = frozenset(),
    mark_roles: bool = False,
) -> tuple[tuple[int, str], ...]:
    """Return prime-exponent cells, optionally marking introduced primes with ``+``."""

    cells: list[tuple[int, str]] = []
    for prime, exponent in _prime_exponents(value):
        label = str(exponent)
        if mark_roles and prime in introduced:
            label = "+" + label
        cells.append((prime, label))
    return tuple(cells)


def _decision_incidence_table(trace: DecisionTrace) -> IncidenceTable:
    """Build the sparse local prime-coordinate table for one greedy decision."""

    rows: list[IncidenceRow] = [
        IncidenceRow(
            leading=("B", str(trace.two_back), f"a_{trace.n - 2}"),
            coordinates=_incidence_coordinates(trace.two_back),
        ),
        IncidenceRow(
            leading=("A", str(trace.previous), f"a_{trace.n - 1}"),
            coordinates=_incidence_coordinates(trace.previous),
        ),
    ]
    for threat in trace.threats:
        rows.append(
            IncidenceRow(
                leading=(
                    "T",
                    str(threat.value),
                    f"a_{threat.used_at}" if threat.used_at is not None else "UNPAID",
                ),
                coordinates=_incidence_coordinates(
                    threat.value,
                    introduced=threat.introduced_primes,
                    mark_roles=True,
                ),
            )
        )
    winner = trace.winner_audit
    rows.append(
        IncidenceRow(
            leading=("W", str(winner.value), f"a_{trace.n}"),
            coordinates=_incidence_coordinates(
                winner.value,
                introduced=winner.introduced_primes,
                mark_roles=True,
            ),
        )
    )
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
        leading_headers=("role", "object", "occurrence"),
        features=features,
        rows=tuple(rows),
    )


def _render_trace_text(
    trace: DecisionTrace,
    *,
    diagnostics: bool,
    max_width: int,
) -> str:
    table = _decision_incidence_table(trace)
    lines = [
        f"EW step {trace.n}: choose a_{trace.n} = {trace.winner}",
        f"least unused = {trace.least_unused}; legal carry primes = {_human_primes(trace.legal_carriers)}",
        "",
        render_incidence_text(table, max_width=max_width),
        "",
        "role: B=two-back, A=previous, T=smaller admissible threat, W=winner",
        f"T/W cells: bare exponent = shared with a_{trace.n - 1}; +exponent = newly introduced prime",
        "B/A cells: ordinary prime exponents; blank cell = prime absent",
        "",
    ]

    if trace.threats:
        lines.append(
            f"All {trace.paid_threat_count} smaller locally admissible candidates were already used; "
            f"{trace.winner} wins."
        )
        last = trace.last_paid_threat
        if last is not None:
            lines.append(f"Last threat paid: {last.value} at a_{last.used_at}.")
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


def _render_trace_markdown(trace: DecisionTrace, *, diagnostics: bool) -> str:
    winner = trace.winner_audit
    lines = [
        f"## EW step {trace.n}: choose `a_{trace.n} = {trace.winner}`",
        "",
        f"- two back: `a_{trace.n - 2} = {trace.two_back} = {_factorization(trace.two_back)}`",
        f"- previous: `a_{trace.n - 1} = {trace.previous} = {_factorization(trace.previous)}`",
        f"- carry primes: `{_human_primes(trace.legal_carriers)}`",
        f"- least unused: `{trace.least_unused}`",
        "",
        f"Factor notation is relative to `a_{trace.n - 1}`: bare prime = shared; `+prime` = new.",
        "",
        "| candidate | factor roles | history |",
        "| ---: | --- | --- |",
    ]
    for threat in trace.threats:
        history = f"used at `a_{threat.used_at}`" if threat.used_at is not None else "**UNPAID**"
        lines.append(f"| {threat.value} | `{_role_factorization(threat)}` | {history} |")
    lines.append(f"| {winner.value} | `{_role_factorization(winner)}` | **WINNER** |")

    lines.extend(("", f"All {trace.paid_threat_count} smaller locally admissible candidates were already used; `{trace.winner}` wins."))
    if diagnostics:
        lines.extend(("", "### Diagnostics", ""))
        lines.append(f"- values below winner: {trace.values_below_winner}")
        lines.append(f"- already used: {trace.used_below_winner}")
        for reason, count in trace.rejection_reason_counts:
            lines.append(f"- {reason.value}: {count}")
    return "\n".join(lines) + "\n"


def render_decision_trace(
    trace: DecisionTrace,
    *,
    output_format: OutputFormat | str = OutputFormat.TEXT,
    diagnostics: bool = False,
    max_width: int = 120,
) -> str:
    """Render one exact greedy decision in the requested output format."""

    format_ = OutputFormat(output_format)
    if format_ is OutputFormat.TEXT:
        return _render_trace_text(
            trace,
            diagnostics=diagnostics,
            max_width=max_width,
        )
    if format_ is OutputFormat.MARKDOWN:
        return _render_trace_markdown(trace, diagnostics=diagnostics)
    if format_ is OutputFormat.JSON:
        return json.dumps(_trace_payload(trace), indent=2, sort_keys=False) + "\n"
    if format_ is OutputFormat.TSV:
        return _render_delimited(_trace_rows(trace), "\t")
    return _render_delimited(_trace_rows(trace), ",")


def _render_candidate_text(audit: CandidateAudit) -> str:
    reasons = ", ".join(reason.value for reason in audit.rejection_reasons) or "none"
    used = f"a_{audit.used_at}" if audit.used_at is not None else "—"
    return "\n".join(
        (
            f"Candidate {audit.value} before a_{audit.n}",
            f"  factorization : {_factorization(audit.value)}",
            f"  factor roles  : {_role_factorization(audit)}",
            f"  used at       : {used}",
            f"  local EW rules: {'PASS' if audit.structurally_admissible else 'FAIL'}",
            f"  globally live : {'YES' if audit.globally_admissible else 'NO'}",
            f"  rejection     : {reasons}",
            "",
            "Factor notation: bare prime = shared with predecessor; +prime = introduced.",
        )
    ) + "\n"


def render_candidate_audit(
    audit: CandidateAudit,
    *,
    output_format: OutputFormat | str = OutputFormat.TEXT,
) -> str:
    """Render one candidate audit in a human- or machine-readable format."""

    format_ = OutputFormat(output_format)
    if format_ is OutputFormat.TEXT:
        return _render_candidate_text(audit)
    if format_ is OutputFormat.MARKDOWN:
        payload = _audit_payload(audit)
        return (
            f"### Candidate `{audit.value}` before `a_{audit.n}`\n\n"
            f"- factorization: `{payload['factorization']}`\n"
            f"- factor roles: `{payload['role_factorization']}`\n"
            f"- used at: `{audit.used_at if audit.used_at is not None else 'unused'}`\n"
            f"- local EW rules: `{'PASS' if audit.structurally_admissible else 'FAIL'}`\n"
            f"- rejection reasons: `{', '.join(payload['rejection_reasons']) or 'none'}`\n"
        )
    if format_ is OutputFormat.JSON:
        return json.dumps(
            {"type": "ew-candidate-audit", "n": audit.n, **_audit_payload(audit)},
            indent=2,
            sort_keys=False,
        ) + "\n"

    row = {
        "n": audit.n,
        "value": audit.value,
        "factorization": _factorization(audit.value),
        "role_factorization": _role_factorization(audit),
        "support": _primes(audit.support),
        "shared_with_previous": _primes(audit.retained_primes),
        "new_primes": _primes(audit.introduced_primes),
        "used_at": audit.used_at if audit.used_at is not None else "",
        "structurally_admissible": audit.structurally_admissible,
        "globally_admissible": audit.globally_admissible,
        "rejection_reasons": ";".join(reason.value for reason in audit.rejection_reasons),
    }
    return _render_delimited([row], "\t" if format_ is OutputFormat.TSV else ",")