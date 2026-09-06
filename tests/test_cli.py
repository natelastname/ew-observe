import ew_observe.cli as cli_module


EW_PREFIX = [1, 2, 6, 15, 35, 14, 12, 33, 55, 10, 18]


def test_step_renders_readable_threat_ledger(monkeypatch, capsys):
    monkeypatch.setattr(cli_module, "_load_ew_terms", lambda count: tuple(EW_PREFIX[:count]))

    cli_module.step(11)

    output = capsys.readouterr().out
    assert "EW step 11: choose a_11 = 18" in output
    assert "Smaller admissible threats (< 18)" in output
    assert "factorization" in output
    assert "2·3" in output
    assert "a_3" in output
    assert "Conclusion: all 3 smaller admissible threats were already used" in output
    assert "Diagnostics" not in output


def test_step_can_show_diagnostics(monkeypatch, capsys):
    monkeypatch.setattr(cli_module, "_load_ew_terms", lambda count: tuple(EW_PREFIX[:count]))

    cli_module.step(11, diagnostics=True)

    output = capsys.readouterr().out
    assert "Diagnostics (rejection counts overlap)" in output
