"""Queue-head presentation wrapper exposing the fresh-prime candidate universe.

The underlying queue-head trace is already built from the reduced decision
trace. This wrapper makes that fact explicit in JSON/TSV/CSV while preserving
the established text/Markdown renderer unchanged.
"""

from __future__ import annotations

import csv
import io
import json

from .presentation import OutputFormat
from .queue_head_presentation import render_queue_head_trace as _base_render
from .queue_heads import QueueHeadTrace


def render_queue_head_trace(
    trace: QueueHeadTrace,
    *,
    output_format: OutputFormat | str = OutputFormat.TEXT,
    diagnostics: bool = False,
    max_width: int = 160,
    candidates_per_table: int = 0,
    queue_depth_order: bool = False,
) -> str:
    """Render queue heads with explicit fresh-prime-frontier machine metadata."""

    format_ = OutputFormat(output_format)
    kwargs = {
        "diagnostics": diagnostics,
        "max_width": max_width,
        "candidates_per_table": candidates_per_table,
        "queue_depth_order": queue_depth_order,
    }
    if format_ in {OutputFormat.TEXT, OutputFormat.MARKDOWN}:
        return _base_render(trace, output_format=format_, **kwargs)

    decision = trace.decision
    if format_ is OutputFormat.JSON:
        payload = json.loads(_base_render(trace, output_format=format_, **kwargs))
        payload["least_unintroduced_prime"] = decision.least_unintroduced_prime
        payload["candidate_universe"] = {
            "kind": "fresh-prime-reduced",
            "prime_ceiling": decision.least_unintroduced_prime,
        }
        payload["reduced_threats"] = payload.pop("exhaustive_threats")
        return json.dumps(payload, indent=2, sort_keys=False) + "\n"

    delimiter = "\t" if format_ is OutputFormat.TSV else ","
    base = _base_render(trace, output_format=format_, **kwargs)
    reader = csv.DictReader(io.StringIO(base), delimiter=delimiter)
    rows = []
    for row in reader:
        enriched = dict(row)
        enriched["least_unintroduced_prime"] = decision.least_unintroduced_prime
        enriched["candidate_universe"] = "fresh-prime-reduced"
        rows.append(enriched)
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
