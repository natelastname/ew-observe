# ew-observe

`ew-observe` is an instrumented research toolkit for the Enots--Wolley greedy sequence.

Its purpose is **not** to become the fastest EW term generator. Its purpose is to explain individual greedy choices, reconstruct the historical reasons that smaller candidates lost, compare unusual events with matched non-events, and turn persistent empirical phenomena into explicit mathematical proof obligations.

## Dependency direction

`ew-observe` consumes the canonical EW implementation and caches from [`lex-earliest-seqs`](https://github.com/natelastname/lex-earliest-seqs).

It intentionally does **not** depend on `enots-wolley-2`. If useful, `enots-wolley-2` can later depend on `ew-observe` for research analyses.

## Exact decision certificates

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

The default `text` format is a sparse prime-coordinate incidence view in the style of the `lex-earliest-seqs` tables. Rather than splitting one decision by prime columns, it groups consecutive candidate rows into smaller self-contained tables. Every table repeats the two incoming terms `B` and `A`, and its prime columns are exactly the primes present in `B`, `A`, and the candidate rows shown in that table.

By default `step` uses a soft line-width target of 160 characters and greedily adds candidates until adding the next one would make that mini-table wider. A single candidate is never split. Disable automatic width grouping with `--max-width 0`:

```bash
uv run ew-observe step 1000 --max-width 0
```

You can instead (or additionally) set an explicit candidate-row limit:

```bash
uv run ew-observe step 1000 --candidates-per-table 12
```

When both `--max-width` and `--candidates-per-table` are positive, whichever bound is reached first starts a new table.

The decision table uses row roles `B` (two-back), `A` (previous), `T` (smaller locally admissible threat), and `W` (winner). On `T` and `W` rows, a bare exponent is a prime shared with the predecessor and `+e` marks a newly introduced prime with exponent `e`. `B` and `A` rows use ordinary prime exponents.

## Candidate lifecycle microscope

A single decision trace is state-centric. The lifecycle microscope fixes one integer and follows it while the real EW state changes around it:

```python
trace = observer.trace_candidate_lifecycle(18, start=6, stop=12)
```

Each lifecycle row records:

- whether the tracked value is `blocked`, `live-lost`, `selected`, or already `used`;
- all local rejection reasons;
- its exact rank among currently unused locally admissible candidates when live;
- every currently live value below it when it loses, with the actual greedy winner singled out;
- the current legal carrier set `P(A) \\ P(B)`;
- the actual support transition `A -> W`: retained, introduced, and dropped primes.

The primes introduced by the actual winner are especially important: they are exactly the legal carrier face for the *next* EW step. Thus a lifecycle table makes carrier-face rotation visible directly.

The generic CLI takes an explicit stop:

```bash
uv run ew-observe track 18 --start 6 --stop 12
```

For prime-debut investigations it can resolve the stopping index automatically:

```bash
uv run ew-observe track 734 --start 745 --until-prime-debut 367
```

If `--start` is omitted, `track` shows the final 16 states by default; change that with `--context`. `--search-limit` bounds automatic prime-debut lookup.

The text table uses compact transition notation:

- `=p` means prime `p` is retained from predecessor to winner;
- `+p` means `p` is introduced by the winner and therefore belongs to the next legal carrier face;
- `-p` means `p` is dropped.

Human text may abbreviate a long beater list, but JSON/CSV/TSV always preserve the exact complete list.

## Output formats

All microscope commands support explicit output formats:

```bash
uv run ew-observe step 11 --format text
uv run ew-observe step 11 --format markdown
uv run ew-observe step 11 --format json
uv run ew-observe step 11 --format tsv
uv run ew-observe step 11 --format csv

uv run ew-observe candidate 11 14 --format json
uv run ew-observe track 18 --start 6 --stop 12 --format json
```

- `text` is optimized for terminal reading;
- `markdown` is retained for research notes and generated artifacts;
- `json` preserves complete structured mathematical data;
- `tsv` and `csv` emit flat analysis-friendly rows.

`--diagnostics` adds overlapping exhaustive rejection counts to human-oriented `step` output. The structured JSON representation always includes those counts.

For the known early step `a_11 = 18`, the threat ledger contains exactly `6`, `12`, and `14`, paid at indices `3`, `7`, and `6` respectively, followed by the winning row for `18`.

A decision trace fails loudly if the supplied prefix is inconsistent with the greedy rule, either because the observed winner is inadmissible/already used or because an unused admissible value lies below it. A candidate lifecycle similarly rejects a prefix if a tracked live candidate is smaller than the claimed winner, or if the claimed winner itself is inadmissible.

## Planned layers

1. **Decision engine** — exact reconstruction of individual EW greedy choices.
2. **Candidate lifecycles** — follow one fixed integer through live, blocked, losing, selected, and carrier-face-rotation states.
3. **Occurrence detectors** — thin definitions of phenomena such as parity defects, canonical `2Q` debuts, `(c-2)q -> cq` spoke maturation, and `Q`-star packets.
4. **Dossiers** — prime-incidence chronology, historical ancestry, queue/spoke state, and exact local counterfactuals for one occurrence.
5. **Matched controls and near misses** — compare events with structurally similar non-events and states one condition away from an event.
6. **Certificate compression** — identify a small common set of exact conditions sufficient to force an observed normal form.

The success criterion is not the number of terms inspected. It is whether the tool reduces an empirical mystery to a smaller set of theorem-shaped obligations.

## Development

```bash
uv sync
uv run pytest
uv run ew-observe --help
```

## License

MIT / Expat
