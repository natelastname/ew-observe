"""Candidate audit presentation with explicit fresh-prime reduction status."""

from __future__ import annotations

import csv
import io
import json

from .decision import CandidateAudit
from .human_sort import prime_exponents
from .presentation import OutputFormat


def _factorization(value: int) -> str:
    factors = prime_exponents(value)
    if not factors:
        return "1"
    return "·".join(
        str(prime) if exponent == 1 else f"{prime}^{exponent}"
        for prime, exponent in factors
    )


def _role_factorization(audit: CandidateAudit) -> str:
    pieces: list[str] = []
    for prime, exponent in prime_exponents(audit.value):
        prefix = "+" if prime in audit.introduced_primes else ""
        piece = str(prime) if exponent == 1 else f"{prime}^{exponent}"
        pieces.append(prefix + piece)
    return "·".join(pieces) if pieces else "1"


def _primes(values) -> str:
    return ",".join(str(value) for value in sorted(values))


def _payload(audit: CandidateAudit) -> dict[str, object]:
    return {
        "type": "ew-candidate-audit",
        "n": audit.n,
        "value": audit.value,
        "factorization": _factorization(audit.value),
        "role_factorization": _role_factorization(audit),
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
        "reduced_structurally_admissible": audit.reduced_structurally_admissible,
        "reduced_globally_admissible": audit.reduced_globally_admissible,
    }


def _render_text(audit: CandidateAudit) -> str:
    primitive = ", ".join(reason.value for reason in audit.rejection_reasons) or "none"
    reduction = ", ".join(reason.value for reason in audit.reduction_reasons) or "none"
    used = f"a_{audit.used_at}" if audit.used_at is not None else "—"
    beyond = _primes(audit.primes_beyond_fresh_frontier) or "—"
    return "\n".join(
        (
            f"Candidate {audit.value} before a_{audit.n}",
            f"  factorization       : {_factorization(audit.value)}",
            f"  factor roles        : {_role_factorization(audit)}",
            f"  used at             : {used}",
            f"  fresh-prime ceiling : Q_{audit.n} = {audit.least_unintroduced_prime}",
            f"  primes above Q      : {beyond}",
            f"  primitive local EW  : {'PASS' if audit.structurally_admissible else 'FAIL'}",
            f"  primitive globally  : {'YES' if audit.globally_admissible else 'NO'}",
            f"  reduced candidate   : {'YES' if audit.in_reduced_candidate_universe else 'NO'}",
            f"  reduced globally    : {'YES' if audit.reduced_globally_admissible else 'NO'}",
            f"  primitive rejection : {primitive}",
            f"  safe reduction      : {reduction}",
            "",
            "Primitive EW rules are definition-level; the fresh-prime ceiling is a safe theorem-level reduction.",
        )
    ) + "\n"


def _render_delimited(row: dict[str, object], delimiter: str) -> str:
    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=list(row),
        delimiter=delimiter,
        lineterminator="\n",
    )
    writer.writeheader()
    writer.writerow(row)
    return output.getvalue()


def render_candidate_audit(
    audit: CandidateAudit,
    *,
    output_format: OutputFormat | str = OutputFormat.TEXT,
) -> str:
    """Render primitive and reduced candidate status without conflating them."""

    format_ = OutputFormat(output_format)
    payload = _payload(audit)
    if format_ is OutputFormat.TEXT:
        return _render_text(audit)
    if format_ is OutputFormat.MARKDOWN:
        beyond = payload["primes_beyond_fresh_frontier"] or "—"
        return (
            f"### Candidate `{audit.value}` before `a_{audit.n}`\n\n"
            f"- fresh-prime ceiling: `Q_{audit.n} = {audit.least_unintroduced_prime}`\n"
            f"- factorization: `{payload['factorization']}`\n"
            f"- primitive globally admissible: `{audit.globally_admissible}`\n"
            f"- in reduced candidate universe: `{audit.in_reduced_candidate_universe}`\n"
            f"- reduced globally admissible: `{audit.reduced_globally_admissible}`\n"
            f"- primes above Q: `{beyond}`\n"
            f"- reduction reasons: `{payload['reduction_reasons'] or 'none'}`\n"
        )
    if format_ is OutputFormat.JSON:
        return json.dumps(payload, indent=2, sort_keys=False) + "\n"

    row = {
        "n": audit.n,
        "value": audit.value,
        "factorization": _factorization(audit.value),
        "support": _primes(audit.support),
        "least_unintroduced_prime": audit.least_unintroduced_prime,
        "primes_beyond_fresh_frontier": _primes(audit.primes_beyond_fresh_frontier),
        "primitive_structurally_admissible": audit.structurally_admissible,
        "primitive_globally_admissible": audit.globally_admissible,
        "in_reduced_candidate_universe": audit.in_reduced_candidate_universe,
        "reduced_globally_admissible": audit.reduced_globally_admissible,
        "primitive_rejection_reasons": ";".join(
            reason.value for reason in audit.rejection_reasons
        ),
        "reduction_reasons": ";".join(
            reason.value for reason in audit.reduction_reasons
        ),
    }
    return _render_delimited(row, "\t" if format_ is OutputFormat.TSV else ",")
