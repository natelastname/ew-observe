import json

import ew_observe.cli as cli_module


EW_PREFIX_23 = [
    1, 2, 6, 15, 35, 14, 12, 33, 55, 10, 18, 21, 77, 22, 20,
    45, 39, 26, 28, 63, 51, 34, 38,
]


def _patch_terms(monkeypatch):
    monkeypatch.setattr(
        cli_module,
        "_load_ew_terms",
        lambda count: tuple(EW_PREFIX_23[:count]),
    )


def test_step_renders_prime_incidence_queue_frontiers(monkeypatch, capsys):
    _patch_terms(monkeypatch)

    cli_module.step(11)

    output = capsys.readouterr().out
    assert "EW step 11: choose a_11 = 18" in output
    assert "role object depth" in output
    assert "L=max previously used value in a losing queue" in output
    assert "+exponent = newly introduced prime" in output
    assert "Compressed 3 already-used threats into 2 represented exact-support queues." in output
    assert "Queue race details" not in output


def test_every_split_human_table_repeats_B_A_and_W(monkeypatch, capsys):
    _patch_terms(monkeypatch)

    cli_module.step(23, max_width=0, candidates_per_table=2)
    output = capsys.readouterr().out

    assert "losing queue rows 1–2 (1/2)" in output
    assert "losing queue rows 3–4 (2/2)" in output
    assert output.count("role object depth") == 2
    assert output.count("B     51") == 2
    assert output.count("A     34") == 2
    assert output.count("W     38") == 2


def test_expanded_human_tables_also_repeat_B_A_and_W(monkeypatch, capsys):
    _patch_terms(monkeypatch)

    cli_module.step(11, queue_depth=False, max_width=0, candidates_per_table=1)
    output = capsys.readouterr().out

    assert "threat rows 1–1 (1/3)" in output
    assert "threat rows 3–3 (3/3)" in output
    assert output.count("role object occurrence") == 3
    assert output.count("B     55") == 3
    assert output.count("A     10") == 3
    assert output.count("W     18") == 3


def test_step_can_show_queue_diagnostics(monkeypatch, capsys):
    _patch_terms(monkeypatch)

    cli_module.step(11, diagnostics=True)

    output = capsys.readouterr().out
    assert "Queue race details" in output
    assert "last-used=14" in output
    assert "current-head=28" in output


def test_step_json_is_machine_readable_and_canonical(monkeypatch, capsys):
    _patch_terms(monkeypatch)

    cli_module.step(23, format="json", sort="depth", queue_depth=False)

    payload = json.loads(capsys.readouterr().out)
    assert payload["n"] == 23
    assert payload["type"] == "ew-decision-queue-frontier-trace"
    assert payload["ordering"] == "display-value-asc,winner-last"
    assert [row["display_value"] for row in payload["queues"]] == [20, 22, 26, 28, 38]
    assert payload["queues"][-1]["kind"] == "winner"


def test_step_queue_heads_machine_view_remains_available(monkeypatch, capsys):
    _patch_terms(monkeypatch)

    cli_module.step(11, format="json", queue_heads=True)

    payload = json.loads(capsys.readouterr().out)
    assert payload["type"] == "ew-decision-queue-head-trace"
    assert [row["value"] for row in payload["queue_heads"]] == [28, 18]


def test_candidate_json_is_machine_readable(monkeypatch, capsys):
    _patch_terms(monkeypatch)

    cli_module.candidate(11, 14, format="json")

    payload = json.loads(capsys.readouterr().out)
    assert payload["type"] == "ew-candidate-audit"
    assert payload["value"] == 14
    assert payload["retained_primes"] == [2]
    assert payload["introduced_primes"] == [7]
