"""
barker.sweep
============
Instrumented sweep infrastructure for hard-prime frontier analysis.

Three capabilities
------------------
1. find_hard_primes(bound)
   All primes p < bound with p ≡ 1 (mod 4) and ord_p(2) odd.

2. cross_sc_matrix(primes)
   For each ordered pair (p, q), whether p is self-conjugate mod 2q².
   Equivalently: whether p could serve as the single-r Turyn witness
   against a candidate where q² appears in the cofactor.

3. pair_sufficiency_analysis(primes, max_k)
   For every k-element subset S (2 ≤ k ≤ max_k) of the hard-prime list,
   check whether there exists a k=2 PAIR (a,b) ⊂ S such that the product
   a*b is self-conjugate modulo x² for every remaining prime x ∈ S  {a,b}.

   By CRT this is equivalent to a*b SC mod (2 * product_{x ∈ S{a,b}} x²),
   which is exactly the Stage 3d composite-r check with s_r decomposed.

Pair-sufficiency conjecture
---------------------------
Empirical result (all tested subsets of the first 7 hard primes below 1000):

    For k = 2, 3, 4, 5, 6, 7:   EVERY k-element subset has a k=2 witness.

No counterexample was found. If this holds universally, then Stage 3d with
k=2 pairs is SUFFICIENT: the k≥3 composite-r branch of check_turyn_composite_r
is never needed for products of distinct hard primes, and the theorem collapses to:

    "For every product u = p_1 · ... · p_k of distinct hard primes,
     there exists a pair (p_i, p_j) such that p_i · p_j is self-conjugate
     modulo 2 · (product of remaining primes)²."

Proving this would require understanding why the product p_i·p_j of two hard
primes has even multiplicative order modulo each remaining prime's square.
See the notes in PairSufficiencyResult.notes for the structural observations.
"""

from __future__ import annotations
from dataclasses import dataclass
from itertools import combinations

from .arithmetic import (
    is_prime, multiplicative_order, is_self_conjugate,
)


def _check(cond, msg):
    """assert that survives python -O: invariant violations must fail loudly."""
    if not cond:
        raise ValueError(msg)


# ---------------------------------------------------------------------------
# Hard prime discovery
# ---------------------------------------------------------------------------

def find_hard_primes(bound: int) -> list[dict]:
    """
    Return all primes p < bound with p ≡ 1 (mod 4) and ord_p(2) odd.

    Each entry: {"prime": p, "ord": d, "f": (p-1)//d, "v2_phi": v2(p-1)}
    """
    results = []
    for p in range(5, bound):
        if not is_prime(p) or p % 4 != 1:
            continue
        d = multiplicative_order(2, p)
        if d % 2 != 0:
            phi = p - 1
            v2 = 0
            while phi % 2 == 0:
                v2 += 1
                phi //= 2
            results.append({
                "prime":  p,
                "ord":    d,
                "f":      (p - 1) // d,
                "v2_phi": v2,
            })
    return results


# ---------------------------------------------------------------------------
# Cross-SC matrix
# ---------------------------------------------------------------------------

@dataclass
class CrossSCMatrix:
    """
    For each ordered pair (p, q) of hard primes, records whether
    p is self-conjugate modulo 2q² (and provides the minimal witness j).

    Attributes
    ----------
    primes  : list of primes (in input order)
    sc      : sc[i][j] = (True/False, j_witness or None)
    degree  : for each prime p, the number of q≠p with p SC mod 2q²
    blind   : pairs (p, q) where p is NOT SC mod 2q²
    """
    primes:  list[int]
    sc:      dict[tuple[int, int], tuple[bool, int | None]]
    degree:  dict[int, int]
    blind:   list[tuple[int, int]]

    def is_sc(self, p: int, q: int) -> bool:
        return self.sc.get((p, q), (False, None))[0]

    def witness_j(self, p: int, q: int) -> int | None:
        return self.sc.get((p, q), (False, None))[1]


def cross_sc_matrix(primes: list[int]) -> CrossSCMatrix:
    """Compute the full cross-SC matrix for a list of (hard) primes."""
    sc_dict:  dict[tuple[int, int], tuple[bool, int | None]] = {}
    degree:   dict[int, int] = {p: 0 for p in primes}
    blind:    list[tuple[int, int]] = []

    for p in primes:
        for q in primes:
            if p == q:
                continue
            result, j = is_self_conjugate(p, 2 * q * q)
            sc_dict[(p, q)] = (result, j)
            if result:
                degree[p] += 1
            else:
                blind.append((p, q))

    return CrossSCMatrix(primes=primes, sc=sc_dict, degree=degree, blind=blind)


# ---------------------------------------------------------------------------
# Pair coverage and sufficiency
# ---------------------------------------------------------------------------

@dataclass
class PairWitnessInfo:
    """
    For a given pair (a, b) within a k-product u = product(S),
    records which remaining primes the pair witnesses against.

    'Witnesses against x' means a*b SC mod x².
    (The mod 2 condition is trivial for odd primes.)

    pair_product   : a * b
    witnesses      : list of remaining primes x for which a*b SC mod x²
    misses         : remaining primes x where a*b NOT SC mod x²
    is_universal   : True iff witnesses covers all remaining primes in S{a,b}
    """
    a:              int
    b:              int
    pair_product:   int
    remaining:      list[int]
    witnesses:      list[int]
    misses:         list[int]
    is_universal:   bool
    witness_js:     dict[int, int]    # x → j where (a*b)^j ≡ -1 (mod x²)


def pair_witness_info(a: int, b: int, remaining: list[int]) -> PairWitnessInfo:
    """Compute witness coverage for pair (a,b) against all primes in remaining."""
    r_ab = a * b
    witnesses:   list[int]         = []
    misses:      list[int]         = []
    witness_js:  dict[int, int]    = {}

    for x in remaining:
        sc, j = is_self_conjugate(r_ab % (x * x), x * x)
        if sc:
            witnesses.append(x)
            _check(j is not None, f"self-conjugate at {x} without a witness index")
            witness_js[x] = j
        else:
            misses.append(x)

    return PairWitnessInfo(
        a=a, b=b,
        pair_product=r_ab,
        remaining=remaining,
        witnesses=witnesses,
        misses=misses,
        is_universal=(len(misses) == 0),
        witness_js=witness_js,
    )


@dataclass
class SubsetSufficiencyResult:
    """
    Result for a single k-element subset S.

    k                : |S|
    subset           : the primes in S
    has_pair_witness : True iff some pair (a,b) ⊂ S is a valid Stage 3d witness
    witness_pair     : the first (a,b) found, or None
    n_pairs_working  : how many of the C(k,2) pairs work
    n_pairs_total    : C(k,2)
    all_pair_info    : PairWitnessInfo for each pair
    """
    k:               int
    subset:          tuple[int, ...]
    has_pair_witness: bool
    witness_pair:    tuple[int, int] | None
    n_pairs_working: int
    n_pairs_total:   int
    all_pair_info:   list[PairWitnessInfo]


@dataclass
class PairSufficiencyResult:
    """
    Aggregate result of pair_sufficiency_analysis over all k-subsets.

    Attributes
    ----------
    primes          : the hard primes tested
    max_k           : largest k tested
    by_k            : {k: {"total": int, "sufficient": int, "failures": [...]}}
    all_sufficient  : True iff every tested subset had a pair witness
    counterexample  : first subset without a pair witness (or None)
    universal_pairs : pairs that witness against ALL other primes in the set
    notes           : human-readable structural observations
    """
    primes:          list[int]
    max_k:           int
    by_k:            dict[int, dict]
    all_sufficient:  bool
    counterexample:  tuple | None
    universal_pairs: list[tuple[int, int]]
    notes:           list[str]


def pair_sufficiency_analysis(
    primes: list[int],
    max_k: int = 6,
) -> PairSufficiencyResult:
    """
    For every k-element subset S (2 ≤ k ≤ max_k) of primes,
    check whether some k=2 pair (a,b) ⊂ S witnesses for the composite-r
    Turyn test: a*b SC mod x² for every x ∈ S  {a, b}.

    This is the k=2 pair-sufficiency hypothesis test.
    """
    by_k: dict[int, dict] = {}
    counterexample = None
    all_ok = True

    for k in range(2, min(max_k + 1, len(primes) + 1)):
        bucket: dict = {"total": 0, "sufficient": 0, "failures": [], "results": []}

        for subset in combinations(primes, k):
            bucket["total"] += 1
            sub_list = list(subset)

            pair_infos = []
            found_pair = None
            n_pairs_working = 0

            for a, b in combinations(sub_list, 2):
                remaining = [x for x in sub_list if x not in (a, b)]
                info = pair_witness_info(a, b, remaining)
                pair_infos.append(info)
                if info.is_universal:
                    n_pairs_working += 1
                    if found_pair is None:
                        found_pair = (a, b)

            has_witness = found_pair is not None
            if has_witness:
                bucket["sufficient"] += 1
            else:
                all_ok = False
                bucket["failures"].append(subset)
                if counterexample is None:
                    counterexample = subset

            bucket["results"].append(SubsetSufficiencyResult(
                k=k, subset=subset,
                has_pair_witness=has_witness,
                witness_pair=found_pair,
                n_pairs_working=n_pairs_working,
                n_pairs_total=len(list(combinations(sub_list, 2))),
                all_pair_info=pair_infos,
            ))

        by_k[k] = bucket

    # Universal pairs: witness against ALL remaining (in the full primes set)
    n = len(primes)
    universal = []
    for a, b in combinations(primes, 2):
        remaining = [x for x in primes if x not in (a, b)]
        info = pair_witness_info(a, b, remaining)
        if info.is_universal:
            universal.append((a, b))

    # Structural notes
    notes: list[str] = []
    n_univ = len(universal)
    n_total = len(list(combinations(primes, 2)))
    notes.append(
        f"{n_univ}/{n_total} pairs are universal witnesses "
        f"(SC mod x² for every remaining hard prime x)."
    )
    if all_ok:
        notes.append(
            "PAIR-SUFFICIENCY HOLDS for all tested subsets: "
            "every k-product has a k=2 witness."
        )
        notes.append(
            "Implication: Stage 3d with k≥3 is never needed for products "
            "of these hard primes. The theorem 'k=2 always suffices' holds empirically."
        )
    else:
        notes.append(
            f"PAIR-SUFFICIENCY FAILS for: {counterexample}. "
            "A k≥3 witness is required for this subset."
        )

    if universal:
        best = max(
            universal,
            key=lambda ab: sum(
                1 for x in primes if x not in ab and
                is_self_conjugate((ab[0]*ab[1]) % (x*x), x*x)[0]
            )
        )
        notes.append(
            f"Strongest universal pair: {best[0]}·{best[1]} = {best[0]*best[1]}."
        )

    return PairSufficiencyResult(
        primes=primes,
        max_k=max_k,
        by_k=by_k,
        all_sufficient=all_ok,
        counterexample=counterexample,
        universal_pairs=universal,
        notes=notes,
    )


# ---------------------------------------------------------------------------
# Full hard-prime sweep
# ---------------------------------------------------------------------------

@dataclass
class SweepResult:
    """
    Full sweep over all 4u² candidates (u composite, ≥2 distinct prime factors).

    Attributes
    ----------
    u_bound     : maximum u tested
    total       : number of candidates tested
    stage_counts: {stage_name: count}
    survivors   : list of (n, u, factors_u) that passed all filters
    """
    u_bound:      int
    total:        int
    stage_counts: dict[str, int]
    survivors:    list[tuple[int, int, dict]]


def run_sweep(u_bound: int, verbose: bool = False) -> SweepResult:
    """
    Sweep all n = 4u² with u ≤ u_bound, u odd, u having ≥ 2 distinct prime factors.

    Returns a SweepResult with stage histogram and any survivors.

    NOTE: Requires a `barker.admissibility` module providing `check_n()`.
    That module is not part of this bundle (it belonged to an earlier
    stage of the research pipeline).  Calling this function will raise
    NotImplementedError until the dependency is restored.
    """
    raise NotImplementedError(
        "run_sweep() depends on barker.admissibility.check_n, "
        "which is not included in this bundle.  "
        "Restore the admissibility module or remove this function."
    )
    from .arithmetic import factorize

    stage_counts: dict[str, int] = {}
    survivors:    list           = []
    total = 0

    for u in range(3, u_bound + 1, 2):
        fac = factorize(u)
        if len(fac) < 2:
            continue
        total += 1
        n = 4 * u * u
        r = check_n(n)
        stage = r.stage if not r.passed else "SURVIVED"
        stage_counts[stage] = stage_counts.get(stage, 0) + 1
        if r.passed:
            survivors.append((n, u, dict(fac)))
            if verbose:
                fstr = "·".join(
                    f"{p}^{e}" if e > 1 else str(p)
                    for p, e in sorted(fac.items())
                )
                print(f"  SURVIVOR: n={n:,}, u={u:,}={fstr}")

    return SweepResult(
        u_bound=u_bound,
        total=total,
        stage_counts=stage_counts,
        survivors=survivors,
    )


def format_sweep_result(result: SweepResult) -> str:
    """Human-readable summary of a SweepResult."""
    lines = []
    div = "─" * 62
    lines.append(div)
    lines.append(f"  Sweep: n = 4u², u ≤ {result.u_bound:,}, ≥2 distinct prime factors")
    lines.append(f"  Candidates tested: {result.total:,}")
    lines.append(div)
    lines.append(f"  {'Stage':<28} {'Count':>6}  {'%':>6}")
    lines.append(f"  {'-'*42}")
    total = result.total
    for stage, count in sorted(result.stage_counts.items(), key=lambda x: -x[1]):
        pct = 100 * count / total if total else 0
        lines.append(f"  {stage:<28} {count:>6}  {pct:>5.1f}%")
    lines.append(div)
    lines.append(f"  Survivors: {len(result.survivors)}")
    if result.survivors:
        for n, u, fac in result.survivors:
            fstr = "·".join(
                f"{p}^{e}" if e > 1 else str(p) for p, e in sorted(fac.items())
            )
            lines.append(f"    n={n:,}, u={u:,}={fstr}")
    else:
        lines.append("    → Zero survivors: pipeline is exhaustive in this range.")
    lines.append(div)
    return "\n".join(lines)


def format_pair_sufficiency(result: PairSufficiencyResult) -> str:
    """Human-readable summary of a PairSufficiencyResult."""
    lines = []
    div = "─" * 62
    lines.append(div)
    lines.append(f"  Pair-Sufficiency Analysis")
    lines.append(f"  Hard primes tested: {result.primes}")
    lines.append(div)
    for k, bucket in result.by_k.items():
        suff = bucket["sufficient"]
        total = bucket["total"]
        status = "✓" if suff == total else "✗ FAILURES"
        lines.append(
            f"  k={k}: {suff:>4}/{total:<4} subsets have a k=2 pair witness  {status}"
        )
    lines.append(div)
    for note in result.notes:
        lines.append(f"  {note}")
    lines.append(div)
    if result.universal_pairs:
        lines.append(f"  Universal pairs ({len(result.universal_pairs)}):")
        for a, b in result.universal_pairs:
            lines.append(f"    {a}·{b} = {a*b:,}")
    lines.append(div)
    return "\n".join(lines)
