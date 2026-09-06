import json

import ew_observe.cli as cli_module
from ew_observe import EWObserver
from ew_observe.queue_head_presentation import ordered_queue_heads, render_queue_head_trace


EW_PREFIX_23 = [
    1, 2, 6, 15, 35, 14, 12, 33, 55, 10, 18, 21, 77, 22, 20,
    45, 39, 26, 28, 63, 51, 34, 38,
]


def test_step_11_collapses_old_members_to_current_queue_heads():
    trace = EWObserver(EW_PREFIX_23[:11]).trace_queue_heads(11)

    assert [head.value for head in trace.heads] == [28, 18]
    assert [(head.value, head.depth, head.source_threats, head.is_winner) for head in trace.heads] == [
        (28, 1, (14,), False),
        (18, 2, (6, 12), True),
    ]


def test_default_queue_head_renderer_shows_only_current_heads():
    trace = EWObserver(EW_PREFIX_23[:11]).trace_queue_heads(11)
    rendered = render_queue_head_trace(trace, max_width=0)

    assert "role object depth" in rendered
    assert "H     28" in rendered
    assert "W     18" in rendered
    assert "Compressed 3 already-used threats into 2 represented exact-support queues." in rendered

    candidate_lines = [
        line
        for line in rendered.splitlines()
        if line.lstrip().startswith(("H ", "W "))
    ]
    assert [int(line.split()[1]) for line in candidate_lines] == [28, 18]
    assert all(int(line.split()[1]) not in {6, 12, 14} for line in candidate_lines)


def test_queue_depth_option_reorders_heads_not_historical_members():
    trace = EWObserver(EW_PREFIX_23).trace_queue_heads(23)

    default = ordered_queue_heads(trace, queue_depth_order=False)
    by_depth = ordered_queue_heads(trace, queue_depth_order=True)

    assert [head.value for head in default] == [40, 44, 52, 56, 38]
    assert [head.value for head in by_depth] == [40, 56, 44, 52, 38]
    assert [head.depth for head in by_depth] == [2, 2, 1, 1, 0]


def test_queue_head_json_keeps_compression_provenance():
    trace = EWObserver(EW_PREFIX_23[:11]).trace_queue_heads(11)
    payload = json.loads(render_queue_head_trace(trace, output_format="json"))

    assert payload["type"] == "ew-decision-queue-head-trace"
    assert payload["view"] == "queue-heads"
    assert [(row["value"], row["queue_depth"]) for row in payload["queue_heads"]] == [
        (28, 1),
        (18, 2),
    ]
    assert payload["queue_heads"][1]["source_threats"] == [6, 12]
    assert [row["value"] for row in payload["exhaustive_threats"]] == [6, 12, 14]


def test_cli_default_is_queue_heads_and_exhaustive_view_is_opt_in(monkeypatch, capsys):
    monkeypatch.setattr(
        cli_module,
        "_load_ew_terms",
        lambda count: tuple(EW_PREFIX_23[:count]),
    )

    cli_module.step(11, max_width=0)
    default = capsys.readouterr().out
    assert "role object depth" in default
    assert "H     28" in default
    assert "role object occurrence" not in default

    cli_module.step(11, max_width=0, exhaustive_threats=True)
    exhaustive = capsys.readouterr().out
    assert "role object occurrence" in exhaustive
    assert "T      6" in exhaustive
