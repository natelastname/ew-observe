# ew-observe

`ew-observe` is an instrumented research toolkit for the Enots--Wolley greedy sequence.

Its purpose is **not** to become the fastest EW term generator. Its purpose is to explain individual greedy choices, reconstruct the historical reasons that smaller candidates lost, compare unusual events with matched non-events, and turn persistent empirical phenomena into explicit mathematical proof obligations.

## Dependency direction

`ew-observe` consumes the canonical EW implementation and caches from [`lex-earliest-seqs`](https://github.com/natelastname/lex-earliest-seqs).

It intentionally does **not** depend on `enots-wolley-2`. If useful, `enots-wolley-2` can later depend on `ew-observe` for research analyses.

## First milestone: exact decision certificates

For a greedy choice

\[
B=a_{n-2},\qquad A=a_{n-1},\qquad W=a_n,
\]

let

\[
R=P(A)\setminus P(B)
\]

be the primes of the predecessor that can legally carry the next term.

The first-pass implementation deliberately uses an exhaustive reference oracle. For every positive integer `x < W` it determines all applicable rejection reasons:

- `used-before`;
- `no-predecessor-overlap`;
- `two-back-conflict`;
- `no-new-prime`.

The locally admissible values below `W` form the **threat set**. Greedy minimality requires every threat to have been used earlier. The default human-facing output is therefore a compact aligned **greedy race** showing each threat, its prime roles, and the exact earlier index at which history paid it.

The full exhaustive scan remains available lazily through the Python API and serves as the reference oracle for later optimized reconstructions.

### Python API

```python
from ew_observe import EWObserver

observer = EWObserver(terms)
trace = observer.trace_step(11)

# Exact status of one value against the state before a_11.
audit = observer.audit_candidate(11, 14)

# Full exhaustive scan from 1 through the observed winner.
for audit in observer.iter_candidate_audits(11):
    ...
```

### CLI

Use the canonical EW cache maintained by `lex-earliest-seqs`:

```bash
uv run ew-observe step 11
uv run ew-observe candidate 11 14
```

The default `text` format is a sparse prime-coordinate incidence table in the style of the `lex-earliest-seqs` tables. It keeps all prime columns on one line by default, even when that produces a very wide table. This makes the entire local support pattern visible at once. Width-based paneling is available only when explicitly requested with a positive `--max-width`, for example:

```bash
uv run ew-observe step 1000 --max-width 100
```

The decision table uses row roles `B` (two-back), `A` (previous), `T` (smaller locally admissible threat), and `W` (winner). On `T` and `W` rows, a bare exponent is a prime shared with the predecessor and `+e` marks a newly introduced prime with exponent `e`. `B` and `A` rows use ordinary prime exponents.

All microscope commands support explicit output formats:

```bash
uv run ew-observe step 11 --format text
uv run ew-observe step 11 --format markdown
uv run ew-observe step 11 --format json
uv run ew-observe step 11 --format tsv
uv run ew-observe step 11 --format csv

uv run ew-observe candidate 11 14 --format json
```

- `text` is optimized for terminal reading;
- `markdown` is retained for research notes and generated artifacts;
- `json` preserves the complete structured decision certificate, including prime sets and rejection reasons;
- `tsv` and `csv` emit one flat row per threat/winner for analysis pipelines.

`--diagnostics` adds overlapping exhaustive rejection counts to human-oriented `step` output. The structured JSON representation always includes those counts.

For the known early step `a_11 = 18`, the threat ledger contains exactly `6`, `12`, and `14`, paid at indices `3`, `7`, and `6` respectively, followed by the winning row for `18`.

A trace fails loudly if the supplied prefix is inconsistent with the greedy rule, either because the observed winner is inadmissible/already used or because an unused admissible value lies below it.

## Planned layers

1. **Decision engine** — exact reconstruction of individual EW greedy choices.
2. **Occurrence detectors** — thin definitions of phenomena such as parity defects, canonical `2Q` debuts, `(c-2)q -> cq` spoke maturation, and `Q`-star packets.
3. **Dossiers** — prime-incidence chronology, historical ancestry, queue/spoke state, and exact local counterfactuals for one occurrence.
4. **Matched controls and near misses** — compare events with structurally similar non-events and states one condition away from an event.
5. **Certificate compression** — identify a small common set of exact conditions sufficient to force an observed normal form.

The success criterion is not the number of terms inspected. It is whether the tool reduces an empirical mystery to a smaller set of theorem-shaped obligations.

## Development

```bash
uv sync
uv run pytest
uv run ew-observe --help
```

## License

MIT / Expat
