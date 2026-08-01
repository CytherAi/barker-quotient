# Bundle: paper + library + verification scripts

This directory contains the paper sources, the Python library, and the
verification scripts. For project orientation, install instructions, and
the one-command verifier, see the [top-level README](../README.md).

**Paper (current):** *Minimal Covering Configurations of Hard Primes: A
Cofactor-Cycle Theorem and the Arithmetic Floor of a 2-Primary Census* —
Malek Alhazmi (CytherAi · 2026).

**Companion theorem:** `realization/realization_paper.tex` and its rendered
PDF prove the global realization and exact iterated-law theorem for the
gauge-reduced residue matrices. `realization/PUBLICATION_FREEZE.md` records
the claim boundary, audit coverage, and explicit stop rule.

`manuscript.md` is the paper (taxonomy, exhaustive enumeration,
discrimination-depth census, conditional geometry, and the exact skeleton
constants), and `manuscript.pdf` is its rendering — rebuilt together; see
"Rebuild the paper" in the [top-level README](../README.md). An earlier
v1.0 manuscript (a 13-configuration Type A/B classification under the
title *Scope and Limits of a 2-Primary Quotient Framework for Barker
Obstructions*) is superseded by the census and is not included in this
repository. For the main results — the 421-configuration census in six
primary strata, the cofactor-cycle theorem, the discrimination ladder,
and the exact skeleton constants R(3,3,3,3) = 1373/5300 and
R(3,3,3,4) = 1123/4215 — read `manuscript.md`.

## File map

| File | Description |
|------|-------------|
| `manuscript.md` | **The census paper** (current revision) |
| `manuscript.pdf` | Rendering of the current revision (rebuild command in the top-level README) |
| `pdf_math_filter.lua` | Pandoc filter mapping prose Unicode mathematics to LaTeX for the PDF build |
| `realization/` | Companion theorem source, rendered PDF, build instructions, and publication-freeze ledger |
| `docs/experiment_a_preregistration.md` | Pre-registered decision rules for the §6.2 experiments |
| `research/` | Post-v1.0 exploratory scripts, caches, and provenance manifests (see `research/RESEARCH.md`) |
| `../skeleton_exact/` | Exact skeleton DP (`exact_dp.py`) and the parity-conditioned census comparator |
| `verify_minimal_k6.py` | Standalone verification of Theorem 4.1 (exhaustive proper-subset minimality) |
| `remark_4_5_1_dn_disconnection.py` | D(N)-disconnection check (Remark 4.2) |
| `audit_verify.py` | Numerical audit (91 checks) |
| `audit_cleanroom.py` | Clean-room independent reimplementation (50 checks, 6320 χ-value comparisons) |
| `code/barker/` | Python library (13 modules) |

## Library modules

| Module | Role |
|---|---|
| `arithmetic.py` | Deterministic Miller–Rabin primality, factorization, multiplicative order, self-conjugacy |
| `two_primary.py` | 2-primary quotient class computation, character tables |
| `sweep.py` | Hard-prime discovery, cross-SC matrix |
| `coverage_search.py` | Exhaustive covering-set search |
| `minimal_cover_search.py` | Optimized minimal covering search (BadPairIndex) |
| `o1_realizability.py` | Cycle graph G_x construction |
| `o1_cycle_obstruction.py` | Edge labels, cycle detection, composition analysis |
| `o1_cycle_classification.py` | 5-cycle classification (Case 1 / Case 2 / Case 3) |
| `cofactor_analysis.py` | Hub Self-Defeat verification, Type A/B classification |
| `known_configs.py` | Canonical list of 12 prior known minimal covering configurations, plus the new k=6 witness in the paper |
| `o1_final_result.py` | Documents the minimal k=6 configuration |
| `o1_structural_analysis.py` | Retrospective structural analysis |
| `o1_program_retrospective.py` | Program-level retrospective |
