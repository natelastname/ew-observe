"""Exact, exhaustive reconstruction of one Enots--Wolley greedy choice.

This module is intentionally a reference oracle rather than an optimized EW
generator. For a supplied real EW prefix it reconstructs the mathematical scan
that certifies the selected term is the least unused admissible positive
integer.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from enum import Enum
from math import gcd

Support = frozenset[int]


class RejectionReason(str, Enum):
    """Independent reasons a positive integer cannot win an EW step."""

    USED_BEFORE = "used-before"
    NO_PREDECESSOR_OVERLAP = "no-predecessor-overlap"
    TWO_BACK_CONFLICT = "two-back-conflict"
    NO_NEW_PRIME = "no-new-prime"


class GreedyTraceError(ValueError):
    """Raised when the supplied prefix is inconsistent with the EW greedy rule."""


def prime_support(value: int) -> Support:
    """Return the distinct prime divisors of a positive integer."""

    if value < 1:
        raise ValueError("value must be positive")
    remaining = value
    factors: set[int] = set()
    divisor = 2
    while divisor * divisor <= remaining:
        if remaining % divisor == 0:
            factors.add(divisor)
            while remaining % divisor == 0:
                remaining //= divisor
        divisor = 3 if divisor == 2 else divisor + 2
    if remaining > 1:
        factors.add(remaining)
    return frozenset(factors)


def _has_new_prime(value: int, previous_support: Support) -> bool:
    """Return whether ``value`` has a prime absent from the predecessor support.

    The exhaustive scan calls this for every value below the winner. Dividing
    only by predecessor primes avoids factoring every rejected integer.
    """

    remaining = value
    for prime in previous_support:
        while remaining % prime == 0:
            remaining //= prime
    return remaining > 1


def _support_label(support: Support) -> str:
    return "{" + ",".join(str(prime) for prime in sorted(support)) + "}"


@dataclass(frozen=True, slots=True)
class CandidateAudit:
    """Exact status of one candidate at one EW selection step."""

    n: int
    value: int
    support: Support
    used_at: int | None
    predecessor_overlap: Support
    two_back_overlap: Support
    retained_primes: Support
    introduced_primes: Support
    rejection_reasons: tuple[RejectionReason, ...]

    @property
    def structurally_admissible(self) -> bool:
        """Whether the candidate satisfies the three local EW conditions."""

        structural = {
            RejectionReason.NO_PREDECESSOR_OVERLAP,
            RejectionReason.TWO_BACK_CONFLICT,
            RejectionReason.NO_NEW_PRIME,
        }
        return not any(reason in structural for reason in self.rejection_reasons)

    @property
    def globally_admissible(self) -> bool:
        """Whether the candidate is both locally admissible and unused."""

        return not self.rejection_reasons


@dataclass(frozen=True, slots=True)
class DecisionTrace:
    """Compact exact certificate for one observed EW greedy decision."""

    n: int
    two_back: int
    previous: int
    winner: int
    two_back_support: Support
    previous_support: Support
    winner_support: Support
    legal_carriers: Support
    least_unused: int
    threats: tuple[CandidateAudit, ...]
    winner_audit: CandidateAudit
    values_below_winner: int
    used_below_winner: int
    rejection_reason_counts: tuple[tuple[RejectionReason, int], ...]

    @property
    def paid_threat_count(self) -> int:
        return sum(threat.used_at is not None for threat in self.threats)

    @property
    def unpaid_threat_count(self) -> int:
        return len(self.threats) - self.paid_threat_count

    @property
    def last_paid_threat(self) -> CandidateAudit | None:
        paid = [threat for threat in self.threats if threat.used_at is not None]
        if not paid:
            return None
        return max(paid, key=lambda threat: threat.used_at or -1)

    def rejection_count(self, reason: RejectionReason) -> int:
        return dict(self.rejection_reason_counts).get(reason, 0)


class EWObserver:
    """Inspect the exact greedy decisions encoded by an EW term prefix.

    Sequence subscripts are one-based: ``trace_step(11)`` explains ``a_11``.
    The supplied sequence is not regenerated or modified.
    """

    def __init__(self, terms: Sequence[int]) -> None:
        if any(
            not isinstance(term, int) or isinstance(term, bool) or term < 1
            for term in terms
        ):
            raise ValueError("EW terms must be positive integers")
        self.terms = tuple(terms)
        first_positions: dict[int, int] = {}
        for n, term in enumerate(self.terms, start=1):
            first_positions.setdefault(term, n)
        self._first_positions = first_positions

    def _state(self, n: int) -> tuple[int, int, int, Support, Support]:
        if n < 3:
            raise ValueError("an EW greedy decision requires n >= 3")
        if n > len(self.terms):
            raise IndexError(f"n={n} exceeds supplied prefix length {len(self.terms)}")
        two_back = self.terms[n - 3]
        previous = self.terms[n - 2]
        winner = self.terms[n - 1]
        return (
            two_back,
            previous,
            winner,
            prime_support(two_back),
            prime_support(previous),
        )

    def used_at_before(self, value: int, n: int) -> int | None:
        """Return the first occurrence of ``value`` before step ``n``, if any."""

        position = self._first_positions.get(value)
        return position if position is not None and position < n else None

    def least_unused_before(self, n: int) -> int:
        """Return the least positive integer not used before selection ``n``."""

        if n < 1 or n > len(self.terms) + 1:
            raise ValueError("n is outside the supplied prefix")
        value = 1
        while self.used_at_before(value, n) is not None:
            value += 1
        return value

    def audit_candidate(self, n: int, value: int) -> CandidateAudit:
        """Classify one positive integer against the exact state before ``a_n``."""

        if value < 1:
            raise ValueError("candidate value must be positive")
        two_back, previous, _winner, two_back_support, previous_support = self._state(n)
        support = prime_support(value)
        predecessor_overlap = support & previous_support
        two_back_overlap = support & two_back_support
        introduced = support - previous_support
        used_at = self.used_at_before(value, n)

        reasons: list[RejectionReason] = []
        if used_at is not None:
            reasons.append(RejectionReason.USED_BEFORE)
        if gcd(value, previous) == 1:
            reasons.append(RejectionReason.NO_PREDECESSOR_OVERLAP)
        if gcd(value, two_back) != 1:
            reasons.append(RejectionReason.TWO_BACK_CONFLICT)
        if not introduced:
            reasons.append(RejectionReason.NO_NEW_PRIME)

        return CandidateAudit(
            n=n,
            value=value,
            support=support,
            used_at=used_at,
            predecessor_overlap=predecessor_overlap,
            two_back_overlap=two_back_overlap,
            retained_primes=predecessor_overlap,
            introduced_primes=introduced,
            rejection_reasons=tuple(reasons),
        )

    def iter_candidate_audits(
        self,
        n: int,
        *,
        include_winner: bool = True,
    ) -> Iterator[CandidateAudit]:
        """Yield the complete detailed scan from ``1`` through the observed winner.

        This is deliberately exhaustive and may be expensive for a very large
        winner. ``trace_step`` performs the same exact classification while only
        materializing detailed audits for the threat ledger and the winner.
        """

        _two_back, _previous, winner, _two_back_support, _previous_support = self._state(n)
        stop = winner + 1 if include_winner else winner
        for value in range(1, stop):
            yield self.audit_candidate(n, value)

    def trace_step(self, n: int) -> DecisionTrace:
        """Return an exact compact greedy certificate for the observed term ``a_n``."""

        two_back, previous, winner, two_back_support, previous_support = self._state(n)
        reason_counts: Counter[RejectionReason] = Counter()
        threats: list[CandidateAudit] = []
        used_below = 0
        first_unpaid_threat: int | None = None

        for value in range(1, winner):
            used_at = self.used_at_before(value, n)
            used = used_at is not None
            if used:
                used_below += 1
                reason_counts[RejectionReason.USED_BEFORE] += 1

            no_overlap = gcd(value, previous) == 1
            if no_overlap:
                reason_counts[RejectionReason.NO_PREDECESSOR_OVERLAP] += 1

            two_back_conflict = gcd(value, two_back) != 1
            if two_back_conflict:
                reason_counts[RejectionReason.TWO_BACK_CONFLICT] += 1

            no_new_prime = not _has_new_prime(value, previous_support)
            if no_new_prime:
                reason_counts[RejectionReason.NO_NEW_PRIME] += 1

            structurally_admissible = not (
                no_overlap or two_back_conflict or no_new_prime
            )
            if structurally_admissible:
                audit = self.audit_candidate(n, value)
                threats.append(audit)
                if not used and first_unpaid_threat is None:
                    first_unpaid_threat = value

        winner_audit = self.audit_candidate(n, winner)
        if not winner_audit.globally_admissible:
            reasons = ", ".join(
                reason.value for reason in winner_audit.rejection_reasons
            )
            raise GreedyTraceError(
                f"observed winner a_{n}={winner} is not globally admissible: {reasons}"
            )
        if first_unpaid_threat is not None:
            raise GreedyTraceError(
                f"unused admissible value {first_unpaid_threat} is below observed winner "
                f"a_{n}={winner}"
            )

        ordered_counts = tuple(
            (reason, reason_counts[reason]) for reason in RejectionReason
        )
        return DecisionTrace(
            n=n,
            two_back=two_back,
            previous=previous,
            winner=winner,
            two_back_support=two_back_support,
            previous_support=previous_support,
            winner_support=winner_audit.support,
            legal_carriers=previous_support - two_back_support,
            least_unused=self.least_unused_before(n),
            threats=tuple(threats),
            winner_audit=winner_audit,
            values_below_winner=winner - 1,
            used_below_winner=used_below,
            rejection_reason_counts=ordered_counts,
        )


def render_candidate_audit(audit: CandidateAudit) -> str:
    """Render one candidate audit in compact human-readable text."""

    reasons = ", ".join(reason.value for reason in audit.rejection_reasons) or "none"
    used = str(audit.used_at) if audit.used_at is not None else "-"
    return "\n".join(
        (
            f"candidate {audit.value} at n={audit.n}",
            f"support: {_support_label(audit.support)}",
            f"retained from predecessor: {_support_label(audit.retained_primes)}",
            f"introduced: {_support_label(audit.introduced_primes)}",
            f"two-back overlap: {_support_label(audit.two_back_overlap)}",
            f"used before at: {used}",
            f"structurally admissible: {audit.structurally_admissible}",
            f"globally admissible: {audit.globally_admissible}",
            f"rejection reasons: {reasons}",
        )
    )


def render_decision_trace(trace: DecisionTrace) -> str:
    """Render the default microscope view: state plus the paid threat ledger."""

    lines = [
        f"EW greedy decision n={trace.n}",
        "",
        "state",
        f"  B = a_{trace.n - 2} = {trace.two_back}  support={_support_label(trace.two_back_support)}",
        f"  A = a_{trace.n - 1} = {trace.previous}  support={_support_label(trace.previous_support)}",
        f"  W = a_{trace.n} = {trace.winner}  support={_support_label(trace.winner_support)}",
        f"  legal carriers P(A) \\ P(B) = {_support_label(trace.legal_carriers)}",
        f"  least unused before selection = {trace.least_unused}",
        "",
        "threat ledger",
        "| value | support | retained | introduced | used at | status |",
        "| ---: | --- | --- | --- | ---: | --- |",
    ]
    for threat in trace.threats:
        lines.append(
            "| "
            + " | ".join(
                (
                    str(threat.value),
                    _support_label(threat.support),
                    _support_label(threat.retained_primes),
                    _support_label(threat.introduced_primes),
                    str(threat.used_at) if threat.used_at is not None else "-",
                    "PAID" if threat.used_at is not None else "UNPAID",
                )
            )
            + " |"
        )
    winner = trace.winner_audit
    lines.append(
        "| "
        + " | ".join(
            (
                str(winner.value),
                _support_label(winner.support),
                _support_label(winner.retained_primes),
                _support_label(winner.introduced_primes),
                "-",
                "WINNER",
            )
        )
        + " |"
    )

    lines.extend(
        (
            "",
            "summary",
            f"  values below winner: {trace.values_below_winner}",
            f"  used values below winner: {trace.used_below_winner}",
            f"  locally admissible threats: {len(trace.threats)}",
            f"  historically paid threats: {trace.paid_threat_count}",
            f"  unpaid threats: {trace.unpaid_threat_count}",
        )
    )
    last = trace.last_paid_threat
    if last is not None:
        lines.append(f"  last threat paid: {last.value} at n={last.used_at}")

    lines.extend(("", "rejection counts below winner (overlapping)"))
    for reason, count in trace.rejection_reason_counts:
        lines.append(f"  {reason.value}: {count}")
    return "\n".join(lines)
