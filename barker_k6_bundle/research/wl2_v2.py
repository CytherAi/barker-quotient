#!/usr/bin/env python3
"""
wl2_v2.py — 2-FWL with both edge types: "cancels" (chi-derived) and
"member" (combinatorial pair-membership).

The bipartite graph has:
  - target vertices (k of them)
  - pair vertices (C(k,2) of them)
  - cancels-edges: target ~ pair iff target cancels pair (arithmetic)
  - member-edges:  target ~ pair iff target is one of pair's two indices (combinatorial)

The previous 2-FWL omitted member-edges. The pair_cancellation_check
canonical form implicitly encodes them (via the -1 markers in M). To
test whether 2-FWL on the *full* labeled graph distinguishes the
1-WL-equivalent pair at k=5 profile (1, 0, 0, 0, 0):

  C_A = (937, 1721, 11257, 16729, 18121)  — class B(δ=1)
  C_B = (1433, 4201, 6361, 9769, 16249)   — class A3
"""

import os
import sys

sys.path.insert(
    0,
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "code"),
)

from barker.sweep import find_hard_primes  # noqa: E402
from barker.two_primary import build_two_primary_table  # noqa: E402

from _common import build_labeled_graph, two_fwl_signature  # noqa: E402


def main():
    print("Loading...")
    hp = find_hard_primes(80000)
    target_primes = [d["prime"] for d in hp[:80]]
    table = build_two_primary_table(target_primes)

    C_A = (937, 1721, 11257, 16729, 18121)
    C_B = (1433, 4201, 6361, 9769, 16249)

    # Shared colour registry: the two signatures are only comparable if their
    # colours are drawn from the same table.
    registry = {}

    print(f"\nC_A [B(δ=1)] = {C_A}")
    ca, ma, ta, na = build_labeled_graph(C_A, table)
    print(f"  vertices={na}, cancels_edges={len(ca)//2}, member_edges={len(ma)//2}")
    sig_A = two_fwl_signature(ca, ma, ta, na, registry, verbose=True)
    nc_A = len(set(sig_A))

    print(f"\nC_B [A3] = {C_B}")
    cb, mb, tb, nb = build_labeled_graph(C_B, table)
    print(f"  vertices={nb}, cancels_edges={len(cb)//2}, member_edges={len(mb)//2}")
    sig_B = two_fwl_signature(cb, mb, tb, nb, registry, verbose=True)
    nc_B = len(set(sig_B))

    print(f"\n  C_A: distinct colors = {nc_A}, signature length = {len(sig_A)}")
    print(f"  C_B: distinct colors = {nc_B}, signature length = {len(sig_B)}")
    print(f"  C_A signature hash = {hash(sig_A)}")
    print(f"  C_B signature hash = {hash(sig_B)}")

    print()
    print("=" * 78)
    if sig_A == sig_B:
        print("  2-FWL with both edge types FAILS: signatures are identical.")
        print("  Genuine 2-FWL-equivalent non-isomorphic pair.")
    else:
        print("  2-FWL with both edge types SUCCEEDS: signatures differ.")
    print("=" * 78)


if __name__ == "__main__":
    main()
