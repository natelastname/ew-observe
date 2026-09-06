import json

import ew_observe.cli as cli_module


EW_PREFIX = [
    1,
    2,
    6,
    15,
    35,
    14,
    12,
    33,
    55,
    10,
    18,
    21,
    77,
    22,
    20,
    45,
    39,
    26,
    28,
    63,
    51,
    34,
    38,
    57,
    69,
    46,
    40,
    65,
    91,
    42,
]


class _FakeRun:
    def __init__(self, terms):
        self.terms = tuple(terms)

    def ensure(self, count):
        if count > len(self.terms):
            return self.terms
        return self.terms[:count]


def test_track_json_uses_requested_window(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        cli_module,
        "_load_ew_terms",
        lambda count: tuple(EW_PREFIX[:count]),
    )

    cli_module.track(18, start=6, stop=12, format="json")

    payload = json.loads(capsys.readouterr().out)
    assert payload["value"] == 18
    assert payload["start"] == 6
    assert payload["stop"] == 12
    assert payload["summary"]["live_loss_steps"] == [7]
    assert payload["summary"]["selected_at"] == 11


def test_until_prime_debut_resolves_first_incidence(monkeypatch) -> None:
    monkeypatch.setattr(cli_module, "_canonical_run", lambda: _FakeRun(EW_PREFIX))

    terms, debut = cli_module._load_until_prime_debut(7, search_limit=30)

    assert debut == 5
    assert terms[debut - 1] == 35


def test_track_defaults_to_final_context(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        cli_module,
        "_load_until_prime_debut",
        lambda prime, search_limit: (tuple(EW_PREFIX), 11),
    )

    cli_module.track(18, until_prime_debut=17, context=4, format="json")

    payload = json.loads(capsys.readouterr().out)
    assert payload["start"] == 8
    assert payload["stop"] == 11
