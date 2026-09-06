import json

import ew_observe.cli as cli_module


EW_PREFIX = [1, 2, 6, 15, 35, 14, 12, 33, 55, 10, 18]


def test_step_renders_prime_incidence_race(monkeypatch, capsys):
    monkeypatch.setattr(cli_module, "_load_ew_terms", lambda count: tuple(EW_PREFIX[:count]))

    cli_module.step(11)

    output = capsys.readouterr().out
    assert "EW step 11: choose a_11 = 18" in output
    assert "role object occurrence" in output
    assert "T=smaller admissible threat" in output
    assert "+exponent = newly introduced prime" in output
    assert "Last threat paid: 12 at a_7." in output
    assert "Diagnostics" not in output


def test_step_can_show_diagnostics(monkeypatch, capsys):
    monkeypatch.setattr(cli_module, "_load_ew_terms", lambda count: tuple(EW_PREFIX[:count]))

    cli_module.step(11, diagnostics=True)

    output = capsys.readouterr().out
    assert "Diagnostics (rejection counts overlap)" in output


def test_step_can_split_by_candidate_count(monkeypatch, capsys):
    monkeypatch.setattr(cli_module, "_load_ew_terms", lambda count: tuple(EW_PREFIX[:count]))

    cli_module.step(11, max_width=0, candidates_per_table=2)

    output = capsys.readouterr().out
    assert "candidate rows 1–2 (1/2)" in output
    assert "candidate rows 3–4 (2/2)" in output
    assert output.count("role object occurrence") == 2


def test_step_can_split_tables_by_width(monkeypatch, capsys):
    monkeypatch.setattr(cli_module, "_load_ew_terms", lambda count: tuple(EW_PREFIX[:count]))

    cli_module.step(11, max_width=32)

    output = capsys.readouterr().out
    assert "candidate rows" in output
    assert output.count("role object occurrence") > 1
    assert "prime columns" not in output


def test_step_json_is_machine_readable(monkeypatch, capsys):
    monkeypatch.setattr(cli_module, "_load_ew_terms", lambda count: tuple(EW_PREFIX[:count]))

    cli_module.step(11, format="json")

    payload = json.loads(capsys.readouterr().out)
    assert payload["n"] == 11
    assert payload["winner"]["value"] == 18


def test_candidate_json_is_machine_readable(monkeypatch, capsys):
    monkeypatch.setattr(cli_module, "_load_ew_terms", lambda count: tuple(EW_PREFIX[:count]))

    cli_module.candidate(11, 14, format="json")

    payload = json.loads(capsys.readouterr().out)
    assert payload["type"] == "ew-candidate-audit"
    assert payload["value"] == 14
    assert payload["retained_primes"] == [2]
    assert payload["introduced_primes"] == [7]
