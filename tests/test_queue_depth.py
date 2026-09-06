import json

import ew_observe.cli as cli_module
from ew_observe import EWObserver
from ew_observe.queue_depth import (
    exact_support_queue_depth,
    exact_support_queue_value,
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


def test_depth_is_a_sort_order_not_a_collapse_switch_side_effect():
    trace = EWObserver(EW_PREFIX_23).trace_queue_heads(23)
    ordered = ordered_queue_frontiers(trace, sort_order="depth")

    assert [queue.frontier_value for queue in ordered] == [20, 28, 22, 26]
    assert [queue.depth for queue in ordered] == [2, 2, 1, 1]


def test_queue_depth_flag_controls_human_collapse(monkeypatch, capsys):
    monkeypatch.setattr(
        cli_module,
        "_load_ew_terms",
        lambda count: tuple(EW_PREFIX_23[:count]),
    )

    cli_module.step(11, queue_depth=True, max_width=0)
    collapsed = capsys.readouterr().out
    assert "queue-frontier mode" in collapsed
    assert "L     14" in collapsed
    assert "T      6" not in collapsed

    cli_module.step(11, queue_depth=False, max_width=0)
    expanded = capsys.readouterr().out
    assert "expanded reduced-threat view" in expanded
    assert "Q_11=13" in expanded
    assert "T      6" in expanded
    assert "T     12" in expanded
    assert "T     14" in expanded


def test_sort_depth_changes_human_order_without_changing_collapse(monkeypatch, capsys):
    monkeypatch.setattr(
        cli_module,
        "_load_ew_terms",
        lambda count: tuple(EW_PREFIX_23[:count]),
    )

    cli_module.step(23, sort="depth", max_width=0)
    output = capsys.readouterr().out
    losing_lines = [line for line in output.splitlines() if line.lstrip().startswith("L ")]
    assert [int(line.split()[1]) for line in losing_lines] == [20, 28, 22, 26]


def test_human_sort_and_collapse_flags_do_not_reorder_machine_json(monkeypatch, capsys):
    monkeypatch.setattr(
        cli_module,
        "_load_ew_terms",
        lambda count: tuple(EW_PREFIX_23[:count]),
    )

    cli_module.step(23, sort="depth", queue_depth=False, format="json")
    payload = json.loads(capsys.readouterr().out)

    assert payload["view"] == "queue-frontiers"
    assert payload["ordering"] == "display-value-asc,winner-last"
    assert payload["candidate_universe"]["kind"] == "fresh-prime-reduced"
    assert [(row["display_value"], row["queue_depth"]) for row in payload["queues"]] == [
        (20, 2),
        (22, 1),
        (26, 1),
        (28, 2),
        (38, 0),
    ]
