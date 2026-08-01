# Minimal Covering Configurations of Hard Primes: A Cofactor-Cycle Theorem and the Arithmetic Floor of a 2-Primary Census

[![Verify](https://github.com/CytherAi/barker-quotient/actions/workflows/verify.yml/badge.svg)](https://github.com/CytherAi/barker-quotient/actions/workflows/verify.yml)
[![License: MIT](https://img.shields.io/badge/code%20license-MIT-blue.svg)](./LICENSE)
[![License: CC BY 4.0](https://img.shields.io/badge/paper%20license-CC%20BY%204.0-lightgrey.svg)](./LICENSE-PAPER)

Source code, two companion papers, and verification suite by Malek Alhazmi
(CytherAi · [cytherai.com](https://cytherai.com), 2026).
The v1.0 release carried the earlier title *Scope and Limits of a 2-Primary
Quotient Framework for Barker Obstructions*; that reading is superseded by
the census paper here.

## What this is

The Barker non-existence conjecture has been open since 1965. The best
lower bound on a counterexample has been frozen since 2014. The existing
algebraic obstruction machinery explains a lot — but not everything.

**Neither paper closes the conjecture.** The census paper classifies the
finite 2-primary covering landscape and proves its cofactor-cycle theorem;
the realization paper characterizes the arithmetic image of the associated
gauge-reduced residue matrices and proves their exact per-prefix and iterated
Chebotarev law. Together they separate a solved support problem from an open
simultaneous-height frequency problem without turning either into a Barker
non-existence claim.

## Status

**`barker_k6_bundle/manuscript.md`** (and its rendered `manuscript.pdf`) is the census paper. Relative to the earlier v1.0 framing — which it supersedes — it re-frames the work around its empirical and structural content:

- the exhaustive enumeration of 421 minimal covering configurations at k ≤ 6, in six primary structural strata (plus the overlapping A_blocked refinement flag), including the interior class B_int;
- the cofactor-cycle theorem at the A1 spine, with S* = {17881, 1801, 14537, 13417, 18121, 18521} as the **unique full-hub (A1) minimal covering at size 6** in this universe — not the first known 6-set, since the census contains 61 of them at k = 6;
- a discrimination-depth ladder over the strata, closing at 2-FWL on 14,857 cross-stratum pairs;
- an **exact** evaluation of the reciprocity-symmetric skeleton null — R(3,3,3,3) = 1373/5300 and R(3,3,3,4) = 1123/4215 by integer dynamic programming over all 1,024 labeled parity graphs — which disproves the depth-flatness the earlier Monte-Carlo estimates suggested and resolves the paper's stated combinatorial open problem.

The companion realization theorem in [`barker_k6_bundle/realization/realization_paper.pdf`](./barker_k6_bundle/realization/realization_paper.pdf) resolves the support question and identifies the skeleton product measure as the exact per-prefix and iterated arithmetic law. The remaining Question 6.2.G is deliberately narrower: whether the finite census in which every prime is bounded by one simultaneous height converges to that iterated law, and, only if it does, at what rate.

See also:

- [`barker_k6_bundle/realization/PUBLIC_STATEMENT.md`](./barker_k6_bundle/realization/PUBLIC_STATEMENT.md) — frozen claim set and public-language boundary

## Background

Barker sequences are binary $\pm 1$ sequences of length $n$ whose
off-peak aperiodic autocorrelations all lie in $\{0, \pm 1\}$; they
are known for $n \in \{1, 2, 3, 4, 5, 7, 11, 13\}$ and conjectured not
to exist for any $n > 13$. The conjecture reduces, via the work of
Turyn, Schmidt, and Leung--Schmidt, to obstruction conditions among
the prime factors of $N$ in the relation $n = 4N^2$. This paper
concerns *hard primes* $p$ — those satisfying $p \equiv 1 \pmod 4$
with $\mathrm{ord}_p(2)$ odd — and the covering structures they
form under the Turyn elimination test.

## The two-paper result

The realization theorem proves that, after row-gauge reduction, quadratic-
reciprocity parity and the conditions involving `2` are the only global
realizability constraints on these 2-power residue matrices. At every fixed
prefix and exact new depth `t >= 3`, it gives fair edge parities, uniform raw
coordinates in their matching parity classes, the exact slice density
`2/4^t`, and infinitely many realizing primes. Successive bounds therefore
produce the exact skeleton product law used by the census.

This is a scoped extension of the residue-matrix program, not an equivalence
claim. Dummit, Dummit, and Kisilevsky characterized the analogous quadratic,
cubic, and quartic matrices; for larger exponents they identify both the
complexity of higher-power reciprocity and possible nonprincipality, and they
remark that dropping primary normalization produces larger classes that seem
less tractable. The realization paper shows that for this rational-prime
family at 2-power depth, quotienting by the row gauge restores an exact
characterization. It does not settle their general higher-power formulation.

The census paper supplies the distinct finite and structural result: an
exhaustive 421-configuration classification, the cofactor-cycle theorem at
the A1 spine, the corrected discrimination ladder, and exact conditioned
skeleton constants. The older Hub Self-Defeat statement remains valid as
Observation 2.4, one mechanism inside that classification rather than the
headline theorem.

The remaining bridge is simultaneous height. Existing explicit Kummer bounds
are uniform in the radical/cyclotomic exponents for a fixed finitely generated
radicand group; Question 6.2.G instead needs uniformity as the prefix group
`<2, p_1, ..., p_r>` and its prime radicands grow. That analytic axis is open
and is deliberately not claimed by either paper.

### What the census says

Across all 421 minimal covering configurations at k ∈ {3,4,5,6} over the
first 80 hard primes, the elimination strata are A1 (full hub), A2
(partial hub), A3 (pure cancellation), B0 (diffuse), B1 (codimension-1
blocked) and B_int (interior), with A_blocked as an overlapping
refinement flag. Type A configurations — those some χ-sum eliminates —
stay above 50% at every k, but the full-hub mechanism collapses (68 → 9
→ 7 → 1), and the interior class B_int appears only at k ≥ 5.

At the A1 spine the structure is a theorem: the cofactor of every
full-hub minimal covering is a single chordless directed cycle in
$G_x[V_x]$, with a structural cutoff $k \le K(N)+1$. The witness at the
extreme is the unique full-hub (A1) minimal covering of size 6:

    S* = {17881, 1801, 14537, 13417, 18121, 18521}

The two Type B survivors of the older reading — the quadruple
$(337, 937, 1433, 1721)$ and the five-set
$(4297, 4409, 5689, 6553, 7753)$ — remain undecided by the framework and
are now placed inside that census rather than presented as the whole
boundary. **The boundary is the result, not a limitation to apologize
for.**

## Repository layout

    barker_k6_bundle/                   # paper + library + verification
        manuscript.md                   # CURRENT paper (source of record)
        manuscript.pdf                  # rendered paper
        realization/                    # companion theorem source, PDF, freeze ledger
        pdf_math_filter.lua             # Unicode-math → LaTeX filter for the PDF build
        verify_minimal_k6.py            # headline k=6 verification (~10s)
        remark_4_5_1_dn_disconnection.py        # D(N)-disconnection check (<1s)
        audit_verify.py                 # 91-claim numerical audit (~10s)
        audit_cleanroom.py              # clean-room reimplementation, 50 checks (~3min)
        code/barker/                    # library (13 modules, pure stdlib)
        research/                       # research scripts + provenance manifests

    skeleton_exact/                     # exact skeleton DP + census comparator
    figures/                            # rendered figures (4.1, 5.1, 5.2)
    tests/                              # 187 pytest tests
    verify_all.sh                       # one-command driver

## Verify

Requires Python 3.9 or newer. The four §8.3 verification scripts are pure
standard library; the provenance gate, the exact skeleton engine and the
test suites need `numpy` (and `pytest`), which the driver installs into a
local `.venv` before running any step that imports them.

    git clone https://github.com/CytherAi/barker-quotient.git
    cd barker-quotient
    ./verify_all.sh

This runs the four verification scripts and the provenance gate, then the
test suites (187 core + 11 exact-skeleton), and prints a pass/fail summary.
Total runtime ~5 minutes. Exits 0 on success, non-zero on any failure —
including a failure to set up the test environment.

To run the steps individually:

    python3 barker_k6_bundle/verify_minimal_k6.py        # headline k=6 result (~10s)
    python3 barker_k6_bundle/remark_4_5_1_dn_disconnection.py    # D(N)-disconnection (<1s)
    python3 barker_k6_bundle/audit_verify.py             # 91-claim audit (~10s)
    python3 barker_k6_bundle/audit_cleanroom.py          # independent re-impl, 6,320 χ-value cross-check (~3min)
    python3 barker_k6_bundle/research/manifest.py verify # provenance + release-inventory gate
    python3 barker_k6_bundle/research/realization_checks.py # theorem guardrails + density slices
    python3 skeleton_exact/exact_dp.py                   # exact skeleton constants + support (~20min)
    pip install pytest numpy && python3 -m pytest tests/ skeleton_exact/

## Rebuild the paper

The current manuscript is Markdown; the PDF is produced with `pandoc` and
`tectonic` (both from Homebrew), plus a small Lua filter that converts the
prose Unicode mathematics into LaTeX:

    brew install pandoc tectonic
    python3 barker_k6_bundle/research/make_figures.py   # needs matplotlib
    cd barker_k6_bundle && pandoc manuscript.md -o manuscript.pdf \
        --pdf-engine=tectonic --lua-filter=pdf_math_filter.lua \
        -V geometry:margin=1in -V fontsize=11pt -V linkcolor=blue -V monofont="Menlo"

The build must report no missing characters; the figures are embedded from
`figures/`.

The realization companion is a standalone LaTeX paper:

    tectonic --outdir output/pdf \
        barker_k6_bundle/realization/realization_paper.tex

Its publication boundary and audit ledger are in
[`barker_k6_bundle/realization/PUBLICATION_FREEZE.md`](./barker_k6_bundle/realization/PUBLICATION_FREEZE.md).

## Cite

> Malek Alhazmi, *Minimal Covering Configurations of Hard Primes: A
> Cofactor-Cycle Theorem and the Arithmetic Floor of a 2-Primary Census*,
> 2026. arXiv: [pending].  (v1.0 title: *Scope and Limits of a 2-Primary
> Quotient Framework for Barker Obstructions*.)

Companion:

> Malek Alhazmi, *Realization of Gauge-Reduced 2-Power Residue Matrices:
> Exact Chebotarev Laws and an Application to Barker Sequences*, 2026.

A `CITATION.cff` file is included for tools that consume citation
metadata (GitHub's "Cite this repository" button, Zenodo, reference
managers).

## License

This repository is dual-licensed:

- **Code** — everything under `barker_k6_bundle/code/`, the verification
  scripts (`verify_minimal_k6.py`, `remark_4_5_1_dn_disconnection.py`,
  `audit_verify.py`, `audit_cleanroom.py`), `verify_all.sh`, and `tests/`
  — is licensed under the **MIT License**. See [`LICENSE`](./LICENSE).
- **Paper and prose** — the manuscript in both LaTeX and Markdown form,
  this README and all other prose files — is licensed under the
  **Creative Commons Attribution 4.0 International (CC BY 4.0)** license.
  See [`LICENSE-PAPER`](./LICENSE-PAPER).
