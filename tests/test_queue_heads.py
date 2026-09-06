import json

import ew_observe.cli as cli_module
from ew_observe import EWObserver
from ew_observe.queue_frontier_presentation import (
    ordered_queue_frontiers,
    render_queue_frontier_trace,
)
from ew_observe.queue_head_presentation import ordered_queue_heads, render_queue_head_trace
from ew_observe.queue_heads import current_exact_support_head


EW_PREFIX_23 = [
    1, 2, 6, 15, 35, 14, 12, 33, 55, 10, 18, 21, 77, 22, 20,
    45, 39, 26, 28, 63, 51, 34, 38,
]


def test_current_head_uses_full_used_set_not_visible_threat_count():
    class FakeObserver:
        def used_at_before(self, value: int, n: int) -> int | None:
            return 1 if value in {6, 12, 18, 24} else None

    depth, head = current_exact_support_head(
        FakeObserver(),
        n=100,
        support=frozenset({2, 3}),
    )

    assert (depth, head) == (4, 36)


def test_step_11_records_last_service_and_current_head_per_queue():
    trace = EWObserver(EW_PREFIX_23[:11]).trace_queue_heads(11)

    assert [head.value for head in trace.heads] == [28, 18]
    assert [head.last_used_value for head in trace.heads] == [14, 12]
    assert [head.frontier_value for head in trace.heads] == [14, 18]
    assert [(head.depth, head.source_threats, head.is_winner) for head in trace.heads] == [
        (1, (14,), False),
        (2, (6, 12), True),
    ]


def test_default_frontier_renderer_shows_max_used_loser_and_winner():
    trace = EWObserver(EW_PREFIX_23[:11]).trace_queue_heads(11)
    rendered = render_queue_frontier_trace(trace, max_width=0)

    assert "role object depth" in rendered
    assert "L     14" in rendered
    assert "W     18" in rendered
    assert "H     28" not in rendered
    assert "L=max previously used value in a losing queue" in rendered

    queue_lines = [
        line
        for line in rendered.splitlines()
        if line.lstrip().startswith(("L ", "W "))
    ]
    assert [int(line.split()[1]) for line in queue_lines] == [14, 18]


def test_explicit_queue_head_renderer_still_shows_current_heads():
    trace = EWObserver(EW_PREFIX_23[:11]).trace_queue_heads(11)
    rendered = render_queue_head_trace(trace, max_width=0)

    assert "H     28" in rendered
    assert "W     18" in rendered


def test_queue_depth_option_reorders_frontiers_by_depth_then_displayed_value():
    trace = EWObserver(EW_PREFIX_23).trace_queue_heads(23)

    default = ordered_queue_frontiers(trace, queue_depth_order=False)
    by_depth = ordered_queue_frontiers(trace, queue_depth_order=True)

    assert by_depth[-1].is_winner
    assert [head.depth for head in by_depth[:-1]] == sorted(
        [head.depth for head in by_depth[:-1]],
        reverse=True,
    )
    for left, right in zip(by_depth[:-2], by_depth[1:-1]):
        if left.depth == right.depth:
            assert left.frontier_value <= right.frontier_value
    assert sorted(head.frontier_value for head in default[:-1]) == [
        head.frontier_value for head in default[:-1]
    ]


def test_current_head_ordering_remains_available():
    trace = EWObserver(EW_PREFIX_23).trace_queue_heads(23)

    default = ordered_queue_heads(trace, queue_depth_order=False)
    by_depth = ordered_queue_heads(trace, queue_depth_order=True)

    assert [head.value for head in default] == [40, 44, 52, 56, 38]
    assert [head.value for head in by_depth] == [40, 56, 44, 52, 38]
    assert [head.depth for head in by_depth] == [2, 2, 1, 1, 0]


def test_frontier_json_keeps_both_last_used_and_current_head():
    trace = EWObserver(EW_PREFIX_23[:11]).trace_queue_heads(11)
    payload = json.loads(render_queue_frontier_trace(trace, output_format="json"))

    assert payload["type"] == "ew-decision-queue-frontier-trace"
    assert payload["view"] == "queue-frontiers"
    assert [(row["display_value"], row["queue_depth"]) for row in payload["queues"]] == [
        (14, 1),
        (18, 2),
    ]
    loser = payload["queues"][0]
    assert loser["kind"] == "loser"
    assert loser["last_used_value"] == 14
    assert loser["current_head"] == 28
    winner = payload["queues"][1]
    assert winner["kind"] == "winner"
    assert winner["display_value"] == 18
    assert winner["last_used_value"] == 12
    assert winner["current_head"] == 18
    assert winner["source_threats"] == [6, 12]


def test_cli_default_is_frontier_with_head_and_exhaustive_views_opt_in(monkeypatch, capsys):
    monkeypatch.setattr(
        cli_module,
        "_load_ew_terms",
        lambda count: tuple(EW_PREFIX_23[:count]),
    )

    cli_module.step(11, max_width=0)
    default = capsys.readouterr().out
    assert "L     14" in default
    assert "W     18" in default
    assert "H     28" not in default

    cli_module.step(11, max_width=0, queue_heads=True)
    heads = capsys.readouterr().out
    assert "H     28" in heads
    assert "W     18" in heads

    cli_module.step(11, max_width=0, exhaustive_threats=True)
    exhaustive = capsys.readouterr().out
    assert "role object occurrence" in exhaustive
    assert "T      6" in exhaustive
