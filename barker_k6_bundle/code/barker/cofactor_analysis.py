"""
barker.cofactor_analysis
=========================
Scope and limits of the 2-primary quotient framework for Barker obstructions.

The central result of this module is a BOUNDARY THEOREM for a method:

  The 2-primary quotient Q_x = (Z/x²Z)* / H_x  ≅  C_{2^t} supports
  an internally complete obstruction theory — with its own covering
  geometry, its own tautological coverage theorem, and its own
  minimality hierarchy — yet this quotient-level theory does not
  control the full Barker problem because the missing obstruction
  lives above the quotient, in the cyclotomic field machinery that
  the finite quotient cannot see.

This is not a limitation to be buried in a discussion section.
It is the paper's deepest theorem: the exact localization of where
the 2-primary projection stops being sufficient.

Three layers of structure
--------------------------

1. INTERNAL MATHEMATICS OF THE QUOTIENT (proved):
   - Coverage is tautological for hub configurations.
   - Hub self-defeat theorem: hub covering sets are self-defeating.
   - Minimality is the genuinely hard question within Q_x.

2. FAILURE ANALYSIS OF THE PROJECTED PROOF ROUTE (computed):
   - Pair-sufficiency and cofactor self-conjugacy decouple.
   - 11/13 known covering sets are Turyn-eliminable despite pair failure.
   - 2/13 survive the Turyn test at every target (non-hub, Type B).

3. BOUNDARY THEOREM FOR THE METHOD (the forest):
   - The quotient sees real structure — it is not vacuous.
   - But it sees only the 2-primary shadow (8 out of ~320M elements
     for x=17881), missing field descent, exponent bounds, and
     character-sum estimates that live in the full group ring.
   - The two Type B survivors mark the exact boundary: they are
     the configurations where quotient-level information ceases
     to determine the Barker outcome.  Whether they survive the
     full cyclotomic machinery is beyond the quotient's scope.

Hub self-defeat theorem
------------------------
THEOREM.  Let S = {x} ∪ C be an O1 (hub-type) covering set where
C ⊂ V_x (i.e., chi_x(p) = 0 for all p ∈ C).  Then the full cofactor
at target x is NOT self-conjugate mod x².

PROOF.
  chi_x(product(C)) = sum_{p ∈ C} chi_x(p)     (chi is a homomorphism)
                     = sum_{p ∈ C} 0             (definition of V_x)
                     = 0
  chi_x = 0  ⟹  product(C) ∈ H_x  ⟹  ord_{x²}(product(C)) is odd
           ⟹  product(C) is NOT self-conjugate mod x².  □

CONSEQUENCE.  The hub structure that creates the covering set at the
pair level simultaneously provides Turyn elimination at the cofactor
level.  Every O1 hub-type covering set is self-defeating.

Classification of known covering sets
--------------------------------------
Of the 13 known minimal covering sets (12 from exhaustive search + k=6):

  TYPE A — self-defeating (11/13):
    Cofactor NOT SC at ≥1 target.  Turyn eliminates.
    Includes: all 7 triples, 3 of 4 five-sets, the k=6 hub config.

  TYPE B — Turyn survivors (2/13):
    Cofactor IS SC at every target.  Turyn cannot eliminate.
    (337, 937, 1433, 1721)           k=4 quad
    (4297, 4409, 5689, 6553, 7753)   k=5 set

  Type B configurations have no hub structure: no single prime puts
  all others in its odd-order subgroup.  The covering structure is
  distributed, keeping the cofactor sum nonzero at every target.

  NOTE: "Turyn survivor" does NOT mean "Barker survivor."  It means
  the 2-primary quotient framework cannot determine the outcome.
  Field descent, exponent bounds, and character-sum estimates —
  all invisible to Q_x — may still eliminate these candidates.
  This is the boundary of the method, not a claim about Barker.

Open questions (within the 2-primary framework)
-------------------------------------------------
  - Do Type B (non-hub) covering configurations exist at k ≥ 6?
  - Is there a structural characterization of Type B configurations
    beyond "no hub and all cofactor sums nonzero"?
  - What is the density of Type B configurations as the prime
    universe grows?

Open questions (beyond the 2-primary framework)
-------------------------------------------------
  - Do the two Type B configurations survive Schmidt's anti-field-descent?
  - Do they survive Leung-Schmidt exponent bounds?
  - Is there a unified test that subsumes both 2-primary and
    field-descent information?
"""

from __future__ import annotations
from dataclasses import dataclass

from .arithmetic import is_self_conjugate
from .two_primary import (
    build_two_primary_table, TwoPrimaryCharacterTable,
)
from .known_configs import ALL_KNOWN_MINIMAL_COVERING


def _check(cond, msg):
    """assert that survives python -O: invariant violations must fail loudly."""
    if not cond:
        raise ValueError(msg)


# ---------------------------------------------------------------------------
# Full-cofactor Turyn test
# ---------------------------------------------------------------------------

@dataclass
class CofactorResult:
    """Result of the full-cofactor Turyn test at a single target."""
    target:        int
    cofactor_chi:  int       # chi_target(product of others) mod 2^t
    modulus:       int       # 2^t
    is_sc:         bool      # True iff cofactor IS self-conjugate mod target²
    sc_witness_j:  int | None


@dataclass
class CofactorAnalysis:
    """Full-cofactor analysis for a configuration."""
    config:           tuple[int, ...]
    k:                int
    targets:          list[CofactorResult]
    n_sc:             int          # targets where cofactor IS SC
    n_not_sc:         int          # targets where cofactor NOT SC
    turyn_eliminates: bool         # True iff cofactor NOT SC at ≥1 target
    is_genuine:       bool         # True iff cofactor IS SC at ALL targets
    obstruction_type: str          # "A-self-defeating" or "B-genuine"
    hub_target:       int | None   # target where chi-sum = 0, if any


def cofactor_test(
    config: tuple[int, ...],
    table: TwoPrimaryCharacterTable | None = None,
) -> CofactorAnalysis:
    """
    Run the full-cofactor Turyn test on a configuration.

    For each target x ∈ config, compute:
      chi_x(product(config \\ {x})) = sum_{p ≠ x} chi_x(p) mod 2^{t_x}

    If this sum is 0, the cofactor has odd order mod x² (NOT SC).
    If nonzero, the cofactor IS SC mod x².

    The Turyn test eliminates if ANY target gives NOT SC.
    """
    primes = list(config)
    if table is None:
        table = build_two_primary_table(primes)

    targets: list[CofactorResult] = []
    hub = None

    for x in primes:
        t = table.depth[x]
        mod = 2 ** t
        others = [p for p in primes if p != x]

        chi_vals = [table.chi[(p, x)] for p in others]
        chi_sum = sum(chi_vals) % mod

        # Independent verification via is_self_conjugate
        r = 1
        for p in others:
            r *= p
        x2 = x * x
        sc, j = is_self_conjugate(r % x2, x2)

        # Consistency check: chi_sum == 0 iff NOT SC
        _check((chi_sum == 0) == (not sc),
               f"Inconsistency at target {x}: chi_sum={chi_sum}, sc={sc}")

        if chi_sum == 0:
            hub = x

        targets.append(CofactorResult(
            target=x, cofactor_chi=chi_sum, modulus=mod,
            is_sc=sc, sc_witness_j=j,
        ))

    n_sc = sum(1 for t in targets if t.is_sc)
    n_not_sc = sum(1 for t in targets if not t.is_sc)
    eliminates = n_not_sc > 0
    genuine = n_sc == len(primes)

    return CofactorAnalysis(
        config=tuple(primes),
        k=len(primes),
        targets=targets,
        n_sc=n_sc,
        n_not_sc=n_not_sc,
        turyn_eliminates=eliminates,
        is_genuine=genuine,
        obstruction_type="B-genuine" if genuine else "A-self-defeating",
        hub_target=hub,
    )


# ---------------------------------------------------------------------------
# Hub self-defeat verification
# ---------------------------------------------------------------------------

def verify_hub_self_defeat(
    hub: int,
    cycle: tuple[int, ...],
    table: TwoPrimaryCharacterTable | None = None,
) -> bool:
    """
    Verify the hub self-defeat theorem for a specific configuration.

    Returns True iff chi_hub(product(cycle)) = 0, confirming the
    cofactor is NOT SC at the hub target.
    """
    config = (hub,) + cycle
    if table is None:
        table = build_two_primary_table(list(config))

    t = table.depth[hub]
    mod = 2 ** t
    chi_sum = sum(table.chi[(p, hub)] for p in cycle) % mod
    return chi_sum == 0


# ---------------------------------------------------------------------------
# Classify all known covering sets
# ---------------------------------------------------------------------------

@dataclass
class CoveringSetClassification:
    """Classification of all known covering sets by Turyn obstruction type."""
    type_a:       list[CofactorAnalysis]   # self-defeating
    type_b:       list[CofactorAnalysis]   # genuine obstruction
    n_total:      int
    n_type_a:     int
    n_type_b:     int
    false_alarm_rate: float


def classify_all_known() -> CoveringSetClassification:
    """Classify all known minimal covering sets as Type A or Type B."""
    type_a: list[CofactorAnalysis] = []
    type_b: list[CofactorAnalysis] = []

    for mc in ALL_KNOWN_MINIMAL_COVERING:
        config = tuple(sorted(mc))
        result = cofactor_test(config)
        if result.is_genuine:
            type_b.append(result)
        else:
            type_a.append(result)

    # Add the k=6 configuration (not in ALL_KNOWN_MINIMAL_COVERING)
    k6 = (1801, 13417, 14537, 17881, 18121, 18521)
    k6_result = cofactor_test(k6)
    if k6_result.is_genuine:
        type_b.append(k6_result)
    else:
        type_a.append(k6_result)

    n = len(type_a) + len(type_b)
    return CoveringSetClassification(
        type_a=type_a,
        type_b=type_b,
        n_total=n,
        n_type_a=len(type_a),
        n_type_b=len(type_b),
        false_alarm_rate=len(type_a) / n if n > 0 else 0.0,
    )


# ---------------------------------------------------------------------------
# Formatted output
# ---------------------------------------------------------------------------

def format_cofactor_analysis(result: CofactorAnalysis) -> str:
    lines, div = [], "─" * 68
    lines.append(div)
    lines.append(f"  COFACTOR ANALYSIS: {result.config}")
    lines.append(f"  Type: {result.obstruction_type}")
    lines.append(div)
    for t in result.targets:
        sc_str = "IS SC" if t.is_sc else "NOT SC"
        lines.append(
            f"  target {t.target}: chi-sum = {t.cofactor_chi} "
            f"(mod {t.modulus}) → {sc_str}"
        )
    lines.append(div)
    if result.turyn_eliminates:
        lines.append(
            f"  Turyn test ELIMINATES at target {result.hub_target}"
        )
    else:
        lines.append("  Turyn test CANNOT eliminate — genuine obstruction")
    lines.append(div)
    return "\n".join(lines)


def format_classification(cls: CoveringSetClassification) -> str:
    lines, div = [], "═" * 72
    lines.append(div)
    lines.append("  PAIR-SUFFICIENCY vs COFACTOR SELF-CONJUGACY")
    lines.append("  Classification of all known minimal covering sets")
    lines.append(div)
    lines.append(
        f"  Total: {cls.n_total}   "
        f"Type A (self-defeating): {cls.n_type_a}   "
        f"Type B (genuine): {cls.n_type_b}"
    )
    lines.append(
        f"  False alarm rate: {cls.false_alarm_rate:.0%}"
    )
    lines.append(div)

    lines.append("  TYPE A — Self-defeating (Turyn eliminates):")
    for r in sorted(cls.type_a, key=lambda x: x.k):
        hub_str = f" [hub={r.hub_target}]" if r.hub_target else ""
        lines.append(f"    k={r.k}: {r.config}{hub_str}")
    lines.append("")

    lines.append("  TYPE B — Genuine Turyn obstructions:")
    for r in sorted(cls.type_b, key=lambda x: x.k):
        lines.append(f"    k={r.k}: {r.config}")
        for t in r.targets:
            lines.append(
                f"      chi_{t.target}(cofactor) = "
                f"{t.cofactor_chi} (mod {t.modulus})"
            )
    lines.append(div)

    lines.append("  REVISED OPEN QUESTION:")
    lines.append("  Do non-hub (Type B) covering configurations exist at k >= 6?")
    lines.append("  Current: k=4 (yes), k=5 (yes), k>=6 (unknown).")
    lines.append(div)
    return "\n".join(lines)
