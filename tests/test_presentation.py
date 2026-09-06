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


def test_human_trace_emphasizes_factorization_and_history():
    trace = EWObserver(EW_PREFIX).trace_step(11)
    rendered = render_decision_trace(trace)

    assert "EW step 11: choose a_11 = 18" in rendered
    assert "a_9 (two back) : 55 = 5·11" in rendered
    assert "a_10 (previous) : 10 = 2·5" in rendered
    assert "candidate" in rendered
    assert "factorization" in rendered
    assert "2·3" in rendered
    assert "a_3" in rendered
    assert "a_7" in rendered
    assert "18 = 2·3^2" in rendered
    assert "Conclusion: all 3 smaller admissible threats were already used" in rendered
    assert "| ---" not in rendered
    assert "Diagnostics" not in rendered


def test_diagnostics_are_opt_in():
    trace = EWObserver(EW_PREFIX).trace_step(11)
    rendered = render_decision_trace(trace, diagnostics=True)

    assert "Diagnostics (rejection counts overlap)" in rendered
    assert "values below winner" in rendered
    assert "used-before" in rendered
