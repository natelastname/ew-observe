from __future__ import annotations

import sys

from cyclopts import App

from .decision import prime_support
from .lifecycle_presentation import render_candidate_lifecycle
from .observer import EWObserver
from .presentation import OutputFormat, render_candidate_audit, render_decision_trace
from .queue_frontier_presentation import render_queue_frontier_trace
from .queue_head_presentation import render_queue_head_trace

app = App()


def _canonical_run():
    from lex_earliest_seqs import open_run, registry

    definition = registry.resolve("A336957")
    return open_run(definition)


def _load_ew_terms(count: int) -> tuple[int, ...]:
    """Load or extend the canonical EW prefix from ``lex-earliest-seqs``."""

    terms = _canonical_run().ensure(count)
    return tuple(int(term) for term in terms)


def _load_until_prime_debut(
    prime: int,
    *,
    search_limit: int,
) -> tuple[tuple[int, ...], int]:
    """Load EW until the first term divisible by the supplied prime."""

    if prime <= 2 or prime_support(prime) != frozenset({prime}):
        raise ValueError("--until-prime-debut requires an odd prime")
    if search_limit < 3:
        raise ValueError("--search-limit must be at least 3")

    run = _canonical_run()
    scanned = 0
    count = min(search_limit, 1024)
    while True:
        terms = tuple(int(term) for term in run.ensure(count))
        for zero_index in range(scanned, len(terms)):
            if terms[zero_index] % prime == 0:
                return terms, zero_index + 1
        scanned = len(terms)
        if count >= search_limit:
            raise ValueError(
                f"prime {prime} did not debut within the first {search_limit} terms"
            )
        count = min(search_limit, max(count * 2, count + 1024))


@app.command
def step(
    n: int,
    *,
    format: str = "text",
    diagnostics: bool = False,
    max_width: int = 160,
    candidates_per_table: int = 0,
    queue_depth: bool = False,
    queue_heads: bool = False,
    exhaustive_threats: bool = False,
) -> None:
    """Explain the exact greedy choice of ``a_n``.

    The default view has one row per represented exact-support queue. Losing
    queues display their maximal previously used member; the winning queue
    displays the actual winner. ``depth`` is the number of prior services of
    that queue before the step. By default losing queues are ordered by their
    displayed value; ``--queue-depth`` orders them by descending depth, then
    ascending displayed value. The winner always remains last.

    ``--queue-heads`` instead displays each represented queue's current first
    unused head. ``--exhaustive-threats`` restores the original uncompressed
    historical threat ledger. These two alternative views are mutually
    exclusive.

    ``--max-width`` is a soft width bound for grouping rows into self-contained
    incidence tables that each repeat the incoming B,A state; use ``0`` for one
    unlimited table. ``--candidates-per-table`` adds an explicit row cap.

    Formats: text (default), markdown, json, tsv, csv.
    """

    if queue_heads and exhaustive_threats:
        raise ValueError("use either --queue-heads or --exhaustive-threats, not both")
    if exhaustive_threats and queue_depth:
        raise ValueError("--queue-depth applies to the one-row-per-queue views")

    observer = EWObserver(_load_ew_terms(n))
    format_ = OutputFormat(format)
    if exhaustive_threats:
        rendered = render_decision_trace(
            observer.trace_step(n),
            output_format=format_,
            diagnostics=diagnostics,
            max_width=max_width,
            candidates_per_table=candidates_per_table,
        )
    else:
        trace = observer.trace_queue_heads(n)
        if queue_heads:
            rendered = render_queue_head_trace(
                trace,
                output_format=format_,
                diagnostics=diagnostics,
                max_width=max_width,
                candidates_per_table=candidates_per_table,
                queue_depth_order=queue_depth,
            )
        else:
            rendered = render_queue_frontier_trace(
                trace,
                output_format=format_,
                diagnostics=diagnostics,
                max_width=max_width,
                candidates_per_table=candidates_per_table,
                queue_depth_order=queue_depth,
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


@app.command
def track(
    value: int,
    *,
    start: int | None = None,
    stop: int | None = None,
    until_prime_debut: int | None = None,
    context: int = 16,
    search_limit: int = 1_000_000,
    format: str = "text",
) -> None:
    """Track one fixed candidate through consecutive real EW states.

    Supply either ``--stop N`` or ``--until-prime-debut Q``. If ``--start`` is
    omitted, the command shows the final ``--context`` steps ending at the
    resolved stop. Formats: text (default), markdown, json, tsv, csv.

    Example: ``ew-observe track 734 --start 745 --until-prime-debut 367``.
    """

    if stop is not None and until_prime_debut is not None:
        raise ValueError("use either --stop or --until-prime-debut, not both")
    if stop is None and until_prime_debut is None:
        raise ValueError("track requires --stop or --until-prime-debut")
    if context < 1:
        raise ValueError("--context must be positive")

    if until_prime_debut is not None:
        terms, resolved_stop = _load_until_prime_debut(
            until_prime_debut,
            search_limit=search_limit,
        )
    else:
        assert stop is not None
        resolved_stop = stop
        terms = _load_ew_terms(resolved_stop)

    resolved_start = (
        start
        if start is not None
        else max(3, resolved_stop - context + 1)
    )
    observer = EWObserver(terms)
    trace = observer.trace_candidate_lifecycle(
        value,
        start=resolved_start,
        stop=resolved_stop,
    )
    sys.stdout.write(
        render_candidate_lifecycle(
            trace,
            output_format=OutputFormat(format),
        )
    )


def cli() -> None:
    app()
