# Human queue sorting experiment

Status: **empirical tooling study, not a theorem**.

## Correction to `prime-lex`

The original version of this note used the wrong convention for `prime-lex`: it
sorted the repeated-prime word from the smallest prime upward, which made the
least prime act like the most-significant digit.

That is not the intended order.

The corrected `prime-lex` order treats the prime-exponent vector

\[
(v_2(n),v_3(n),v_5(n),\ldots)
\]

as prime digits with `v_2` least significant. Thus two values are compared at
the **largest prime where their exponent vectors differ**. Equivalently, the
finite sort key is the nonzero `(prime, exponent)` pairs ordered from largest
prime downward.

For example:

- `12 = 2^2*3 -> ((3,1),(2,2))`;
- `18 = 2*3^2 -> ((3,2),(2,1))`;
- `20 = 2^2*5 -> ((5,1),(2,2))`.

Hence `12 <prime-lex 18 <prime-lex 20`.

The old `prime-lex` grouping statistics below were therefore measuring a
different order and are **invalid for the corrected definition**. They should
not be used as evidence about the new order. The experiment should be rerun
before drawing any structural conclusion about corrected `prime-lex`.

## Question

For the human `step` microscope, which ordering of losing exact-support queue
rows most clearly exposes the local EW mechanism?

The tested row representative is the serviced frontier: for a losing
exact-support queue of depth `d`, display its maximal previously used member
`q_{d-1}`. The winner is fixed as context and is not part of the sortable body.

The candidate human sorts are:

- `value`: displayed value ascending;
- `depth`: queue depth descending, displayed value ascending;
- `prime-lex`: corrected reverse lexicographic order on prime exponents;
- `retained`: lowest retained/continuity prime ascending, displayed value ascending.

## Method

I independently regenerated the first 5,000 EW terms from the defining greedy
rule and checked the initial prefix against the published A336957 prefix. For
each greedy step `n=3..5000`, I reconstructed the represented losing
exact-support queues and their serviced frontiers, depths, and retained primes.

The purpose was not to infer asymptotic behavior from 5,000 terms. It was only
to discriminate human presentation strategies.

## Results unaffected by the correction

There are 4,998 inspected greedy steps.

- 2,110 steps (42.2%) have more than one legal continuity prime `P(A) \\ P(B)`.
- 1,814 steps (36.3%) contain at least one losing queue retaining more than one continuity prime.

Thus retained-prime organization is not a rare corner case.

For `value`, `depth`, and `retained`, the earlier retained-class grouping results
remain valid. Restricting to the 2,099 inspected steps in which losing rows
contain at least two distinct lowest-retained-prime labels:

| human sort | perfect retained grouping |
| --- | ---: |
| `value` | 3 / 2,099 = 0.14% |
| `depth` | 0 / 2,099 = 0% |
| `retained` | 2,099 / 2,099 = 100% |

The former `prime-lex = 60.7%` row is intentionally omitted because it used the
incorrect least-prime-as-MSB convention.

### Cost of duplicating multi-retained queues into every carrier block

A stronger retained-prime view would duplicate a queue once for every retained
continuity prime rather than assigning it only to its smallest retained prime.

Across the inspected prefix this would add 64,717 rows to 1,072,082 losing
queue rows, an aggregate increase of only **6.0%**. The worst single-step
inflation in this prefix is about **37%**.

This makes a separate `retained-blocks` human view plausible. It should be
treated as a view that changes row multiplicity, not merely as a sort order.

## Interpretation

- `value` remains a good neutral default because it makes the least-value geometry immediately visible and imposes the least extra structure.
- `depth` is a maturity diagnostic and is useful when the question is queue exhaustion or prepayment.
- corrected `prime-lex` is now a mathematically natural prime-digit order, but its empirical structural value is **unmeasured after the correction**.
- `retained` is the clearest direct view of the current EW continuity channels, but it uses the state we are trying to understand.
- A duplicated `retained-blocks` view is likely worth trying separately because it makes every carrier block semantically complete at modest empirical row cost.

No default should be changed solely from this finite presentation experiment.
The useful test is which order compresses the specific prime-debut and defect
dossiers we care about into the clearest repeated normal forms.
