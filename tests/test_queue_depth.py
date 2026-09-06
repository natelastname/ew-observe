import ew_observe.cli as cli_module
from ew_observe import EWObserver
from ew_observe.queue_depth import exact_support_queue_depth
from ew_observe.queue_depth_presentation import (
    queue_depth_candidate_order,
    render_queue_depth_decision_trace,
)


EW_PREFIX = [1, 2, 6, 15, 35, 14, 12, 33, 55, 10, 18]


def test_exact_support_queue_depth_is_zero_based_rank():
    assert exact_support_queue_depth(6) == 0
    assert exact_support_queue_depth(12) == 1
    assert exact_support_queue_depth(18) == 2
    assert exact_support_queue_depth(24) == 3
    assert exact_support_queue_depth(14) == 0
    assert exact_support_queue_depth(8) == 2


def test_queue_depth_order_is_descending_then_numeric_with_winner_last():
    trace = EWObserver(EW_PREFIX).trace_step(11)
    ordered = queue_depth_candidate_order(trace)

    assert [audit.value for audit in ordered] == [12, 6, 14, 18]
    assert [exact_support_queue_depth(audit.value) for audit in ordered] == [1, 0, 0, 2]


def test_queue_depth_renderer_replaces_occurrence_column():
    trace = EWObserver(EW_PREFIX).trace_step(11)
    rendered = render_queue_depth_decision_trace(trace, max_width=0)

    assert "role object depth" in rendered
    assert "role object occurrence" not in rendered
    assert "queue-depth mode" in rendered
    assert "depth = number of smaller values with exactly the same prime support" in rendered

    candidate_lines = [
        line
        for line in rendered.splitlines()
        if line.lstrip().startswith(("T ", "W "))
    ]
    assert [int(line.split()[1]) for line in candidate_lines] == [12, 6, 14, 18]


def test_step_queue_depth_mode_is_optional(monkeypatch, capsys):
    monkeypatch.setattr(cli_module, "_load_ew_terms", lambda count: tuple(EW_PREFIX[:count]))

    cli_module.step(11, queue_depth=True, max_width=0)

    output = capsys.readouterr().out
    assert "role object depth" in output
    assert "Deepest paid threat: 12 at queue depth 1." in output


def test_step_default_remains_occurrence_order(monkeypatch, capsys):
    monkeypatch.setattr(cli_module, "_load_ew_terms", lambda count: tuple(EW_PREFIX[:count]))

    cli_module.step(11, max_width=0)

    output = capsys.readouterr().out
    assert "role object occurrence" in output
    assert "queue-depth mode" not in output
