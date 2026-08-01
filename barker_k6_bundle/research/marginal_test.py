#!/usr/bin/env python3
"""
marginal_test.py — compare three nulls for P(σ=0 | w=2) at (t=3) on the
1590 zero-δ minimal-covering cofactors at N=160:

  (1) uniform-pairs null:           1/5 = 0.2000   (t → ∞ limit)
  (2) iid-uniform-values null:      3/13 ≈ 0.2308  (Z/8 \\ {0} uniform, all 7 classes)
  (3) iid-empirical-marginal null:  conditions on the empirical χ-marginal
                                     extracted from the (t=3, w=2) cofactors

(3) asks: if χ-values were drawn iid from the EMPIRICAL marginal observed at
zero-δ cofactors (which is odd-dominated, contrary to the universe-uniform
Chebotarev marginal), what would P(σ=0 | w=2) be? Is the apparent 6.6 pp
deficit against (2) explained by the marginal asymmetry, or does it survive?

Reads the t=3 w=2 tuple histogram cache produced by per_depth_w2.py.
"""

from __future__ import annotations
import json
import os
import sys
from collections import Counter
from fractions import Fraction
from itertools import product


def _check(cond, msg):
    """assert that survives python -O: invariant violations must fail loudly."""
    if not cond:
        raise ValueError(msg)

CACHE_DIR = os.path.dirname(os.path.abspath(__file__))


def load_hist(N: int) -> Counter:
    path = os.path.join(CACHE_DIR, f"_per_depth_w2_t3_tuples_N{N}.json")
    with open(path) as f:
        raw = json.load(f)
    # Keys are "[v1, v2, v3, v4]" strings; parse back to sorted-tuple multisets
    return Counter({tuple(json.loads(k)): v for k, v in raw.items()})


def is_witness(a, b, mod=8):
    return (a + b) % mod == 0


def w_and_sigma(values, mod=8):
    """Return (witness_count, sigma)."""
    n = len(values)
    w = 0
    for i in range(n):
        for j in range(i + 1, n):
            if is_witness(values[i], values[j], mod):
                w += 1
    sigma = sum(values) % mod
    return w, sigma


def iid_null_sigma0_given_w2(marginal, mod=8):
    """
    P(σ=0 | w=2) under iid draws with the given marginal (dict v -> probability).
    Enumerates (ℤ/mod \\ {0})^4 exhaustively (7^4 = 2401 tuples).
    """
    p_sigma0_w2 = 0.0
    p_w2 = 0.0
    for tup in product(range(1, mod), repeat=4):
        prob = 1.0
        for v in tup:
            prob *= marginal.get(v, 0.0)
        w, sigma = w_and_sigma(tup, mod)
        if w == 2:
            p_w2 += prob
            if sigma == 0:
                p_sigma0_w2 += prob
    if p_w2 == 0:
        return None, 0.0
    return p_sigma0_w2 / p_w2, p_w2


def main():
    N = 160
    hist = load_hist(N)
    mod = 8

    # Empirical χ-marginal at (t=3, w=2 cofactors)
    total_positions = 0
    counts = Counter()
    for multiset, c in hist.items():
        for v in multiset:
            counts[v] += c
            total_positions += c
    empirical_marginal = {v: counts[v] / total_positions for v in range(1, mod)}
    uniform_marginal = {v: Fraction(1, mod - 1) for v in range(1, mod)}

    print(f"=== Empirical χ-marginal at (t=3, w=2 cofactors), N={N} ===")
    print(f"Total cofactor χ-positions: {total_positions} = 1590 × 4")
    print()
    print(f"{'value':>5} {'parity':>6} {'empirical':>10} {'uniform 1/7':>11} {'ratio':>7}")
    odd_sum = even_sum = 0
    for v in range(1, mod):
        emp = empirical_marginal[v]
        unif = float(uniform_marginal[v])
        parity = "odd" if v % 2 else "even"
        if v % 2:
            odd_sum += emp
        else:
            even_sum += emp
        print(f"  {v:>3}  {parity:>6}  {emp:>10.4f}  {unif:>11.4f}  {emp/unif:>7.3f}")
    print()
    print(f"P(χ odd | t=3, w=2 cofactor) empirical: {odd_sum:.4f}")
    print(f"P(χ odd) uniform on ℤ/8\\{{0}}:           4/7 = {4/7:.4f}")
    print(f"Odd-bias factor: {odd_sum / (4/7):.3f}")

    # Sanity: the universe-wide Chebotarev marginal at t=3 hubs is uniform.
    # The odd-dominance here is the EFFECT of the (zero-δ minimal covering + w=2)
    # conditioning, not an artifact of the universe.

    print()
    print("=== Three nulls for P(σ=0 | w=2) at t=3 ===")
    # (1) uniform-pairs
    print(f"  (1) Uniform-pairs (t→∞ limit):           0.2000")
    # (2) iid-uniform-values null
    iid_u_marg = {v: 1 / (mod - 1) for v in range(1, mod)}
    p_u, _ = iid_null_sigma0_given_w2(iid_u_marg, mod)
    print(f"  (2) iid-uniform-values (1/7 each):       {p_u:.4f}   (closed form 3/13 = {3/13:.4f})")
    # (3) iid-empirical-marginal null
    p_e, _ = iid_null_sigma0_given_w2(empirical_marginal, mod)
    print(f"  (3) iid-empirical-marginal (odd-skewed): {p_e:.4f}")
    print()

    # Empirical σ=0 rate at (t=3, w=2)
    sigma0_count = 0
    w2_count = 0
    for multiset, c in hist.items():
        # For each multiset, every ordering with this multiset has the same (w, σ)
        # only when the multiset assignment is uniform over permutations. Actually
        # (w, σ) is fully determined by the multiset alone, since w depends only
        # on which pair-sums vanish and σ is the sum. So multiset → (w, σ).
        w, sigma = w_and_sigma(list(multiset), mod)
        _check(w == 2, f"non-w=2 multiset {multiset} in histogram?")
        w2_count += c
        if sigma == 0:
            sigma0_count += c
    empirical_rate = sigma0_count / w2_count
    print(f"Empirical P(σ=0 | t=3, w=2): {sigma0_count}/{w2_count} = {empirical_rate:.4f}")

    print()
    print("=== Excess of empirical over each null ===")
    print(f"  vs (1) uniform-pairs:           {(empirical_rate - 0.20) * 100:+.2f} pp")
    print(f"  vs (2) iid-uniform-values:      {(empirical_rate - p_u) * 100:+.2f} pp")
    print(f"  vs (3) iid-empirical-marginal:  {(empirical_rate - p_e) * 100:+.2f} pp")
    print()
    print("(3) is the test the marginal hypothesis demands:")
    if abs(empirical_rate - p_e) < 0.01:
        print("    The empirical rate is within 1 pp of iid-empirical-marginal null.")
        print("    → The 6.6 pp 'deficit' against iid-uniform-values is EXPLAINED by")
        print("      the odd-dominance of the cofactor χ-marginal under minimal-covering")
        print("      conditioning. The genuine question reduces to: WHY are zero-δ")
        print("      minimal-covering cofactors at depth-3 hubs odd-dominated?")
    else:
        print(f"    The empirical exceeds iid-empirical-marginal by {(empirical_rate - p_e) * 100:+.2f} pp.")
        print("    → The odd-dominance does NOT fully explain the deficit; there is")
        print("      residual structure beyond the marginal (joint dependence among")
        print("      the four χ-values).")

    # Save summary
    summary = {
        "N": N,
        "empirical_marginal": {str(k): v for k, v in empirical_marginal.items()},
        "odd_fraction_empirical": odd_sum,
        "odd_fraction_uniform": 4 / 7,
        "nulls": {
            "uniform_pairs": 0.20,
            "iid_uniform_values": p_u,
            "iid_empirical_marginal": p_e,
        },
        "empirical_sigma0_rate": empirical_rate,
        "excess_pp": {
            "vs_uniform_pairs": (empirical_rate - 0.20) * 100,
            "vs_iid_uniform_values": (empirical_rate - p_u) * 100,
            "vs_iid_empirical_marginal": (empirical_rate - p_e) * 100,
        },
    }
    out = os.path.join(CACHE_DIR, "_marginal_test_summary.json")
    with open(out, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nSaved {out}")


if __name__ == "__main__":
    main()
