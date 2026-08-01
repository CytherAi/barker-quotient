# Realization theorem companion paper

This directory contains the circulation draft
`realization_paper.tex`. Its theorem characterizes the row-gauge-reduced
2-power residue matrices realized by primes `p == 1 (mod 4)` for which
`ord_p(2)` is odd, and proves the exact per-prefix and iterated Chebotarev
laws.

The frozen external claim set and reusable public-language boundary are in
[`PUBLIC_STATEMENT.md`](./PUBLIC_STATEMENT.md).  The publication audit and stop
rule are in [`PUBLICATION_FREEZE.md`](./PUBLICATION_FREEZE.md).

The proof is mathematical. The deterministic falsification harness lives at
`../research/realization_checks.py`; its JSON receipt is
`../research/_realization_checks.json`. The harness checks the finite affine
algebra, Frobenius-slice counts, gauge action, implementation-coordinate
identification, and the numerical density slices. It is not a substitute for
the proof.

Build from the repository root:

```sh
mkdir -p output/pdf
tectonic --outdir output/pdf \
  barker_k6_bundle/realization/realization_paper.tex
```

Publication boundary: simultaneous-height convergence, finite-range bias,
larger censuses, and the separate eligibility-bias program are open research
and are not prerequisites for this paper.
