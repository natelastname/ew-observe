import json

from ew_observe import EWObserver, render_decision_trace

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


def test_text_trace_is_aligned_and_uses_compact_prime_roles():
    trace = EWObserver(EW_PREFIX).trace_step(11)
    rendered = render_decision_trace(trace)

    assert "EW step 11: choose a_11 = 18" in rendered
    assert "a_9 (two back) = 55 = 5·11" in rendered
    assert "a_10 (previous) = 10 = 2·5" in rendered
    assert "bare prime = shared; +prime = new" in rendered
    assert "candidate  factor roles" in rendered
    assert "6  2·+3" in rendered
    assert "12  2^2·+3" in rendered
    assert "14  2·+7" in rendered
    assert "18  2·+3^2" in rendered
    assert "used at a_3" in rendered
    assert "WINNER" in rendered
    assert "| ---" not in rendered
    assert "Diagnostics" not in rendered


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
