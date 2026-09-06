import pytest

from ew_observe.decision import (
    EWObserver,
    GreedyTraceError,
    ReductionReason,
    RejectionReason,
    render_decision_trace,
)

EW_PREFIX = [
    1,
    2,
    6,
    15,
    35,
    14,
    12,
    33,
    55,
    10,
    18,
    21,
    77,
    22,
    20,
    45,
    39,
    26,
    28,
    63,
    51,
    34,
    38,
    57,
    69,
    46,
    40,
    65,
    91,
    42,
]


def test_candidate_audit_preserves_all_primitive_rejection_reasons():
    observer = EWObserver(EW_PREFIX)

    assert observer.audit_candidate(11, 4).rejection_reasons == (
        RejectionReason.NO_NEW_PRIME,
    )
    assert observer.audit_candidate(11, 9).rejection_reasons == (
        RejectionReason.NO_PREDECESSOR_OVERLAP,
    )
    assert observer.audit_candidate(11, 5).rejection_reasons == (
        RejectionReason.TWO_BACK_CONFLICT,
        RejectionReason.NO_NEW_PRIME,
    )
    assert observer.audit_candidate(11, 15).rejection_reasons == (
        RejectionReason.USED_BEFORE,
        RejectionReason.TWO_BACK_CONFLICT,
    )


def test_fresh_prime_frontier_distinguishes_primitive_from_reduced_admissibility():
    observer = EWObserver(EW_PREFIX)
    audit = observer.audit_candidate(11, 34)  # 34 = 2 * 17

    assert observer.least_unintroduced_prime_before(11) == 13
    assert audit.least_unintroduced_prime == 13
    assert audit.rejection_reasons == ()
    assert audit.structurally_admissible
    assert audit.globally_admissible
    assert audit.primes_beyond_fresh_frontier == frozenset({17})
    assert audit.reduction_reasons == (
        ReductionReason.PRIME_BEYOND_LEAST_UNINTRODUCED,
    )
    assert not audit.in_reduced_candidate_universe
    assert not audit.reduced_globally_admissible


def test_trace_step_builds_reduced_paid_threat_ledger():
    trace = EWObserver(EW_PREFIX).trace_step(11)

    assert (trace.two_back, trace.previous, trace.winner) == (55, 10, 18)
    assert trace.legal_carriers == frozenset({2})
    assert trace.least_unused == 3
    assert trace.least_unintroduced_prime == 13
    assert [threat.value for threat in trace.threats] == [6, 12, 14]
    assert [threat.used_at for threat in trace.threats] == [3, 7, 6]
    assert all(
        not threat.primes_beyond_fresh_frontier for threat in trace.threats
    )
    assert trace.paid_threat_count == 3
    assert trace.unpaid_threat_count == 0
    assert trace.last_paid_threat is not None
    assert (trace.last_paid_threat.value, trace.last_paid_threat.used_at) == (12, 7)
    assert trace.winner_audit.reduced_globally_admissible


def test_observed_early_winners_respect_fresh_prime_frontier():
    observer = EWObserver(EW_PREFIX)
    for n in range(3, len(EW_PREFIX) + 1):
        trace = observer.trace_step(n)
        assert max(trace.winner_support) <= trace.least_unintroduced_prime


def test_iter_candidate_audits_is_complete_through_winner():
    audits = list(EWObserver(EW_PREFIX).iter_candidate_audits(11))
    assert [audit.value for audit in audits] == list(range(1, 19))
    assert audits[-1].reduced_globally_admissible


def test_trace_rejects_non_greedy_prefix():
    bad_prefix = EW_PREFIX[:10] + [26]
    with pytest.raises(GreedyTraceError, match="unused reduced-admissible value 18"):
        EWObserver(bad_prefix).trace_step(11)


def test_trace_rejects_observed_winner_beyond_fresh_prime_frontier():
    with pytest.raises(GreedyTraceError, match="beyond least unintroduced prime Q_3=3"):
        EWObserver([1, 2, 10]).trace_step(3)


def test_default_render_is_reduced_threat_ledger_not_full_scan():
    rendered = render_decision_trace(EWObserver(EW_PREFIX).trace_step(11))
    assert "reduced threat ledger" in rendered
    assert "least unintroduced prime Q_11 = 13" in rendered
    assert "| 6 | {2,3} | {2} | {3} | 3 | PAID |" in rendered
    assert "| 18 | {2,3} | {2} | {3} | - | WINNER |" in rendered
    assert "last threat paid: 12 at n=7" in rendered
