"""Candidate-centric chronology across consecutive EW greedy states.

The single-step decision microscope answers why one observed winner was minimal.
This module turns the viewpoint around: fix one candidate and follow its exact
status while the real EW state changes around it.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import gcd

from .decision import (
    CandidateAudit,
    EWObserver as BaseEWObserver,
    GreedyTraceError,
    Support,
    prime_support,
)


class CandidateLifecycleStatus(str, Enum):
    """High-level status of a tracked value at one selection step."""

    BLOCKED = "blocked"
    LIVE_LOST = "live-lost"
    SELECTED = "selected"
    USED = "used"


@dataclass(frozen=True, slots=True)
class CandidateLifecycleStep:
    """One row in a candidate lifecycle chronology."""

    n: int
    two_back: int
    previous: int
    winner: int
    legal_carriers: Support
    candidate_audit: CandidateAudit
    status: CandidateLifecycleStatus
    live_rank: int | None
    beating_candidates: tuple[int, ...]
    winning_blocker: int | None
    winner_retained_primes: Support
    winner_introduced_primes: Support
    winner_dropped_primes: Support

    @property
    def next_face(self) -> Support:
        """Prime face made legal for the following step by this winner.

        At the next selection the current predecessor/winner pair becomes
        ``(previous, winner)``. Hence the next legal carrier set is exactly
        ``P(winner) \\ P(previous)``, i.e. the primes introduced by the winner.
        """

        return self.winner_introduced_primes

    @property
    def beating_count(self) -> int:
        return len(self.beating_candidates)


@dataclass(frozen=True, slots=True)
class CandidateLifecycleTrace:
    """Exact status history of one fixed candidate over an EW interval."""

    value: int
    start: int
    stop: int
    first_used_at: int | None
    steps: tuple[CandidateLifecycleStep, ...]

    @property
    def live_steps(self) -> tuple[int, ...]:
        return tuple(
            step.n
            for step in self.steps
            if step.status
            in {CandidateLifecycleStatus.LIVE_LOST, CandidateLifecycleStatus.SELECTED}
        )

    @property
    def live_loss_steps(self) -> tuple[int, ...]:
        return tuple(
            step.n
            for step in self.steps
            if step.status is CandidateLifecycleStatus.LIVE_LOST
        )

    @property
    def first_live_at(self) -> int | None:
        return self.live_steps[0] if self.live_steps else None

    @property
    def selected_at(self) -> int | None:
        if self.first_used_at is None:
            return None
        if self.start <= self.first_used_at <= self.stop:
            return self.first_used_at
        return None


def _is_reduced_globally_admissible(
    observer: BaseEWObserver,
    *,
    n: int,
    value: int,
    two_back: int,
    previous: int,
    previous_support: Support,
    least_unintroduced_prime: int,
) -> bool:
    """Fast lifecycle predicate for the reduced EW candidate universe."""

    if observer.used_at_before(value, n) is not None:
        return False
    if gcd(value, previous) == 1 or gcd(value, two_back) != 1:
        return False
    support = prime_support(value)
    if not (support - previous_support):
        return False
    return not any(prime > least_unintroduced_prime for prime in support)


def _beating_candidates(
    observer: BaseEWObserver,
    *,
    n: int,
    target: int,
    winner: int,
    two_back: int,
    previous: int,
    previous_support: Support,
    least_unintroduced_prime: int,
) -> tuple[int, ...]:
    """Return every currently live reduced candidate strictly below ``target``.

    For a valid EW prefix, ``winner`` is the least such value. Starting the
    scan at the observed winner avoids rechecking the entire lower integer
    interval while still producing the exact rank of the tracked candidate.
    """

    if winner >= target:
        return ()
    values = tuple(
        value
        for value in range(winner, target)
        if _is_reduced_globally_admissible(
            observer,
            n=n,
            value=value,
            two_back=two_back,
            previous=previous,
            previous_support=previous_support,
            least_unintroduced_prime=least_unintroduced_prime,
        )
    )
    if not values or values[0] != winner:
        raise GreedyTraceError(
            f"observed winner a_{n}={winner} is not the least live reduced value below "
            f"tracked candidate {target}"
        )
    return values


def trace_candidate_lifecycle(
    observer: BaseEWObserver,
    value: int,
    *,
    start: int,
    stop: int,
) -> CandidateLifecycleTrace:
    """Track one fixed positive integer through consecutive EW states.

    ``start`` and ``stop`` are inclusive one-based sequence indices. Whenever
    the tracked candidate is live in the reduced candidate universe but loses,
    the trace records all reduced-live candidates below it, its exact live
    rank, and the actual greedy winner. Every row also records the support
    transition ``previous -> winner``.
    """

    if value < 1:
        raise ValueError("tracked candidate must be positive")
    if start < 3:
        raise ValueError("candidate lifecycle requires start >= 3")
    if stop < start:
        raise ValueError("stop must be at least start")
    if stop > len(observer.terms):
        raise IndexError(
            f"stop={stop} exceeds supplied prefix length {len(observer.terms)}"
        )

    steps: list[CandidateLifecycleStep] = []
    for n in range(start, stop + 1):
        two_back = observer.terms[n - 3]
        previous = observer.terms[n - 2]
        winner = observer.terms[n - 1]
        two_back_support = prime_support(two_back)
        previous_support = prime_support(previous)
        winner_support = prime_support(winner)
        legal_carriers = previous_support - two_back_support
        least_unintroduced = observer.least_unintroduced_prime_before(n)

        candidate_audit = observer.audit_candidate(n, value)
        winner_audit = observer.audit_candidate(n, winner)
        if not winner_audit.reduced_globally_admissible:
            primitive_reasons = ", ".join(
                reason.value for reason in winner_audit.rejection_reasons
            ) or "none"
            reduction_reasons = ", ".join(
                reason.value for reason in winner_audit.reduction_reasons
            ) or "none"
            raise GreedyTraceError(
                f"observed winner a_{n}={winner} is not reduced-globally admissible: "
                f"primitive={primitive_reasons}; reduction={reduction_reasons}"
            )

        beating_candidates: tuple[int, ...] = ()
        live_rank: int | None = None
        winning_blocker: int | None = None

        if winner == value:
            if not candidate_audit.reduced_globally_admissible:
                raise GreedyTraceError(
                    f"tracked candidate {value} is observed at a_{n} but is not reduced-live"
                )
            status = CandidateLifecycleStatus.SELECTED
            live_rank = 1
        elif candidate_audit.reduced_globally_admissible:
            if winner > value:
                raise GreedyTraceError(
                    f"tracked candidate {value} is reduced-live at n={n} but observed winner "
                    f"{winner} is larger"
                )
            status = CandidateLifecycleStatus.LIVE_LOST
            beating_candidates = _beating_candidates(
                observer,
                n=n,
                target=value,
                winner=winner,
                two_back=two_back,
                previous=previous,
                previous_support=previous_support,
                least_unintroduced_prime=least_unintroduced,
            )
            live_rank = len(beating_candidates) + 1
            winning_blocker = winner
        elif candidate_audit.used_at is not None:
            status = CandidateLifecycleStatus.USED
        else:
            status = CandidateLifecycleStatus.BLOCKED

        steps.append(
            CandidateLifecycleStep(
                n=n,
                two_back=two_back,
                previous=previous,
                winner=winner,
                legal_carriers=legal_carriers,
                candidate_audit=candidate_audit,
                status=status,
                live_rank=live_rank,
                beating_candidates=beating_candidates,
                winning_blocker=winning_blocker,
                winner_retained_primes=previous_support & winner_support,
                winner_introduced_primes=winner_support - previous_support,
                winner_dropped_primes=previous_support - winner_support,
            )
        )

    first_used_at = observer.used_at_before(value, stop + 1)
    return CandidateLifecycleTrace(
        value=value,
        start=start,
        stop=stop,
        first_used_at=first_used_at,
        steps=tuple(steps),
    )
