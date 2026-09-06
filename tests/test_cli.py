import json

import ew_observe.cli as cli_module


EW_PREFIX = [1, 2, 6, 15, 35, 14, 12, 33, 55, 10, 18]


def test_step_renders_prime_incidence_queue_frontiers(monkeypatch, capsys):
    monkeypatch.setattr(cli_module, "_load_ew_terms", lambda count: tuple(EW_PREFIX[:count]))

    cli_module.step(11)

    output = capsys.readouterr().out
    assert "EW step 11: choose a_11 = 18" in output
    assert "role object depth" in output
    assert "L=max previously used value in a losing queue" in output
    assert "+exponent = newly introduced prime" in output
    assert "Compressed 3 already-used threats into 2 represented exact-support queues." in output
    assert "Queue race details" not in output


def test_step_can_show_queue_diagnostics(monkeypatch, capsys):
    monkeypatch.setattr(cli_module, "_load_ew_terms", lambda count: tuple(EW_PREFIX[:count]))

    cli_module.step(11, diagnostics=True)

    output = capsys.readouterr().out
    assert "Queue race details" in output
    assert "last-used=14" in output
    assert "current-head=28" in output


def test_step_can_split_by_queue_row_count(monkeypatch, capsys):
    monkeypatch.setattr(cli_module, "_load_ew_terms", lambda count: tuple(EW_PREFIX[:count]))

    cli_module.step(11, max_width=0, candidates_per_table=1)

    output = capsys.readouterr().out
    assert "queue rows 1–1 (1/2)" in output
    assert "queue rows 2–2 (2/2)" in output
    assert output.count("role object depth") == 2


def test_step_can_split_tables_by_width(monkeypatch, capsys):
    monkeypatch.setattr(cli_module, "_load_ew_terms", lambda count: tuple(EW_PREFIX[:count]))

    cli_module.step(11, max_width=24)

    output = capsys.readouterr().out
    assert "queue rows" in output
    assert output.count("role object depth") > 1
    assert "prime columns" not in output


def test_step_json_is_machine_readable(monkeypatch, capsys):
    monkeypatch.setattr(cli_module, "_load_ew_terms", lambda count: tuple(EW_PREFIX[:count]))

    cli_module.step(11, format="json")

    payload = json.loads(capsys.readouterr().out)
    assert payload["n"] == 11
    assert payload["type"] == "ew-decision-queue-frontier-trace"
    assert [row["display_value"] for row in payload["queues"]] == [14, 18]
    assert payload["queues"][0]["current_head"] == 28
    assert payload["queues"][-1]["kind"] == "winner"


def test_step_queue_heads_remains_available(monkeypatch, capsys):
    monkeypatch.setattr(cli_module, "_load_ew_terms", lambda count: tuple(EW_PREFIX[:count]))

    cli_module.step(11, format="json", queue_heads=True)

    payload = json.loads(capsys.readouterr().out)
    assert payload["type"] == "ew-decision-queue-head-trace"
    assert [row["value"] for row in payload["queue_heads"]] == [28, 18]


def test_candidate_json_is_machine_readable(monkeypatch, capsys):
    monkeypatch.setattr(cli_module, "_load_ew_terms", lambda count: tuple(EW_PREFIX[:count]))

    cli_module.candidate(11, 14, format="json")

    payload = json.loads(capsys.readouterr().out)
    assert payload["type"] == "ew-candidate-audit"
    assert payload["value"] == 14
    assert payload["retained_primes"] == [2]
    assert payload["introduced_primes"] == [7]
