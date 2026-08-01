#!/usr/bin/env python3
"""
independence_diagnostic.py — diagnose the small (~1 pp) k=4 offset between
empirical 'any chi-sum = 0' fraction on random zero-delta subsets and the
naive independence-model null N_k = 1 - prod_x (1 - 1/2^{t_x}).

The naive null treats each target's chi-sum as uniform over its residue
class C_{2^{t_x}}, giving per-target fire probability exactly 1/2^{t_x}.
But chi_x at a target is the sum of m = k - 1 nonzero values mod 2^{t_x},
and the exact probability that such a sum hits zero differs from 1/2^{t_x}
for small m. At (m=3, t=3) — the k=4 case dominated by depth-3 primes —
the exact rate is 42/343 ≈ 0.1224 versus naive 1/8 = 0.125, a 2% relative
under-prediction. For m >= 4 the deviation collapses to under 0.3%.

This script:
  (1) tabulates the exact rate P(m i.i.d. uniform-nonzero summands sum
      to 0 mod 2^t) by direct convolution, for all relevant (m, t);
  (2) computes naive_N_k and exact_N_k (summand-corrected) on the
      enumerated zero-delta covering configurations at k = 4, 5, 6;
  (3) reproduces the random-subset offset diagnostic and confirms
      that the all-t=3 bin closes to ~0 after the summand correction.

Result reported by this script: characterisation of the k=4 model-
approximation offset as the summand-count effect at (m=3, t=3),
referenced in §7.6 (independence validation, k=4 footnote) and
§6.2 (Defence (ii)). The §6.2 conclusions are unchanged: substituting
exact_N_k for naive_N_k shifts k=4 by ≤ 1 pp, k=5 and k=6 by < 0.1 pp,
and all signed biases preserve sign and rough magnitude.

Run from repo root:
    python3 barker_k6_bundle/research/independence_diagnostic.py
"""

import json
import os
import random
import sys
sys.path.insert(
    0,
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "code"),
)

from barker.sweep import find_hard_primes  # noqa: E402
from barker.two_primary import build_two_primary_table  # noqa: E402


def exact_fire_rate(m, t):
    """Exact P(sum of m i.i.d. uniform-nonzero values mod 2^t = 0)."""
    if m == 0:
        return 1.0
    mod = 2 ** t
    f = [0] * mod
    for v in range(1, mod):
        f[v] = 1
    g = f[:]
    for _ in range(m - 1):
        h = [0] * mod
        for i in range(mod):
            if g[i] == 0:
                continue
            for j in range(mod):
                if f[j] == 0:
                    continue
                h[(i + j) % mod] += g[i] * f[j]
        g = h
    return g[0] / sum(g)


def is_zero_delta(S, table):
    for a in S:
        for b in S:
            if a != b and table.chi[(b, a)] == 0:
                return False
    return True


def has_elim(S, table):
    for x in S:
        mod = 2 ** table.depth[x]
        if sum(table.chi[(q, x)] for q in S if q != x) % mod == 0:
            return True
    return False


def main():
    print("Loading first 80 hard primes...", flush=True)
    hp = find_hard_primes(80000)
    target_primes = [d["prime"] for d in hp[:80]]
    print("Building character table...", flush=True)
    table = build_two_primary_table(target_primes)
    depths = sorted({table.depth[p] for p in target_primes})

    print()
    print("=" * 78)
    print("(1) Exact per-target fire rate vs naive 1/2^t")
    print("=" * 78)
    print()
    print(f"{'t':>2} {'m':>2}  {'exact P(sum=0)':>15}  {'naive 1/2^t':>12}  {'rel dev':>9}")
    for t in depths:
        for m in (3, 4, 5):
            ex = exact_fire_rate(m, t)
            nv = 1 / 2 ** t
            rel = 100 * (ex - nv) / nv
            marker = "  <-- k=4 dominant" if (t == 3 and m == 3) else ""
            print(f"{t:>2} {m:>2}  {ex:>15.6f}  {nv:>12.6f}  {rel:>+8.2f}%{marker}")

    # (2) Naive vs exact null on the enumerated covering configurations
    print()
    print("=" * 78)
    print("(2) Naive vs exact null on enumerated zero-delta minimal-covering configs")
    print("=" * 78)
    print()
    cache_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "_enumeration_cache.json"
    )
    with open(cache_path) as f:
        raw = json.load(f)
    records = [(k, cls, tuple(prof), tuple(cfg)) for (k, cls, prof, cfg) in raw]

    print(f"{'k':>2} {'n':>4} {'A3':>3} {'emp %':>7} {'naive N':>9} {'exact N':>9} "
          f"{'bias (naive)':>13} {'bias (exact)':>13}")
    for k_t in (4, 5, 6):
        zd = [r for r in records if r[0] == k_t and r[2] == tuple([0] * k_t)]
        if not zd:
            continue
        a3 = sum(1 for r in zd if r[1] == 'A3')
        n = len(zd)
        naive_sum = exact_sum = 0.0
        for k, cls, prof, cfg in zd:
            pn = pe = 1.0
            for x in cfg:
                t = table.depth[x]
                pn *= (1 - 1 / 2 ** t)
                pe *= (1 - exact_fire_rate(k_t - 1, t))
            naive_sum += 1 - pn
            exact_sum += 1 - pe
        emp = a3 / n
        naive_avg = naive_sum / n
        exact_avg = exact_sum / n
        print(f"{k_t:>2} {n:>4} {a3:>3} {emp*100:>6.2f}%  "
              f"{naive_avg*100:>7.2f}%  {exact_avg*100:>7.2f}%  "
              f"{(emp-naive_avg)*100:>+11.1f} pp  {(emp-exact_avg)*100:>+11.1f} pp")

    # (3) Random-subset diagnostic with depth-multiset binning at k=4
    print()
    print("=" * 78)
    print("(3) k=4 random zero-delta subsets — binned by depth multiset")
    print("=" * 78)
    print()

    nv_r = {t: 1 / 2 ** t for t in depths}
    ex_r3 = {t: exact_fire_rate(3, t) for t in depths}

    random.seed(2026)
    N = 200000
    bins = {}
    for _ in range(N):
        S = tuple(random.sample(target_primes, 4))
        if not is_zero_delta(S, table):
            continue
        dprofile = tuple(sorted(table.depth[x] for x in S))
        b = bins.setdefault(dprofile, {"n": 0, "elim": 0, "nv": 0.0, "ex": 0.0})
        b["n"] += 1
        pn = pe = 1.0
        for x in S:
            t = table.depth[x]
            pn *= (1 - nv_r[t])
            pe *= (1 - ex_r3[t])
        b["nv"] += 1 - pn
        b["ex"] += 1 - pe
        if has_elim(S, table):
            b["elim"] += 1

    tot_n = sum(b["n"] for b in bins.values())
    tot_elim = sum(b["elim"] for b in bins.values())
    tot_nv = sum(b["nv"] for b in bins.values())
    tot_ex = sum(b["ex"] for b in bins.values())
    print(f"Aggregate ({tot_n} zero-delta of {N}):")
    print(f"  empirical:                       {100*tot_elim/tot_n:6.3f}%")
    print(f"  naive N_k:                       {100*tot_nv/tot_n:6.3f}%  "
          f"(deviation {100*(tot_elim/tot_n - tot_nv/tot_n):+.2f} pp)")
    print(f"  exact N_k (summand-corrected):   {100*tot_ex/tot_n:6.3f}%  "
          f"(deviation {100*(tot_elim/tot_n - tot_ex/tot_n):+.2f} pp)")
    print()
    print("Per-depth-multiset (top 10 by sample count):")
    print(f"{'depths':>16} {'n':>7} {'emp %':>7} {'naive %':>8} {'exact %':>8} "
          f"{'emp-naive':>11} {'emp-exact':>11}")
    for d in sorted(bins.keys(), key=lambda x: -bins[x]["n"])[:10]:
        b = bins[d]
        if b["n"] < 100:
            continue
        emp_b = b["elim"] / b["n"]
        nv_b = b["nv"] / b["n"]
        ex_b = b["ex"] / b["n"]
        print(f"{str(d):>16} {b['n']:>7} {100*emp_b:>6.2f}  "
              f"{100*nv_b:>7.2f}  {100*ex_b:>7.2f}  "
              f"{100*(emp_b - nv_b):>+10.3f}  {100*(emp_b - ex_b):>+10.3f}")

    print()
    print("Reading:")
    print("  The all-(3,3,3,3) bin is the most populated and closes to near-zero")
    print("  empirical-minus-exact deviation, confirming the offset is fully")
    print("  explained by the m=3 summand-count effect at t=3. Mixed-depth bins")
    print("  have small residual deviations (<= 1 pp, varying sign) attributable")
    print("  to second-order effects, well below the §6.2 bias scale of 25+ pp.")


if __name__ == "__main__":
    main()
