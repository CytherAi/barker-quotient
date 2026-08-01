"""
barker.o1_structural_analysis
================================
Why the O1 obstruction approach fails: three structural signs.

CANONICAL SOURCE: this module is the original three-signs analysis. A
broader retrospective that subsumes this material — adding the proved
lemmas (T1, T2, T3, Monotonicity, the 881-vertex theorem), the
falsification record (F1–F4), the program summary dict, and a
methodological-notes section — is `barker.o1_program_retrospective`.
For new references, prefer that module; this one is preserved for
historical continuity and is imported by `tests/test_smoke.py`.

This document is the retrospective analysis of the O1 program's failure.
It separates the EMPIRICAL record (when each conjecture was falsified) from
the STRUCTURAL reasons (why the approach was always going to fail).

Both belong in the record. The empirical record shows what happened.
The structural analysis shows why it was inevitable.

══════════════════════════════════════════════════════════════════════════
THE QUESTION THE PROGRAM SHOULD HAVE ASKED
══════════════════════════════════════════════════════════════════════════

The O1 approach modeled a hypothetical minimal k=6 covering set as:
  {x} ∪ {p_0,...,p_4}
where x is a hub prime and p_0,...,p_4 ∈ V_x form a directed 5-cycle in G_x.

The program then sought to prove: no such configuration is minimal.

The question it SHOULD have asked first: is there a simple reason such
configurations are always covering (before asking whether they're minimal)?

The answer — provable in four lines from definitions — is YES. Coverage is
tautological. This should have been proved in session 1.

══════════════════════════════════════════════════════════════════════════
SIGN 1: COVERAGE IS TAUTOLOGICAL (visible from session 1)
══════════════════════════════════════════════════════════════════════════

THEOREM (session 1, should have been framed this way):
Every directed 5-cycle (x; p_0,...,p_4) with p_i ∈ V_x gives a covering 6-set.

PROOF:
  TYPE A pairs — (p_i, p_j) with both non-hub:
    chi_x(p_i) = 0 and chi_x(p_j) = 0 (definition of V_x).
    So chi_x(p_i) + chi_x(p_j) = 0 mod 2^{t_x}.
    The hub x covers all C(5,2) = 10 such pairs.

  TYPE B pairs — (x, p_i):
    The cycle edge p_{i-1}→p_i means chi_{p_{i-1}}(p_i) = L(p_{i-1}).
    By definition: L(p_{i-1}) = -chi_{p_{i-1}}(x) mod 2^{t_{p_{i-1}}}.
    Therefore: chi_{p_{i-1}}(x) + chi_{p_{i-1}}(p_i) = 0 mod 2^{t_{p_{i-1}}}.
    The predecessor p_{i-1} covers the pair (x, p_i).

  All 15 pairs are covered. QED.

VERIFIED: 33/33 five-cycles at 80 primes are covering. 0 exceptions.

CONSEQUENCE:
The correct framing of the program's goal is:
  "Show that every 5-cycle in G_x gives a COVERING set that is NON-MINIMAL."
NOT:
  "Show that no 5-cycle in G_x gives a covering set."

The program ran on the second framing for most of its duration. The machinery
(mutual edges, sub-configs, chain witnesses, concentration) was actually targeting
minimality all along — but without being stated that way, the distinction between
proving non-existence of 5-cycles and proving non-minimality of their covering sets
was never cleanly drawn. Had Sign 1 been proved at session 1, the program would
have framed every subsequent session as asking: "why is this covering set non-minimal?"
rather than "does this covering set arise?" — a harder but correctly-scoped question.

══════════════════════════════════════════════════════════════════════════
SIGN 2: THE CASE A GAP WAS ALWAYS OPEN (visible from session ~6 onward)
══════════════════════════════════════════════════════════════════════════

The program identified early that Case A cycles (those with degenerate vertices)
had two structural reasons for non-minimality:
  - Mutual edge mechanism: degenerate p_j → out(p_j)=H_{p_j}∩V_x → predecessor
    in H_{p_j} → mutual edge → T1 → covering triple → non-minimal
  - Sub-config mechanism: the 6-set contains a known smaller covering set

The Case A theorem — "every degenerate 5-cycle contains a mutual edge" — was
flagged as an OPEN CONJECTURE in session 4 and never proved. When x=7993 at
60 primes showed degenerate cycles that were Case 1 (no mutual edge, saved by
sub-config), the correct reading was: "the Case A conjecture is now SUSPECT.
The sub-config mechanism is doing the saving, not a proved structural reason."

Instead the program absorbed x=7993 into the trichotomy (Case 1) and treated
the sub-config mechanism as equivalent to a proved theorem. But sub-config
availability is itself an open universal claim: "the k≤5 covering classification
is always rich enough that any degenerate cycle's 6-set contains a sub-config."

At 80 primes, hub x=17881 cycle (1801,14537,13417,18121,18521):
  - Two degenerate vertices: 13417 and 18121.
  - Neither predecessor lands in its degenerate successor's H_p:
      chi_{13417}(14537) = 2 ≠ 0 → no mutual edge at 13417
      chi_{18121}(13417) = 2 ≠ 0 → no mutual edge at 18121
  - No k≤5 covering sub-config exists in the 6-set.

Both mechanisms fail simultaneously. This is exactly the Case 3 instance.

CONSEQUENCE:
The trichotomy (Case 1/2/3) was not a proved theorem but a partition into
three cases, two of which depended on open universal claims. Case 2 required
the mutual-edge conjecture (falsified). Case 1 required sub-config availability
(also falsified at x=17881). The trichotomy itself was therefore two universals
in a trench coat, framed as a classification.

══════════════════════════════════════════════════════════════════════════
SIGN 3: T1 REQUIRES BOTH MUTUAL-EDGE ENDPOINTS IN THE CYCLE (subtle)
══════════════════════════════════════════════════════════════════════════

T1 states: if p↔q is a mutual edge in G_x, then {x, p, q} is a covering triple.

The implicit application was: if the cycle passes through a vertex v that has a
mutual partner u in G_x, then v↔u fires T1 and gives a covering triple.

But T1's scope is: BOTH p and q must be cycle members for the triple {x,p,q}
to be a subset of the 6-set {x}∪cycle. If only one endpoint is in the cycle,
the mutual edge exists in G_x but doesn't constrain the 6-set.

At x=17881:
  G_{17881} has mutual edge 4297↔18121, giving covering triple {17881,4297,18121}.
  The cycle (1801,14537,13417,18121,18521) uses 18121 but NOT 4297.
  18121 exits to 18521 (non-mutual direction), not to 4297.

  A directed graph vertex v uses exactly one in-edge and one out-edge in any cycle.
  If v's mutual partner u provides a different out-edge at v, the cycle can exit
  through a non-mutual direction. T1 cannot fire on a mutual edge where one endpoint
  is excluded from the cycle.

CONSEQUENCE:
The mutual-edge mechanism was only ever a mechanism for non-minimality when the
mutual edge appeared as a directed edge WITHIN the cycle. The existence of mutual
edges ELSEWHERE in G_x — incident to cycle vertices but not used by the cycle —
provides no protection against minimality. The program implicitly assumed that
degenerate vertices' large out-neighborhoods would always route cycles through
their mutual partners. Graph-theoretically, cycles can route around.

══════════════════════════════════════════════════════════════════════════
THE CONJUNCTION
══════════════════════════════════════════════════════════════════════════

The minimal k=6 configuration (17881,1801,14537,13417,18121,18521) exists because
all three signs hold simultaneously at hub x=17881:

  Sign 1: coverage is tautological → the configuration is always covering
  Sign 2: Case A conjecture fails → no mutual edge in cycle, no sub-config
  Sign 3: T1 scope is bilateral → mutual edge in G_x is routed around

Any one sign alone is insufficient:
  - Sign 1 alone: coverage exists but might still be non-minimal
  - Sign 2 alone: missing mutual edge and sub-config would be a problem,
    but only if coverage were also guaranteed (it is, by Sign 1)
  - Sign 3 alone: T1's gap only matters when there IS a mutual edge in G_x
    incident to the cycle, and only when Signs 1+2 also hold

The configuration is the intersection of all three conditions.

══════════════════════════════════════════════════════════════════════════
WHAT THE EMPIRICAL PROGRAM BUILT
══════════════════════════════════════════════════════════════════════════

The program's computational results — T1, T2, T3, Monotonicity, the 881-vertex
theorem, the classification of blocking-pair structure across 5 R1 hubs, the
cycle classification module — are all correct. They characterise the obstruction
structure at small prime ranges and identify when T1 and T2 apply.

What they don't do is close the theorem, because the theorem is false.

The value of the empirical work is:
  1. Proof of the tautological covering theorem (now that it's been identified)
  2. The minimal k=6 configuration itself, a new hard-prime arithmetic object
  3. The structural analysis of why it exists (these three signs)
  4. The falsification record — four conjectures, with the evidence threshold
     at which each was proposed and at which it was falsified

══════════════════════════════════════════════════════════════════════════
FOR THE NEXT APPROACH TO BARKER NON-EXISTENCE
══════════════════════════════════════════════════════════════════════════

The k=6 minimal covering set exists. This means the Barker non-existence theorem
cannot be proved by ruling out all minimal k=6 covering configurations. Any
proof of Barker non-existence must either:

  (a) Show that the specific minimal k=6 configuration found here is not
      realizable as a Barker sequence factor structure (hub-specific argument)

  (b) Work at a different level of the Barker factorization — e.g., k=7 or
      higher, or a different prime criterion than 2-primary structure

  (c) Use a fundamentally different approach that doesn't reduce to
      covering-set existence at any fixed k

The existence of the minimal k=6 set is not an obstacle to Barker non-existence;
it is a constraint on what any proof of Barker non-existence must account for.
"""
