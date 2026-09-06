import json

from ew_observe import (
    CandidateLifecycleStatus,
    EWObserver,
    render_candidate_lifecycle,
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


def test_candidate_lifecycle_finds_live_loss_and_later_selection() -> None:
    trace = EWObserver(EW_PREFIX).trace_candidate_lifecycle(18, start=6, stop=12)
    by_n = {step.n: step for step in trace.steps}

    assert by_n[6].status is CandidateLifecycleStatus.BLOCKED

    lost = by_n[7]
    assert lost.status is CandidateLifecycleStatus.LIVE_LOST
    assert lost.live_rank == 2
    assert lost.beating_candidates == (12,)
    assert lost.winning_blocker == 12
    assert lost.legal_carriers == frozenset({2})
    assert lost.winner_retained_primes == frozenset({2})
    assert lost.winner_introduced_primes == frozenset({3})
    assert lost.winner_dropped_primes == frozenset({7})
    assert lost.next_face == frozenset({3})

    selected = by_n[11]
    assert selected.status is CandidateLifecycleStatus.SELECTED
    assert selected.live_rank == 1
    assert selected.beating_candidates == ()

    used = by_n[12]
    assert used.status is CandidateLifecycleStatus.USED
    assert used.candidate_audit.used_at == 11

    assert trace.first_live_at == 7
    assert trace.live_steps == (7, 11)
    assert trace.live_loss_steps == (7,)
    assert trace.selected_at == 11
    assert trace.first_used_at == 11


def test_lifecycle_text_emphasizes_face_transition() -> None:
    trace = EWObserver(EW_PREFIX).trace_candidate_lifecycle(18, start=6, stop=12)
    rendered = render_candidate_lifecycle(trace)

    assert "EW candidate lifecycle: 18" in rendered
    assert "LIVE-LOST" in rendered
    assert "SELECTED" in rendered
    assert "USED@a_11" in rendered
    assert "=2 +3 -7" in rendered
    assert "+primes are the next legal carrier face" in rendered


def test_lifecycle_json_preserves_exact_beaters_and_support_roles() -> None:
    trace = EWObserver(EW_PREFIX).trace_candidate_lifecycle(18, start=6, stop=12)
    payload = json.loads(render_candidate_lifecycle(trace, output_format="json"))

    assert payload["type"] == "ew-candidate-lifecycle"
    assert payload["value"] == 18
    assert payload["summary"]["live_steps"] == [7, 11]
    row = next(step for step in payload["steps"] if step["n"] == 7)
    assert row["status"] == "live-lost"
    assert row["live_rank"] == 2
    assert row["beating_candidates"] == [12]
    assert row["winning_blocker"] == 12
    assert row["winner_transition"]["retained_primes"] == [2]
    assert row["winner_transition"]["introduced_primes"] == [3]
    assert row["winner_transition"]["dropped_primes"] == [7]
    assert row["winner_transition"]["next_face"] == [3]
