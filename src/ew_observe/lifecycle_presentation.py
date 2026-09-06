"""Presentation layer for candidate lifecycle traces."""

from __future__ import annotations

import csv
import io
import json
from collections.abc import Iterable, Sequence

from .decision import CandidateAudit, RejectionReason, ReductionReason
from .lifecycle import (
    CandidateLifecycleStatus,
    CandidateLifecycleStep,
    CandidateLifecycleTrace,
)
from .presentation import OutputFormat


def _primes(values: Iterable[int]) -> str:
    ordered = sorted(values)
    return ",".join(str(value) for value in ordered) if ordered else "—"


def _machine_primes(values: Iterable[int]) -> str:
    return ";".join(str(value) for value in sorted(values))


def _blockers(audit: CandidateAudit) -> tuple[RejectionReason, ...]:
    return tuple(
        reason
        for reason in audit.rejection_reasons
        if reason is not RejectionReason.USED_BEFORE
    )


def _short_reason(reason: RejectionReason) -> str:
    return {
        RejectionReason.NO_PREDECESSOR_OVERLAP: "no-overlap",
        RejectionReason.TWO_BACK_CONFLICT: "2-back",
        RejectionReason.NO_NEW_PRIME: "no-new",
        RejectionReason.USED_BEFORE: "used",
    }[reason]


def _short_reduction(reason: ReductionReason) -> str:
    return {
        ReductionReason.PRIME_BEYOND_LEAST_UNINTRODUCED: ">Q",
    }[reason]


def _status_text(step: CandidateLifecycleStep) -> str:
    if step.status is CandidateLifecycleStatus.SELECTED:
        return "SELECTED"
    if step.status is CandidateLifecycleStatus.LIVE_LOST:
        return "LIVE-LOST"
    if step.status is CandidateLifecycleStatus.USED:
        used_at = step.candidate_audit.used_at
        return f"USED@a_{used_at}" if used_at is not None else "USED"

    primitive = _blockers(step.candidate_audit)
    reductions = step.candidate_audit.reduction_reasons
    labels = [
        *(_short_reason(reason) for reason in primitive),
        *(_short_reduction(reason) for reason in reductions),
    ]
    return "BLOCKED" if not labels else "BLOCKED:" + ",".join(labels)


def _compact_values(values: Sequence[int], *, limit: int = 7) -> str:
    if not values:
        return "—"
    if len(values) <= limit:
        return ",".join(str(value) for value in values)
    shown = ",".join(str(value) for value in values[: limit - 2])
    return f"{shown},…,{values[-1]} ({len(values)})"


def _transition_text(step: CandidateLifecycleStep) -> str:
    pieces: list[str] = []
    if step.winner_retained_primes:
        pieces.append("=" + _primes(step.winner_retained_primes))
    if step.winner_introduced_primes:
        pieces.append("+" + _primes(step.winner_introduced_primes))
    if step.winner_dropped_primes:
        pieces.append("-" + _primes(step.winner_dropped_primes))
    return " ".join(pieces) if pieces else "—"


def _render_grid(headers: Sequence[str], rows: Sequence[Sequence[str]]) -> str:
    if any(len(row) != len(headers) for row in rows):
        raise ValueError("table rows must match header width")
    widths = [len(header) for header in headers]
    for row in rows:
        for index, cell in enumerate(row):
            widths[index] = max(widths[index], len(cell))

    def line(row: Sequence[str]) -> str:
        return "  ".join(
            cell.rjust(width) if index in {0, 1, 2, 3} else cell.ljust(width)
            for index, (cell, width) in enumerate(zip(row, widths, strict=True))
        ).rstrip()

    divider = "  ".join("-" * width for width in widths).rstrip()
    return "\n".join((line(headers), divider, *(line(row) for row in rows)))


def _audit_payload(audit: CandidateAudit) -> dict[str, object]:
    return {
        "value": audit.value,
        "support": sorted(audit.support),
        "used_at": audit.used_at,
        "predecessor_overlap": sorted(audit.predecessor_overlap),
        "two_back_overlap": sorted(audit.two_back_overlap),
        "retained_primes": sorted(audit.retained_primes),
        "introduced_primes": sorted(audit.introduced_primes),
        "least_unintroduced_prime": audit.least_unintroduced_prime,
        "primes_beyond_fresh_frontier": sorted(audit.primes_beyond_fresh_frontier),
        "primitive_rejection_reasons": [
            reason.value for reason in audit.rejection_reasons
        ],
        "reduction_reasons": [reason.value for reason in audit.reduction_reasons],
        "primitive_structurally_admissible": audit.structurally_admissible,
        "primitive_globally_admissible": audit.globally_admissible,
        "in_reduced_candidate_universe": audit.in_reduced_candidate_universe,
        "reduced_globally_admissible": audit.reduced_globally_admissible,
    }


def _step_payload(step: CandidateLifecycleStep) -> dict[str, object]:
    return {
        "n": step.n,
        "state": {
            "two_back": step.two_back,
            "previous": step.previous,
            "winner": step.winner,
        },
        "least_unintroduced_prime": step.candidate_audit.least_unintroduced_prime,
        "legal_carriers": sorted(step.legal_carriers),
        "candidate": _audit_payload(step.candidate_audit),
        "status": step.status.value,
        "live_rank": step.live_rank,
        "beating_candidates": list(step.beating_candidates),
        "winning_blocker": step.winning_blocker,
        "winner_transition": {
            "retained_primes": sorted(step.winner_retained_primes),
            "introduced_primes": sorted(step.winner_introduced_primes),
            "dropped_primes": sorted(step.winner_dropped_primes),
            "next_face": sorted(step.next_face),
        },
    }


def _trace_payload(trace: CandidateLifecycleTrace) -> dict[str, object]:
    return {
        "type": "ew-candidate-lifecycle",
        "candidate_universe": "fresh-prime-reduced",
        "value": trace.value,
        "start": trace.start,
        "stop": trace.stop,
        "summary": {
            "first_used_at": trace.first_used_at,
            "first_live_at": trace.first_live_at,
            "live_steps": list(trace.live_steps),
            "live_loss_steps": list(trace.live_loss_steps),
            "selected_at": trace.selected_at,
        },
        "steps": [_step_payload(step) for step in trace.steps],
    }


def _render_text(trace: CandidateLifecycleTrace) -> str:
    rows: list[tuple[str, ...]] = []
    for step in trace.steps:
        rows.append(
            (
                str(step.n),
                str(step.two_back),
                str(step.previous),
                str(step.winner),
                str(step.candidate_audit.least_unintroduced_prime),
                _primes(step.legal_carriers),
                _status_text(step),
                str(step.live_rank) if step.live_rank is not None else "—",
                _compact_values(step.beating_candidates),
                _transition_text(step),
            )
        )

    lines = [
        f"EW candidate lifecycle: {trace.value}",
        f"steps a_{trace.start} through a_{trace.stop}; live/rank uses fresh-prime-reduced universe",
        "",
        _render_grid(
            (
                "n",
                "B",
                "A",
                "W",
                "Q",
                "carriers",
                "candidate status",
                "rank",
                "beaters",
                "A→W",
            ),
            rows,
        ),
        "",
        "A→W notation: = retained, + introduced, - dropped; +primes are the next legal carrier face.",
        "Q is the least globally unintroduced prime; BLOCKED:>Q means the candidate crosses that frontier.",
        "rank is among currently unused reduced-admissible candidates; beaters are exact in JSON/CSV/TSV.",
        "",
        f"first live step : {trace.first_live_at if trace.first_live_at is not None else '—'}",
        f"live-loss steps : {_compact_values(trace.live_loss_steps)}",
        f"selected at     : {trace.selected_at if trace.selected_at is not None else '—'}",
    ]
    if trace.first_used_at is not None and trace.selected_at is None:
        lines.append(f"first used at   : {trace.first_used_at} (outside this window)")
    return "\n".join(lines) + "\n"


def _render_markdown(trace: CandidateLifecycleTrace) -> str:
    lines = [
        f"## EW candidate lifecycle: `{trace.value}`",
        "",
        f"Steps `a_{trace.start}` through `a_{trace.stop}` in the fresh-prime-reduced candidate universe.",
        "",
        "| n | B | A | W | Q | legal carriers | candidate status | rank | beaters | A→W |",
        "| ---: | ---: | ---: | ---: | ---: | --- | --- | ---: | --- | --- |",
    ]
    for step in trace.steps:
        lines.append(
            "| "
            + " | ".join(
                (
                    str(step.n),
                    str(step.two_back),
                    str(step.previous),
                    str(step.winner),
                    str(step.candidate_audit.least_unintroduced_prime),
                    _primes(step.legal_carriers),
                    _status_text(step),
                    str(step.live_rank) if step.live_rank is not None else "—",
                    _compact_values(step.beating_candidates),
                    _transition_text(step),
                )
            )
            + " |"
        )
    lines.extend(
        (
            "",
            "`A→W`: `=` retained, `+` introduced, `-` dropped. The introduced primes are the next legal carrier face.",
            "",
            f"- first live step: `{trace.first_live_at}`",
            f"- live-loss steps: `{list(trace.live_loss_steps)}`",
            f"- selected at: `{trace.selected_at}`",
        )
    )
    return "\n".join(lines) + "\n"


def _flat_rows(trace: CandidateLifecycleTrace) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for step in trace.steps:
        audit = step.candidate_audit
        rows.append(
            {
                "value": trace.value,
                "n": step.n,
                "two_back": step.two_back,
                "previous": step.previous,
                "winner": step.winner,
                "least_unintroduced_prime": audit.least_unintroduced_prime,
                "legal_carriers": _machine_primes(step.legal_carriers),
                "status": step.status.value,
                "used_at": audit.used_at or "",
                "primitive_structurally_admissible": audit.structurally_admissible,
                "primitive_globally_admissible": audit.globally_admissible,
                "in_reduced_candidate_universe": audit.in_reduced_candidate_universe,
                "reduced_globally_admissible": audit.reduced_globally_admissible,
                "primes_beyond_fresh_frontier": _machine_primes(
                    audit.primes_beyond_fresh_frontier
                ),
                "primitive_rejection_reasons": ";".join(
                    reason.value for reason in audit.rejection_reasons
                ),
                "reduction_reasons": ";".join(
                    reason.value for reason in audit.reduction_reasons
                ),
                "live_rank": step.live_rank or "",
                "beating_candidates": ";".join(
                    str(value) for value in step.beating_candidates
                ),
                "winning_blocker": step.winning_blocker or "",
                "winner_retained_primes": _machine_primes(
                    step.winner_retained_primes
                ),
                "winner_introduced_primes": _machine_primes(
                    step.winner_introduced_primes
                ),
                "winner_dropped_primes": _machine_primes(
                    step.winner_dropped_primes
                ),
                "next_face": _machine_primes(step.next_face),
            }
        )
    return rows


def _render_delimited(rows: Sequence[dict[str, object]], delimiter: str) -> str:
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


def render_candidate_lifecycle(
    trace: CandidateLifecycleTrace,
    *,
    output_format: OutputFormat | str = OutputFormat.TEXT,
) -> str:
    """Render a candidate lifecycle in a human- or machine-readable format."""

    format_ = OutputFormat(output_format)
    if format_ is OutputFormat.TEXT:
        return _render_text(trace)
    if format_ is OutputFormat.MARKDOWN:
        return _render_markdown(trace)
    if format_ is OutputFormat.JSON:
        return json.dumps(_trace_payload(trace), indent=2, sort_keys=False) + "\n"
    rows = _flat_rows(trace)
    if format_ is OutputFormat.TSV:
        return _render_delimited(rows, "\t")
    return _render_delimited(rows, ",")
