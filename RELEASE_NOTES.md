<!--
Maintenance note: when an arXiv ID is assigned, update three places:
  1. README.md       — line ~68 ("How to cite" block)
  2. CITATION.cff    — line ~46 (commented arXiv identifier block)
  3. This file       — line ~37 (Citation section)
Quick locator across all three:
    grep -rnE '\[pending\]|filled after|XXXX\.XXXXX' .
-->

# v1.2 — Realization theorem companion and publication freeze

**Release candidate:** 2026-07-30
**Author:** Malek Alhazmi (CytherAi · [cytherai.com](https://cytherai.com))

This candidate adds the companion paper *Realization of Gauge-Reduced
2-Power Residue Matrices: Exact Chebotarev Laws and an Application to Barker
Sequences*. It proves the exact per-prefix extension law, global realization,
the density `2/4^t`, and the exact iterated matrix law. The census manuscript
now cites that theorem and narrows Question 6.2.G to simultaneous-height
convergence; finite absences remain unobserved admissible motifs.

The proof is accompanied by a registered falsification harness, not replaced
by it. The harness pins the affine commutator and derived subgroup at depths
2--6, 20 exact slice counts, 56 non-vacuous coordinate checks, and the prime
slices below 20,000,000. The publication-freeze ledger records the complete
claim boundary and the stop rule: additional census sampling, `k = 7`
eligibility work, and finite-range bias analysis are separate research
projects rather than release blockers.

End-to-end release-candidate state:

- **5 verification entry points**, all PASS, including the provenance gate
- **pytest suite:** **198 / 198 PASS** (187 core + 11 exact-skeleton)
- **Provenance:** 110-file release inventory, 165 / 165 manifest-referenced
  paths git-tracked, every registered artifact matching its manifest
- **Rendered papers:** 57-page census companion and 10-page realization paper,
  both rebuilt from current sources and visually inspected

---

# v1.1 — Cofactor-cycle theorem, exact reciprocity skeleton, and a corrected pooling

**Released:** 2026-07-28
**Author:** Malek Alhazmi (CytherAi · [cytherai.com](https://cytherai.com))

Source and verification suite for the revised paper *Minimal Covering
Configurations of Hard Primes: A Cofactor-Cycle Theorem and the Arithmetic
Floor of a 2-Primary Census*. The v1.0 title and its "first known k = 6"
framing are superseded: `S*` is the unique **A1** covering at its size, and the
census contains 61 minimal coverings at k = 6.

## Results proved or computed in this release

- **Cofactor-cycle theorem** on A1 minimal coverings, with the structural
  cutoff k ≤ K(N) + 1, and `S*` reconstructed as the unique full-hub
  configuration at its size
- **Exhaustive classification** of 421 minimal coverings at k ≤ 6 into six
  primary strata (plus the A_blocked refinement flag), with the k = 5 zero-δ
  extension carried to N = 100..160
- **Exact evaluation of the reciprocity skeleton**: R(3,3,3,3) = 1373/5300 and
  R(3,3,3,4) = 1123/4215 by integer dynamic programming over the 1,024 labeled
  parity graphs. Depth-flatness of the benchmark is exactly **false**
  (+0.7373 pp), and the census moves the opposite way
- **Exact maximal-pairwise evaluation**:
  R = 28345526604025309972212577 / 106403745905832904560284283 = 0.2663959,
  a movement of −0.0033 pp from the independent-digit constant — 0.2% of the
  distance to the observed 844/3379 = 0.2498

## Correction within this release cycle

The maximal-pairwise value was first published as **0.2663752**, obtained by
contracting one depth-3 hub and multiplying by four. That pooling assumes the
four hubs are exchangeable, and they are not: vertex labels are the primes in
increasing order, the measured joint is indexed in that order, and it is not
symmetric — the even sector holds 1,100 pairs at (χ_p(q), χ_q(p)) = (2, 6)
against 953 at (6, 2) — so relabelling a hub onto the contracted vertex
transposes the joint on every edge whose endpoint order the relabelling
reverses.

The engine's validation could not detect this. It re-runs the same code with
uniform digits, which makes both joints all-ones and hence symmetric — exactly
the input class in which the shortcut is exact — and the provenance gate then
reproduced and value-checked that output. The corrected computation contracts
all four hubs and pools them; it moves the value by 0.0021 pp, so the published
reading is unchanged, but it was unestablished until the estimand itself was
computed.

Hardening applied in response, so the failure mode fails by name rather than by
luck: the value gate now pins the exact per-hub numerator/denominator pairs and
the symmetrized-joint sensitivity as well as the pooled rational; the engine
carries a positive control that uniform joints must produce four identical
hubs; the Monte-Carlo check asserts per-hub counts, not only the aggregate; and
three regression tests exercise the pooling on deliberately asymmetric joints.
Separately, `262099 = 349 × 751` was found not to be prime and was replaced by
`262111`, making the CRT set the seven largest primes below 2^18 as documented.

## End-to-end verification of v1.1

Reproduced from a fresh clone:

- **5 verification entry points**, all PASS, including the provenance gate
- **pytest suite:** **175 / 175 PASS** (164 core + 11 exact-skeleton)
- **Provenance:** 98-file release inventory, 150 / 150 manifest-referenced
  paths git-tracked, every registered artifact matching its manifest

---

# v1.0 — Hub Self-Defeat Theorem and the minimal k=6 covering set

**Released:** 2026-05-16
**Author:** Malek Alhazmi (CytherAi · [cytherai.com](https://cytherai.com))

First public release of the source and verification suite for the paper
*Scope and Limits of a 2-Primary Quotient Framework for Barker
Obstructions*.

For an overview of the repository, see the [top-level README](./README.md).
For the bundle's contents, see [`barker_k6_bundle/README.md`](./barker_k6_bundle/README.md).

## Results proved or computed in this release

- **Hub Self-Defeat Theorem** (Theorem 5.2)
- **General Coverage Theorem** (Theorem 2.3)
- **Minimal k=6 covering set** `S = {17881, 1801, 14537, 13417, 18121, 18521}` (Theorem 4.1)
- **Type A/B classification** of all 13 known minimal covering sets of hard primes — 11 Type A, 2 Type B (the k=4 quadruple `(337, 937, 1433, 1721)` and the k=5 set `(4297, 4409, 5689, 6553, 7753)`)
- **Cross-structure** (Remark 5.7): the k=6 hub 17881 lies in V_p for {937, 1721, 4297, 5081, 6361, 13417, 15289, 17737}; three of these are Type B elements

## End-to-end verification of v1.0

Reproduced from a fresh clone on system Python 3.9.6 (macOS), no setup:

- **4 verification scripts:** 65 + 48 + 5 + 2 = **120 distinct numerical checks, all PASS**
- **pytest suite:** **143 / 143 PASS** (~60 seconds)
- **Clean-room reimplementation:** **6,320 χ-value comparisons** against the library, zero divergences

## License

- Code: MIT (see [`LICENSE`](./LICENSE))
- Paper and prose: CC BY 4.0 (see [`LICENSE-PAPER`](./LICENSE-PAPER))

## Citation

> Malek Alhazmi, *Scope and Limits of a 2-Primary Quotient Framework for
> Barker Obstructions*, 2026. arXiv: [filled after submission].

To cite the code release specifically:

> Malek Alhazmi, *barker-quotient v1.0*, 2026.
> https://github.com/CytherAi/barker-quotient/releases/tag/v1.0
