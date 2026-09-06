"""Exact-support queue compression for one EW greedy decision."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .decision import DecisionTrace, GreedyTraceError, Support
from .queue_depth import exact_support_queue_value, iter_exact_support_queue


class QueueHeadObserver(Protocol):
    def trace_step(self, n: int) -> DecisionTrace: ...

    def used_at_before(self, value: int, n: int) -> int | None: ...


@dataclass(frozen=True, slots=True)
class ExactQueueHead:
    """Service frontier and current first-unused value of one exact-support queue."""

    support: Support
    value: int
    depth: int
    last_used_value: int | None
    source_threats: tuple[int, ...]
    is_winner: bool

    @property
    def frontier_value(self) -> int:
        """Value shown in the default race view.

        Losing queues show their maximal previously serviced item. The winning
        queue shows the actual winner, which is its current head before service.
        """

        if self.is_winner:
            return self.value
        if self.last_used_value is None:
            raise AssertionError("represented losing queue has no prior service")
        return self.last_used_value


@dataclass(frozen=True, slots=True)
class QueueHeadTrace:
    """One-row-per-exact-queue compression of an EW decision certificate."""

    decision: DecisionTrace
    heads: tuple[ExactQueueHead, ...]

    @property
    def winner_head(self) -> ExactQueueHead:
        for head in self.heads:
            if head.is_winner:
                return head
        raise AssertionError("queue trace has no winner")

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
    """Compress the exhaustive threat ledger to one row per represented queue.

    The represented queues are exactly the supports witnessed by a smaller
    historical threat, together with the winner support. This is the finite set
    naturally induced by the exhaustive greedy certificate; it does not attempt
    to enumerate the infinitely many untouched admissible supports whose first
    values already lie above the winner.

    Each queue records both its current first-unused head q_d and its maximal
    previously serviced member q_{d-1} when d>0. The default presentation uses
    q_{d-1} for losing queues and the actual winner q_d for the winning queue.
    """

    decision = observer.trace_step(n)
    represented_supports = {
        *(threat.support for threat in decision.threats),
        decision.winner_audit.support,
    }

    heads: list[ExactQueueHead] = []
    for support in represented_supports:
        depth, value = current_exact_support_head(observer, n=n, support=support)
        last_used_value = (
            exact_support_queue_value(support, depth - 1)
            if depth > 0
            else None
        )
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
        if not is_winner and last_used_value is None:
            raise GreedyTraceError(
                f"represented losing support {sorted(support)} has no prior queue service"
            )
        heads.append(
            ExactQueueHead(
                support=support,
                value=value,
                depth=depth,
                last_used_value=last_used_value,
                source_threats=source_threats,
                is_winner=is_winner,
            )
        )

    competitors = sorted(
        (head for head in heads if not head.is_winner),
        key=lambda head: head.frontier_value,
    )
    winner = next(head for head in heads if head.is_winner)
    return QueueHeadTrace(decision=decision, heads=(*competitors, winner))
