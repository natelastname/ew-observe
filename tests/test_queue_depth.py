import json

import ew_observe.cli as cli_module
from ew_observe import EWObserver
from ew_observe.queue_depth import (
    exact_support_queue_depth,
    exact_support_queue_value,
)
from ew_observe.queue_depth_presentation import (
    queue_depth_candidate_order,
    render_queue_depth_decision_trace,
)
from ew_observe.queue_frontier_presentation import ordered_queue_frontiers


EW_PREFIX_23 = [
    1, 2, 6, 15, 35, 14, 12, 33, 55, 10, 18, 21, 77, 22, 20,
    45, 39, 26, 28, 63, 51, 34, 38,
]


def test_exact_support_queue_depth_is_zero_based_rank():
    assert exact_support_queue_depth(6) == 0
    assert exact_support_queue_depth(12) == 1
    assert exact_support_queue_depth(18) == 2
    assert exact_support_queue_depth(24) == 3
    assert exact_support_queue_depth(14) == 0
    assert exact_support_queue_depth(8) == 2
    assert exact_support_queue_value(frozenset({2, 3}), 3) == 24
    assert exact_support_queue_value(frozenset({2, 7}), 1) == 28


def test_legacy_exhaustive_queue_depth_order_remains_available():
    trace = EWObserver(EW_PREFIX_23[:11]).trace_step(11)
    ordered = queue_depth_candidate_order(trace)

    assert [audit.value for audit in ordered] == [12, 6, 14, 18]
    assert [exact_support_queue_depth(audit.value) for audit in ordered] == [1, 0, 0, 2]

    rendered = render_queue_depth_decision_trace(trace, max_width=0)
    assert "role object depth" in rendered


def test_queue_depth_orders_losing_queue_frontiers_not_historical_members():
    trace = EWObserver(EW_PREFIX_23).trace_queue_heads(23)
    ordered = ordered_queue_frontiers(trace, queue_depth_order=True)

    assert [queue.frontier_value for queue in ordered] == [20, 28, 22, 26, 38]
    assert [queue.depth for queue in ordered] == [2, 2, 1, 1, 0]
    assert ordered[-1].is_winner


def test_step_queue_depth_reorders_default_frontier_view(monkeypatch, capsys):
    monkeypatch.setattr(
        cli_module,
        "_load_ew_terms",
        lambda count: tuple(EW_PREFIX_23[:count]),
    )

    cli_module.step(23, queue_depth=True, max_width=0)

    output = capsys.readouterr().out
    assert "queue-frontier mode: losing queues sorted by descending depth" in output
    queue_lines = [
        line
        for line in output.splitlines()
        if line.lstrip().startswith(("L ", "W "))
    ]
    assert [int(line.split()[1]) for line in queue_lines] == [20, 28, 22, 26, 38]


def test_step_queue_depth_json_is_machine_readable(monkeypatch, capsys):
    monkeypatch.setattr(
        cli_module,
        "_load_ew_terms",
        lambda count: tuple(EW_PREFIX_23[:count]),
    )

    cli_module.step(23, queue_depth=True, format="json")

    payload = json.loads(capsys.readouterr().out)
    assert payload["view"] == "queue-frontiers"
    assert payload["ordering"] == "queue-depth-desc,display-value-asc,winner-last"
    assert [(row["display_value"], row["queue_depth"]) for row in payload["queues"]] == [
        (20, 2),
        (28, 2),
        (22, 1),
        (26, 1),
        (38, 0),
    ]


def test_step_default_is_frontier_value_order(monkeypatch, capsys):
    monkeypatch.setattr(
        cli_module,
        "_load_ew_terms",
        lambda count: tuple(EW_PREFIX_23[:count]),
    )

    cli_module.step(11, max_width=0)

    output = capsys.readouterr().out
    assert "queue-frontier mode: one row per represented exact-support queue" in output
    assert "L     14" in output
    assert "W     18" in output
    assert "role object occurrence" not in output
