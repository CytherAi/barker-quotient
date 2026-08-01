# Publication freeze: realization theorem and census companion

Date: 2026-07-30

## Freeze decision

The publication unit is frozen as two papers with distinct jobs:

1. `realization_paper.tex` proves the realization and exact iterated-law
   theorem for gauge-reduced 2-power residue matrices.
2. `../manuscript.md` is the exhaustive finite census and structural companion.

The realization paper is ready for specialist mathematical review.  This
means that every stated theorem has a written proof, the load-bearing finite
algebra has an independently reproducible falsification harness, the cited
Kummer intersection has an external theorem-level check, and the rendered PDF
has passed visual inspection.  It does **not** mean that the new proof has
already been peer reviewed or accepted.

Further computation is not a prerequisite for either paper.  The remaining
questions require new analytic theory, a new scalable enumeration algorithm,
or a separate research paper; none can change the theorems at their stated
scope.

## Frozen claim set

### Realization paper: proved

- For primes `p == 1 (mod 4)` with `ord_p(2)` odd, the only realizability
  constraints on the gauge-reduced 2-power residue matrix are quadratic-
  reciprocity parity and the conditions involving `2`.
- For any fixed realized prefix and exact new depth `t >= 3`, the next-prime
  law is prefix-independent: fair parity bits, independent uniform raw
  coordinates inside the matching parity classes, followed by row-gauge
  quotienting.
- The exact-depth slice has density `2/4^t`; exact depth 2 is impossible in
  this prime family.
- Every admissible gauge class is realized by infinitely many ordered tuples
  of distinct primes.
- Successive prime bounds give the exact iterated product law, independent of
  adjoining order.
- Unconditional marked product law (corollary): depth marks are independent
  with `P(T = t) = 3/4^(t-2)`; conditional on depths, raw pair coordinates
  are independent and uniform on reciprocity-compatible fibers; the
  gauge-reduced law is the row-gauge pushforward.  The family is exchangeable
  and projectively consistent and extends to a countable random structure.
  Nested limits only.
- Rado skeleton (corollary): the mutual-quadratic-residue graph on this
  family is isomorphic to the countable Rado graph.
- Consequently the skeleton used by the census is the exact iterated
  arithmetic law, not merely a fitted or Monte-Carlo null model.

### Census companion: exact finite or computational results

- The cofactor-cycle theorem and its finite-universe cutoff.
- The 421-configuration exhaustive census at `k <= 6`, including the unique
  size-6 full-hub instance and the corrected six-stratum taxonomy.
- The corrected discrimination ladder and the eleven unit orbits.
- The exact skeleton constants `1373/5300` and `1123/4215`, including the
  failure of depth flatness.
- The exact maximal-pairwise contraction and its scoped negative result.
- The finite census residuals are descriptive counts against exact constants,
  not significance statements and not evidence of non-realizability.

### Computational guardrail, not proof

`../research/realization_checks.py` checks the affine commutator and derived
subgroup through depths 2--6, 20 exact Frobenius-slice counts, conjugacy as a
common row gauge, 56 non-vacuous implementation/Kummer coordinate identities,
and all prime slices below 20,000,000.  Its value-gated output is
`../research/_realization_checks.json`.  The harness is expressly a
falsification receipt; the number-field proof remains the source of the
theorem.

## Claims deliberately excluded

- No solution of the even Barker conjecture and no new Barker obstruction.
- No simultaneous-height convergence theorem, tuple-density asymptotic, or
  finite-range bias constant.
- No claim that finite census absences are forbidden patterns.  They remain
  unobserved skeleton-admissible motifs.
- No claim about nonabelian, class-group, or higher-cohomological invariants
  that do not factor through the gauge-reduced matrix.
- No method-class no-go theorem.  The realizability corollary removes one
  specific premise -- that an admissible matrix state cannot arise among the
  relevant primes -- while leaving Barker-specific conditions on realized
  states and all information above the quotient available.
- No eligibility-bias mechanism, `k = 7` extrapolation, or universal peak
  theorem.  Those results and questions belong to the separate exploratory
  thread `../research/eligibility_bias_program.md`.
- No inference from Monte-Carlo intervals to exhaustive censuses, and no
  significance language for fitted in-sample baselines.
- No universal-homogeneity (Fraïssé) theorem.  The one-point extension
  property in the full gauge-valued signature is proved; formalizing the
  category of gauge-valued structures and identifying the arithmetic
  structure as its generic object is a labeled remark left to later work.

## Full-audit coverage ledger

| Area | Coverage | Freeze disposition |
|---|---|---|
| Mathematical definitions and gauge | Row convention, parity, exact depth, hardness, and raw-to-orbit law checked end to end | Frozen |
| Kummer radical and Wang exceptional line | Independent valuation proof, exact order drop, affine presentation, negative regression for the wrong commutator convention | Frozen; specialist review requested |
| Field intersection | Self-contained commutator/inertia proof plus Perucca--Sgobba--Tronto theorem-level cross-check | Frozen; specialist review requested |
| Frobenius coordinates | Base field `B_0`, Kummer-coordinate identification, and source of row gauge checked explicitly | Frozen |
| Chebotarev law | Fiber non-emptiness, conjugacy stability, slice cardinality, density, and depth floor checked | Frozen |
| Iterated law | Raw product measure, equivariance, quotient-last construction, and adjoining-order independence written as a theorem | Frozen |
| Barker consequence | Restricted to global realizability; no Barker-specific no-go inference | Frozen |
| Census source, tests, caches, figures | Existing numerical, audit, clean-room, exact-DP, Rédei, Burde, and maximal-pairwise paths retained and gated | Frozen |
| Public prose and metadata | README, release notes, manuscript, references, test counts, and release boundaries synchronized | Frozen after final gate |
| Rendered artifacts | Both PDFs compiled from current sources, checked for warnings/missing glyphs, and visually inspected | Frozen after final render |
| Historical drafts | Retained for provenance and explicitly superseded; not part of the current claim set | Archived |
| Exploratory untracked outputs | Audited for claim leakage; none is a dependency of the frozen papers unless registered above | Excluded |

## Stop rule and remaining program

The audit stops here because the next useful steps cross the publication
boundary:

1. **Simultaneous-height convergence or finite-range bias:** requires uniform
   effective Chebotarev/Fourier analysis for prefix-dependent fields.  The
   Perucca--Sgobba--Tronto bounds are uniform in the radical and cyclotomic
   exponents for each fixed finitely generated group `G`; the missing axis is
   uniformity as `G = <2, p_1, ..., p_r>` gains generators and its prime
   radicands grow.  This is a separate analytic theorem, not an omitted
   consequence of the cited Kummer result.
2. **Larger or targeted censuses:** requires a new factorization or scalable
   enumeration method; more sampling cannot prove the needed frequency law.
3. **Eligibility-bias mechanisms:** a separate finite-combinatorics project
   whose results do not affect the realization theorem.
4. **New Barker obstructions:** must use Barker-specific information or data
   above the abelian gauge-reduced quotient.

These are high-value research directions, but low-value release blockers.
The correct next action is expert review of the proof, not another experiment.

## Reproduction commands

From the repository root:

```sh
python3 barker_k6_bundle/research/realization_checks.py
./verify_all.sh
tectonic --outdir output/pdf \
  barker_k6_bundle/realization/realization_paper.tex
```

The manifest gate pins the theorem harness and both publication artifacts by
hash and by named values.  A manifest-only commit must follow the content
commit, preserving the repository's established two-commit provenance rule.
