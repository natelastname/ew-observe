import json

from ew_observe import EWObserver, render_decision_trace
from ew_observe.presentation import _decision_incidence_table

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


def test_text_trace_is_sparse_prime_incidence_table():
    trace = EWObserver(EW_PREFIX).trace_step(11)
    rendered = render_decision_trace(trace)

    assert "EW step 11: choose a_11 = 18" in rendered
    assert "role object occurrence" in rendered
    assert "B=two-back, A=previous, T=smaller admissible threat, W=winner" in rendered
    assert "bare exponent = shared with a_10; +exponent = newly introduced prime" in rendered
    assert "Last threat paid: 12 at a_7." in rendered
    assert "Diagnostics" not in rendered

    table = _decision_incidence_table(trace)
    assert table.features == (2, 3, 5, 7, 11)
    assert table.rows[0].leading == ("B", "55", "a_9")
    assert table.rows[0].coordinates == ((5, "1"), (11, "1"))
    assert table.rows[1].leading == ("A", "10", "a_10")
    assert table.rows[1].coordinates == ((2, "1"), (5, "1"))
    assert table.rows[2].leading == ("T", "6", "a_3")
    assert table.rows[2].coordinates == ((2, "1"), (3, "+1"))
    assert table.rows[3].coordinates == ((2, "2"), (3, "+1"))
    assert table.rows[4].coordinates == ((2, "1"), (7, "+1"))
    assert table.rows[5].leading == ("W", "18", "a_11")
    assert table.rows[5].coordinates == ((2, "1"), (3, "+2"))


def test_text_trace_splits_candidate_rows_by_explicit_count():
    trace = EWObserver(EW_PREFIX).trace_step(11)
    rendered = render_decision_trace(
        trace,
        max_width=0,
        candidates_per_table=2,
    )

    assert "candidate rows 1–2 (1/2)" in rendered
    assert "candidate rows 3–4 (2/2)" in rendered
    assert rendered.count("role object occurrence") == 2
    assert rendered.count("a_9") == 2
    assert rendered.count("a_10") == 2
    assert "prime columns" not in rendered


def test_text_trace_splits_candidate_rows_to_respect_width():
    trace = EWObserver(EW_PREFIX).trace_step(11)
    rendered = render_decision_trace(trace, max_width=32)

    assert "candidate rows" in rendered
    assert rendered.count("role object occurrence") > 1
    assert "Each table repeats B and A" in rendered
    assert "prime columns" not in rendered


def test_markdown_is_retained_as_explicit_export():
    trace = EWObserver(EW_PREFIX).trace_step(11)
    rendered = render_decision_trace(trace, output_format="markdown")

    assert "| candidate | factor roles | history |" in rendered
    assert "| 6 | `2·+3` | used at `a_3` |" in rendered
    assert "| 18 | `2·+3^2` | **WINNER** |" in rendered


def test_json_preserves_structured_mathematical_data():
    trace = EWObserver(EW_PREFIX).trace_step(11)
    payload = json.loads(render_decision_trace(trace, output_format="json"))

    assert payload["type"] == "ew-decision-trace"
    assert payload["n"] == 11
    assert payload["state"]["two_back"] == {"n": 9, "value": 55, "support": [5, 11]}
    assert payload["state"]["previous"] == {"n": 10, "value": 10, "support": [2, 5]}
    assert payload["legal_carriers"] == [2]
    assert [row["value"] for row in payload["threats"]] == [6, 12, 14]
    assert payload["threats"][0]["retained_primes"] == [2]
    assert payload["threats"][0]["introduced_primes"] == [3]
    assert payload["winner"]["value"] == 18
    assert payload["winner"]["role_factorization"] == "2·+3^2"
    assert payload["rejection_counts"]["used-before"] > 0


def test_tsv_is_flat_and_analysis_friendly():
    trace = EWObserver(EW_PREFIX).trace_step(11)
    rendered = render_decision_trace(trace, output_format="tsv")
    lines = rendered.splitlines()

    assert lines[0].startswith("n\ttwo_back\tprevious\twinner\t")
    assert "\tthreat\t6\t2·3\t2·+3\t" in lines[1]
    assert "\twinner\t18\t2·3^2\t2·+3^2\t" in lines[-1]


def test_diagnostics_are_opt_in():
    trace = EWObserver(EW_PREFIX).trace_step(11)
    rendered = render_decision_trace(trace, diagnostics=True)

    assert "Diagnostics (rejection counts overlap)" in rendered
    assert "values below winner" in rendered
    assert "used-before" in rendered
