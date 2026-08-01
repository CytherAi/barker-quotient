#!/usr/bin/env python3
"""
wl2_refinement.py — test whether 2-Folklore-Weisfeiler-Lehman (2-FWL)
distinguishes the single remaining 1-WL-equivalent configuration pair
at k=5 profile (1, 0, 0, 0, 0):

  C_A = (937, 1721, 11257, 16729, 18121)  — class B(δ=1)
  C_B = (1433, 4201, 6361, 9769, 16249)   — class A3

These two have non-isomorphic bipartite pair-cancellation graphs but
identical 1-WL color signatures. 2-FWL refines colors of *ordered
pairs of vertices* by neighbor-pair multisets and is strictly stronger
than 1-WL (in fact equivalent to 3-WL in the standard hierarchy).

If 2-FWL produces distinct signatures, the compact-invariant ladder
closes completely at this level for the enumerated dataset.

If 2-FWL also fails, we have a known 2-FWL-equivalent non-isomorphic
pair of bipartite graphs — a much rarer phenomenon worth examining
directly.
"""

import os
import sys
from itertools import combinations

sys.path.insert(
    0,
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "code"),
)

from barker.sweep import find_hard_primes  # noqa: E402
from barker.two_primary import build_two_primary_table  # noqa: E402


def build_bipartite(C, table):
    Cs = sorted(C)
    k = len(Cs)
    pair_list = list(combinations(range(k), 2))
    n_pairs = len(pair_list)
    n_vertices = k + n_pairs

    edges = set()
    for ti in range(k):
        x = Cs[ti]
        mod = 2 ** table.depth[x]
        for pi, (a, b) in enumerate(pair_list):
            if a == ti or b == ti:
                continue
            s = (table.chi[(Cs[a], x)] + table.chi[(Cs[b], x)]) % mod
            if s == 0:
                pv = k + pi
                edges.add((ti, pv))
                edges.add((pv, ti))

    vertex_types = [0] * k + [1] * n_pairs  # 0 = target, 1 = pair-vertex
    return edges, vertex_types, n_vertices


def two_fwl_signature(edges, vertex_types, n):
    """2-FWL on ordered pairs. Returns sorted multiset of stable colors."""
    # Initial color: depends on whether u==v, whether (u,v) is an edge,
    # and the vertex-types of u and v.
    colors = {}
    for u in range(n):
        for v in range(n):
            if u == v:
                key = ("D", vertex_types[u])
            elif (u, v) in edges:
                key = ("E", vertex_types[u], vertex_types[v])
            else:
                key = ("N", vertex_types[u], vertex_types[v])
            colors[(u, v)] = key

    def canon(coldict):
        unique = {}
        result = {}
        # Sort for determinism
        for key in sorted(coldict.keys()):
            v = coldict[key]
            if v not in unique:
                unique[v] = len(unique)
            result[key] = unique[v]
        return result

    colors = canon(colors)

    for iteration in range(50):
        new_input = {}
        for u in range(n):
            for v in range(n):
                # For each w, gather (c(u, w), c(w, v))
                pair_multiset = tuple(
                    sorted((colors[(u, w)], colors[(w, v)]) for w in range(n))
                )
                new_input[(u, v)] = (colors[(u, v)], pair_multiset)
        new_colors = canon(new_input)
        # Compare
        if all(new_colors[k] == colors[k] for k in colors):
            print(f"  2-FWL stable after {iteration + 1} iteration(s)")
            colors = new_colors
            break
        colors = new_colors
    else:
        print("  2-FWL did not stabilize in 50 iterations")

    return tuple(sorted(colors.values()))


def main():
    print("Loading...")
    hp = find_hard_primes(80000)
    target_primes = [d["prime"] for d in hp[:80]]
    table = build_two_primary_table(target_primes)

    C_A = (937, 1721, 11257, 16729, 18121)
    C_B = (1433, 4201, 6361, 9769, 16249)

    for name, C in [("C_A [B(δ=1)]", C_A), ("C_B [A3]", C_B)]:
        print(f"\n{name} = {C}")
        edges, vtypes, n = build_bipartite(C, table)
        print(f"  bipartite graph: {n} vertices, {len(edges) // 2} edges")
        sig = two_fwl_signature(edges, vtypes, n)
        # Hash signature for compact comparison
        sig_hash = hash(sig)
        n_colors = len(set(sig))
        print(f"  2-FWL signature length = {len(sig)}, distinct colors = {n_colors}")
        print(f"  hash = {sig_hash}")
        print(f"  signature (first 30 entries): {sig[:30]}")

    # Compute both and compare
    print()
    print("=" * 78)
    print("  COMPARISON")
    print("=" * 78)
    e1, t1, n1 = build_bipartite(C_A, table)
    e2, t2, n2 = build_bipartite(C_B, table)
    sig1 = two_fwl_signature(e1, t1, n1)
    sig2 = two_fwl_signature(e2, t2, n2)
    if sig1 == sig2:
        print("  2-FWL FAILS: signatures are identical.")
        print("  The two configurations are 2-FWL-equivalent.")
    else:
        print("  2-FWL SUCCEEDS: signatures differ.")
        print("  The configurations are distinguished by 2-FWL refinement.")


if __name__ == "__main__":
    main()
