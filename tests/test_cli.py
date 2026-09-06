import ew_observe.cli as cli_module


EW_PREFIX = [1, 2, 6, 15, 35, 14, 12, 33, 55, 10, 18]


def test_step_renders_threat_ledger(monkeypatch, capsys):
    monkeypatch.setattr(cli_module, "_load_ew_terms", lambda count: tuple(EW_PREFIX[:count]))

    cli_module.step(11)

    output = capsys.readouterr().out
    assert "EW greedy decision n=11" in output
    assert "threat ledger" in output
    assert "| 6 | {2,3} | {2} | {3} | 3 | PAID |" in output
