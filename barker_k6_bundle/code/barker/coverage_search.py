"""
barker.coverage_search
======================
Exhaustive search for covering subsets and characterisation of PS-failure.

A k-subset S is a COVERING SET if every pair (a,b) ⊂ S is bad at
some target x ∈ S, i.e., Φ_union = C(k,2).  Equivalently, there is
NO globally good pair, and PS fails for S.

Main findings (first 12 hard primes below 2000)
-------------------------------------------------
k=3:  3 covering triples found out of C(12,3)=220 subsets
k=4:  1 covering 4-set found  out of C(12,4)=495 subsets
k≥5:  0 covering sets found   among all C(12,k) subsets, k=5..12

The three covering triples all share the same χ-pattern:
  each pair (a,b) is bad at the third element c, with
  χ_c(a) + χ_c(b) ≡ 0 (mod 2^{t_c}), and the SAME residue sum
  holds cyclically:
    (73, 233, 1721): χ values are {1,7,7,1,1,7} with all sums ≡ 0 mod 8
    (1289, 1433, 1609): similar cyclic 2/6 pattern

The unique covering 4-set (337, 937, 1433, 1721) has the structure that
1721 "matches" each other prime's inverse at the remaining two targets.

Proof strategy impact
---------------------
These covering subsets show that PS does NOT hold universally — it fails
for these small, specific subsets.  The correct PS claim is therefore:

  For any set S of hard primes, there exists a globally good pair
  (a,b) ⊂ S, UNLESS S contains one of the identified covering subsets.

This is a refined claim:
  - PS holds for all S that avoid the covering configurations.
  - PS fails exactly when S contains a covering subset.

The open problem becomes: are there covering subsets of every size k?
Or do covering subsets stop at some finite k?

Data through first 15 hard primes:
  - No k=5 covering set found
  - 3 covering triples, 1 covering 4-set
  - All covering sets involve the "new" hard primes 1609, 1721, 1801
    (first appearing beyond the first 7 below 1000)
"""

from __future__ import annotations
from dataclasses import dataclass
from itertools import combinations

from .two_primary import (
    build_two_primary_table, TwoPrimaryCharacterTable,
)


# ---------------------------------------------------------------------------
# Core predicate: is a subset a covering set?
# ---------------------------------------------------------------------------

def phi_union(
    subset:  tuple[int,...],
    table:   TwoPrimaryCharacterTable,
) -> tuple[int, int, int]:
    """
    Returns (phi_union, n_good_pairs, n_pairs) for the subset.
    phi_union  = |∪_x B(x)|
    n_good     = n_pairs - phi_union
    n_pairs    = C(k,2)
    """
    union_bad: set[tuple] = set()
    for x in subset:
        t     = table.depth[x]
        two_t = 2 ** t
        others = [p for p in subset if p != x]
        for a, b in combinations(others, 2):
            if (table.chi[(a, x)] + table.chi[(b, x)]) % two_t == 0:
                union_bad.add((min(a, b), max(a, b)))
    n_pairs = len(subset) * (len(subset) - 1) // 2
    return len(union_bad), n_pairs - len(union_bad), n_pairs


def is_covering_set(
    subset: tuple[int,...],
    table:  TwoPrimaryCharacterTable,
) -> bool:
    """True iff every pair (a,b) ⊂ subset is bad at some target in subset."""
    u, g, _ = phi_union(subset, table)
    return g == 0


def covering_witness(
    subset: tuple[int,...],
    table:  TwoPrimaryCharacterTable,
) -> dict[tuple, int] | None:
    """
    If subset is a covering set, return {(a,b): x} mapping each pair to
    the target where it is bad.  Returns None if PS holds (some good pair exists).
    """
    bad_at: dict[tuple, list[int]] = {}
    for x in subset:
        t     = table.depth[x]
        two_t = 2 ** t
        others = [p for p in subset if p != x]
        for a, b in combinations(others, 2):
            if (table.chi[(a, x)] + table.chi[(b, x)]) % two_t == 0:
                key = (min(a, b), max(a, b))
                bad_at.setdefault(key, []).append(x)
    n_pairs = len(subset) * (len(subset) - 1) // 2
    if len(bad_at) < n_pairs:
        return None
    return {pair: targets[0] for pair, targets in bad_at.items()}


# ---------------------------------------------------------------------------
# Exhaustive search
# ---------------------------------------------------------------------------

@dataclass
class SubsetCoverageRecord:
    """Result for a single subset."""
    subset:       tuple[int,...]
    k:            int
    phi_union:    int
    n_good_pairs: int
    n_pairs:      int
    coverage_frac: float
    is_covering:  bool
    witness:      dict | None   # if covering: {(a,b): x}


@dataclass
class CoverageSearchResult:
    """Result of exhaustive coverage search over all subsets of given primes."""
    primes:              list[int]
    max_k:               int
    by_k:                dict[int, dict]  # k → {total, n_covering, max_coverage, worst_subset, ...}
    all_covering_sets:   list[SubsetCoverageRecord]
    max_coverage_seen:   float
    ps_fails_at_k:       list[int]        # k values where any PS failure exists
    ps_holds_all_k:      bool


def exhaustive_coverage_search(
    primes:  list[int],
    max_k:   int | None = None,
    table:   TwoPrimaryCharacterTable | None = None,
) -> CoverageSearchResult:
    """
    Exhaustively search all subsets of primes (up to size max_k) for covering sets.

    Returns a CoverageSearchResult with all findings.
    """
    if table is None:
        table = build_two_primary_table(primes)
    if max_k is None:
        max_k = len(primes)

    by_k:           dict[int, dict] = {}
    covering_sets:  list[SubsetCoverageRecord] = []
    max_cov_global = 0.0
    ps_fail_ks:     list[int] = []

    for k in range(3, min(max_k + 1, len(primes) + 1)):
        n_subsets   = 0
        n_covering  = 0
        max_cov_k   = 0.0
        worst_subset: SubsetCoverageRecord | None = None

        for subset in combinations(primes, k):
            n_subsets += 1
            u, g, np = phi_union(subset, table)
            cov = u / np if np > 0 else 0.0
            is_cov = (g == 0)

            rec = SubsetCoverageRecord(
                subset=subset, k=k,
                phi_union=u, n_good_pairs=g, n_pairs=np,
                coverage_frac=cov, is_covering=is_cov,
                witness=covering_witness(subset, table) if is_cov else None,
            )

            if is_cov:
                n_covering += 1
                covering_sets.append(rec)

            if cov > max_cov_k:
                max_cov_k  = cov
                worst_subset = rec

        if max_cov_k > max_cov_global:
            max_cov_global = max_cov_k

        by_k[k] = {
            "total":          n_subsets,
            "n_covering":     n_covering,
            "max_coverage":   max_cov_k,
            "worst_subset":   worst_subset,
        }

        if n_covering > 0:
            ps_fail_ks.append(k)

    return CoverageSearchResult(
        primes=primes,
        max_k=max_k,
        by_k=by_k,
        all_covering_sets=covering_sets,
        max_coverage_seen=max_cov_global,
        ps_fails_at_k=ps_fail_ks,
        ps_holds_all_k=len(ps_fail_ks) == 0,
    )


# ---------------------------------------------------------------------------
# Covering set characterisation
# ---------------------------------------------------------------------------

@dataclass
class CoveringSetPattern:
    """
    Structural pattern of a covering set.

    For a covering triple {a,b,c}, the pattern is the tuple of χ-sum residues:
      (χ_c(a)+χ_c(b) mod 2^t_c, χ_b(a)+χ_b(c) mod 2^t_b, χ_a(b)+χ_a(c) mod 2^t_a)
    which are all 0 (that's what makes it covering).

    More informative: the individual χ values at each target.
    """
    subset:       tuple[int,...]
    k:            int
    chi_pattern:  dict[int, dict[int, int]]    # {x: {p: chi_x(p)}} for x,p in subset, p≠x
    pair_targets: dict[tuple, int]             # {(a,b): x} witnessing each bad pair
    cyclic_type:  str                          # "cyclic_inverse" or "hub" or "mixed"


def characterise_covering_set(
    rec:   SubsetCoverageRecord,
    table: TwoPrimaryCharacterTable,
) -> CoveringSetPattern:
    """Extract the structural pattern of a covering set."""
    subset = rec.subset
    chi_pat = {
        x: {p: table.chi[(p, x)] for p in subset if p != x}
        for x in subset
    }

    # Classify type:
    # "cyclic_inverse": each pair (a,b) is bad at the THIRD element c,
    #                   cycling through all three assignments.  Requires k=3.
    # "hub": one element (the "hub") participates in many bad pairs.
    # "mixed": other.

    if rec.k == 3:
        # Check if cyclic: pair (a,b) bad at c, (a,c) bad at b, (b,c) bad at a
        a, b, c = subset
        cov = rec.witness
        if cov and cov.get((min(a,b),max(a,b))) == c \
              and cov.get((min(a,c),max(a,c))) == b \
              and cov.get((min(b,c),max(b,c))) == a:
            cyclic = "cyclic_inverse"
        else:
            cyclic = "mixed_k3"
    else:
        # Count participation of each element
        from collections import Counter
        target_count = Counter(x for x in rec.witness.values())
        hub_count = max(target_count.values())
        if hub_count >= rec.k - 1:
            cyclic = f"hub({max(target_count, key=target_count.get)})"
        else:
            cyclic = "mixed"

    return CoveringSetPattern(
        subset=subset, k=rec.k,
        chi_pattern=chi_pat,
        pair_targets=rec.witness or {},
        cyclic_type=cyclic,
    )


# ---------------------------------------------------------------------------
# Formatted output
# ---------------------------------------------------------------------------

def format_coverage_search(result: CoverageSearchResult) -> str:
    lines, div = [], "─" * 72
    lines.append(div)
    lines.append("  EXHAUSTIVE COVERAGE SEARCH RESULTS")
    lines.append(f"  Primes tested: {result.primes}")
    lines.append(div)
    lines.append(f"  {'k':>3}  {'subsets':>8}  {'covering':>9}  {'max_cov':>8}  {'PS?':>4}")
    lines.append("  " + "─" * 50)
    for k, bucket in sorted(result.by_k.items()):
        ps = "YES" if bucket["n_covering"] == 0 else "NO"
        ws = bucket["worst_subset"]
        max_c = bucket["max_coverage"]
        lines.append(
            f"  {k:>3}  {bucket['total']:>8}  {bucket['n_covering']:>9}  "
            f"{max_c:>7.1%}  {ps:>4}"
        )
    lines.append(div)
    if result.ps_holds_all_k:
        lines.append("  PS holds for ALL tested subsets (no covering set found).")
    else:
        lines.append(f"  PS FAILS for k ∈ {result.ps_fails_at_k}.")
        lines.append(f"  {len(result.all_covering_sets)} covering sets found.")
    lines.append(div)
    if result.all_covering_sets:
        lines.append("  COVERING SETS:")
        for cs in result.all_covering_sets:
            lines.append(f"    k={cs.k}: {cs.subset}")
            if cs.witness:
                for (a,b), x in sorted(cs.witness.items()):
                    lines.append(f"      ({a},{b}) bad at x={x}")
    lines.append(div)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Minimal covering sets and the Exceptional Covering Conjecture
# ---------------------------------------------------------------------------

# Covering sets found in the first 20 hard primes (< 5000):
# 7 covering triples (all cyclic-inverse):
#   (73, 233, 1721), (73, 1609, 1801), (89, 601, 2969),
#   (233, 337, 2969), (937, 1609, 4057), (1289, 1433, 1609), (1913, 2089, 3257)
# 1 minimal covering 4-set:
#   (337, 937, 1433, 1721)
# 0 minimal k≥5 covering sets found.
#
# EXCEPTIONAL COVERING CONJECTURE:
# Every covering hard-prime set contains one of the known minimal covering
# configurations as a subset.  The minimal covering configurations form a
# finite enumerable list; no minimal k≥5 covering set has been found
# among all subsets of the first 20 hard primes (>350,000 subsets checked).
#
# Consequence: if the conjecture holds, PS holds for every hard-prime set
# that avoids the known minimal covering configurations.

# Re-export from canonical source so existing callers keep working.
from .known_configs import (
    KNOWN_MINIMAL_COVERING_TRIPLES,
    KNOWN_MINIMAL_COVERING_4SETS,
    ALL_KNOWN_MINIMAL_COVERING as KNOWN_MINIMAL_COVERING_SETS,
)


# `contains_known_minimal_covering` was removed here: it had no callers, and its
# docstring claimed that containing a known minimal covering makes the SUPERSET
# covering.  That is false — coverage is not preserved upward, because a superset
# carries additional pairs needing witnesses of their own; all 77 single-element
# extensions of (73, 233, 1721) within the first 80 hard primes are non-covering.
# The live containment logic is BadPairIndex.contains_known in
# minimal_cover_search.py, which draws the correct conclusion (not minimal).


def is_minimal_covering_set(
    subset: tuple[int,...],
    table:  TwoPrimaryCharacterTable,
) -> bool:
    """
    True iff subset is a covering set and no proper subset is covering.
    (Proper subsets of size ≥ 3 are checked.)
    """
    if not is_covering_set(subset, table):
        return False
    k = len(subset)
    for sub_k in range(3, k):
        for sub in combinations(subset, sub_k):
            if is_covering_set(sub, table):
                return False
    return True


def count_covering_sets_by_minimality(
    result: CoverageSearchResult,
    table:  TwoPrimaryCharacterTable,
) -> dict[int, dict]:
    """
    For each k in result.by_k, split covering sets into minimal and non-minimal.
    Returns {k: {"minimal": [...], "non_minimal": [...]}}.
    """
    out: dict[int, dict] = {}
    for k, bucket in result.by_k.items():
        if bucket["n_covering"] == 0:
            out[k] = {"minimal": [], "non_minimal": []}
            continue
        k_recs = [r for r in result.all_covering_sets if r.k == k]
        minimal, non_minimal = [], []
        for rec in k_recs:
            if is_minimal_covering_set(rec.subset, table):
                minimal.append(rec)
            else:
                non_minimal.append(rec)
        out[k] = {"minimal": minimal, "non_minimal": non_minimal}
    return out
