from __future__ import annotations

import sys

from cyclopts import App

from .decision import EWObserver
from .presentation import OutputFormat, render_candidate_audit, render_decision_trace

app = App()


def _load_ew_terms(count: int) -> tuple[int, ...]:
    """Load or extend the canonical EW prefix from ``lex-earliest-seqs``."""

    from lex_earliest_seqs import open_run, registry

    definition = registry.resolve("A336957")
    run = open_run(definition)
    terms = run.ensure(count)
    return tuple(int(term) for term in terms)


@app.command
def step(
    n: int,
    *,
    format: str = "text",
    diagnostics: bool = False,
) -> None:
    """Explain the exact greedy choice of ``a_n`` using the threat ledger.

    Formats: text (default), markdown, json, tsv, csv.
    """

    observer = EWObserver(_load_ew_terms(n))
    rendered = render_decision_trace(
        observer.trace_step(n),
        output_format=OutputFormat(format),
        diagnostics=diagnostics,
    )
    sys.stdout.write(rendered)


@app.command
def candidate(n: int, value: int, *, format: str = "text") -> None:
    """Audit one positive integer against the EW state before ``a_n``.

    Formats: text (default), markdown, json, tsv, csv.
    """

    observer = EWObserver(_load_ew_terms(n))
    rendered = render_candidate_audit(
        observer.audit_candidate(n, value),
        output_format=OutputFormat(format),
    )
    sys.stdout.write(rendered)


def cli() -> None:
    app()
