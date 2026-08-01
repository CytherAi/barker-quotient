#!/usr/bin/env python3
"""
depth_profile_cut.py — the one admissible test for the stalled compression
of the transversal excess.

The proof of "minimality induces transversal bias" reduces, via the cofactor
cycle theorem (Theorem B), to: does the chordless 4-cycle constraint on the
all-QNR cofactor force the hub-incident χ_x-class-word toward the balanced
AABB-with-complementary-fill pattern?

The bridge is Lemma 2.1 (parity symmetry): χ_p(q) ≡ χ_q(p) (mod 2). The
cycle constrains intra-cofactor edges (χ_{p_i}(p_{i+1})); the transversal
is a hub-incident property (χ_x(p_i)). Parity symmetry couples them
pairwise mod 2, but the transversal target σ_x = 0 (mod 8) needs the full
2-adic depth at x. Mod-2 reciprocity discards the higher digits.

The proof stalls *informatively*: the residual is predicted to correlate
with the cofactor depth profile. If the cofactor primes are themselves
t = 3, parity symmetry nearly closes the loop and the residual is a mod-8
reciprocity-closure fact (theorem-reachable). If the cofactor includes
high-depth primes (t ≥ 4), the discarded high digits give the excess room
to hide — predicted to weaken or invert.

Test: among (t_x = 3, w_x = 2, all-QNR cofactor) targets at N = 160,
stratify by cofactor depth profile and compare σ=0 rate against 1/5.

Reads `_per_depth_w2_cache_N160.json`.
"""

from __future__ import annotations
import json
import math
import os
import sys
from collections import defaultdict, Counter
from itertools import combinations

sys.path.insert(
    0,
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "code"),
)

from barker.sweep import find_hard_primes  # noqa: E402
from barker.two_primary import build_two_primary_table  # noqa: E402

from _common import chi_sum  # noqa: E402

CACHE_DIR = os.path.dirname(os.path.abspath(__file__))


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
    N = 160
    cache_file = os.path.join(CACHE_DIR, f"_per_depth_w2_cache_N{N}.json")
    if not os.path.exists(cache_file):
        print(f"Missing cache: {cache_file}")
        sys.exit(1)

    hp = find_hard_primes(60000)
    primes = [d["prime"] for d in hp[:N]]
    table = build_two_primary_table(primes)
    with open(cache_file) as f:
        zd5_primes = [tuple(s) for s in json.load(f)]

    # Collect all-QNR w=2 targets at t_x=3
    targets = []
    for S in zd5_primes:
        for x in S:
            if table.depth[x] != 3:
                continue
            C = [p for p in S if p != x]
            mod = 8
            values = [table.chi[(p, x)] for p in C]
            # check all-QNR (all odd)
            if not all(v % 2 == 1 for v in values):
                continue
            w = sum(
                1
                for a, b in combinations(C, 2)
                if (table.chi[(a, x)] + table.chi[(b, x)]) % mod == 0
            )
            if w != 2:
                continue
            sigma = chi_sum(x, C, table)
            cofactor_depths = tuple(sorted(table.depth[p] for p in C))
            targets.append({
                "x": x,
                "S": tuple(sorted(S)),
                "cofactor_depths": cofactor_depths,
                "sigma0": sigma == 0,
                "multiset": tuple(sorted(values)),
            })

    print(f"Total (t_x=3, w_x=2, all-QNR) targets at N={N}: {len(targets)}")
    sigma0_total = sum(1 for t in targets if t["sigma0"])
    print(f"  σ=0 (= multiset (1,3,5,7)): {sigma0_total}")
    print(f"  σ≠0 (= all-odd collisions): {len(targets) - sigma0_total}")
    print(f"  Overall rate: {sigma0_total / len(targets):.4f}")
    print(f"  vs 1/5 null: {(sigma0_total / len(targets) - 0.2) * 100:+.2f} pp")
    print()

    # Stratify by cofactor depth profile
    # The binary cut the obstruction predicts: cofactor all-depth-3 vs at-least-one-higher
    strata = {
        "all-t=3 cofactor": [t for t in targets if t["cofactor_depths"] == (3, 3, 3, 3)],
        "mixed-depth cofactor (≥1 of t≥4)": [t for t in targets if t["cofactor_depths"] != (3, 3, 3, 3)],
    }

    print("=== Depth-profile stratification: predicted by the proof obstruction ===")
    print(f"{'stratum':<36} {'n':>5} {'σ=0':>5} {'rate':>8} {'vs 1/5':>10} {'95% CI':>20}")
    print("-" * 95)
    for name, group in strata.items():
        n = len(group)
        s0 = sum(1 for t in group if t["sigma0"])
        rate = s0 / n if n else 0
        lo, hi = wilson_ci(s0, n)
        excess = (rate - 0.2) * 100 if n else 0
        sig = "*" if (lo > 0.2 or hi < 0.2) else ""
        print(f"{name:<36} {n:>5} {s0:>5} {rate:>8.4f} {excess:>+8.2f} pp [{lo:.3f},{hi:.3f}] {sig}")
    print()

    # Finer stratification by exact cofactor depth profile
    by_profile = defaultdict(lambda: [0, 0])
    for t in targets:
        by_profile[t["cofactor_depths"]][1] += 1
        if t["sigma0"]:
            by_profile[t["cofactor_depths"]][0] += 1

    print("=== Per-cofactor-depth-profile breakdown (sorted by n) ===")
    print(f"{'cofactor depths':<22} {'n':>5} {'σ=0':>5} {'rate':>8} {'vs 1/5':>10} {'95% CI':>20}")
    print("-" * 78)
    for profile in sorted(by_profile.keys(), key=lambda k: -by_profile[k][1]):
        s0, n = by_profile[profile]
        rate = s0 / n
        lo, hi = wilson_ci(s0, n)
        excess = (rate - 0.2) * 100
        sig = "*" if (lo > 0.2 or hi < 0.2) else ""
        print(f"{str(profile):<22} {n:>5} {s0:>5} {rate:>8.4f} {excess:>+8.2f} pp [{lo:.3f},{hi:.3f}] {sig}")

    # Save summary
    out = {
        "N": N,
        "n_targets": len(targets),
        "overall_rate": sigma0_total / len(targets) if targets else 0,
        "overall_excess_pp": (sigma0_total / len(targets) - 0.2) * 100 if targets else 0,
        "binary_stratification": {
            name: {
                "n": len(group),
                "sigma0": sum(1 for t in group if t["sigma0"]),
                "rate": sum(1 for t in group if t["sigma0"]) / len(group) if group else 0,
                "excess_pp": (sum(1 for t in group if t["sigma0"]) / len(group) - 0.2) * 100 if group else 0,
                "ci": list(wilson_ci(sum(1 for t in group if t["sigma0"]), len(group))),
            }
            for name, group in strata.items()
        },
        "per_profile": {
            str(profile): {"sigma0": s0, "n": n, "rate": s0 / n if n else 0}
            for profile, (s0, n) in by_profile.items()
        },
    }
    out_path = os.path.join(CACHE_DIR, "_depth_profile_cut.json")
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"\nSaved {out_path}")

    print()
    print("=== Pre-registered reading of the result ===")
    all_t3 = strata["all-t=3 cofactor"]
    mixed = strata["mixed-depth cofactor (≥1 of t≥4)"]
    if all_t3 and mixed:
        all_t3_rate = sum(1 for t in all_t3 if t["sigma0"]) / len(all_t3)
        mixed_rate = sum(1 for t in mixed if t["sigma0"]) / len(mixed)
        if all_t3_rate > 0.20 + 0.04 and mixed_rate < all_t3_rate - 0.03:
            print("  Outcome A — predicted direction: excess concentrates in all-t=3 cofactors.")
            print("    The residual is a mod-8 reciprocity-closure fact at the cycle level.")
            print("    The brick: a theorem on the 4-cycle pushed to full 2-adic depth.")
        elif abs(all_t3_rate - mixed_rate) < 0.02:
            print("  Outcome B — flat: stratification does not organize the excess.")
            print("    The fixed point asserts itself. The paper as written is the paper that ships,")
            print("    strengthened by having resisted the next admissible structural cut.")
        else:
            print("  Outcome C — mixed/inverted: the excess lives where the obstruction predicts")
            print("    it would hide — in the discarded high digits of mixed-depth cycles.")
            print("    Genuinely harder object; do not chase further here.")
        print()
        print(f"  Empirical:  all-t=3 rate = {all_t3_rate:.4f}, mixed rate = {mixed_rate:.4f}")
        print(f"  Difference: {(all_t3_rate - mixed_rate) * 100:+.2f} pp")


if __name__ == "__main__":
    main()
