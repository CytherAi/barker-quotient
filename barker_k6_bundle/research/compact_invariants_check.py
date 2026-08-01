#!/usr/bin/env python3
"""
compact_invariants_check.py — test whether any compact (small)
permutation-invariant of the pair-cancellation incidence matrix
suffices to classify configurations within multi-class δ-profiles.

The full canonical pair-incidence matrix resolves all 20 multi-class
profiles (pair_cancellation_check.py). But that's a k × C(k,2) object;
calling the resulting classifier "structural" stretches the term — it's
essentially a complete fingerprint.

A useful theorem would compress the matrix to something compact:
a single integer, a sorted tuple of length O(k), a small bipartite-
graph statistic. This script tests a battery of such invariants
against the multi-class profiles and reports which (if any) resolve
all 20.

Compact invariants tested:

  I1  total_cancellations      sum of incidence-matrix 1's
  I2  max_target_load          max # pairs any single target cancels
  I3  max_pair_witnesses       max # targets any single pair has
  I4  target_load_multiset     sorted tuple of per-target loads
  I5  pair_witness_multiset    sorted tuple of per-pair witness counts
  I6  joint_load_witness       sorted tuple of (load, witness) at each 1-cell
  I7  four_cycles              # 4-cycles in the bipartite cancellation graph
  I8  co_witness_pairs         # target-pairs sharing ≥ 1 common cancellation
  I9  triangle_count           # (t1, t2, t3) all sharing a common cancellation
  I10 (I4, I5)                 joint of target_load_multiset and pair_witness_multiset

For each invariant, count how many multi-class profiles it resolves
(no two configs in different classes share its value).
"""

import json
import os
import sys
from collections import defaultdict
from itertools import combinations

sys.path.insert(
    0,
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "code"),
)

from barker.sweep import find_hard_primes  # noqa: E402
from barker.two_primary import build_two_primary_table  # noqa: E402


CACHE_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "_enumeration_cache.json"
)


def compact_invariants(C, table):
    Cs = sorted(C)
    k = len(Cs)
    pairs = list(combinations(range(k), 2))
    n_pairs = len(pairs)

    M = [[0] * n_pairs for _ in range(k)]
    for i in range(k):
        x = Cs[i]
        mod = 2 ** table.depth[x]
        for pi, (a, b) in enumerate(pairs):
            if a == i or b == i:
                M[i][pi] = -1
                continue
            s = (table.chi[(Cs[a], x)] + table.chi[(Cs[b], x)]) % mod
            M[i][pi] = 1 if s == 0 else 0

    target_loads = [sum(1 for p in range(n_pairs) if M[i][p] == 1) for i in range(k)]
    pair_witnesses = [sum(1 for i in range(k) if M[i][p] == 1) for p in range(n_pairs)]
    total = sum(target_loads)

    target_load_mset = tuple(sorted(target_loads, reverse=True))
    pair_witness_mset = tuple(sorted(pair_witnesses, reverse=True))

    joint = []
    for i in range(k):
        for p in range(n_pairs):
            if M[i][p] == 1:
                joint.append((target_loads[i], pair_witnesses[p]))
    joint_mset = tuple(sorted(joint))

    four_cycles = 0
    for i1, i2 in combinations(range(k), 2):
        common = sum(1 for p in range(n_pairs) if M[i1][p] == 1 and M[i2][p] == 1)
        four_cycles += common * (common - 1) // 2

    co_witness = sum(
        1 for i1, i2 in combinations(range(k), 2)
        if any(M[i1][p] == 1 and M[i2][p] == 1 for p in range(n_pairs))
    )

    triangle_count = 0
    for i1, i2, i3 in combinations(range(k), 3):
        for p in range(n_pairs):
            if M[i1][p] == 1 and M[i2][p] == 1 and M[i3][p] == 1:
                triangle_count += 1

    return {
        "I1_total": total,
        "I2_max_load": max(target_loads) if target_loads else 0,
        "I3_max_witness": max(pair_witnesses) if pair_witnesses else 0,
        "I4_target_load_mset": target_load_mset,
        "I5_pair_witness_mset": pair_witness_mset,
        "I6_joint_mset": joint_mset,
        "I7_four_cycles": four_cycles,
        "I8_co_witness": co_witness,
        "I9_triangle_count": triangle_count,
        "I10_load_witness_joint": (target_load_mset, pair_witness_mset),
    }


def resolves(invariant_values, classes):
    grouped = defaultdict(set)
    for v, c in zip(invariant_values, classes):
        grouped[v].add(c)
    return all(len(s) == 1 for s in grouped.values())


def main():
    print("Loading...", flush=True)
    hp = find_hard_primes(80000)
    target_primes = [d["prime"] for d in hp[:80]]
    table = build_two_primary_table(target_primes)

    with open(CACHE_FILE) as f:
        records = json.load(f)
    records = [(k, cls, tuple(profile), tuple(config))
               for k, cls, profile, config in records]

    by_profile = defaultdict(list)
    for k, cls, profile, config in records:
        by_profile[(k, profile)].append((cls, config))
    multi_profiles = {k: v for k, v in by_profile.items()
                      if len({c for c, _ in v}) > 1}
    print(f"  {len(multi_profiles)} multi-class profiles, "
          f"{sum(len(v) for v in multi_profiles.values())} configs to invariate",
          flush=True)
    print()

    invariant_names = [
        "I1_total", "I2_max_load", "I3_max_witness",
        "I4_target_load_mset", "I5_pair_witness_mset",
        "I6_joint_mset", "I7_four_cycles", "I8_co_witness",
        "I9_triangle_count", "I10_load_witness_joint",
    ]
    invariant_short = {
        "I1_total":              "total",
        "I2_max_load":           "max-load",
        "I3_max_witness":        "max-wit",
        "I4_target_load_mset":   "load-msets",
        "I5_pair_witness_mset":  "wit-msets",
        "I6_joint_mset":         "joint-mset",
        "I7_four_cycles":        "4-cycles",
        "I8_co_witness":         "co-witness",
        "I9_triangle_count":     "triangles",
        "I10_load_witness_joint":"load+wit",
    }

    # Compute invariants for all configs in multi-class profiles
    invariant_values = defaultdict(dict)  # profile -> config -> invariants
    profile_configs = {}
    profile_classes = {}
    for prof, rows in multi_profiles.items():
        cfgs, clss, invs = [], [], []
        for cls, config in rows:
            cfgs.append(config)
            clss.append(cls)
            invs.append(compact_invariants(config, table))
        profile_configs[prof] = cfgs
        profile_classes[prof] = clss
        invariant_values[prof] = invs

    # For each individual invariant, count resolved profiles
    print("=" * 78)
    print("  INDIVIDUAL INVARIANT RESOLUTION")
    print("=" * 78)
    print(f"{'invariant':>25}  {'#resolved':>10}  {'#unresolved':>11}")
    individual_resolved = {}
    for inv_name in invariant_names:
        resolved_count = 0
        unresolved_profiles = []
        for prof in multi_profiles:
            vals = [invs[inv_name] for invs in invariant_values[prof]]
            if resolves(vals, profile_classes[prof]):
                resolved_count += 1
            else:
                unresolved_profiles.append(prof)
        individual_resolved[inv_name] = (resolved_count, unresolved_profiles)
        print(f"{inv_name:>25}  {resolved_count:>10}  {20 - resolved_count:>11}")

    # Detailed per-profile breakdown for the strongest individual invariants
    print()
    print("=" * 78)
    print("  PER-PROFILE RESOLUTION BY INVARIANT (✓ = resolves; ✗ = does not)")
    print("=" * 78)
    short_names = [invariant_short[n] for n in invariant_names]
    header = "  " + " ".join(f"{n:>10}" for n in short_names)
    print(f"  {'profile':>22}  {'classes':>14}  " + " ".join(f"{n[:5]:>5}" for n in short_names))
    for prof in sorted(multi_profiles):
        k, profile = prof
        cls_set = sorted(set(profile_classes[prof]))
        results = []
        for inv_name in invariant_names:
            vals = [invs[inv_name] for invs in invariant_values[prof]]
            results.append("✓" if resolves(vals, profile_classes[prof]) else "✗")
        cls_str = ",".join(cls_set)
        prof_str = f"k={k} {profile}"
        print(f"  {prof_str:>22}  {cls_str:>14}  " + " ".join(f"{r:>5}" for r in results))

    # Try every PAIR of invariants
    print()
    print("=" * 78)
    print("  TWO-INVARIANT COMBINATIONS — best resolution")
    print("=" * 78)
    best_pair = None
    best_count = 0
    for i in range(len(invariant_names)):
        for j in range(i + 1, len(invariant_names)):
            n1, n2 = invariant_names[i], invariant_names[j]
            count = 0
            for prof in multi_profiles:
                vals = [(invs[n1], invs[n2]) for invs in invariant_values[prof]]
                if resolves(vals, profile_classes[prof]):
                    count += 1
            if count > best_count:
                best_count = count
                best_pair = (n1, n2)
    print(f"Best pair: {best_pair}  resolves {best_count} / 20")

    # Try the full tuple of all 10 invariants
    print()
    full_count = 0
    full_unresolved = []
    for prof in multi_profiles:
        vals = [tuple(invs[name] for name in invariant_names) for invs in invariant_values[prof]]
        if resolves(vals, profile_classes[prof]):
            full_count += 1
        else:
            full_unresolved.append(prof)
    print(f"Full tuple of all 10 invariants: resolves {full_count} / 20")
    if full_unresolved:
        print(f"  unresolved profiles: {full_unresolved}")

    # Find best single invariant
    print()
    print("=" * 78)
    print("  STRONGEST SINGLE INVARIANT")
    print("=" * 78)
    best_single = max(invariant_names, key=lambda n: individual_resolved[n][0])
    bn, bp = individual_resolved[best_single]
    print(f"  {best_single}: {bn} / 20 resolved")
    if bp:
        print(f"  unresolved by this invariant:")
        for prof in bp:
            print(f"    k={prof[0]} profile={prof[1]} "
                  f"classes={sorted(set(profile_classes[prof]))}")


if __name__ == "__main__":
    main()
