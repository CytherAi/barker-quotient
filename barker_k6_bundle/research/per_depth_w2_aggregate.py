#!/usr/bin/env python3
"""
per_depth_w2_aggregate.py — read the per-N k=5 zero-δ enumeration caches
and emit a single JSON summary with per-(t, w) breakdown, collision rate,
and Wilson CIs for cross-N comparison.

Outputs:
    _per_depth_w2_summary.json
"""

from __future__ import annotations
import json
import math
import os
import sys
from collections import defaultdict, Counter
from fractions import Fraction
from itertools import combinations

sys.path.insert(
    0,
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "code"),
)

from barker.sweep import find_hard_primes  # noqa: E402
from barker.two_primary import build_two_primary_table  # noqa: E402

from _common import chi_sum  # noqa: E402

CACHE_DIR = os.path.dirname(os.path.abspath(__file__))


def null_w2(t: int) -> Fraction:
    return Fraction(2 ** (t - 1) - 1, 5 * 2 ** (t - 1) - 7)


def has_negation_collision(values, mod):
    n = len(values)
    for a in range(n):
        target = (-values[a]) % mod
        eq = [i for i in range(n) if i != a and values[i] == target]
        if len(eq) >= 2:
            return True
    return False


def wilson_ci(x, n, z=1.96):
    if n == 0:
        return (0.0, 1.0)
    p = x / n
    z2 = z * z
    denom = 1 + z2 / n
    centre = (p + z2 / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z2 / (4 * n * n)) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


def analyse(N: int):
    cache_file = os.path.join(CACHE_DIR, f"_per_depth_w2_cache_N{N}.json")
    if not os.path.exists(cache_file):
        return None

    hp = find_hard_primes(60000 if N <= 160 else 100000)
    primes = [d["prime"] for d in hp[:N]]
    table = build_two_primary_table(primes)
    with open(cache_file) as f:
        zd5_primes = [tuple(s) for s in json.load(f)]

    per_t_w = defaultdict(lambda: defaultdict(lambda: [0, 0, 0]))
    t3_w2_tuples = []
    for S in zd5_primes:
        for x in S:
            C = [p for p in S if p != x]
            tx = table.depth[x]
            mod = 2 ** tx
            values = [table.chi[(p, x)] for p in C]
            w = sum(
                1
                for a, b in combinations(C, 2)
                if (table.chi[(a, x)] + table.chi[(b, x)]) % mod == 0
            )
            sigma = chi_sum(x, C, table)
            collision = has_negation_collision(values, mod)
            per_t_w[tx][w][1] += 1
            if sigma == 0:
                per_t_w[tx][w][0] += 1
            if collision:
                per_t_w[tx][w][2] += 1
            if tx == 3 and w == 2:
                t3_w2_tuples.append(tuple(sorted(values)))

    out = {
        "N": N,
        "minimal_coverings": len(zd5_primes),
        "per_t_w": {},
        "t3_w2_tuple_hist": dict(Counter(map(str, t3_w2_tuples))),
    }
    for t in sorted(per_t_w):
        out["per_t_w"][str(t)] = {}
        for w in sorted(per_t_w[t]):
            s0, tot, cc = per_t_w[t][w]
            rec = {"sigma0": s0, "collision": cc, "total": tot}
            if w == 2 and tot > 0:
                null_frac = null_w2(t)
                rec["null"] = float(null_frac)
                rec["null_str"] = str(null_frac)
                rec["sigma0_rate"] = s0 / tot
                rec["collision_rate"] = cc / tot
                rec["sigma0_excess_pp"] = (s0 / tot - float(null_frac)) * 100
                rec["collision_deficit_pp"] = (cc / tot - (1 - float(null_frac))) * 100
                lo, hi = wilson_ci(s0, tot)
                rec["sigma0_ci"] = [lo, hi]
                rec["null_in_ci"] = lo <= float(null_frac) <= hi
            out["per_t_w"][str(t)][str(w)] = rec
    return out


def main():
    summary = {"universes": []}
    for N in (80, 100, 120, 140, 160):
        res = analyse(N)
        if res:
            summary["universes"].append(res)

    out_path = os.path.join(CACHE_DIR, "_per_depth_w2_summary.json")
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"Wrote {out_path}")
    print(f"Universes: {[u['N'] for u in summary['universes']]}")


if __name__ == "__main__":
    main()
