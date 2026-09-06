import ew_observe.cli as cli_module
from ew_observe import EWObserver
from ew_observe.viewer import ViewerSession, ViewerState, viewport_lines


EW_PREFIX = [
    1, 2, 6, 15, 35, 14, 12, 33, 55, 10, 18, 21, 77, 22, 20,
    45, 39, 26, 28, 63, 51, 34, 38,
]


def _trace_loader(n: int):
    return EWObserver(EW_PREFIX[:n]).trace_queue_heads(n)


def test_viewer_starts_in_collapsed_frontier_value_view():
    session = ViewerSession(11, _trace_loader)

    assert session.state.collapsed
    assert session.state.queue_representation == "frontier"
    assert session.state.sort_order == "value"
    document = session.document()
    assert "L     14" in document
    assert "W     18" in document


def test_viewer_keys_switch_sort_collapse_representation_and_details():
    session = ViewerSession(11, _trace_loader)

    session.handle_key("x")
    assert session.state.sort_order == "prime-lex"

    session.handle_key("c")
    assert not session.state.collapsed
    expanded = session.document()
    assert "T      6" in expanded
    assert "T     12" in expanded
    assert "T     14" in expanded

    session.handle_key("c")
    session.handle_key("f")
    assert session.state.queue_representation == "head"
    heads = session.document()
    assert "H     28" in heads
    assert "W     18" in heads

    session.handle_key("i")
    assert session.state.diagnostics


def test_viewer_sort_keys_are_independent_of_collapse():
    session = ViewerSession(23, _trace_loader)
    session.handle_key("c")

    session.handle_key("d")
    assert session.state.sort_order == "depth"
    assert not session.state.collapsed

    session.handle_key("r")
    assert session.state.sort_order == "retained"
    assert not session.state.collapsed

    session.handle_key("v")
    assert session.state.sort_order == "value"


def test_viewer_step_navigation_uses_cache():
    calls: list[int] = []

    def load(n: int):
        calls.append(n)
        return _trace_loader(n)

    session = ViewerSession(11, load)
    assert calls == [11]

    session.handle_key("]")
    assert session.state.n == 12
    assert calls == [11, 12]

    session.handle_key("[")
    assert session.state.n == 11
    assert calls == [11, 12]

    session.handle_key("]")
    assert session.state.n == 12
    assert calls == [11, 12]


def test_viewport_lines_crop_and_clamp_both_axes():
    state = ViewerState(n=3, x=3, y=1)
    cropped = viewport_lines(
        "abcdef\n012345\nuvwxyz",
        state,
        width=3,
        height=2,
    )
    assert cropped == ("345", "xyz")

    state.x = 10**6
    state.y = 10**6
    cropped = viewport_lines(
        "abcdef\n012345\nuvwxyz",
        state,
        width=3,
        height=2,
    )
    assert state.x == 3
    assert state.y == 1
    assert cropped == ("345", "xyz")


def test_help_is_an_in_place_pager_document():
    session = ViewerSession(11, _trace_loader)
    session.handle_key("?")
    assert session.state.show_help
    assert "EW interactive viewer" in session.document()
    assert "collapse / expand exact queues" in session.document()


def test_q_requests_exit():
    session = ViewerSession(11, _trace_loader)
    assert session.handle_key("q") is False


def test_cli_view_uses_requested_invocation_pattern(monkeypatch):
    captured = {}

    def fake_run_viewer(n, loader):
        captured["n"] = n
        captured["loader"] = loader

    monkeypatch.setattr(cli_module, "run_viewer", fake_run_viewer)

    cli_module.view(10_000)

    assert captured["n"] == 10_000
    assert captured["loader"] is cli_module._load_ew_terms
