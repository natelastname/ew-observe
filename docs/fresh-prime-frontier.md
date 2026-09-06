# Fresh-prime frontier reduction

This is a **safe theorem-level reduction**, not an extra clause in the Enots--Wolley definition.

Before selecting `a_n`, let

\[
Q_n=\min\{p\text{ prime}:p\nmid a_1a_2\cdots a_{n-1}\}
\]

be the least globally unintroduced prime, and let

\[
R_n=P(a_{n-1})\setminus P(a_{n-2})
\]

be the legal continuity primes. Assuming `R_n` is nonempty, put `r=min R_n`.

Then `r Q_n` is always a legitimate unused candidate:

- it overlaps `a_{n-1}` through `r`;
- it is coprime to `a_{n-2}` because `r` is legal and `Q_n` has never appeared anywhere;
- it introduces `Q_n` relative to the predecessor;
- it is unused because no earlier term contains `Q_n`.

Now suppose another primitive candidate `x` contains a prime `p>Q_n`. It must also retain some legal continuity prime `s in R_n`, so

\[
x\ge sp\ge rp>rQ_n.
\]

Therefore `x` cannot be the least unused admissible candidate. Hence the EW race may be restricted safely to

\[
\boxed{P(x)\subseteq\{p:p\le Q_n\}.}
\]

Equivalently, no selected EW term can contain a prime larger than the least globally unintroduced prime at that step.

## Tooling semantics

`ew-observe` keeps the two layers distinct:

- **primitive EW admissibility** means unused plus the original local overlap / two-back / new-prime conditions;
- **reduced admissibility** additionally applies the fresh-prime frontier above.

`CandidateAudit.globally_admissible` deliberately retains the primitive meaning. The reduction is exposed separately through:

- `least_unintroduced_prime`;
- `primes_beyond_fresh_frontier`;
- `reduction_reasons`;
- `in_reduced_candidate_universe`;
- `reduced_globally_admissible`.

Decision threat ledgers, queue races, lifecycle live-rank calculations, and the interactive viewer use the **reduced** universe. Direct candidate audits preserve both classifications so the reduction remains auditable.

For example, before `a_11=18`, the seen primes are `2,3,5,7,11`, so `Q_11=13`. The candidate `34=2*17` is unused and passes all primitive local EW conditions, but it is discarded from the reduced race because `17>13`.
