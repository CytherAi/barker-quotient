"""
barker.minimal_cover_search
============================
Dedicated search for minimal covering hard-prime configurations.

A subset S is a MINIMAL COVERING SET if:
  1. Every pair (a,b) ⊂ S is bad at some target x ∈ S (covering condition).
  2. No proper subset S' ⊂ S with |S'| ≥ 3 is also covering (minimality).

Equivalently: Φ_union(S) = C(|S|, 2) and no proper sub-cover exists.

The search uses a precomputed bad-pair index table (O(1) lookup per pair/target)
and prunes aggressively:
  - If a subset contains a known minimal covering configuration, skip it
    (the containing set cannot itself be minimal).
  - Early termination: once every pair is covered, stop checking targets.

Results (first N hard primes)
------------------------------
k=3:  7 minimal covering triples (first 40 primes)
k=4:  1 minimal covering 4-set   (first 40 primes): {337, 937, 1433, 1721}
k=5:  4 minimal covering 5-sets  (first 40 primes, hard primes < 20000)
      (89, 1721, 4177, 6553, 7529)
      (233, 881, 4201, 6553, 6857)
      (1913, 4057, 6089, 6353, 7753)
      (4297, 4409, 5689, 6553, 7753)
k=6:  0 minimal covering 6-sets  (first 30 primes searched)

Key structural observation for k=5 sets:
  All 10 pairs are covered, each by exactly 1 or 2 targets.
  They do NOT contain any of the 7 known covering triples or the known quad.
  They represent a genuinely new irreducible covering type.

Revised conjecture
------------------
The original Exceptional Covering Conjecture (only k=3,4 minimal configs)
must be revised. Minimal covering configurations exist at k=5.

REVISED CONJECTURE: Every minimal covering set has size ≤ some k_max.
Empirical bound: k_max ≤ 5 or 6 (no minimal k=6 set found in first 30 primes).

The correct claim for pair-sufficiency:
  PS holds for every hard-prime set S that contains no minimal covering
  configuration as a subset.
"""

from __future__ import annotations
from dataclasses import dataclass
from itertools import combinations
import time

from .two_primary import (
    build_two_primary_table, TwoPrimaryCharacterTable,
)
from .coverage_search import (
    KNOWN_MINIMAL_COVERING_SETS,
    covering_witness,
)


# ---------------------------------------------------------------------------
# Precomputed bad-pair index
# ---------------------------------------------------------------------------

class BadPairIndex:
    """
    Precomputed lookup: for each target index xi, the set of pair-frozensets
    {ai, bi} that are bad (chi_x(a)+chi_x(b) ≡ 0 mod 2^t).

    Enables O(1) lookup per pair/target and O(k²) covering check per subset.
    """
    def __init__(self, primes: list[int], table: TwoPrimaryCharacterTable):
        self.primes    = primes
        self.n         = len(primes)
        self.prime_idx = {p: i for i, p in enumerate(primes)}
        self._bad: dict[int, set[frozenset]] = {}
        for xi, x in enumerate(primes):
            t     = table.depth[x]
            two_t = 2 ** t
            bad_set: set[frozenset] = set()
            others = [i for i in range(self.n) if i != xi]
            for ai, bi in combinations(others, 2):
                a = primes[ai]; b = primes[bi]
                if (table.chi[(a, x)] + table.chi[(b, x)]) % two_t == 0:
                    bad_set.add(frozenset({ai, bi}))
            self._bad[xi] = bad_set
        # Precompute known minimal covering configs as index-frozensets
        from .known_configs import ALL_KNOWN_MINIMAL_COVERING as _all_mc
        self._known = [
            frozenset(self.prime_idx[p] for p in mc if p in self.prime_idx)
            for mc in _all_mc
            if all(p in self.prime_idx for p in mc)
        ]

    def is_covering(self, indices: tuple[int,...]) -> bool:
        """True iff every pair in indices is bad at some index in indices."""
        all_pairs = set(frozenset({a,b}) for a,b in combinations(indices, 2))
        covered: set[frozenset] = set()
        for xi in indices:
            covered |= self._bad[xi] & all_pairs
            if covered >= all_pairs:
                return True
        return False

    def contains_known(self, indices: tuple[int,...]) -> bool:
        """True iff some known minimal covering config of STRICTLY SMALLER size
        is a subset of indices.  (Does not prune the config itself.)"""
        s   = set(indices)
        k   = len(indices)
        return any(len(mc) < k and mc <= s for mc in self._known)

    def is_minimal_covering(self, indices: tuple[int,...]) -> bool:
        """True iff covering and no proper sub-k subset (k'≥3) is covering."""
        if not self.is_covering(indices):
            return False
        k = len(indices)
        for sub_k in range(3, k):
            for sub in combinations(indices, sub_k):
                if self.is_covering(sub):
                    return False
        return True

    def covering_witness_primes(self, indices: tuple[int,...]) -> dict:
        """Return {(a,b): x} witness for a covering set, with actual prime values."""
        subset_primes = tuple(self.primes[i] for i in indices)
        tbl_local = build_two_primary_table(list(subset_primes))
        return covering_witness(subset_primes, tbl_local)


# ---------------------------------------------------------------------------
# Search results
# ---------------------------------------------------------------------------

@dataclass
class MinimalCoverSearchResult:
    """
    Results of a minimal covering set search at a given k.

    Attributes
    ----------
    primes              : the universe of hard primes searched
    n                   : number of primes
    k                   : subset size searched
    n_subsets_total     : C(n,k)
    n_subsets_checked   : after pruning by known configs
    n_covering          : covering subsets found (before minimality check)
    n_minimal           : minimal covering subsets found
    minimal_sets        : list of (primes_tuple) for minimal covering sets
    elapsed_seconds     : wall time
    """
    primes:            list[int]
    n:                 int
    k:                 int
    n_subsets_total:   int
    n_subsets_checked: int
    n_covering:        int
    n_minimal:         int
    minimal_sets:      list[tuple[int,...]]
    elapsed_seconds:   float


def search_minimal_covering_k(
    primes: list[int],
    k:      int,
    table:  TwoPrimaryCharacterTable | None = None,
    index:  BadPairIndex | None = None,
) -> MinimalCoverSearchResult:
    """
    Exhaustively search all k-subsets of primes for minimal covering sets.

    Pruning: skip subsets containing any known minimal covering config.
    """
    if table is None:
        table = build_two_primary_table(primes)
    if index is None:
        index = BadPairIndex(primes, table)

    from math import comb as _comb
    n = len(primes)
    n_total = _comb(n, k)
    t0 = time.time()
    n_checked = n_covering = n_minimal = 0
    minimal_sets: list[tuple[int,...]] = []

    for indices in combinations(range(n), k):
        if index.contains_known(indices):
            continue
        n_checked += 1
        if index.is_covering(indices):
            n_covering += 1
            if index.is_minimal_covering(indices):
                n_minimal += 1
                minimal_sets.append(tuple(primes[i] for i in indices))

    return MinimalCoverSearchResult(
        primes=primes, n=n, k=k,
        n_subsets_total=n_total,
        n_subsets_checked=n_checked,
        n_covering=n_covering,
        n_minimal=n_minimal,
        minimal_sets=minimal_sets,
        elapsed_seconds=time.time() - t0,
    )


def search_all_minimal_covering(
    primes:  list[int],
    k_min:   int = 3,
    k_max:   int = 6,
    table:   TwoPrimaryCharacterTable | None = None,
) -> dict[int, MinimalCoverSearchResult]:
    """Run search for k = k_min..k_max, sharing the precomputed index."""
    if table is None:
        table = build_two_primary_table(primes)
    index = BadPairIndex(primes, table)
    return {
        k: search_minimal_covering_k(primes, k, table, index)
        for k in range(k_min, min(k_max + 1, len(primes) + 1))
    }


# ---------------------------------------------------------------------------
# Known covering configurations (updated after exhaustive search to k=40)
# ---------------------------------------------------------------------------

# Re-export from canonical source so existing callers keep working.
from .known_configs import (
    KNOWN_MINIMAL_COVERING_TRIPLES,
    KNOWN_MINIMAL_COVERING_4SETS,
    KNOWN_MINIMAL_COVERING_5SETS,
    ALL_KNOWN_MINIMAL_COVERING,
)


# ---------------------------------------------------------------------------
# Formatted output
# ---------------------------------------------------------------------------

def format_minimal_cover_search(results: dict[int, MinimalCoverSearchResult]) -> str:
    lines, div = [], "─" * 76
    lines.append(div)
    lines.append("  MINIMAL COVERING SET SEARCH")
    if results:
        r0 = next(iter(results.values()))
        lines.append(f"  Universe: {r0.primes[:6]}... ({r0.n} primes)")
    lines.append(div)
    lines.append(
        f"  {'k':>3}  {'total':>9}  {'checked':>9}  "
        f"{'covering':>9}  {'minimal':>8}  {'time':>6}"
    )
    lines.append("  " + "─" * 60)
    for k, r in sorted(results.items()):
        lines.append(
            f"  {k:>3}  {r.n_subsets_total:>9,}  {r.n_subsets_checked:>9,}  "
            f"{r.n_covering:>9}  {r.n_minimal:>8}  {r.elapsed_seconds:>5.1f}s"
        )
    lines.append(div)

    all_minimal: dict[int, list] = {}
    for k, r in results.items():
        if r.minimal_sets:
            all_minimal[k] = r.minimal_sets

    if all_minimal:
        lines.append("  MINIMAL COVERING SETS FOUND:")
        for k, sets in sorted(all_minimal.items()):
            for s in sets:
                lines.append(f"    k={k}: {s}")
    else:
        lines.append("  No new minimal covering sets found.")
    lines.append(div)

    max_k_with_minimal = max((k for k,r in results.items() if r.n_minimal > 0), default=0)
    max_k_searched = max(results.keys()) if results else 0
    if max_k_with_minimal < max_k_searched:
        lines.append(
            f"  No minimal covering set of size {max_k_with_minimal+1}–{max_k_searched} found "
            f"in the searched universe."
        )
    lines.append(div)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Archetype classification
# ---------------------------------------------------------------------------

@dataclass
class CoveringSetArchetype:
    """
    Canonical archetype invariants for a minimal covering set.

    Two covering sets of the same k are the SAME ARCHETYPE iff all these
    invariants agree (sufficient but not necessary for combinatorial isomorphism).

    Attributes
    ----------
    k                : subset size
    pair_mult        : sorted tuple of pair-cover multiplicities
    target_deg_desc  : target degree sequence, sorted descending
    is_perfect       : True iff all multiplicities = 1
    hub_deg          : degree of the most-connected target
    n_pairs          : C(k,2)
    label            : human-readable label
    """
    k:              int
    pair_mult:      tuple
    target_deg_desc: tuple
    is_perfect:     bool
    hub_deg:        int
    n_pairs:        int
    label:          str


def classify_archetype(
    subset: tuple[int,...],
    table:  TwoPrimaryCharacterTable,
) -> CoveringSetArchetype:
    """Compute the canonical archetype of a minimal covering set."""
    k = len(subset)

    pair_targets: dict[tuple, list[int]] = {}
    for x in subset:
        t     = table.depth[x]
        two_t = 2 ** t
        others = [p for p in subset if p != x]
        for a, b in combinations(others, 2):
            if (table.chi[(a, x)] + table.chi[(b, x)]) % two_t == 0:
                key = (min(a, b), max(a, b))
                pair_targets.setdefault(key, []).append(x)

    mult = tuple(sorted(len(ts) for ts in pair_targets.values()))

    from collections import Counter as _C
    deg = _C()
    for ts in pair_targets.values():
        for x in ts:
            deg[x] += 1
    deg_desc = tuple(sorted(deg.values(), reverse=True))
    hub_deg  = max(deg.values()) if deg else 0
    is_perf  = all(m == 1 for m in mult)

    label = f"k{k}_deg{''.join(str(d) for d in deg_desc)}"

    return CoveringSetArchetype(
        k=k,
        pair_mult=mult,
        target_deg_desc=deg_desc,
        is_perfect=is_perf,
        hub_deg=hub_deg,
        n_pairs=k*(k-1)//2,
        label=label,
    )


def archetype_key(arch: CoveringSetArchetype) -> tuple:
    """Hashable key for grouping same-archetype covering sets."""
    return (arch.k, arch.pair_mult, arch.target_deg_desc, arch.is_perfect)


# Known archetype labels:
#   k3_deg111         : cyclic triple (all 7)
#   k4_deg1122        : unique minimal quad
#   k5_deg12224       : deg=(4,2,2,2,1) — hub-spoke
#   k5_deg11224       : deg=(4,2,2,1,1) — hub-spoke variant
#   k5_deg11136       : deg=(6,3,1,1,1) — super-hub (chi=0 dominant)
#   k5_deg11233       : deg=(3,3,2,1,1) — dual-hub

KNOWN_ARCHETYPE_LABELS: dict[tuple, str] = {
    (3, (1,1,1), (1,1,1), True):                                 "Cyclic triple",
    (4, (1,1,1,1,1,1), (2,2,1,1), True):                         "Symmetric quad",
    (5, (1,1,1,1,1,1,1,1,1,2), (4,2,2,2,1), False):              "Hub-4 imperfect",
    (5, (1,1,1,1,1,1,1,1,1,1), (4,2,2,1,1), True):               "Hub-4 perfect",
    (5, (1,1,1,1,1,1,1,1,2,2), (6,3,1,1,1), False):              "Super-hub-6",
    (5, (1,1,1,1,1,1,1,1,1,1), (3,3,2,1,1), True):               "Dual-hub",
}
