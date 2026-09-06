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

The reference decision engine exhaustively checks every positive integer `x < W` and records all applicable rejection reasons:

- `used-before`;
- `no-predecessor-overlap`;
- `two-back-conflict`;
- `no-new-prime`.

The locally admissible values below `W` form the exhaustive historical **threat set**. Greedy minimality requires every such threat to have been used earlier. The exhaustive ledger remains available as a reference oracle, but the default human view compresses it by exact prime support.

### Exact-support queue race

For a support `S`, let

\[
q_0(S)<q_1(S)<q_2(S)<\cdots
\]

be the increasing exact-support queue. Before a given EW step, suppose exactly the first `d` values have been used. Then

- `d` is the queue depth / prior service count;
- `q_{d-1}(S)` is the maximal previously used value when `d>0`;
- `q_d(S)` is the current first-unused head.

The default human `step` view uses **one row per represented exact-support queue**. A losing queue displays its maximal previously used value `q_{d-1}`. The winning queue displays the actual winner `q_d = W`. Thus the table shows how far each competing queue has already been serviced rather than repeating every old member of that queue.

The represented finite queue set is the collection of supports witnessed by the exhaustive threats below `W`, together with the winner support. The tool deliberately does not pretend to enumerate the infinitely many untouched supports whose first possible values already lie above `W`.

### Python API

```python
from ew_observe import EWObserver

observer = EWObserver(terms)
decision = observer.trace_step(11)
queues = observer.trace_queue_heads(11)

# Exact status of one value against the state before a_11.
audit = observer.audit_candidate(11, 14)

# Full exhaustive scan from 1 through the observed winner.
for audit in observer.iter_candidate_audits(11):
    ...
```

Each queue in `queues.heads` records both its current first-unused `value` and its `last_used_value`, as well as its service `depth` and the exhaustive threat rows compressed into that queue.

### CLI: human views

Use the canonical EW cache maintained by `lex-earliest-seqs`:

```bash
uv run ew-observe step 11
uv run ew-observe candidate 11 14
```

The default `text` format is a sparse prime-coordinate incidence view in the style of the `lex-earliest-seqs` tables. Every self-contained mini-table repeats the complete incoming decision context **at the top**:

- `B`: two-back term;
- `A`: previous term;
- `W`: actual winner.

The sortable body then contains either queue representatives or exhaustive historical threats. In the default collapsed view, `L` is the maximal previously used value from a losing exact-support queue.

The `depth` column is the number of values already serviced in that exact queue before the step. On `L` and `W` rows, a bare exponent is a prime shared with the predecessor and `+e` marks a newly introduced prime with exponent `e`.

Human presentation has two independent axes: **collapse** and **sort**.

Queue collapse is enabled by default and controlled by the boolean `--queue-depth` option. Cyclopts also exposes the negative form:

```bash
# default: one representative row per exact queue
uv run ew-observe step 1000 --queue-depth

# expanded historical threat rows
uv run ew-observe step 1000 --no-queue-depth
```

`--exhaustive-threats` is retained as an explicit alias for the expanded human ledger.

Sorting is independent of collapse:

```bash
uv run ew-observe step 1000 --sort value
uv run ew-observe step 1000 --sort prime-lex
uv run ew-observe step 1000 --sort depth
uv run ew-observe step 1000 --sort retained
```

The current experimental human sort orders are:

- `value`: displayed numerical value ascending;
- `prime-lex`: reverse lexicographic order on the prime-exponent vector `(v_2,v_3,v_5,...)`, with `v_2` the least-significant digit. Equivalently, compare at the largest prime where the exponents differ; e.g. `12=2^2*3 -> ((3,1),(2,2))` and `18=2*3^2 -> ((3,2),(2,1))`, so `12 <prime-lex 18`;
- `depth`: queue depth descending, numerical value ascending to break ties;
- `retained`: lowest retained/continuity prime ascending, then numerical value.

The winner is never part of the sortable body because it is fixed in the context rows of every table.

The alternate current-head representation remains available explicitly:

```bash
uv run ew-observe step 1000 --queue-heads
```

The default text output groups body rows into smaller self-contained incidence tables. `--max-width` is a soft width target; `--candidates-per-table` adds an explicit row cap. Use `--max-width 0` for one unlimited table. In every case, **each table repeats B, A, and W** before its body rows.

For the early step `a_11 = 18`, the exhaustive threats are `6`, `12`, and `14`. The default queue view collapses them to two queues:

- support `{2,7}` has depth 1, last-used value `14`, and current head `28`; it loses;
- support `{2,3}` has depth 2, last-used value `12`, and current head `18`; `18` wins.

Thus the default body has `L 14`, while `W 18` appears in the fixed context at the top of the table.

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

The generic CLI takes an explicit stop:

```bash
uv run ew-observe track 18 --start 6 --stop 12
```

For prime-debut investigations it can resolve the stopping index automatically:

```bash
uv run ew-observe track 734 --start 745 --until-prime-debut 367
```

If `--start` is omitted, `track` shows the final 16 states by default; change that with `--context`. `--search-limit` bounds automatic prime-debut lookup.

## Output formats and machine-data guarantee

Microscope commands support explicit output formats:

```bash
uv run ew-observe step 11 --format text
uv run ew-observe step 11 --format markdown
uv run ew-observe step 11 --format json
uv run ew-observe step 11 --format tsv
uv run ew-observe step 11 --format csv

uv run ew-observe candidate 11 14 --format json
uv run ew-observe track 18 --start 6 --stop 12 --format json
```

- `text` and `markdown` are human presentation formats;
- `json` preserves complete structured mathematical data;
- `tsv` and `csv` emit flat analysis-friendly rows.

Human-only choices such as `--sort`, `--queue-depth/--no-queue-depth`, width splitting, and repeated context rows **do not reorder, discard, or weaken machine-readable output**. Default JSON/TSV/CSV use a stable canonical queue-frontier order regardless of those human flags.

The default queue-frontier JSON includes, for each queue, `display_value`, `queue_depth`, `last_used_value`, `current_head`, support, and the historical `source_threats` compressed into the row. It also retains the full exhaustive threat list. Thus human compression does not discard the current-head race or its provenance.

`--diagnostics` adds hidden current heads to the human queue-frontier view. `--exhaustive-threats --format json` continues to expose the original full decision certificate explicitly.

A decision trace fails loudly if the supplied prefix is inconsistent with the greedy rule, either because the observed winner is inadmissible/already used or because an unused admissible value lies below it.

## Planned layers

1. **Decision engine** — exact reconstruction of individual EW greedy choices.
2. **Queue race microscope** — one-row-per-exact-queue serviced frontiers, current heads, and interchangeable human sorting views.
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
