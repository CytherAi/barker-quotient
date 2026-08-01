#!/usr/bin/env python3
"""
all_odd_sigma0_stability.py — track the confound-free all-odd σ=0 rate at
(t=3, w=2) across N. Among all-odd cofactor multisets in (Z/8\\{0})^4 with
values drawn from the QNR set {1, 3, 5, 7}:

  σ=0 w=2 ⟺ multiset = (1, 3, 5, 7)

(the only way 4 odd values from {1,3,5,7} can partition into a complete
complementary pair-of-pairs).

The iid-uniform-within-odd null is computed by direct enumeration over
{1,3,5,7}^4. Within the all-odd sector the χ-marginal is empirically near-
uniform across the odd classes (each ≈ 0.21 vs 1/4 = 0.25 — close), so the
product null and the empirical-marginal null nearly coincide here. This is
the cell where Q2a — the genuine negation-closure preference — is
isolated from Q1's QR-suppression confound.

Reads `_per_depth_w2_t3_tuples_N{N}.json` for N ∈ {80, 100, 120, 140, 160}.
"""

from __future__ import annotations
import json
import math
import os
from collections import Counter
from itertools import product

CACHE_DIR = os.path.dirname(os.path.abspath(__file__))


def load_hist(N):
    path = os.path.join(CACHE_DIR, f"_per_depth_w2_t3_tuples_N{N}.json")
    if not os.path.exists(path):
        return None
    with open(path) as f:
        raw = json.load(f)
    return Counter({tuple(json.loads(k)): v for k, v in raw.items()})


def is_all_odd(multiset):
    return all(v % 2 == 1 for v in multiset)


def compute_iid_uniform_within_odd_sigma0_rate(mod=8):
    """Brute-force iid-uniform within {1,3,5,7}: enumerate 4^4 = 256 ordered
    tuples, filter w=2, count σ=0."""
    sigma0 = 0
    w2 = 0
    for tup in product([1, 3, 5, 7], repeat=4):
        w = 0
        for i in range(4):
            for j in range(i + 1, 4):
                if (tup[i] + tup[j]) % mod == 0:
                    w += 1
        if w == 2:
            w2 += 1
            if sum(tup) % mod == 0:
                sigma0 += 1
    return sigma0, w2, sigma0 / w2 if w2 else 0


def wilson_ci(x, n, z=1.96):
    if n == 0:
        return (0.0, 1.0)
    p = x / n
    z2 = z * z
    denom = 1 + z2 / n
    centre = (p + z2 / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z2 / (4 * n * n)) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


def main():
    # Closed-form iid-uniform-within-odd null
    s0_null, w2_null, null_rate = compute_iid_uniform_within_odd_sigma0_rate()
    print(f"=== iid-uniform-within-odd null (brute force on {{1,3,5,7}}^4) ===")
    print(f"  σ=0 w=2 tuples: {s0_null} / {w2_null} = {null_rate:.6f}")
    print(f"  (closed form: 24/120 = 1/5 — only multiset (1,3,5,7) gives σ=0; 4! orderings)")
    print()

    # Per-N all-odd σ=0 rate
    print(f"{'N':>4} {'all-odd σ=0':>12} {'all-odd total':>15} {'rate':>8} {'null':>8} {'excess':>10} {'95% CI':>22} {'sig?':>5}")
    print("-" * 95)
    rows = []
    for N in (80, 100, 120, 140, 160):
        hist = load_hist(N)
        if hist is None:
            continue
        all_odd_total = sum(c for ms, c in hist.items() if is_all_odd(ms))
        sigma0_count = hist.get((1, 3, 5, 7), 0)
        if all_odd_total == 0:
            continue
        rate = sigma0_count / all_odd_total
        excess = (rate - null_rate) * 100
        lo, hi = wilson_ci(sigma0_count, all_odd_total)
        sig = "*" if (lo > null_rate or hi < null_rate) else ""
        print(
            f"{N:>4} {sigma0_count:>12} {all_odd_total:>15} {rate:>8.4f} "
            f"{null_rate:>8.4f} {excess:>+8.2f} pp [{lo:.3f},{hi:.3f}] {sig:>5}"
        )
        rows.append({
            "N": N,
            "all_odd_sigma0": sigma0_count,
            "all_odd_total": all_odd_total,
            "rate": rate,
            "null_rate": null_rate,
            "excess_pp": excess,
            "ci": [lo, hi],
            "null_excluded": bool(lo > null_rate or hi < null_rate),
        })

    print()
    print("=== Sample-weighted mean excess across N with null-excluding CI ===")
    sig_rows = [r for r in rows if r["null_excluded"]]
    if sig_rows:
        tw = sum(r["all_odd_total"] for r in sig_rows)
        mean = sum(r["excess_pp"] * r["all_odd_total"] for r in sig_rows) / tw
        print(f"  N values where CI excludes null: {[r['N'] for r in sig_rows]}")
        print(f"  Total sample size: {tw}")
        print(f"  Sample-weighted excess: {mean:+.2f} pp")
    else:
        print("  No N where CI excludes null.")

    out = os.path.join(CACHE_DIR, "_all_odd_sigma0_stability.json")
    with open(out, "w") as f:
        json.dump({"null_rate": null_rate, "rows": rows}, f, indent=2)
    print(f"\nSaved {out}")


if __name__ == "__main__":
    main()
