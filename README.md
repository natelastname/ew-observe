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

The reference oracle exhaustively checks every positive integer `x < W` and records all applicable rejection reasons:

- `used-before`;
- `no-predecessor-overlap`;
- `two-back-conflict`;
- `no-new-prime`.

The locally admissible values below `W` form the exhaustive historical **threat set**. Greedy minimality requires every threat to have been used earlier. That exhaustive ledger is preserved as the correctness oracle, but it is not the default human view.

### Exact-support queue-head compression

Values with the same exact prime support form an increasing exact-support queue. EW can only consume that queue in increasing order: if a larger value with support `S` were chosen while a smaller unused value with the same support remained, the smaller value would satisfy exactly the same local support conditions and would beat it greedily.

Therefore the mechanistic state of one represented exact-support queue is completely summarized by its current first-unused **queue head** and its zero-based depth (the number of already-serviced values in that queue).

The default `step` view groups the exhaustive threats by exact support and replaces every historical group with one current queue-head row. The represented queues are the supports witnessed by at least one smaller historical threat, together with the winner support. Untouched supports are not enumerated: the exhaustive greedy certificate already guarantees that no untouched admissible support has a first value below the winner.

For example, before `a_11 = 18`, the historical threat values `6` and `12` both belong to support `{2,3}`. They collapse to the current queue head `18` at depth 2. The historical threat `14` belongs to `{2,7}` and collapses to current head `28` at depth 1. Thus the default race is between current heads `28` and winning head `18`, not between historical values `6,12,14`.

### Python API

```python
from ew_observe import EWObserver

observer = EWObserver(terms)

# Exhaustive correctness certificate.
decision = observer.trace_step(11)

# Default mechanistic compression to current exact-support heads.
queue_trace = observer.trace_queue_heads(11)

# Exact status of one value against the state before a_11.
audit = observer.audit_candidate(11, 14)

# Full exhaustive scan from 1 through the observed winner.
for audit in observer.iter_candidate_audits(11):
    ...
```

## CLI

Use the canonical EW cache maintained by `lex-earliest-seqs`:

```bash
uv run ew-observe step 11
uv run ew-observe candidate 11 14
```

The default `step` text output is a sparse prime-coordinate incidence view of the **current queue heads**. Row roles are:

- `B`: two-back term;
- `A`: previous term;
- `H`: current nonwinning exact-support queue head;
- `W`: winning queue head.

The `depth` column is the number of already-serviced values in that exact-support queue. On `H` and `W` rows, a bare exponent is a prime shared with the predecessor and `+e` marks a newly introduced prime with exponent `e`. `B` and `A` rows use ordinary prime exponents.

By default nonwinning heads are ordered by numerical head value, with `W` left last for readability. To order heads by descending queue depth, breaking ties by ascending head value:

```bash
uv run ew-observe step 1000 --queue-depth
```

The old exhaustive historical ledger remains available explicitly:

```bash
uv run ew-observe step 1000 --exhaustive-threats
```

### Table grouping

Rather than splitting one table by prime columns, `step` groups queue-head rows into smaller self-contained tables. Every table repeats `B` and `A`, and its prime columns are exactly the primes present in those incoming terms and the queue heads shown there.

By default `step` uses a soft line-width target of 160 characters. Disable automatic width grouping with:

```bash
uv run ew-observe step 1000 --max-width 0
```

You can instead or additionally set an explicit row cap:

```bash
uv run ew-observe step 1000 --candidates-per-table 12
```

When both bounds are positive, whichever is reached first starts a new table. A single queue head is never split across prime-column panels.

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

uv run ew-observe step 11 --queue-depth --format json
uv run ew-observe step 11 --exhaustive-threats --format json
uv run ew-observe candidate 11 14 --format json
uv run ew-observe track 18 --start 6 --stop 12 --format json
```

- `text` is optimized for terminal reading;
- `markdown` is retained for research notes and generated artifacts;
- `json` preserves structured mathematical data;
- `tsv` and `csv` emit flat analysis-friendly rows.

The default structured `step` output includes each current queue head, its support, queue depth, and the historical threat values compressed into that queue. JSON also retains the exhaustive source-threat list. `--exhaustive-threats` restores the original uncompressed decision representation directly.

A decision trace fails loudly if the supplied prefix is inconsistent with the greedy rule, either because the observed winner is inadmissible/already used or because an unused admissible value lies below it. Queue-head compression also verifies that the winner really is the current head of its exact-support queue and that no represented competing head lies below it.

## Planned layers

1. **Decision engine** — exact reconstruction of individual EW greedy choices.
2. **Queue-head microscope** — compress historical threats to the current state of each represented exact-support queue.
3. **Candidate lifecycles** — follow one fixed integer through live, blocked, losing, selected, and carrier-face-rotation states.
4. **Occurrence detectors** — thin definitions of phenomena such as parity defects, canonical `2Q` debuts, `(c-2)q -> cq` spoke maturation, and `Q`-star packets.
5. **Dossiers** — prime-incidence chronology, historical ancestry, queue/spoke state, and exact local counterfactuals for one occurrence.
6. **Matched controls and near misses** — compare events with structurally similar non-events and states one condition away from an event.
7. **Certificate compression** — identify a small common set of exact conditions sufficient to force an observed normal form.

The success criterion is not the number of terms inspected. It is whether the tool reduces an empirical mystery to a smaller set of theorem-shaped obligations.

## Development

```bash
uv sync
uv run pytest
uv run ew-observe --help
```

## License

MIT / Expat
