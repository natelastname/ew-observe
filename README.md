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

be the primes of the predecessor that can legally carry the next term. The first implementation target is to reconstruct the exact race among the carrier streams indexed by `R` and produce a certificate explaining why `W` is the least unused admissible integer.

A decision certificate should expose:

- the supports of `B`, `A`, and `W`;
- the legal carrier primes `P(A) \\ P(B)`;
- the least current candidate on each carrier stream;
- the winning stream and winning value;
- rejected values and all applicable reasons: already used, no predecessor overlap, two-back mask, or failure to introduce a new prime;
- exact counterfactual heads for restricted races when requested.

The representation should remain compact by default, with rejected stream prefixes expanded only on demand.

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
