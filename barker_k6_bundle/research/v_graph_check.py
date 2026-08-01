#!/usr/bin/env python3
"""
v_graph_check.py — for each multi-class δ-profile in the cached
enumeration, check whether the directed V-graph itself (not just the
δ-profile = sorted out-degree sequence) distinguishes configs in
different classes.

The V-graph on S has a directed edge x → y iff y ∈ V_x ∩ S.
The δ-profile is the sorted out-degree sequence.
The canonical isomorphism class of the V-graph carries strictly more
information than its out-degree sequence.

If for every multi-class profile, the configs in different classes
have *isomorphic* V-graphs (= same canonical form), then V-graph
refinement cannot resolve cancellation; the question is genuinely
arithmetic.

If at least one multi-class profile has its classes separated by
non-isomorphic V-graphs, then V-graph refinement might decide
cancellation and my earlier conclusion was over-strong.

Uses brute-force canonicalization via vertex permutations
(k! ≤ 720 for k ≤ 6, fast).
"""

import json
import os
import sys
from collections import defaultdict
from itertools import permutations

sys.path.insert(
    0,
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "code"),
)

from barker.sweep import find_hard_primes  # noqa: E402
from barker.two_primary import build_two_primary_table  # noqa: E402


CACHE_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "_enumeration_cache.json"
)


def adjacency_matrix(C, table):
    Cs = sorted(C)
    k = len(Cs)
    A = tuple(
        tuple(
            1 if (i != j and table.chi[(Cs[j], Cs[i])] == 0) else 0
            for j in range(k)
        )
        for i in range(k)
    )
    return A


def canonical_form(A):
    k = len(A)
    best = None
    for perm in permutations(range(k)):
        flat = tuple(tuple(A[perm[i]][perm[j]] for j in range(k)) for i in range(k))
        if best is None or flat < best:
            best = flat
    return best


def v_graph_summary(A):
    k = len(A)
    out_deg = tuple(sorted((sum(row) for row in A), reverse=True))
    in_deg = tuple(
        sorted((sum(A[i][j] for i in range(k)) for j in range(k)), reverse=True)
    )
    two_cycles = sum(1 for i in range(k) for j in range(i + 1, k)
                     if A[i][j] and A[j][i])
    n_edges = sum(sum(r) for r in A)
    return {
        "out_deg": out_deg,
        "in_deg": in_deg,
        "two_cycles": two_cycles,
        "n_edges": n_edges,
    }


def main():
    print("Loading first 80 hard primes + character table...")
    hp = find_hard_primes(80000)
    target_primes = [d["prime"] for d in hp[:80]]
    table = build_two_primary_table(target_primes)

    with open(CACHE_FILE) as f:
        records = json.load(f)
    records = [(k, cls, tuple(profile), tuple(config))
               for k, cls, profile, config in records]
    print(f"  loaded {len(records)} minimal coverings")

    by_profile = defaultdict(list)
    for k, cls, profile, config in records:
        by_profile[(k, profile)].append((cls, config))

    multi_profiles = {k: rows for k, rows in by_profile.items()
                      if len({c for c, _ in rows}) > 1}

    print(f"  {len(multi_profiles)} multi-class profiles to check\n")

    resolved = []     # V-graph refinement DOES distinguish classes
    unresolved = []   # V-graph refinement DOES NOT distinguish classes
    partial = []      # mixed: some classes share canonical V-graph, others don't

    for (k, profile), rows in sorted(multi_profiles.items()):
        # Compute canonical V-graph for each config in this profile
        canon_to_classes = defaultdict(set)
        canon_to_configs = defaultdict(list)
        in_deg_to_classes = defaultdict(set)
        for cls, config in rows:
            A = adjacency_matrix(config, table)
            summary = v_graph_summary(A)
            canon = canonical_form(A)
            canon_to_classes[canon].add(cls)
            canon_to_configs[canon].append((cls, config, summary))
            in_deg_to_classes[summary["in_deg"]].add(cls)

        # Any canonical V-graph that appears in multiple classes?
        ambiguous_canons = {c: cls for c, cls in canon_to_classes.items()
                            if len(cls) > 1}

        # Any in-degree sequence that appears in multiple classes?
        ambiguous_in_degs = {ind: cls for ind, cls in in_deg_to_classes.items()
                             if len(cls) > 1}

        all_classes_in_profile = sorted({c for c, _ in rows})

        if not ambiguous_canons:
            resolved.append((k, profile, all_classes_in_profile, len(canon_to_classes)))
        elif len(ambiguous_canons) == len(canon_to_classes):
            unresolved.append((k, profile, all_classes_in_profile,
                               len(canon_to_classes), ambiguous_canons))
        else:
            partial.append((k, profile, all_classes_in_profile,
                            len(canon_to_classes), ambiguous_canons))

        print(
            f"  k={k} profile={profile}: "
            f"{len(rows)} configs, classes={all_classes_in_profile}, "
            f"distinct V-graphs={len(canon_to_classes)}, "
            f"ambiguous V-graphs={len(ambiguous_canons)}, "
            f"in-deg-sequences distinct={len(in_deg_to_classes)}, "
            f"in-deg ambiguous={len(ambiguous_in_degs)}"
        )

    print()
    print("=" * 78)
    print("  SUMMARY OF V-GRAPH REFINEMENT TEST")
    print("=" * 78)
    print(f"Multi-class profiles total:                          {len(multi_profiles)}")
    print(f"Resolved by V-graph (different classes → different graphs): {len(resolved)}")
    print(f"Partial (some classes share V-graph, others split):  {len(partial)}")
    print(f"Unresolved (all V-graphs ambiguous):                  {len(unresolved)}")

    print()
    print("=" * 78)
    print("  PROFILES WHERE V-GRAPH RESOLVES THE SPLIT")
    print("=" * 78)
    for k, profile, classes, n_canons in resolved:
        print(f"  k={k} profile={profile} classes={classes} → {n_canons} distinct V-graphs")

    print()
    print("=" * 78)
    print("  PROFILES WHERE V-GRAPH IS COMPLETELY AMBIGUOUS")
    print("=" * 78)
    for k, profile, classes, n_canons, ambig in unresolved:
        print(f"  k={k} profile={profile} classes={classes}")
        print(f"    {n_canons} distinct canonical V-graphs, all ambiguous:")
        for canon, cls_set in ambig.items():
            print(f"      classes {sorted(cls_set)} share a canonical V-graph")

    print()
    print("=" * 78)
    print("  PARTIAL CASES (mixed)")
    print("=" * 78)
    for k, profile, classes, n_canons, ambig in partial:
        print(f"  k={k} profile={profile} classes={classes}: "
              f"{n_canons} V-graphs, {len(ambig)} ambiguous")
        for canon, cls_set in ambig.items():
            print(f"      classes {sorted(cls_set)} share a canonical V-graph")


if __name__ == "__main__":
    main()
