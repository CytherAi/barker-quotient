#!/usr/bin/env python3
"""
substructure_baseline.py — permutation test for the V-substructure
clustering of the featured combinatorial objects.

Question: do the 21 primes appearing in the paper's named extremal sets
(S*, the discrimination-depth singleton, the B0 quadruple, the B1
five-set) form a denser V-subgraph among themselves than a size-matched
random subset of the first 80 hard primes?

Method:
  1. Compute the internal V-edge density of the 21 featured primes —
     directed V-edges (a, b) with chi_a(b) = 0, normalised by k(k-1).
  2. Sample N random 21-element subsets of the universe; compute the
     same density for each; report the empirical distribution.
  3. Position the featured-set density in that distribution.
  4. Sanity controls: swap 17881 (the S* hub) with each of {881, 1913,
     11113} — the three non-featured primes with the highest
     featured-fraction at comparable in-degree — and report the swapped
     subset's density to test single-vertex robustness.

Produces the numbers reported in §5.8 (Remark 5.6) and Figure 5.2's
substructure-level evidence.

Scope: established on the first 80 hard primes; no claim about wider
universes (see Question 6.4 in §6).

Run from repo root:
    python3 barker_k6_bundle/research/substructure_baseline.py
"""

import os
import random
import sys

sys.path.insert(
    0,
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "code"),
)

from barker.sweep import find_hard_primes  # noqa: E402
from barker.two_primary import build_two_primary_table  # noqa: E402


S_STAR = (17881, 1801, 14537, 13417, 18121, 18521)
SINGLETON_A = (1433, 4201, 6361, 9769, 16249)
SINGLETON_B = (937, 1721, 11257, 16729, 18121)
B0_QUAD = (337, 937, 1433, 1721)
B1_FIVE = (4297, 4409, 5689, 6553, 7753)
CONTROL_PRIMES = (881, 1913, 11113)  # non-featured comparable in-degree


def v_edge_count(subset, table):
    """Count ordered directed V-edges (a, b) with a != b, both in subset,
    chi_a(b) = 0 (equivalently b in V_a)."""
    n = 0
    for a in subset:
        for b in subset:
            if a == b:
                continue
            if table.chi[(b, a)] == 0:
                n += 1
    return n


def main():
    print("Loading first 80 hard primes...", flush=True)
    hp = find_hard_primes(80000)
    target_primes = [d["prime"] for d in hp[:80]]
    print("Building character table...", flush=True)
    table = build_two_primary_table(target_primes)

    featured = sorted(set(S_STAR) | set(SINGLETON_A) | set(SINGLETON_B)
                      | set(B0_QUAD) | set(B1_FIVE))
    n = len(featured)
    max_edges = n * (n - 1)

    feat_edges = v_edge_count(featured, table)
    feat_density = feat_edges / max_edges
    univ_edges = v_edge_count(target_primes, table)
    univ_density = univ_edges / (80 * 79)

    print()
    print("=" * 78)
    print("V-substructure permutation test")
    print("=" * 78)
    print(f"Featured set: {n} primes")
    print(f"  internal V-edges:  {feat_edges} of {max_edges} possible")
    print(f"  density:           {feat_density*100:.2f}%")
    print()
    print(f"Universe (n=80):")
    print(f"  V-edges:           {univ_edges} of {80*79} possible")
    print(f"  density:           {univ_density*100:.2f}%")
    print(f"  ratio (feat/univ): {feat_density/univ_density:.2f}x")

    # Permutation test
    random.seed(42)
    n_trials = 5000
    print()
    print(f"Permutation test ({n_trials} random {n}-subsets, seed=42):", flush=True)
    densities = []
    for _ in range(n_trials):
        s = random.sample(target_primes, n)
        densities.append(v_edge_count(s, table) / max_edges)
    densities.sort()

    mean = sum(densities) / n_trials
    median = densities[n_trials // 2]
    p95 = densities[int(0.95 * n_trials)]
    p99 = densities[int(0.99 * n_trials)]
    p999 = densities[int(0.999 * n_trials)] if n_trials >= 1000 else max(densities)
    p_above = sum(1 for d in densities if d >= feat_density) / n_trials

    print(f"  mean random density:   {mean*100:.2f}%")
    print(f"  median:                {median*100:.2f}%")
    print(f"  95th percentile:       {p95*100:.2f}%")
    print(f"  99th percentile:       {p99*100:.2f}%")
    print(f"  99.9th percentile:     {p999*100:.2f}%")
    print(f"  P(random >= featured): {p_above*100:.2f}%")

    # Swap controls
    print()
    print("Swap controls — replace 17881 with a non-featured comparable prime")
    print(f"(featured baseline density: {feat_density*100:.2f}%):")
    for c in CONTROL_PRIMES:
        new = sorted((set(featured) - {17881}) | {c})
        ed = v_edge_count(new, table)
        d = ed / max_edges
        print(f"  17881 -> {c}:  density {d*100:.2f}%  ({ed} edges)")

    print()
    print("Conclusion (this enumeration):")
    if p_above < 0.01:
        print(f"  Featured V-density at the {(1-p_above)*100:.1f}-th percentile of random;")
        print(f"  clustering is significant, not network density. The substructure is a")
        print(f"  property of the 21 featured primes as constituted in this paper, not")
        print(f"  a prediction about future extremal-object placement.")
    else:
        print(f"  Featured V-density is within the random-subset distribution;")
        print(f"  no substructure-level clustering claim is supported.")


if __name__ == "__main__":
    main()
