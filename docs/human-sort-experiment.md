# Human queue sorting experiment

Status: **empirical tooling study, not a theorem**.

## Question

For the human `step` microscope, which ordering of losing exact-support queue rows most clearly exposes the local EW mechanism?

The tested row representative is the serviced frontier: for a losing exact-support queue of depth `d`, display its maximal previously used member `q_{d-1}`. The winner is fixed as context and is not part of the sortable body.

The candidate human sorts are:

- `value`: displayed value ascending;
- `depth`: queue depth descending, displayed value ascending;
- `prime-lex`: lexicographic order of the prime-factor word (for example `2^2*7 -> (2,2,7)`);
- `retained`: lowest retained/continuity prime ascending, displayed value ascending.

## Method

I independently regenerated the first 5,000 EW terms from the defining greedy rule and checked the initial prefix against the published A336957 prefix. For each greedy step `n=3..5000`, I reconstructed the represented losing exact-support queues and their serviced frontiers, depths, and retained primes.

The purpose was not to infer asymptotic behavior from 5,000 terms. It was only to discriminate human presentation strategies.

## Results

There are 4,998 inspected greedy steps.

- 2,110 steps (42.2%) have more than one legal continuity prime `P(A) \\ P(B)`.
- 1,814 steps (36.3%) contain at least one losing queue retaining more than one continuity prime.

Thus retained-prime organization is not a rare corner case.

### How strongly do the sorts group continuity channels?

Restrict to the 2,099 inspected steps in which the losing rows contain at least two distinct labels under `lowest retained prime`.

A sort has *perfect retained grouping* when every lowest-retained-prime class occurs in one contiguous run. The observed rates were:

| human sort | perfect retained grouping |
| --- | ---: |
| `value` | 3 / 2,099 = 0.14% |
| `depth` | 0 / 2,099 = 0% |
| `prime-lex` | 1,275 / 2,099 = 60.7% |
| `retained` | 2,099 / 2,099 = 100% |

`prime-lex` is therefore substantially more structural than numerical order: it often recovers continuity-prime blocks without being told the current carrier set.

### Cost of duplicating multi-retained queues into every carrier block

A stronger retained-prime view would duplicate a queue once for every retained continuity prime rather than assigning it only to its smallest retained prime.

Across the inspected prefix this would add 64,717 rows to 1,072,082 losing queue rows, an aggregate increase of only **6.0%**. The worst single-step inflation in this prefix is about **37%**.

This makes a separate `retained-blocks` human view plausible. It should be treated as a view that changes row multiplicity, not merely as a sort order.

## Interpretation

- `value` remains a good neutral default because it makes the least-value geometry immediately visible and imposes the least extra structure.
- `depth` is a maturity diagnostic. It deliberately destroys arithmetic/carrier grouping and is useful when the question is queue exhaustion or prepayment.
- `prime-lex` is the most interesting alternative order. It groups arithmetic families and frequently recovers continuity-prime blocks implicitly.
- `retained` is the clearest direct view of the current EW continuity channels, but it uses the state we are trying to understand and therefore exposes less spontaneous arithmetic structure than `prime-lex`.
- A duplicated `retained-blocks` view is likely worth trying separately because it makes every carrier block semantically complete at modest empirical row cost.

No default should be changed solely from this finite presentation experiment. The useful test is which order compresses the specific prime-debut and defect dossiers we care about into the clearest repeated normal forms.
