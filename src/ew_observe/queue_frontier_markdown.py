"""Markdown-only queue-frontier renderer with fixed B/A/W context."""

from __future__ import annotations

from .queue_frontier_presentation import ordered_queue_frontiers
from .queue_heads import QueueHeadTrace


def _support(values: frozenset[int]) -> str:
    return ",".join(str(value) for value in sorted(values))


def render_queue_frontier_markdown(
    trace: QueueHeadTrace,
    *,
    candidates_per_table: int = 0,
    sort_order: str = "value",
) -> str:
    queues = list(ordered_queue_frontiers(trace, sort_order=sort_order))
    if candidates_per_table > 0:
        groups = [
            queues[start : start + candidates_per_table]
            for start in range(0, len(queues), candidates_per_table)
        ] or [[]]
    else:
        groups = [queues]

    d = trace.decision
    w = trace.winner_head
    lines = [
        f"## EW step {d.n}: queue-frontier view",
        "",
        f"Human sort: `{sort_order}`.",
        "",
    ]
    for index, group in enumerate(groups, start=1):
        if len(groups) > 1:
            lines.extend((f"### Queue table {index}/{len(groups)}", ""))
        lines.extend(
            (
                "| role | object | depth | support | current head |",
                "| --- | ---: | ---: | --- | ---: |",
                f"| B | {d.two_back} |  | `{_support(d.two_back_support)}` |  |",
                f"| A | {d.previous} |  | `{_support(d.previous_support)}` |  |",
                f"| W | {d.winner} | {w.depth} | `{_support(w.support)}` | {w.value} |",
            )
        )
        for queue in group:
            lines.append(
                f"| L | {queue.frontier_value} | {queue.depth} | "
                f"`{_support(queue.support)}` | {queue.value} |"
            )
        lines.append("")
    return "\n".join(lines)
