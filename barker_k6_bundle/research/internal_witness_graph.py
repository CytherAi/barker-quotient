#!/usr/bin/env python3
"""
internal_witness_graph.py — exploratory probe #4 (research/, post-v1.0).

The intrinsic topology of each covering's internal pair-witness
assignment, independent of the external target system.

For a covering C, every pair {a, b} ⊂ C has an internal witness set
    W(a, b) = {c ∈ C \\ {a, b} : chi_c(a) + chi_c(b) = 0 mod 2^{t_c}}
with |W(a, b)| >= 1 for every pair (the covering property).

This script computes, for each known minimal covering, six intrinsic
invariants of the witness graph:

  1. pair-multiplicity distribution
       how many pairs have |W| = 1, 2, 3, ...?
       (1 = barely-covered pair; high values = redundantly witnessed.)
  2. witness-load d(c) per vertex
       how many pairs does each prime c in C witness?
       Highly concentrated on one c -> star-like (hub structure).
       Roughly equal -> distributed.
  3. hub saturation = max d(c) / C(k-1, 2)
       fraction of "non-self-involving" pairs the best witness covers;
       1.0 means c witnesses every pair not involving itself
       (the V-hub).
  4. minimum cover size
       smallest # of primes to witness all C(k, 2) pairs.  Computed
       EXACTLY by scanning subsets in increasing size (k <= 6 here);
       the greedy choice is only an upper bound and is reported
       separately for comparison.
       Star-like covering -> cover size ~2; distributed -> close to k.
  5. witness incidences = sum |W(a, b)|, and the number of DISTINCT
       2-simplices of the complex with full 1-skeleton on C and a
       triangle {a, b, c} whenever c in W(a, b).  These differ: the
       triangle {a, b, c} is counted up to three times by the
       incidence sum (once per pair of its vertices whose witness set
       contains the third), so only the distinct count belongs in the
       Euler characteristic.
  6. residual-covered-after-hub-removal
       True iff after deleting the max-load vertex, the remaining
       (k-1)-vertex sub-system still covers all pairs that don't
       involve the removed vertex. (Cone-point witness.)

Compares Type A vs Type B only — random non-coverings are irrelevant
because they have no internal witness graph (not coverings).

Run from repo root:
    python3 barker_k6_bundle/research/internal_witness_graph.py
"""

import os
import sys
from collections import Counter
from itertools import combinations

sys.path.insert(
    0,
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "code"),
)

from barker.cofactor_analysis import classify_all_known  # noqa: E402
from barker.sweep import find_hard_primes  # noqa: E402
from barker.two_primary import build_two_primary_table  # noqa: E402


def witness_data(C, table):
    Cs = sorted(C)
    k = len(Cs)
    pairs = list(combinations(Cs, 2))
    n_pairs = len(pairs)
    max_pos_load = (k - 1) * (k - 2) // 2  # C(k-1, 2)

    W = {}
    for (a, b) in pairs:
        wit = []
        for c in Cs:
            if c == a or c == b:
                continue
            mod = 2 ** table.depth[c]
            if (table.chi[(a, c)] + table.chi[(b, c)]) % mod == 0:
                wit.append(c)
        W[(a, b)] = wit

    mult_dist = Counter(len(W[pair]) for pair in pairs)
    load = {c: 0 for c in Cs}
    for pair, wits in W.items():
        for c in wits:
            load[c] += 1
    load_dist = Counter(load.values())
    max_load = max(load.values()) if load else 0
    argmax_load = [c for c, lo in load.items() if lo == max_load]
    hub_sat = max_load / max_pos_load if max_pos_load else 0.0

    p_witness = {c: set(pp for pp in pairs if c in W[pp]) for c in Cs}

    # Greedy cover — an upper bound on the minimum, not the minimum.
    uncovered = set(pairs)
    greedy = []
    while uncovered:
        best_c, best_cov = None, set()
        for c in Cs:
            cov = uncovered & p_witness[c]
            if len(cov) > len(best_cov):
                best_c, best_cov = c, cov
        if not best_cov:
            break
        greedy.append((best_c, len(best_cov)))
        uncovered -= best_cov
    greedy_size = len(greedy) if not uncovered else None

    # Exact minimum cover: k <= 6, so scanning by increasing size is cheap.
    all_pairs = set(pairs)
    min_cover = None
    for size in range(1, k + 1):
        hit = next(
            (sub for sub in combinations(Cs, size)
             if set().union(*(p_witness[c] for c in sub)) == all_pairs),
            None,
        )
        if hit is not None:
            min_cover = hit
            break

    total_incidences = sum(len(W[pair]) for pair in pairs)
    # Distinct 2-simplices: {a, b, c} is one triangle however many of its
    # three vertex-pairs happen to list the third vertex as a witness.
    triangles = {frozenset((a, b, c)) for (a, b) in pairs for c in W[(a, b)]}
    euler = k - n_pairs + len(triangles)

    h = argmax_load[0]
    remaining_pairs = [p for p in pairs if h not in p]
    residual_uncovered = [p for p in remaining_pairs
                          if not any(c != h for c in W[p])]
    residual_ok = len(residual_uncovered) == 0

    return {
        "config": tuple(Cs),
        "k": k,
        "n_pairs": n_pairs,
        "max_pos_load": max_pos_load,
        "mult_dist": dict(sorted(mult_dist.items())),
        "load": dict(load),
        "load_dist": dict(sorted(load_dist.items())),
        "max_load": max_load,
        "argmax_load": argmax_load,
        "hub_saturation": hub_sat,
        "cover_size": len(min_cover) if min_cover else None,
        "min_cover": min_cover,
        "greedy_cover_size": greedy_size,
        "greedy_cover": greedy,
        "total_incidences": total_incidences,
        "n_triangles": len(triangles),
        "euler_char": euler,
        "residual_covered": residual_ok,
    }


def main():
    print("Loading first 80 hard primes and character table...")
    hp = find_hard_primes(80000)
    target_primes = [d["prime"] for d in hp[:80]]
    table = build_two_primary_table(target_primes)
    cls = classify_all_known()

    rows = []
    for r in cls.type_a + cls.type_b:
        Cs = tuple(sorted(r.config))
        lab = "B" if r.is_genuine else "A"
        rows.append((lab, witness_data(Cs, table)))
    rows.sort(key=lambda x: (x[0], x[1]["k"]))

    print()
    print("=" * 78)
    print("  INTERNAL WITNESS GRAPH — intrinsic topology of each covering")
    print("=" * 78)

    for lab, d in rows:
        print()
        print(f"k={d['k']}  [Type {lab}]  {d['config']}")
        print(
            f"  n_pairs = {d['n_pairs']}   max possible single-vertex load "
            f"= C(k-1, 2) = {d['max_pos_load']}"
        )
        print(f"  pair multiplicity |W(a,b)|: {d['mult_dist']}")
        load_lines = ", ".join(f"{c}->{l}" for c, l in d["load"].items())
        print(f"  load d(c): {load_lines}")
        print(f"  load distribution: {d['load_dist']}")
        print(
            f"  max load = {d['max_load']}  at {d['argmax_load']}   "
            f"hub saturation = {d['hub_saturation']:.3f}"
        )
        print(
            f"  minimum internal cover: {d['cover_size']} vertices "
            f"{d['min_cover']}   (greedy gives {d['greedy_cover_size']}, "
            f"steps = {d['greedy_cover']})"
        )
        print(
            f"  witness incidences = {d['total_incidences']}   "
            f"distinct triangles = {d['n_triangles']}   "
            f"Euler χ = {d['euler_char']}"
        )
        print(
            f"  residual-covers-after-hub-removal: {d['residual_covered']}"
        )

    print()
    print("=" * 78)
    print("  SUMMARY")
    print("=" * 78)
    print(
        f"{'Type':4} {'k':>2}  {'config':36}  "
        f"{'maxLd':>5} {'maxPos':>6} {'satur':>5} {'cover':>5} "
        f"{'inc':>4} {'tri':>4} {'χ':>4} {'resOK':>5}"
    )
    for lab, d in rows:
        cfg_str = str(d["config"])
        if len(cfg_str) > 34:
            cfg_str = cfg_str[:31] + "..."
        print(
            f"{lab:4} {d['k']:>2}  {cfg_str:36}  "
            f"{d['max_load']:>5} "
            f"{d['max_pos_load']:>6} "
            f"{d['hub_saturation']:>5.2f} "
            f"{d['cover_size']:>5} "
            f"{d['total_incidences']:>4} "
            f"{d['n_triangles']:>4} "
            f"{d['euler_char']:>4} "
            f"{'Y' if d['residual_covered'] else 'N':>5}"
        )


if __name__ == "__main__":
    main()
