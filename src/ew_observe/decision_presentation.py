"""Decision-trace presentation enriched with the fresh-prime reduction.

The older presentation module remains the incidence-table implementation. This
wrapper preserves its human output while augmenting every machine format with
the theorem-level candidate-universe metadata.
"""

from __future__ import annotations

import csv
import io
import json

from .decision import CandidateAudit, DecisionTrace
from .presentation import OutputFormat, render_decision_trace as _base_render


def _reduction_fields(audit: CandidateAudit) -> dict[str, object]:
    return {
        "least_unintroduced_prime": audit.least_unintroduced_prime,
        "primes_beyond_fresh_frontier": sorted(audit.primes_beyond_fresh_frontier),
        "primitive_globally_admissible": audit.globally_admissible,
        "in_reduced_candidate_universe": audit.in_reduced_candidate_universe,
        "reduced_structurally_admissible": audit.reduced_structurally_admissible,
        "reduced_globally_admissible": audit.reduced_globally_admissible,
        "reduction_reasons": [reason.value for reason in audit.reduction_reasons],
    }


def _render_json(trace: DecisionTrace, **kwargs) -> str:
    payload = json.loads(
        _base_render(trace, output_format=OutputFormat.JSON, **kwargs)
    )
    payload["least_unintroduced_prime"] = trace.least_unintroduced_prime
    payload["candidate_universe"] = {
        "kind": "fresh-prime-reduced",
        "prime_ceiling": trace.least_unintroduced_prime,
        "primitive_structural_candidates_pruned_below_winner": (
            trace.fresh_frontier_pruned_threats
        ),
    }
    for row, audit in zip(payload["threats"], trace.threats, strict=True):
        row.update(_reduction_fields(audit))
    payload["winner"].update(_reduction_fields(trace.winner_audit))
    payload["summary"]["fresh_frontier_pruned_threats"] = (
        trace.fresh_frontier_pruned_threats
    )
    return json.dumps(payload, indent=2, sort_keys=False) + "\n"


def _render_delimited(
    trace: DecisionTrace,
    *,
    format_: OutputFormat,
    **kwargs,
) -> str:
    delimiter = "\t" if format_ is OutputFormat.TSV else ","
    base = _base_render(trace, output_format=format_, **kwargs)
    reader = csv.DictReader(io.StringIO(base), delimiter=delimiter)
    old_rows = list(reader)
    audits = [*trace.threats, trace.winner_audit]
    rows: list[dict[str, object]] = []
    for row, audit in zip(old_rows, audits, strict=True):
        row = dict(row)
        row["least_unintroduced_prime"] = audit.least_unintroduced_prime
        row["primes_beyond_fresh_frontier"] = ";".join(
            str(prime) for prime in sorted(audit.primes_beyond_fresh_frontier)
        )
        row["primitive_globally_admissible"] = audit.globally_admissible
        row["in_reduced_candidate_universe"] = audit.in_reduced_candidate_universe
        row["reduced_globally_admissible"] = audit.reduced_globally_admissible
        row["reduction_reasons"] = ";".join(
            reason.value for reason in audit.reduction_reasons
        )
        rows.append(row)

    if not rows:
        return ""
    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=list(rows[0]),
        delimiter=delimiter,
        lineterminator="\n",
    )
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def render_decision_trace(
    trace: DecisionTrace,
    *,
    output_format: OutputFormat | str = OutputFormat.TEXT,
    diagnostics: bool = False,
    max_width: int = 160,
    candidates_per_table: int = 0,
) -> str:
    """Render a reduced decision trace without changing established human text."""

    format_ = OutputFormat(output_format)
    kwargs = {
        "diagnostics": diagnostics,
        "max_width": max_width,
        "candidates_per_table": candidates_per_table,
    }
    if format_ in {OutputFormat.TEXT, OutputFormat.MARKDOWN}:
        return _base_render(trace, output_format=format_, **kwargs)
    if format_ is OutputFormat.JSON:
        return _render_json(trace, **kwargs)
    return _render_delimited(trace, format_=format_, **kwargs)
