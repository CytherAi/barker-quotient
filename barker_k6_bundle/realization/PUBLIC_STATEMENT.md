# Final claim set and public statement

This document is the public-language boundary for the two-paper release.  The
proofs remain in the papers; this file records the strongest claims they
support and the claims they deliberately exclude.

## Paper A: realization theorem

### One-sentence claim

For primes $p \equiv 1 \pmod 4$ with $\operatorname{ord}_p(2)$ odd,
quadratic reciprocity and the conditions at $2$ are the only realizability
constraints on the row-gauge-reduced 2-power residue matrix, and the arithmetic
supplies not merely the support but an exact prefix-independent transition law.

### Proved

- **Exact extension law.** For any fixed realized prefix and prescribed depth
  $t \ge 3$: fair parity bits on the new edges, uniform column coordinates in
  their parity classes, uniform row coordinates in the matching classes, and
  the new row observed modulo one common odd unit.  The law is independent of
  the numerical prefix.
- **Realization.** Every admissible gauge class, for every depth vector with
  entries at least $3$, is realized by infinitely many ordered tuples of
  distinct primes.
- **Exact-depth density.** $\delta_t=2/4^t$, with exact depth $2$ impossible
  in this family.  This is derived from the Galois structure, not assumed.
  Summing gives $1/24$, recovering the $p\equiv1\pmod8$ part of Hasse's
  $7/24$ by an independent route through the degree calculation.
- **Exact iterated law.** Successive prime bounds give an exact matrix product
  law independent of adjoining order.
- **Scoped consequence.** No skeleton-admissible pattern is globally absent,
  so a proposed Barker argument cannot discard such a pattern by asserting
  that its gauge-reduced matrix is arithmetically unrealizable.

### Not claimed

No solution of the even Barker conjecture and no new Barker obstruction.  No
simultaneous-height convergence, tuple-density asymptotic, or finite-range bias
constant.  Nothing about nonabelian, class-group, or higher-cohomological data
that does not factor through the gauge-reduced matrix.  Finite census absences
remain unobserved skeleton-admissible motifs, never forbidden.  The realization
corollary blocks one inference step; it is not a no-go theorem for a method
class.

### Positioning

Dummit--Dummit--Kisilevsky characterize the analogous matrices at exponents
$2,3,4$.  Their quadratic construction is equivalent to using 2-primary
generators, while their cubic and quartic constructions use primary generators
of prime ideals explicitly.  They explain that larger $m$ is more complicated
for two reasons: $m$-th power reciprocity becomes more complicated, and prime
ideals of $\mathbb Q(\zeta_m)$ need not be principal.  Their closing remark
then considers dropping the primary normalization and says that the resulting
larger classes seem less tractable to characterization.

This paper gives a scoped reply to that remark.  Rational prime radicands avoid
the generator and principality problem.  The row-gauge quotient absorbs the
remaining generator normalization and permits the characterization to be
proved without first classifying the full higher-reciprocity law numerically.
For this prime family, that restores an exact characterization at arbitrary
2-power depth.  The gauge is the mathematical move, not a bookkeeping detail.
No claim is made that the two higher-power formulations are equivalent; that
bridge remains open.

Their realization arguments adjoin primes one at a time by Chebotarev.  The
extension law here is the exact quantitative form of that qualitative step.
Schinzel's single-row prescription is the classical precedent: over
$\mathbb Q$, it includes 2-power exponents for multiplicatively independent
prime radicands.  The new content is the coupled prime-indexed matrix, exact
depth fiber, common row gauge, and transition law.  Perucca--Sgobba--Tronto
supply an independent theorem-level check on the Kummer intersection.  Evan
Dummit's finite-field $d$-th-power residue matrices are the other live
extension direction.

## Paper B: census companion

### One-sentence claim

An exhaustive structural classification of minimal covering configurations of
these primes, a cofactor-cycle theorem forcing every full-hub cofactor to a
single chordless directed cycle, and the exact evaluation of the reciprocity
skeleton against which the census's modulus-8 residues are measured.

### Proved or exhaustively computed

- Every A1 minimal covering has cofactor a single chordless directed cycle,
  with structural cutoff $k\le K(N)+1$; $K(80)=19$, so $k\le20$.  The A1
  census reconstructs exactly as $68,9,7,1$ at $k=3,4,5,6$.
- $S^*=\{17881,1801,14537,13417,18121,18521\}$ is the unique full-hub
  minimal covering at size $6$ in the first 80 hard primes, one of 61 minimal
  coverings at that size, verified against all 41 relevant proper subsets.
- 421 minimal coverings at $k\le6$, in six primary structural strata with
  the blocked refinement recorded separately.
- Exact skeleton constants
  $R(3,3,3,3)=1373/5300$ and
  $R(3,3,3,4)=1123/4215$; depth flatness is exactly false by $+0.7373$
  percentage points.
- The discrimination ladder has
  V-graph $\succ$ delta-profile and
  2-FWL $\succ$ 1-WL $\succ I_6$, with the two chains mutually
  incomparable.
- The exact maximal-pairwise contraction and its scoped negative result.

### Not claimed

No new Barker obstruction and no extension of the Turyn cofactor test's reach.
The finite census residuals are descriptive counts against exact constants,
with no significance statement attached.  Support and per-prefix/iterated
frequencies are settled by Paper A; the simultaneous-height regime remains
open.

## Public post

Most realization theorems stop at existence: the object occurs.
This one computes the exact law by which it occurs.

Two companion papers, public and frozen for review.

**Paper 1 -- the realization theorem.**

Take the primes $p\equiv1\pmod4$ for which 2 has odd multiplicative order.
Each carries a 2-power residue coordinate defined only up to an odd unit, so a
matrix of mutual residue data between such primes has an intrinsic row gauge
and no canonical numerical entries.

Which of these matrices actually occur?

After gauge reduction: every matrix consistent with quadratic reciprocity and
the conditions at $2$.  There are no other constraints.  And the arithmetic
supplies more than existence:

- For any tuple of such primes already in hand, the next prime arrives by an
  exact transition law that does not depend on the tuple: fair parity bits on
  the new edges, uniform higher digits inside their parity classes, and one
  common odd unit on the new row.
- The depth-$t$ slice has exact density $2/4^t$.
- Summing the slices gives $1/24$, agreeing, by an independent route through
  the degree calculation, with the $p\equiv1\pmod8$ part of Hasse's 1966
  density theorem.
- Iterating gives an exact product law, independent of the order in which the
  primes are adjoined.

Dummit, Dummit, and Kisilevsky characterized the analogous matrices at
exponents $2,3,4$.  Their quadratic construction is equivalent to using
2-primary generators; their cubic and quartic constructions explicitly use
primary generators of prime ideals.  They note that larger exponents face two
obstacles: higher reciprocity grows more complicated, and the relevant ideals
need not remain principal.  Their closing remark judges the larger matrix
classes obtained without primary normalization less tractable.

This paper gives a scoped response to that judgment.  Rational prime radicands
avoid the generator and principality problem.  The row-gauge quotient absorbs
the remaining normalization and permits the characterization without first
classifying the full higher-reciprocity law.  Quotienting by that gauge restores
an exact characterization for the full 2-power tower within this prime family.
The gauge is the mathematical move, not a normalization detail.  Whether this
formulation and theirs are equivalent at higher exponents remains open -- the
natural next question.

**Paper 2 -- the census.**

The structural theorem: the cofactor of every full-hub minimal covering of
hard primes is forced to a single chordless directed cycle, with an exact size
cutoff -- $k\le20$ in the first 80 hard primes.  One line survives from the
first draft: the same subgroup membership that builds a full-hub covering
already forces the Turyn cofactor test to eliminate it.  Coverage and
elimination are the same algebraic fact.

The census is now exhaustive, not curated:

- 421 minimal covering configurations at $k\le6$ over the first 80 hard
  primes: 225, 77, 58, 61 by size.
- Six structural strata: elimination fires in 322; survival holds in 99.
- The cycle theorem reconstructs the full-hub census exactly as 68, 9, 7, 1
  and predicts exactly one full-hub configuration at $k=7$.
- $S^*=\{17881,1801,14537,13417,18121,18521\}$ is not the first size-6
  minimal covering -- the census holds 61 of them -- but is the unique one with
  full-hub structure.  The theorem-guided exhaustive reconstruction establishes
  that uniqueness.
- The reciprocity skeleton is evaluated exactly:
  $R(3,3,3,3)=1373/5300$ and $R(3,3,3,4)=1123/4215$.  Depth flatness is
  exactly false.  The finite census moves against the constants with depth,
  reported as counts against exact rationals with no significance statements.

For Dummit--Dummit--Kisilevsky's configuration types, finite-height counts can
sit far from their limiting frequencies; they cite the
Dummit--Granville--Kisilevsky small-prime bias theorem as the explanation.
The census therefore does not estimate its constants: it computes them exactly
and reports the finite counts against them.  The realization theorem certifies
those constants as the arithmetic law in the iterated limit, not as a fitted
model.  It does not establish simultaneous-height convergence.

**What is not claimed.**

No Barker length is eliminated, and the even Barker conjecture is untouched.
The theorem blocks exactly one inference step: a proposed argument cannot
discard a configuration by asserting that its residue matrix is arithmetically
unrealizable, because every admissible matrix occurs.  Whether finite-height
censuses converge to the exact law is open.  Patterns absent from the census
are unobserved, never "forbidden."

**The reproducibility stack is public:**

- One command: `./verify_all.sh`; normal, optimized, and fresh-clone runs are
  all green at this freeze.
- 198 tests (187 core + 11 exact-skeleton), on Python 3.9 or newer.
- 91 numerical audit checks; 50 clean-room checks; 6,320 character values
  cross-checked by an independent reimplementation, with zero divergence.
- 12 experiments pinned by two-tier provenance manifests: 110 inventoried
  files and 165 of 165 referenced paths Git-tracked and hash-verified.
- The four arithmetic verification scripts use only the Python standard
  library.  The provenance gate, exact engine, and test suites additionally
  require NumPy, and the tests require pytest; the driver installs both into a
  local virtual environment when needed.

If a computation is wrong, the independent implementation should disagree.
If an artifact changes, provenance should fail.  If a claim exceeds its
evidence, the frozen claim boundary blocks the release.

The theorems are the results.  The harness exists so that a stranger can try
to break them.

