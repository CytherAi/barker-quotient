#!/usr/bin/env python3
"""
wl_refinement.py — test whether 1-Weisfeiler-Lehman color refinement
on the bipartite pair-cancellation incidence graph distinguishes the
2 profiles unresolved by simpler compact invariants:

  k=5 (1, 0, 0, 0, 0):  A3 vs B(δ=1)   (6 configs)
  k=5 (3, 2, 0, 0, 0):  A2 vs A3 vs B1  (4 configs)

The bipartite graph has vertex set V = targets ∪ pair-vertices, with an
edge x ~ {a, b} iff target x cancels pair {a, b}.

Initial vertex coloring: each vertex's degree (target-load for targets;
witness count for pairs).

WL iteration: refine each vertex's color by the sorted multiset of its
neighbors' current colors. Repeat until colors stabilize.

The final sorted multiset of stable colors is the 1-WL fingerprint.
Compact (O(k + C(k,2)) integers after stabilization).

If 1-WL distinguishes the unresolved configs, the compact-invariant
residue closes to 0. If not, those configs are 1-WL-equivalent (a
known graph-isomorphism phenomenon) and require even higher
refinements or arithmetic data to separate.
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


def build_bipartite(C, table):
    """Return adjacency lists for bipartite cancellation graph.
    Targets indexed 0..k-1; pairs indexed k..k+C(k,2)-1.
    """
    Cs = sorted(C)
    k = len(Cs)
    pair_list = list(combinations(range(k), 2))
    n_pairs = len(pair_list)
    n_vertices = k + n_pairs

    adj = [[] for _ in range(n_vertices)]
    for ti in range(k):
        x = Cs[ti]
        mod = 2 ** table.depth[x]
        for pi, (a, b) in enumerate(pair_list):
            if a == ti or b == ti:
                continue
            s = (table.chi[(Cs[a], x)] + table.chi[(Cs[b], x)]) % mod
            if s == 0:
                pv = k + pi
                adj[ti].append(pv)
                adj[pv].append(ti)
    return adj, k, n_vertices


def wl_signature(adj, n_vertices, type_labels):
    """1-WL color refinement. Returns sorted multiset of stable colors."""
    colors = list(type_labels)
    iterations = 0
    while True:
        new_colors_input = []
        for v in range(n_vertices):
            neighbor_multiset = tuple(sorted(colors[u] for u in adj[v]))
            new_colors_input.append((colors[v], neighbor_multiset))
        # Hash inputs to compact integer colors
        unique = {}
        new_colors = []
        for x in new_colors_input:
            if x not in unique:
                unique[x] = len(unique)
            new_colors.append(unique[x])
        if new_colors == colors:
            break
        colors = new_colors
        iterations += 1
        if iterations > 50:
            break
    return tuple(sorted(colors))


def main():
    print("Loading...", flush=True)
    hp = find_hard_primes(80000)
    target_primes = [d["prime"] for d in hp[:80]]
    table = build_two_primary_table(target_primes)

    with open(CACHE_FILE) as f:
        records = json.load(f)
    records = [(k, cls, tuple(profile), tuple(config))
               for k, cls, profile, config in records]

    # Focus on the 2 unresolved profiles + sanity-check on a resolved profile
    targets = [
        (5, (1, 0, 0, 0, 0)),
        (5, (3, 2, 0, 0, 0)),
    ]

    by_profile = defaultdict(list)
    for k, cls, profile, config in records:
        by_profile[(k, profile)].append((cls, config))

    for prof in targets:
        rows = by_profile[prof]
        k, profile = prof
        print()
        print(f"k={k} profile={profile}: {len(rows)} configs")
        sigs_to_classes = defaultdict(set)
        sigs_to_configs = defaultdict(list)

        for cls, config in rows:
            adj, num_targets, n_v = build_bipartite(config, table)
            # Initial labels: 0 for targets, 1 for pairs (encodes bipartiteness)
            initial = [0] * num_targets + [1] * (n_v - num_targets)
            # Augment initial labels with vertex degree to seed refinement
            initial_with_degree = [
                (initial[v], len(adj[v])) for v in range(n_v)
            ]
            # Canonicalize seed
            unique_init = {}
            seed = []
            for x in initial_with_degree:
                if x not in unique_init:
                    unique_init[x] = len(unique_init)
                seed.append(unique_init[x])
            sig = wl_signature(adj, n_v, seed)
            sigs_to_classes[sig].add(cls)
            sigs_to_configs[sig].append((cls, config))

        n_sigs = len(sigs_to_classes)
        ambiguous = sum(1 for cls_set in sigs_to_classes.values() if len(cls_set) > 1)
        print(f"  distinct WL signatures = {n_sigs}, ambiguous = {ambiguous}")
        for sig, cls_set in sigs_to_classes.items():
            cfgs_here = sigs_to_configs[sig]
            print(f"    signature with classes {sorted(cls_set)}: {len(cfgs_here)} configs")
            for cls, cfg in cfgs_here:
                print(f"      [{cls}] {cfg}")

    # Resolution outcome
    print()
    print("=" * 78)
    print("  WL REFINEMENT OUTCOME")
    print("=" * 78)
    overall_resolved = True
    for prof in targets:
        rows = by_profile[prof]
        sigs_to_classes = defaultdict(set)
        for cls, config in rows:
            adj, num_targets, n_v = build_bipartite(config, table)
            initial = [0] * num_targets + [1] * (n_v - num_targets)
            initial_with_degree = [(initial[v], len(adj[v])) for v in range(n_v)]
            unique_init = {}
            seed = []
            for x in initial_with_degree:
                if x not in unique_init:
                    unique_init[x] = len(unique_init)
                seed.append(unique_init[x])
            sig = wl_signature(adj, n_v, seed)
            sigs_to_classes[sig].add(cls)
        ambiguous = any(len(s) > 1 for s in sigs_to_classes.values())
        if ambiguous:
            overall_resolved = False
            print(f"  {prof}: NOT resolved by 1-WL")
        else:
            print(f"  {prof}: RESOLVED by 1-WL")

    if overall_resolved:
        print("\nAll previously-unresolved profiles are resolved by 1-WL refinement.")
    else:
        print("\nSome profiles remain unresolved even by 1-WL.")


if __name__ == "__main__":
    main()
