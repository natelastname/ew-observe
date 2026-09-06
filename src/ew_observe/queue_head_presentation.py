"""Default queue-head-oriented presentation for EW decision traces."""

from __future__ import annotations

import csv
import io
import json
from collections.abc import Sequence

from .decision import Support
from .incidence import IncidenceRow, IncidenceTable, render_text as render_incidence_text
from .presentation import OutputFormat
from .queue_heads import ExactQueueHead, QueueHeadTrace


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


def _factorization(value: int) -> str:
    factors = _prime_exponents(value)
    if not factors:
        return "1"
    return "·".join(
        str(prime) if exponent == 1 else f"{prime}^{exponent}"
        for prime, exponent in factors
    )


def _incidence_coordinates(
    value: int,
    *,
    introduced: Support = frozenset(),
    mark_roles: bool = False,
) -> tuple[tuple[int, str], ...]:
    cells: list[tuple[int, str]] = []
    for prime, exponent in _prime_exponents(value):
        label = str(exponent)
        if mark_roles and prime in introduced:
            label = "+" + label
        cells.append((prime, label))
    return tuple(cells)


def _human_primes(primes: Support) -> str:
    return ",".join(str(prime) for prime in sorted(primes)) or "—"


def _primes(primes: Support) -> str:
    return ",".join(str(prime) for prime in sorted(primes))


def ordered_queue_heads(
    trace: QueueHeadTrace,
    *,
    queue_depth_order: bool = False,
) -> tuple[ExactQueueHead, ...]:
    """Order competitor heads for display, always leaving the winner last."""

    competitors = list(trace.competitor_heads)
    if queue_depth_order:
        competitors.sort(key=lambda head: (-head.depth, head.value))
    else:
        competitors.sort(key=lambda head: head.value)
    return (*competitors, trace.winner_head)


def _head_row(trace: QueueHeadTrace, head: ExactQueueHead) -> IncidenceRow:
    decision = trace.decision
    introduced = head.support - decision.previous_support
    return IncidenceRow(
        leading=("W" if head.is_winner else "H", str(head.value), str(head.depth)),
        coordinates=_incidence_coordinates(
            head.value,
            introduced=introduced,
            mark_roles=True,
        ),
    )


def _table(trace: QueueHeadTrace, heads: Sequence[ExactQueueHead]) -> IncidenceTable:
    decision = trace.decision
    rows = [
        IncidenceRow(
            leading=("B", str(decision.two_back), ""),
            coordinates=_incidence_coordinates(decision.two_back),
        ),
        IncidenceRow(
            leading=("A", str(decision.previous), ""),
            coordinates=_incidence_coordinates(decision.previous),
        ),
        *(_head_row(trace, head) for head in heads),
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
    trace: QueueHeadTrace,
    *,
    max_width: int,
    candidates_per_table: int,
    queue_depth_order: bool,
) -> tuple[tuple[int, int, IncidenceTable], ...]:
    if max_width < 0:
        raise ValueError("max_width must be nonnegative")
    if candidates_per_table < 0:
        raise ValueError("candidates_per_table must be nonnegative")

    heads = list(ordered_queue_heads(trace, queue_depth_order=queue_depth_order))
    groups: list[list[ExactQueueHead]] = []
    current: list[ExactQueueHead] = []

    for head in heads:
        split_for_count = (
            bool(current)
            and candidates_per_table > 0
            and len(current) >= candidates_per_table
        )
        split_for_width = False
        if current and not split_for_count and max_width > 0:
            split_for_width = _table_width(_table(trace, [*current, head])) > max_width

        if split_for_count or split_for_width:
            groups.append(current)
            current = []
        current.append(head)

    if current:
        groups.append(current)

    tables: list[tuple[int, int, IncidenceTable]] = []
    start = 1
    for group in groups:
        end = start + len(group) - 1
        tables.append((start, end, _table(trace, group)))
        start = end + 1
    return tuple(tables)


def _head_payload(head: ExactQueueHead) -> dict[str, object]:
    return {
        "kind": "winner" if head.is_winner else "head",
        "value": head.value,
        "queue_depth": head.depth,
        "factorization": _factorization(head.value),
        "support": sorted(head.support),
        "source_threats": list(head.source_threats),
    }


def _payload(trace: QueueHeadTrace, *, queue_depth_order: bool) -> dict[str, object]:
    decision = trace.decision
    ordered = ordered_queue_heads(trace, queue_depth_order=queue_depth_order)
    return {
        "type": "ew-decision-queue-head-trace",
        "view": "queue-heads",
        "ordering": (
            "queue-depth-desc,value-asc,winner-last"
            if queue_depth_order
            else "head-value-asc,winner-last"
        ),
        "n": decision.n,
        "state": {
            "two_back": {"n": decision.n - 2, "value": decision.two_back},
            "previous": {"n": decision.n - 1, "value": decision.previous},
        },
        "legal_carriers": sorted(decision.legal_carriers),
        "least_unused": decision.least_unused,
        "queue_heads": [_head_payload(head) for head in ordered],
        "exhaustive_threats": [
            {
                "value": threat.value,
                "support": sorted(threat.support),
                "used_at": threat.used_at,
            }
            for threat in decision.threats
        ],
    }


def _flat_rows(
    trace: QueueHeadTrace,
    *,
    queue_depth_order: bool,
) -> list[dict[str, object]]:
    decision = trace.decision
    rows: list[dict[str, object]] = []
    for head in ordered_queue_heads(trace, queue_depth_order=queue_depth_order):
        rows.append(
            {
                "n": decision.n,
                "kind": "winner" if head.is_winner else "head",
                "value": head.value,
                "queue_depth": head.depth,
                "support": _primes(head.support),
                "new_primes": _primes(head.support - decision.previous_support),
                "source_threats": ";".join(str(value) for value in head.source_threats),
            }
        )
    return rows


def _render_delimited(rows: Sequence[dict[str, object]], delimiter: str) -> str:
    if not rows:
        return ""
    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=list(rows[0]),
        delimiter=delimiter,
        lineterminator="\n",
    )
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def _render_text(
    trace: QueueHeadTrace,
    *,
    diagnostics: bool,
    max_width: int,
    candidates_per_table: int,
    queue_depth_order: bool,
) -> str:
    decision = trace.decision
    tables = _tables(
        trace,
        max_width=max_width,
        candidates_per_table=candidates_per_table,
        queue_depth_order=queue_depth_order,
    )
    lines = [
        f"EW step {decision.n}: choose a_{decision.n} = {decision.winner}",
        f"least unused = {decision.least_unused}; legal carry primes = {_human_primes(decision.legal_carriers)}",
        (
            "queue-head mode: H rows sorted by descending depth, then ascending head; W stays last"
            if queue_depth_order
            else "queue-head mode: one current unused head per represented exact-support queue"
        ),
        "",
    ]

    for index, (start, end, table) in enumerate(tables, start=1):
        if len(tables) > 1:
            lines.append(f"queue rows {start}–{end} ({index}/{len(tables)})")
        lines.append(render_incidence_text(table, max_width=0))
        lines.append("")

    if len(tables) > 1:
        lines.append("Each table repeats B and A; prime columns are local to the queue heads shown.")
    lines.extend(
        (
            "depth = number of already-serviced values in that exact-support queue",
            "role: B=two-back, A=previous, H=current nonwinning queue head, W=winning queue head",
            f"H/W cells: bare exponent = shared with a_{decision.n - 1}; +exponent = newly introduced prime",
            "B/A cells: ordinary prime exponents; blank cell = prime absent",
            "",
        )
    )

    collapsed = len(decision.threats)
    represented = len(trace.heads)
    lines.append(
        f"Compressed {collapsed} already-used threats into {represented} represented exact-support queues."
    )
    if trace.competitor_heads:
        smallest = min(trace.competitor_heads, key=lambda head: head.value)
        lines.append(
            f"Smallest nonwinning current head: {smallest.value} at depth {smallest.depth}; "
            f"winner is {decision.winner}."
        )
    else:
        lines.append(f"No previously serviced competing queue is represented; winner is {decision.winner}.")

    if diagnostics:
        lines.extend(("", "Exhaustive source threats"))
        for threat in decision.threats:
            lines.append(
                f"  {threat.value}: support={{{','.join(str(p) for p in sorted(threat.support))}}}, "
                f"used at a_{threat.used_at}"
            )

    return "\n".join(lines) + "\n"


def _render_markdown(trace: QueueHeadTrace, *, queue_depth_order: bool) -> str:
    lines = [
        f"## EW step {trace.decision.n}: queue-head view",
        "",
        "| kind | head | depth | support | collapsed threats |",
        "| --- | ---: | ---: | --- | --- |",
    ]
    for head in ordered_queue_heads(trace, queue_depth_order=queue_depth_order):
        collapsed = ", ".join(str(value) for value in head.source_threats) or "—"
        lines.append(
            f"| {'winner' if head.is_winner else 'head'} | {head.value} | {head.depth} | "
            f"`{_primes(head.support)}` | {collapsed} |"
        )
    return "\n".join(lines) + "\n"


def render_queue_head_trace(
    trace: QueueHeadTrace,
    *,
    output_format: OutputFormat | str = OutputFormat.TEXT,
    diagnostics: bool = False,
    max_width: int = 160,
    candidates_per_table: int = 0,
    queue_depth_order: bool = False,
) -> str:
    """Render the deduplicated exact-support queue-head view."""

    format_ = OutputFormat(output_format)
    if format_ is OutputFormat.TEXT:
        return _render_text(
            trace,
            diagnostics=diagnostics,
            max_width=max_width,
            candidates_per_table=candidates_per_table,
            queue_depth_order=queue_depth_order,
        )
    if format_ is OutputFormat.MARKDOWN:
        return _render_markdown(trace, queue_depth_order=queue_depth_order)
    if format_ is OutputFormat.JSON:
        return json.dumps(
            _payload(trace, queue_depth_order=queue_depth_order),
            indent=2,
            sort_keys=False,
        ) + "\n"
    rows = _flat_rows(trace, queue_depth_order=queue_depth_order)
    if format_ is OutputFormat.TSV:
        return _render_delimited(rows, "\t")
    return _render_delimited(rows, ",")
