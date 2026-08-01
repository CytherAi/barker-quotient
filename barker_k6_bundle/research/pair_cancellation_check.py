#!/usr/bin/env python3
"""
pair_cancellation_check.py — test whether pair-cancellation incidence
further reduces the V-graph-unresolved arithmetic residue.

Pair-cancellation incidence is strictly richer than V-graph incidence:
  V-graph edge:        x → y iff χ_x(y) = 0
  Pair-cancellation:   x ~ {a, b} iff χ_x(a) + χ_x(b) = 0  (a, b ≠ x)

For each multi-class δ-profile in the cached enumeration, compute the
canonical form of the *internal* pair-cancellation incidence matrix
(k × C(k,2)) and check whether classes within the profile have
distinct canonical forms.

For the 5 V-graph-unresolved profiles this is the decisive next test:
  - if pair-cancellation distinguishes the classes for some of them,
    the irreducible residue shrinks further;
  - if pair-cancellation fails on the same 5 profiles, the residue is
    stable against this refinement (but the (3,1,1,1,0,0) outlier
    becomes especially important: only 2 configs but with non-trivial
    V-graph that failed, and now non-trivial pair-incidence too).

Canonicalization: brute-force vertex permutations, k! ≤ 720 for k ≤ 6.
"""

import json
import os
import sys
from collections import defaultdict
from itertools import combinations, permutations

sys.path.insert(
    0,
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "code"),
)

from barker.sweep import find_hard_primes  # noqa: E402
from barker.two_primary import build_two_primary_table  # noqa: E402


CACHE_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "_enumeration_cache.json"
)


def pair_incidence_canonical(C, table):
    Cs = sorted(C)
    k = len(Cs)
    pair_list = list(combinations(range(k), 2))
    n_pairs = len(pair_list)
    pair_idx = {p: i for i, p in enumerate(pair_list)}

    # M[i][p] = 1 if Cs[i] cancels pair_list[p] at target Cs[i], else 0, or -1 if i is in pair
    M = [[0] * n_pairs for _ in range(k)]
    for i in range(k):
        x = Cs[i]
        mod = 2 ** table.depth[x]
        for pi, (ia, ib) in enumerate(pair_list):
            if ia == i or ib == i:
                M[i][pi] = -1
                continue
            s = (table.chi[(Cs[ia], x)] + table.chi[(Cs[ib], x)]) % mod
            M[i][pi] = 1 if s == 0 else 0

    best = None
    for perm in permutations(range(k)):
        new_M = [[0] * n_pairs for _ in range(k)]
        for p, (a, b) in enumerate(pair_list):
            orig_a, orig_b = perm[a], perm[b]
            orig_pair = (min(orig_a, orig_b), max(orig_a, orig_b))
            q = pair_idx[orig_pair]
            for i in range(k):
                new_M[i][p] = M[perm[i]][q]
        flat = tuple(tuple(row) for row in new_M)
        if best is None or flat < best:
            best = flat
    return best


def main():
    print("Loading first 80 hard primes + character table...", flush=True)
    hp = find_hard_primes(80000)
    target_primes = [d["prime"] for d in hp[:80]]
    table = build_two_primary_table(target_primes)

    with open(CACHE_FILE) as f:
        records = json.load(f)
    records = [(k, cls, tuple(profile), tuple(config))
               for k, cls, profile, config in records]
    print(f"  loaded {len(records)} minimal coverings", flush=True)

    by_profile = defaultdict(list)
    for k, cls, profile, config in records:
        by_profile[(k, profile)].append((cls, config))

    multi_profiles = {k: rows for k, rows in by_profile.items()
                      if len({c for c, _ in rows}) > 1}

    print(f"  {len(multi_profiles)} multi-class profiles", flush=True)
    print()

    # Track outcomes
    resolved = []
    unresolved = []
    partial = []

    for (k, profile), rows in sorted(multi_profiles.items()):
        canon_to_classes = defaultdict(set)
        canon_to_count = defaultdict(int)
        for cls, config in rows:
            canon = pair_incidence_canonical(config, table)
            canon_to_classes[canon].add(cls)
            canon_to_count[canon] += 1

        all_classes_in_profile = sorted({c for c, _ in rows})
        ambiguous = {c: cls for c, cls in canon_to_classes.items()
                     if len(cls) > 1}

        if not ambiguous:
            resolved.append((k, profile, all_classes_in_profile,
                             len(canon_to_classes), len(rows)))
        elif len(ambiguous) == len(canon_to_classes):
            unresolved.append((k, profile, all_classes_in_profile,
                               len(canon_to_classes), ambiguous, len(rows)))
        else:
            partial.append((k, profile, all_classes_in_profile,
                            len(canon_to_classes), ambiguous, len(rows)))

        print(
            f"  k={k} profile={profile}: "
            f"{len(rows)} configs, classes={all_classes_in_profile}, "
            f"distinct pair-incidences={len(canon_to_classes)}, "
            f"ambiguous={len(ambiguous)}",
            flush=True,
        )

    print()
    print("=" * 78)
    print("  PAIR-CANCELLATION REFINEMENT TEST")
    print("=" * 78)
    print(f"Multi-class profiles total:                          {len(multi_profiles)}")
    print(f"Resolved by pair-cancellation incidence:             {len(resolved)}")
    print(f"Partial (some classes split, some share):            {len(partial)}")
    print(f"Unresolved (all share one canonical pair-incidence): {len(unresolved)}")

    print()
    print("=" * 78)
    print("  UNRESOLVED PROFILES (the true irreducible arithmetic residue)")
    print("=" * 78)
    total_irreducible_configs = 0
    for k, profile, classes, n_canons, ambig, n_rows in unresolved:
        print(f"  k={k} profile={profile} classes={classes} ({n_rows} configs)")
        for canon, cls_set in ambig.items():
            print(f"    classes {sorted(cls_set)} share a canonical pair-incidence")
        total_irreducible_configs += n_rows
    print()
    print(f"Configs in pair-incidence-irreducible profiles: {total_irreducible_configs}")

    print()
    print("=" * 78)
    print("  PARTIAL CASES")
    print("=" * 78)
    for k, profile, classes, n_canons, ambig, n_rows in partial:
        print(f"  k={k} profile={profile} classes={classes} ({n_rows} configs, "
              f"{n_canons} distinct incidences, {len(ambig)} ambiguous)")
        for canon, cls_set in ambig.items():
            print(f"    classes {sorted(cls_set)} share a canonical pair-incidence")


if __name__ == "__main__":
    main()
