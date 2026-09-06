from __future__ import annotations

from cyclopts import App

from .decision import EWObserver, render_candidate_audit
from .presentation import render_decision_trace

app = App()


def _load_ew_terms(count: int) -> tuple[int, ...]:
    """Load or extend the canonical EW prefix from ``lex-earliest-seqs``."""

    from lex_earliest_seqs import open_run, registry

    definition = registry.resolve("A336957")
    run = open_run(definition)
    terms = run.ensure(count)
    return tuple(int(term) for term in terms)


@app.command
def step(n: int, *, diagnostics: bool = False) -> None:
    """Explain the exact greedy choice of ``a_n`` using the threat ledger."""

    observer = EWObserver(_load_ew_terms(n))
    print(render_decision_trace(observer.trace_step(n), diagnostics=diagnostics))


@app.command
def candidate(n: int, value: int) -> None:
    """Audit one positive integer against the EW state before ``a_n``."""

    observer = EWObserver(_load_ew_terms(n))
    print(render_candidate_audit(observer.audit_candidate(n, value)))


def cli() -> None:
    app()
