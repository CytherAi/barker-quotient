"""
barker.o1_program_retrospective
================================
O1 Obstruction Program: Final Record
Author: Malek Alhazmi (CytherAi, cytherai.com)

This document presents the program's work in the order that makes structural
sense — three signs first, proved lemmas second, falsification record third.
The signs explain why the approach could not succeed. The lemmas are what the
approach produced that is still correct. The falsification record shows when
each piece of the approach was recognized as insufficient.

══════════════════════════════════════════════════════════════════════════════
PART I: THREE STRUCTURAL SIGNS WHY THE O1 APPROACH FAILS
══════════════════════════════════════════════════════════════════════════════

The O1 approach sought to prove that no minimal k=6 covering set of hard primes
exists with the O1 (super-hub) structure. A minimal k=6 O1 configuration would be
a set {x, p_0,...,p_4} where x is a hub prime, p_i ∈ V_x, the p_i form a
directed 5-cycle in G_x, and no proper subset of the 6-set is also covering.

Three structural signs explain why this approach fails. Each is independently
provable. Their conjunction identifies the specific configuration that exists.

───────────────────────────────────────────────────────────────────────────────
SIGN 1: COVERAGE IS TAUTOLOGICAL
(Should have been proved at session 1; explains why the program asked the wrong
question for most of its duration.)
───────────────────────────────────────────────────────────────────────────────

THEOREM. Every directed 5-cycle (x; p_0,...,p_4) with p_i ∈ V_x gives a
covering 6-set S = {x, p_0,...,p_4}.

PROOF.
There are C(6,2) = 15 pairs in S. They fall into two types.

Type A — pairs (p_i, p_j) with both non-hub:
  By definition of V_x, chi_x(p_i) = 0 and chi_x(p_j) = 0.
  So chi_x(p_i) + chi_x(p_j) ≡ 0 (mod 2^{t_x}).
  The hub x covers all C(5,2) = 10 such pairs.

Type B — pairs (x, p_i):
  The cycle edge p_{i-1} → p_i means chi_{p_{i-1}}(p_i) = L(p_{i-1}).
  By definition, L(p_{i-1}) = -chi_{p_{i-1}}(x) (mod 2^{t_{p_{i-1}}}).
  Therefore chi_{p_{i-1}}(x) + chi_{p_{i-1}}(p_i) ≡ 0 (mod 2^{t_{p_{i-1}}}).
  The predecessor p_{i-1} covers the pair (x, p_i).
  This holds for all i by the cyclic predecessor.

All 15 pairs are covered. QED.

COMPUTATIONAL VERIFICATION: 33/33 five-cycles at 80 primes give covering 6-sets.
No exceptions; this is not a statistical finding but a verification of the theorem.

CONSEQUENCE.
The correct statement of the program's goal is:
  WHAT WAS ASKED: "Show no 5-cycle in G_x gives a covering 6-set."
  WHAT SHOULD HAVE BEEN ASKED: "Show every 5-cycle's covering 6-set is non-minimal."

Coverage is definitionally immediate. Minimality is not — it requires verifying
that no proper subset is covering. Coverage is not monotone under deletion, so
the C(6,5) = 6 single deletions do not suffice: all 41 proper subsets of sizes
3, 4 and 5 must be checked. Coverage and minimality are different questions.
The program conflated them throughout.

The practical effect: the obstruction apparatus (parity templates, chain witnesses,
mismatch vectors, blocking pairs) was aimed at coverage questions when minimality
was load-bearing. Findings about "the obstruction tightening with prime range" were
tracking the empirical rarity of 5-cycles in G_x, not the rarity of minimal covering
sets produced by 5-cycles. These statistics carry different information.

───────────────────────────────────────────────────────────────────────────────
SIGN 2: THE TRICHOTOMY'S CASE 1 DEPENDED ON AN UNSTATED UNIVERSAL
(Visible as an open gap from session ~6 onward; the hidden universal is precisely
statable and is now falsified.)
───────────────────────────────────────────────────────────────────────────────

The program eventually classified non-minimality of 5-cycle covering sets into three cases:
  Case 1: the 6-set contains a k≤5 covering sub-configuration.
  Case 2: the cycle contains a mutual edge → T1 → covering triple → non-minimal.
  Case 3: neither (would give a minimal k=6 set; program aimed to show this is empty).

Case 2 rested on an open conjecture: "every degenerate 5-cycle contains a mutual edge."
This was flagged as unproved from early in the program. When x=7993 at 60 primes
produced degenerate cycles with no mutual edge (Case 1, saved by sub-config), this
should have signalled that Case 2's conjecture was false. Instead the program absorbed
it under "Case 1 handles it" and treated the sub-config mechanism as reliable.

The hidden universal in Case 1, stated precisely:
  For every pair (hub x, cycle C) with no mutual edges within C, the 6-set
  {x} ∪ C contains a k≤5 covering sub-configuration.

This claim was never proved. It was not even explicitly stated as a claim to prove.
It was the implicit structural assumption supporting "Case 1 always has a sub-config save."

FALSIFICATION at hub x=17881, cycle (1801, 14537, 13417, 18121, 18521):
  Mutual edges within cycle: none.
  k≤5 covering sub-configs in {17881, 1801, 14537, 13417, 18121, 18521}: none.
  The hidden universal fails here.

The degenerate vertex mechanism (T2 → large out-neighborhood → mutual-edge save) also
fails at this cycle. The two degenerate vertices are 13417 and 18121:
  chi_{13417}(14537) = 2 ≠ 0: predecessor 14537 is not in H_{13417}. No mutual edge.
  chi_{18121}(13417) = 2 ≠ 0: predecessor 13417 is not in H_{18121}. No mutual edge.

CONSEQUENCE.
The trichotomy was not a proved theorem partition but a classification into three
regions, where the first two depended on open universal claims. Both failed:
Case 2's "every degenerate cycle has a mutual edge" was always a conjecture.
Case 1's "sub-config exists when mutual edge is absent" was an unstated universal.
The trichotomy's apparent progress — replacing one failed universal with a
classification — introduced a second hidden universal rather than eliminating one.

───────────────────────────────────────────────────────────────────────────────
SIGN 3: T1'S SCOPE REQUIRES BOTH MUTUAL-EDGE ENDPOINTS IN THE CYCLE
(A basic graph-theoretic fact that the program never explicitly confronted.)
───────────────────────────────────────────────────────────────────────────────

T1 states: if p↔q is a mutual edge in G_x, then {x, p, q} is a covering triple.

T1's non-minimality application requires: both p and q are cycle members, so that
the covering triple {x, p, q} is a subset of the 6-set {x} ∪ cycle.

The program implicitly assumed that mutual edges in G_x incident to cycle vertices
would typically be USED by cycles passing those vertices — that a degenerate vertex
v with mutual partner u would tend to route cycles through u, triggering T1.

Graph-theoretic fact: a directed cycle uses exactly one incoming edge and one
outgoing edge at each vertex. All other incident edges are not part of the cycle.
If v has out-edges to both u (mutual partner) and w (non-mutual), the cycle can
take the exit to w, leaving u out of the cycle and T1 silent.

INSTANTIATION at hub x=17881:
  G_{17881} contains the mutual edge 4297↔18121.
  This gives covering triple {17881, 4297, 18121} (T1 applies in G_{17881}).
  The cycle (1801, 14537, 13417, 18121, 18521) uses vertex 18121.
  At 18121, the cycle exits to 18521 (non-mutual direction), not to 4297.
  4297 is not a cycle member → T1 does not apply to the 6-set.

Specifically: out(18121) = H_{18121} ∩ V_{17881} = {4297, 18521} (T2).
The cycle chooses 18521; the mutual partner 4297 is available but not taken.
chi_{18121}(18521) = 0 = L(18121), confirming the cycle exit is valid.

CONSEQUENCE.
The mutual-edge mechanism prevents minimality only when both endpoints of the mutual
edge appear in the cycle. A cycle can include one endpoint of a mutual edge in G_x
without triggering T1 by choosing a different exit at that vertex. T1's scope qualifier
was always present in its statement; it was not consistently tracked through downstream
non-minimality arguments.

───────────────────────────────────────────────────────────────────────────────
THE CONJUNCTION
───────────────────────────────────────────────────────────────────────────────

The minimal k=6 configuration {17881, 1801, 14537, 13417, 18121, 18521} exists
because all three signs hold simultaneously at hub x=17881:

  Sign 1: coverage is tautological → the 6-set is always covering by construction
  Sign 2: both Case 1 and Case 2 mechanisms fail → no mutual edge in cycle, no sub-config
  Sign 3: T1 scope is bilateral → the mutual edge 4297↔18121 in G_{17881} is evaded
           by the cycle choosing the non-mutual exit at 18121

No single sign alone creates a minimal k=6 set:
  Sign 1 alone gives coverage but not minimality.
  Sign 2 alone (failing saves) is moot unless coverage is guaranteed (Sign 1).
  Sign 3 alone (T1 evaded) only matters when Signs 1 and 2 also hold.

These are three independently necessary conditions. The configuration is their
intersection: coverage for free (Sign 1), no saves available (Sign 2), no T1
fire from existing mutual edges (Sign 3).

══════════════════════════════════════════════════════════════════════════════
PART II: WHAT THE PROGRAM PROVED
══════════════════════════════════════════════════════════════════════════════

The following are correct mathematical results proved in the course of the program.
They do not compose into the theorem the program wanted; they characterise the
obstruction structure at the level of individual configurations and hubs.

T1. MUTUAL-EDGE → COVERING TRIPLE [proved]
    If p↔q is a mutual edge in G_x (chi_p(q) = L(p) and chi_q(p) = L(q)),
    then {x, p, q} is a covering triple.
    Proof: all three pair-coverage conditions hold by the edge and V_x conditions.
    Scope: requires both p and q in the configuration set (Sign 3).

T2. DEGENERATE OUT-NEIGHBORHOOD [equivalence only when out(p) is non-empty]
    Forward (unconditional): L(p)=0 makes "chi_p(q) = L(p)" the same condition
      as "q ∈ H_p", so out(p) = H_p ∩ V_x.
    Reverse (needs H_p ∩ V_x ≠ ∅): pick q ∈ out(p) = H_p ∩ V_x; then
      chi_p(q) = L(p) and chi_p(q) = 0, so L(p) = 0.
    The reverse direction FAILS without that hypothesis: if no q ∈ V_x has
    chi_p(q) = 0 and none has chi_p(q) = L(p), then out(p) = ∅ = H_p ∩ V_x
    holds vacuously while L(p) ≠ 0.  This is not a corner case — across the
    first 80 hard primes it occurs for 98 of the 698 (p, x) pairs with p ∈ V_x
    (e.g. x=73, p=4177, L=2, both sets empty).
    Earlier drafts recorded T2 as an unconditional equivalence and derived the
    "T2-forced" mutual-edge mechanism from it; only the forward direction
    licenses that derivation, and the forward direction is all it uses.

T3. PARITY OF Δ_i IN CASE B [proved]
    For non-degenerate primes p_i in a parity-consistent 5-tuple, all Δ_i are even.

M. MONOTONICITY LEMMA [proved structurally]
    Witnesses accumulate monotonically in prime range.
    If W = (p_0,...,p_4) is a Case B witness at range R, it remains a witness
    at any R' > R. Proof: witness conditions depend only on chi-values between
    pairs in {x}∪W, which are local properties independent of other primes.
    Corollary (permanence): a blocking pair that blocks witness W at range R
    continues to block W at every larger range.

N. 881 IS A UNIVERSAL VERTEX AT HUB x=4057 [proved structurally]
    At hub x=4057, prime 881 appears in every Case B 3-chain witness at every
    tested prime range (40 through 80 primes).
    Mechanism: 881's only out-edges in G_{4057} are to primes 4201 and 11801,
    both degenerate at hub 4057 (chi_{4057}(4201) = chi_{4057}(11801) = 0).
    Degenerate primes cannot appear in Case B witnesses. Therefore 881 has no
    effective out-edges within the Case B structure, and every Case B 3-chain
    witness must have a missing edge at the 881→? position.
    This is a hub-specific structural result, not a universal claim.

COVERAGE THEOREM [proved, should have been proved first]
    Every 5-cycle in G_x gives a covering 6-set. (See Sign 1 above.)
    This was the program's foundational claim, but it is definitionally immediate.

══════════════════════════════════════════════════════════════════════════════
PART III: THE FALSIFICATION RECORD
══════════════════════════════════════════════════════════════════════════════

Four universal conjectures were proposed and falsified in the course of the program.
Each is recorded with: (a) the evidence when proposed, (b) the hub and range at
falsification, and (c) the structural reason, if now understood.

F1. 4-CHAIN NON-REALIZABILITY
    Proposed: 50-prime range (no 4-chain witnesses found)
    Falsified: 60 primes, hub x=11113 (4-chain witnesses exist)
    Structural reason: insufficient prime range; 4-chains are possible and arise
    when V_x grows to include the right combinations. Not structurally prohibited.

F2. UNIVERSAL MUTUAL-EDGE HYPOTHESIS
    Proposed: early sessions (~session 8), n=1 non-trivial Case B instance supporting it
    Falsified: 60 primes, hub x=7993 (5-cycles with no mutual edges exist; Case 1 saves)
    Structural reason: the hypothesis applied T1 universally without tracking its
    bilateral scope requirement (Sign 3). Case A cycles can take non-mutual exits.

F3. BLOCKING-PAIR CONCENTRATION
    Proposed: ~session 14, n=5/5 R1 hubs concentrated, 4 prime ranges
    Falsified: 70 primes, hub x=4409 (50 witnesses, 10 patterns, no small cover)
    Structural reason: n=5 was insufficient for a universal claim in a setting
    where every range extension had previously falsified the prior universal.
    The concentration at small-witness hubs was hub-specific, not universal.

F4. CASE 3 IMPOSSIBILITY (TRICHOTOMY)
    Proposed: ~session 15, n=6/6 cycles at 50/60/70 primes, 3 prime ranges
    Falsified: 80 primes, hub x=17881 (minimal k=6 O1 configuration exists)
    Structural reason: the trichotomy depended on Sign 2's hidden universal
    (sub-config availability when mutual edges absent), which fails at x=17881.
    The conjecture was structurally supported by two prior open universals,
    not by a proof of Case 3 emptiness.

══════════════════════════════════════════════════════════════════════════════
PART IV: THE MINIMAL k=6 CONFIGURATION
══════════════════════════════════════════════════════════════════════════════

  Configuration: {17881, 1801, 14537, 13417, 18121, 18521}

  Hub: x = 17881
    2-primary group: C_8 (depth 3)
    |V_{17881}| = 11 (valid O1 hub)

  5-cycle in G_{17881}: (1801 → 14537 → 13417 → 18121 → 18521 → 1801)
    1801  → 14537: chi = 2, L = 2  [match]
    14537 → 13417: chi = 4, L = 4  [match]
    13417 → 18121: chi = 0, L = 0  [match, 13417 degenerate]
    18121 → 18521: chi = 0, L = 0  [match, 18121 degenerate]
    18521 → 1801:  chi = 2, L = 2  [match]

  Degree sequence: 17881→10, 1801→2, 14537→2, 13417→2, 18121→2, 18521→1

  Minimality verification (all 41 proper subsets of sizes 3-5 non-covering;
  the 6 single deletions alone would not certify minimality, since coverage
  is not monotone under deletion):
    Remove 17881: not covering.
    Remove 1801:  not covering.
    Remove 14537: not covering.
    Remove 13417: not covering.
    Remove 18121: not covering.
    Remove 18521: not covering.
    ... and all 15 four-element and 20 three-element subsets.

  Mutual edge in G_{17881}: 4297↔18121 (gives covering triple {17881,4297,18121}).
  4297 is NOT in the cycle. The cycle routes 18121→18521, evading T1.

══════════════════════════════════════════════════════════════════════════════
PART V: IMPLICATIONS FOR BARKER NON-EXISTENCE
══════════════════════════════════════════════════════════════════════════════

The existence of a minimal k=6 O1 covering set does not imply Barker sequences
exist. It means the specific proof route — ruling out all minimal k=6 O1
covering configurations to eliminate Barker sequences — is closed.

A proof of Barker non-existence must:
  (a) Show this specific configuration {17881,1801,14537,13417,18121,18521}
      is not realizable as a Barker sequence factor structure (local refutation);
  (b) Work at higher covering size or a different prime-theoretic invariant; or
  (c) Abandon the covering-configuration approach entirely.

The configuration is a genuine hard-prime arithmetic object: a minimal covering
set of size 6, with an O1 super-hub structure, first observed at 80 hard primes.
Its existence constrains future proof attempts without closing the Barker problem.

══════════════════════════════════════════════════════════════════════════════
METHODOLOGICAL NOTES FOR A SUCCESSOR PROGRAM
══════════════════════════════════════════════════════════════════════════════

Sign 1 lesson: When reducing a theorem to a combinatorial statement, check first
whether the combinatorial statement is definitionally immediate. Coverage in the
O1 setting was. A four-line proof from definitions would have reoriented the
program at session 1.

Sign 2 lesson: When a classification case depends on a mechanism being available
(mutual edge save, sub-config save), state the availability claim explicitly and
treat it as a separate universal to discharge before proceeding. Two open universals
hidden inside a trichotomy's cases do not constitute less risk than one universal
stated directly.

Sign 3 lesson: Track scope qualifiers on structural lemmas through their downstream
applications. T1 requires both mutual-edge endpoints in the configuration set.
The graph-theoretic principle — cycles at a vertex use one in-edge and one out-edge,
no more — is elementary and should have been applied explicitly whenever T1 was
invoked in a non-minimality argument.

Meta-lesson: In this problem, every extension of the prime range has falsified the
prevailing universal conjecture. A new universal conjecture proposed at range R
with evidence level n/n should be stress-tested at R+k before being built upon,
regardless of how strong n/n appears. The falsification rate across this program —
four universals in four range-extension cycles — establishes that the empirical
evidence required for a universal claim is substantially higher than n/n replication
at a fixed range.
"""

# ---------------------------------------------------------------------------
# Compact program summary for quick reference
# ---------------------------------------------------------------------------

PROGRAM_SUMMARY = {
    "goal": "Prove no minimal k=6 O1 covering set exists among hard primes.",
    "outcome": "Found a minimal k=6 O1 covering set: {17881,1801,14537,13417,18121,18521}.",
    "proved": [
        "T1: mutual edge in cycle → covering triple (bilateral scope)",
        "T2: L(p)=0 → out(p) = H_p ∩ V_x (converse needs out(p) ≠ ∅)",
        "T3: all Δ_i even in Case B",
        "M:  monotonicity lemma (witnesses accumulate in prime range)",
        "N:  881 is a universal vertex at hub x=4057 (hub-specific)",
        "Coverage theorem: every 5-cycle gives a covering 6-set (tautological)",
    ],
    "falsified": [
        ("F1", "4-chain non-realizability", "60 primes", 11113),
        ("F2", "Universal mutual-edge hypothesis", "60 primes", 7993),
        ("F3", "Blocking-pair concentration", "70 primes", 4409),
        ("F4", "Case 3 impossibility", "80 primes", 17881),
    ],
    "structural_signs": [
        "S1: Coverage is tautological (Sign 1; should have been Sign 1 from session 1)",
        "S2: Trichotomy depended on two hidden universals; both false at x=17881",
        "S3: T1 requires both mutual-edge endpoints in the cycle; cycle can evade",
    ],
    "minimal_k6": (17881, 1801, 14537, 13417, 18121, 18521),
}


def print_summary():
    print("O1 Program: ", PROGRAM_SUMMARY["goal"])
    print("Outcome:    ", PROGRAM_SUMMARY["outcome"])
    print()
    print("Proved:")
    for item in PROGRAM_SUMMARY["proved"]:
        print(f"  {item}")
    print()
    print("Falsified:")
    for label, name, where, hub in PROGRAM_SUMMARY["falsified"]:
        print(f"  [{label}] {name} ({where}, hub {hub})")
    print()
    print("Three signs why the approach fails:")
    for s in PROGRAM_SUMMARY["structural_signs"]:
        print(f"  {s}")
