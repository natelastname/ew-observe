import pytest

from ew_observe.decision import (
    EWObserver,
    GreedyTraceError,
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


def test_candidate_audit_preserves_all_rejection_reasons():
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


def test_trace_step_builds_paid_threat_ledger():
    trace = EWObserver(EW_PREFIX).trace_step(11)

    assert (trace.two_back, trace.previous, trace.winner) == (55, 10, 18)
    assert trace.legal_carriers == frozenset({2})
    assert trace.least_unused == 3
    assert [threat.value for threat in trace.threats] == [6, 12, 14]
    assert [threat.used_at for threat in trace.threats] == [3, 7, 6]
    assert trace.paid_threat_count == 3
    assert trace.unpaid_threat_count == 0
    assert trace.last_paid_threat is not None
    assert (trace.last_paid_threat.value, trace.last_paid_threat.used_at) == (12, 7)
    assert trace.winner_audit.globally_admissible


def test_iter_candidate_audits_is_complete_through_winner():
    audits = list(EWObserver(EW_PREFIX).iter_candidate_audits(11))
    assert [audit.value for audit in audits] == list(range(1, 19))
    assert audits[-1].globally_admissible


def test_trace_rejects_non_greedy_prefix():
    bad_prefix = EW_PREFIX[:10] + [26]
    with pytest.raises(GreedyTraceError, match="unused admissible value 18"):
        EWObserver(bad_prefix).trace_step(11)


def test_default_render_is_threat_ledger_not_full_scan():
    rendered = render_decision_trace(EWObserver(EW_PREFIX).trace_step(11))
    assert "threat ledger" in rendered
    assert "| 6 | {2,3} | {2} | {3} | 3 | PAID |" in rendered
    assert "| 18 | {2,3} | {2} | {3} | - | WINNER |" in rendered
    assert "last threat paid: 12 at n=7" in rendered
