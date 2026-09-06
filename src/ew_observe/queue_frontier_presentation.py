"""Default serviced-frontier presentation for EW exact-support queue races."""

from __future__ import annotations

import csv
import io
import json
from collections.abc import Sequence

from .decision import Support
from .human_sort import prime_exponents, prime_lex_key
from .incidence import IncidenceRow, IncidenceTable, render_text as render_incidence_text
from .presentation import OutputFormat
from .queue_heads import ExactQueueHead, QueueHeadTrace

HUMAN_SORT_ORDERS = ("value", "prime-lex", "depth", "retained")


def _incidence_coordinates(
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


def _human_primes(primes: Support) -> str:
    return ",".join(str(prime) for prime in sorted(primes)) or "—"


def _primes(primes: Support) -> str:
    return ",".join(str(prime) for prime in sorted(primes))


def _retained_primes(trace: QueueHeadTrace, queue: ExactQueueHead) -> Support:
    return queue.support & trace.decision.previous_support


def ordered_queue_frontiers(
    trace: QueueHeadTrace,
    *,
    sort_order: str = "value",
) -> tuple[ExactQueueHead, ...]:
    """Order losing queue rows for human display; winner is context, not sortable."""

    if sort_order not in HUMAN_SORT_ORDERS:
        raise ValueError(
            f"unknown human sort order {sort_order!r}; choose one of {', '.join(HUMAN_SORT_ORDERS)}"
        )

    competitors = list(trace.competitor_heads)
    if sort_order == "value":
        competitors.sort(key=lambda queue: queue.frontier_value)
    elif sort_order == "depth":
        competitors.sort(key=lambda queue: (-queue.depth, queue.frontier_value))
    elif sort_order == "prime-lex":
        competitors.sort(
            key=lambda queue: (prime_lex_key(queue.frontier_value), queue.frontier_value)
        )
    else:
        competitors.sort(
            key=lambda queue: (
                min(_retained_primes(trace, queue), default=float("inf")),
                queue.frontier_value,
            )
        )
    return tuple(competitors)


def _winner_row(trace: QueueHeadTrace) -> IncidenceRow:
    decision = trace.decision
    queue = trace.winner_head
    introduced = queue.support - decision.previous_support
    return IncidenceRow(
        leading=("W", str(decision.winner), str(queue.depth)),
        coordinates=_incidence_coordinates(
            decision.winner,
            introduced=introduced,
            mark_roles=True,
        ),
    )


def _loser_row(trace: QueueHeadTrace, queue: ExactQueueHead) -> IncidenceRow:
    decision = trace.decision
    display_value = queue.frontier_value
    introduced = queue.support - decision.previous_support
    return IncidenceRow(
        leading=("L", str(display_value), str(queue.depth)),
        coordinates=_incidence_coordinates(
            display_value,
            introduced=introduced,
            mark_roles=True,
        ),
    )


def _table(trace: QueueHeadTrace, queues: Sequence[ExactQueueHead]) -> IncidenceTable:
    """Build one self-contained human table with B, A, and W fixed at the top."""

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
        _winner_row(trace),
        *(_loser_row(trace, queue) for queue in queues),
    ]
    features = tuple(
        sorted({prime for row in rows for prime, _cell in row.coordinates})
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
    sort_order: str,
) -> tuple[tuple[int, int, IncidenceTable], ...]:
    if max_width < 0:
        raise ValueError("max_width must be nonnegative")
    if candidates_per_table < 0:
        raise ValueError("candidates_per_table must be nonnegative")

    queues = list(ordered_queue_frontiers(trace, sort_order=sort_order))
    if not queues:
        return ((0, 0, _table(trace, ())),)

    groups: list[list[ExactQueueHead]] = []
    current: list[ExactQueueHead] = []

    for queue in queues:
        split_for_count = (
            bool(current)
            and candidates_per_table > 0
            and len(current) >= candidates_per_table
        )
        split_for_width = False
        if current and not split_for_count and max_width > 0:
            split_for_width = _table_width(_table(trace, [*current, queue])) > max_width
        if split_for_count or split_for_width:
            groups.append(current)
            current = []
        current.append(queue)

    if current:
        groups.append(current)

    tables: list[tuple[int, int, IncidenceTable]] = []
    start = 1
    for group in groups:
        end = start + len(group) - 1
        tables.append((start, end, _table(trace, group)))
        start = end + 1
    return tuple(tables)


def _queue_payload(queue: ExactQueueHead) -> dict[str, object]:
    return {
        "kind": "winner" if queue.is_winner else "loser",
        "display_value": queue.frontier_value,
        "queue_depth": queue.depth,
        "last_used_value": queue.last_used_value,
        "current_head": queue.value,
        "support": sorted(queue.support),
        "source_threats": list(queue.source_threats),
    }


def _canonical_machine_order(trace: QueueHeadTrace) -> tuple[ExactQueueHead, ...]:
    """Stable machine order, deliberately independent of human presentation flags."""

    competitors = sorted(trace.competitor_heads, key=lambda queue: queue.frontier_value)
    return (*competitors, trace.winner_head)


def _payload(trace: QueueHeadTrace) -> dict[str, object]:
    decision = trace.decision
    return {
        "type": "ew-decision-queue-frontier-trace",
        "view": "queue-frontiers",
        "ordering": "display-value-asc,winner-last",
        "n": decision.n,
        "state": {
            "two_back": {"n": decision.n - 2, "value": decision.two_back},
            "previous": {"n": decision.n - 1, "value": decision.previous},
        },
        "legal_carriers": sorted(decision.legal_carriers),
        "least_unused": decision.least_unused,
        "queues": [_queue_payload(queue) for queue in _canonical_machine_order(trace)],
        "exhaustive_threats": [
            {"value": threat.value, "support": sorted(threat.support), "used_at": threat.used_at}
            for threat in decision.threats
        ],
    }


def _flat_rows(trace: QueueHeadTrace) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for queue in _canonical_machine_order(trace):
        rows.append(
            {
                "n": trace.decision.n,
                "kind": "winner" if queue.is_winner else "loser",
                "display_value": queue.frontier_value,
                "queue_depth": queue.depth,
                "last_used_value": queue.last_used_value if queue.last_used_value is not None else "",
                "current_head": queue.value,
                "support": _primes(queue.support),
                "new_primes": _primes(queue.support - trace.decision.previous_support),
                "source_threats": ";".join(str(value) for value in queue.source_threats),
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
    sort_order: str,
) -> str:
    decision = trace.decision
    tables = _tables(
        trace,
        max_width=max_width,
        candidates_per_table=candidates_per_table,
        sort_order=sort_order,
    )
    lines = [
        f"EW step {decision.n}: choose a_{decision.n} = {decision.winner}",
        f"least unused = {decision.least_unused}; legal carry primes = {_human_primes(decision.legal_carriers)}",
        f"queue-frontier mode: one row per represented exact-support queue; human sort={sort_order}",
        "",
    ]

    for index, (start, end, table) in enumerate(tables, start=1):
        if len(tables) > 1:
            lines.append(f"losing queue rows {start}–{end} ({index}/{len(tables)})")
        lines.append(render_incidence_text(table, max_width=0))
        lines.append("")

    if len(tables) > 1:
        lines.append("Each table repeats B, A, and W; prime columns are local to the losing queues shown.")
    lines.extend(
        (
            "depth = number of values already serviced in that exact-support queue before this step",
            "role: B=two-back, A=previous, W=winner, L=max previously used value in a losing queue",
            f"L/W cells: bare exponent = shared with a_{decision.n - 1}; +exponent = newly introduced prime",
            "B/A cells: ordinary prime exponents; blank cell = prime absent",
            "",
        )
    )

    lines.append(
        f"Compressed {len(decision.threats)} already-used threats into {len(trace.heads)} represented exact-support queues."
    )
    if diagnostics:
        lines.extend(("", "Queue race details"))
        for queue in _canonical_machine_order(trace):
            if queue.is_winner:
                lines.append(
                    f"  W support={{{_primes(queue.support)}}}: head={queue.value}, depth={queue.depth}"
                )
            else:
                lines.append(
                    f"  L support={{{_primes(queue.support)}}}: last-used={queue.last_used_value}, "
                    f"current-head={queue.value}, depth={queue.depth}"
                )

    return "\n".join(lines) + "\n"


def _render_markdown(trace: QueueHeadTrace, *, sort_order: str) -> str:
    lines = [
        f"## EW step {trace.decision.n}: queue-frontier view",
        "",
        f"Human sort: `{sort_order}`. The context rows `B`, `A`, and `W` are fixed above the losing queues.",
        "",
        "| kind | displayed value | depth | current head | support | collapsed threats |",
        "| --- | ---: | ---: | ---: | --- | --- |",
    ]
    winner = trace.winner_head
    lines.append(
        f"| winner | {trace.decision.winner} | {winner.depth} | {winner.value} | "
        f"`{_primes(winner.support)}` | {', '.join(str(v) for v in winner.source_threats) or '—'} |"
    )
    for queue in ordered_queue_frontiers(trace, sort_order=sort_order):
        collapsed = ", ".join(str(value) for value in queue.source_threats) or "—"
        lines.append(
            f"| loser | {queue.frontier_value} | {queue.depth} | {queue.value} | "
            f"`{_primes(queue.support)}` | {collapsed} |"
        )
    return "\n".join(lines) + "\n"


def render_queue_frontier_trace(
    trace: QueueHeadTrace,
    *,
    output_format: OutputFormat | str = OutputFormat.TEXT,
    diagnostics: bool = False,
    max_width: int = 160,
    candidates_per_table: int = 0,
    sort_order: str = "value",
) -> str:
    """Render one representative row per exact queue using its serviced frontier.

    Human sort options affect only text/Markdown. JSON/TSV/CSV use a stable
    canonical order and preserve the complete queue/frontier/threat data.
    """

    format_ = OutputFormat(output_format)
    if format_ is OutputFormat.TEXT:
        return _render_text(
            trace,
            diagnostics=diagnostics,
            max_width=max_width,
            candidates_per_table=candidates_per_table,
            sort_order=sort_order,
        )
    if format_ is OutputFormat.MARKDOWN:
        return _render_markdown(trace, sort_order=sort_order)
    if format_ is OutputFormat.JSON:
        return json.dumps(_payload(trace), indent=2, sort_keys=False) + "\n"
    rows = _flat_rows(trace)
    if format_ is OutputFormat.TSV:
        return _render_delimited(rows, "\t")
    return _render_delimited(rows, ",")
