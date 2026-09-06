"""Exact-support queue-head compression for one EW greedy decision."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .decision import DecisionTrace, GreedyTraceError, Support
from .queue_depth import iter_exact_support_queue


class QueueHeadObserver(Protocol):
    def trace_step(self, n: int) -> DecisionTrace: ...

    def used_at_before(self, value: int, n: int) -> int | None: ...


@dataclass(frozen=True, slots=True)
class ExactQueueHead:
    """Current first-unused value of one exact-support queue."""

    support: Support
    value: int
    depth: int
    source_threats: tuple[int, ...]
    is_winner: bool


@dataclass(frozen=True, slots=True)
class QueueHeadTrace:
    """Queue-head compression of an exact EW decision certificate."""

    decision: DecisionTrace
    heads: tuple[ExactQueueHead, ...]

    @property
    def winner_head(self) -> ExactQueueHead:
        for head in self.heads:
            if head.is_winner:
                return head
        raise AssertionError("queue-head trace has no winner")

    @property
    def competitor_heads(self) -> tuple[ExactQueueHead, ...]:
        return tuple(head for head in self.heads if not head.is_winner)


def current_exact_support_head(
    observer: QueueHeadObserver,
    *,
    n: int,
    support: Support,
) -> tuple[int, int]:
    """Return ``(depth, value)`` for the first unused exact-support queue item."""

    for depth, value in enumerate(iter_exact_support_queue(support)):
        if observer.used_at_before(value, n) is None:
            return depth, value
    raise AssertionError("finite EW history exhausted an infinite exact-support queue")


def trace_queue_heads(observer: QueueHeadObserver, n: int) -> QueueHeadTrace:
    """Compress the exhaustive threat ledger to current exact-support heads.

    The represented queues are exactly the supports witnessed by a smaller
    historical threat, together with the winner support. This is the finite set
    naturally induced by the exhaustive greedy certificate; it does not attempt
    to enumerate the infinitely many untouched admissible supports whose first
    values already lie above the winner.
    """

    decision = observer.trace_step(n)
    represented_supports = {
        *(threat.support for threat in decision.threats),
        decision.winner_audit.support,
    }

    heads: list[ExactQueueHead] = []
    for support in represented_supports:
        depth, value = current_exact_support_head(observer, n=n, support=support)
        source_threats = tuple(
            sorted(
                threat.value
                for threat in decision.threats
                if threat.support == support
            )
        )
        is_winner = support == decision.winner_audit.support
        if is_winner and value != decision.winner:
            raise GreedyTraceError(
                f"winner support queue head is {value}, not observed winner {decision.winner}"
            )
        if not is_winner and value < decision.winner:
            raise GreedyTraceError(
                f"unused exact-support queue head {value} lies below observed winner "
                f"a_{n}={decision.winner}"
            )
        heads.append(
            ExactQueueHead(
                support=support,
                value=value,
                depth=depth,
                source_threats=source_threats,
                is_winner=is_winner,
            )
        )

    competitors = sorted(
        (head for head in heads if not head.is_winner),
        key=lambda head: head.value,
    )
    winner = next(head for head in heads if head.is_winner)
    return QueueHeadTrace(decision=decision, heads=(*competitors, winner))
