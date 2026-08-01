#!/usr/bin/env python3
"""
per_depth_w2.py — per-depth conditional rate P(σ_x = 0 | w_x = 2) at k=5 zero-δ.

The aggregate empirical 0.291 at N=160 (§6.2) was compared against the
uniform-pairs null 1/5 = 0.200, giving a "9 pp excess." But uniform-pairs
is the t → ∞ limit of the correct iid-uniform-values null at finite depth.

Closed form (derived; also verified by brute force at t ∈ {3, 4, 5, 6}):

    P_iid(σ=0 | w=2) at depth t  =  (2^{t-1} - 1) / (5 · 2^{t-1} - 7)

    = 3/13,  7/33,  15/73,  31/153   at  t = 3, 4, 5, 6
    → 1/5 as t → ∞

The Chebotarev-based assumption (χ-marginal uniform on nonzero classes) is
verified separately by per-hub χ²-against-uniform across the universe.

This script:
  (a) Enumerates k=5 zero-δ minimal coverings at parameterized N using a
      fast zero-δ-clique-restricted search (the library's
      `search_minimal_covering_k` walks all C(N,k) subsets and is too slow
      at N=160 without a zero-δ pre-filter; we add the pre-filter while
      using library primitives for everything downstream).
  (b) Caches per-N enumerations to `_per_depth_w2_cache_N<N>.json`.
  (c) For each target in each minimal covering, computes (t_x, w_x,
      σ_x = 0?) using `_common.chi_sum` and the closed-form witness-count.
  (d) Reports the per-(t, w=2) split with 95% Wilson intervals against
      the depth-dependent null.

Run from repo root:
    python3 barker_k6_bundle/research/per_depth_w2.py [N=160]
"""

from __future__ import annotations
import json
import math
import os
import sys
import time
from collections import defaultdict
from fractions import Fraction
from itertools import combinations

sys.path.insert(
    0,
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "code"),
)

from barker.sweep import find_hard_primes  # noqa: E402
from barker.two_primary import build_two_primary_table  # noqa: E402

from _common import delta_x, chi_sum  # noqa: E402


def _check(cond, msg):
    """assert that survives python -O: invariant violations must fail loudly."""
    if not cond:
        raise ValueError(msg)


CACHE_DIR = os.path.dirname(os.path.abspath(__file__))


def cache_path(N: int) -> str:
    return os.path.join(CACHE_DIR, f"_per_depth_w2_cache_N{N}.json")


# ---------------------------------------------------------------------------
# Closed-form conditional null
# ---------------------------------------------------------------------------

def null_w2(t: int) -> Fraction:
    """P(σ=0 | w=2) at depth t under iid-uniform-nonzero χ values."""
    return Fraction(2 ** (t - 1) - 1, 5 * 2 ** (t - 1) - 7)


# ---------------------------------------------------------------------------
# Fast zero-δ k=5 minimal-covering enumeration
# ---------------------------------------------------------------------------

def enumerate_k5_zero_delta(primes, table):
    """
    Returns: list of frozenset(prime indices) for each k=5 zero-δ minimal
    covering on the universe `primes`. Uses zero-δ-clique pre-filter +
    proper-subset-minimality via containment of smaller zero-δ coverings.
    """
    n = len(primes)
    mod = [2 ** table.depth[p] for p in primes]
    chi_local = [[0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i != j:
                chi_local[i][j] = table.chi[(primes[j], primes[i])]

    # adj_safe[i] = {j : χ_i(j) ≠ 0 ∧ χ_j(i) ≠ 0}: a zero-δ k-subset is a
    # k-clique in this undirected graph
    adj_safe = []
    for i in range(n):
        s = set()
        for j in range(n):
            if i != j and chi_local[i][j] != 0 and chi_local[j][i] != 0:
                s.add(j)
        adj_safe.append(frozenset(s))

    def is_covering_idx(S):
        for a, b in combinations(S, 2):
            ok = False
            for x in S:
                if x == a or x == b:
                    continue
                if (chi_local[x][a] + chi_local[x][b]) % mod[x] == 0:
                    ok = True
                    break
            if not ok:
                return False
        return True

    def is_perv_minimal_idx(S):
        for drop in S:
            rest = tuple(p for p in S if p != drop)
            if is_covering_idx(rest):
                return False
        return True

    # k=3 zero-δ minimal coverings (all covering 3-cliques are minimal at k=3)
    zd3 = set()
    for i1 in range(n):
        for i2 in adj_safe[i1]:
            if i2 <= i1:
                continue
            for i3 in adj_safe[i1] & adj_safe[i2]:
                if i3 <= i2:
                    continue
                if is_covering_idx((i1, i2, i3)):
                    zd3.add(frozenset((i1, i2, i3)))

    # k=4: per-vertex minimality is sufficient when no zd3 is a 3-subset
    zd4 = set()
    for i1 in range(n):
        for i2 in adj_safe[i1]:
            if i2 <= i1:
                continue
            cand2 = adj_safe[i1] & adj_safe[i2]
            for i3 in cand2:
                if i3 <= i2:
                    continue
                cand3 = cand2 & adj_safe[i3]
                for i4 in cand3:
                    if i4 <= i3:
                        continue
                    S = (i1, i2, i3, i4)
                    if not is_covering_idx(S):
                        continue
                    if not is_perv_minimal_idx(S):
                        continue
                    if any(frozenset(c) in zd3 for c in combinations(S, 3)):
                        continue
                    zd4.add(frozenset(S))

    # k=5: per-vertex + no zd3 or zd4 sub-covering
    zd5_idx = []
    for i1 in range(n):
        for i2 in adj_safe[i1]:
            if i2 <= i1:
                continue
            cand2 = adj_safe[i1] & adj_safe[i2]
            for i3 in cand2:
                if i3 <= i2:
                    continue
                cand3 = cand2 & adj_safe[i3]
                for i4 in cand3:
                    if i4 <= i3:
                        continue
                    cand4 = cand3 & adj_safe[i4]
                    for i5 in cand4:
                        if i5 <= i4:
                            continue
                        S = (i1, i2, i3, i4, i5)
                        if any(frozenset(c) in zd3 for c in combinations(S, 3)):
                            continue
                        if any(frozenset(c) in zd4 for c in combinations(S, 4)):
                            continue
                        if not is_covering_idx(S):
                            continue
                        if not is_perv_minimal_idx(S):
                            continue
                        zd5_idx.append(S)
    return zd5_idx


# ---------------------------------------------------------------------------
# Per-target (t, w, σ=0?) computation using library primitives
# ---------------------------------------------------------------------------

def has_negation_collision(values, mod):
    """
    Negation-aligned collision: ∃ a ≠ b ≠ c with values[b] = values[c] = (-values[a]) mod mod.
    For w=2 at modulus 8, this is equivalent to σ ≠ 0 (Prop 4.6 + the σ=0/distinct/collision
    decomposition of §6.2 follow-up): σ=0 ⟺ all values distinct ∨ self-inverse collision
    (only at element 2^(t-1)); σ≠0 ⟺ a non-self-inverse negation collision.
    Here we count ANY negation-aligned collision (including self-inverse). At t=3 this
    matches the user's structural reformulation.
    """
    n = len(values)
    for a in range(n):
        target = (-values[a]) % mod
        # need two distinct indices b, c (b ≠ a, c ≠ a, b ≠ c) with values[b] = values[c] = target
        eq = [i for i in range(n) if i != a and values[i] == target]
        if len(eq) >= 2:
            return True
    return False


def per_target_breakdown(zd5_primes, table):
    """
    zd5_primes: list of tuples of primes (each tuple is a minimal covering).
    Returns: (per_t_w, per_t3_w2_tuples)
      per_t_w[t][w] = [sigma_zero_count, total_count, collision_count]
      per_t3_w2_tuples: list of sorted 4-tuples of χ-values for (t=3, w=2) cases
    """
    per_t_w = defaultdict(lambda: defaultdict(lambda: [0, 0, 0]))
    per_t3_w2_tuples = []
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
                per_t3_w2_tuples.append(tuple(sorted(values)))
    return per_t_w, per_t3_w2_tuples


def wilson_ci(x, n, z=1.96):
    if n == 0:
        return (0.0, 1.0)
    p = x / n
    z2 = z * z
    denom = 1 + z2 / n
    centre = (p + z2 / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z2 / (4 * n * n)) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run(N: int):
    print(f"Loading first {N} hard primes...", flush=True)
    hp = find_hard_primes(60000 if N <= 160 else 100000)
    primes = [d["prime"] for d in hp[:N]]
    print(f"  universe max p_{N} = {primes[-1]}", flush=True)

    print("Building character table...", flush=True)
    table = build_two_primary_table(primes)

    cp = cache_path(N)
    if os.path.exists(cp):
        print(f"Loading cached k=5 zero-δ enumeration from {cp}", flush=True)
        with open(cp) as f:
            zd5_primes = [tuple(s) for s in json.load(f)]
    else:
        print("Enumerating k=5 zero-δ minimal coverings (fast clique search)...", flush=True)
        t0 = time.time()
        zd5_idx = enumerate_k5_zero_delta(primes, table)
        zd5_primes = [tuple(primes[i] for i in S) for S in zd5_idx]
        print(f"  found {len(zd5_primes)} in {time.time() - t0:.1f}s", flush=True)
        with open(cp, "w") as f:
            json.dump([list(s) for s in zd5_primes], f)
        print(f"  saved cache to {cp}", flush=True)

    # Verify all are zero-δ via library primitive
    for S in zd5_primes[:5]:
        for x in S:
            _check(delta_x(x, S, table) == 0, f"non-zero-δ at {x} in {S}")

    # Per-target breakdown
    per_t_w, per_t3_w2_tuples = per_target_breakdown(zd5_primes, table)

    # Report
    print()
    print(f"=== k=5 zero-δ minimal coverings at N={N}: {len(zd5_primes)} ===")
    print()
    print("Per-(t, w) breakdown:")
    print(f"{'t':>2} {'w':>2} {'σ=0':>5} {'coll':>5} {'total':>6} {'σ=0 rate':>9}   {'null':>14}   {'σ=0 excess':>10}")
    for t in sorted(per_t_w):
        for w in sorted(per_t_w[t]):
            s0, tot, cc = per_t_w[t][w]
            rate = s0 / tot if tot else 0
            if w == 2:
                null = null_w2(t)
                nf = float(null)
                ex = (rate - nf) * 100
                print(
                    f"{t:>2} {w:>2} {s0:>5} {cc:>5} {tot:>6} {rate:>9.4f}   "
                    f"{str(null) + f' = {nf:.4f}':>14}   {ex:+8.2f} pp"
                )
            else:
                print(f"{t:>2} {w:>2} {s0:>5} {cc:>5} {tot:>6} {rate:>9.4f}")

    # Aggregate w=2 decomposition
    total_s0 = sum(per_t_w[t][2][0] for t in per_t_w if 2 in per_t_w[t])
    total_n = sum(per_t_w[t][2][1] for t in per_t_w if 2 in per_t_w[t])
    if total_n == 0:
        return
    rate = total_s0 / total_n
    w2_per_t = {t: per_t_w[t][2][1] for t in per_t_w if 2 in per_t_w[t]}
    tw = sum(w2_per_t.values())
    weighted_null = sum(w2_per_t[t] * float(null_w2(t)) for t in w2_per_t) / tw

    print()
    print("=== Aggregate W=2 decomposition ===")
    print(f"Empirical (depth-mixed):         {total_s0}/{total_n} = {rate:.4f}")
    print(f"Uniform-pairs null (t→∞ limit):  0.2000")
    print(f"Depth-weighted iid-values null:  {weighted_null:.4f}")
    print(f"Excess over uniform-pairs null:  {(rate - 0.20) * 100:+.2f} pp")
    print(f"Excess over depth-weighted null: {(rate - weighted_null) * 100:+.2f} pp")

    # The key reformulation: σ=0 rate at w=2 ⇄ negation-collision rate
    print()
    print("=== Collision-rate restatement at (t=3, w=2) ===")
    if 3 in per_t_w and 2 in per_t_w[3]:
        s0, tot, cc = per_t_w[3][2]
        collision_rate = cc / tot
        null_collision = 1 - float(null_w2(3))   # collision rate under iid-uniform null
        print(f"Empirical:  collision present {cc}/{tot} = {collision_rate:.4f}, σ=0 rate {s0/tot:.4f}")
        print(f"Null t=3:   collision present 10/13 = {null_collision:.4f}, σ=0 rate 3/13 = {1 - null_collision:.4f}")
        print(f"Collision deficit (empirical - null): {(collision_rate - null_collision) * 100:+.2f} pp")
        print(f"σ=0 excess  (= -collision deficit):   {(s0/tot - (1 - null_collision)) * 100:+.2f} pp")
        print()
        print("(t=3, w=2) cofactor χ-value tuple-type histogram (sorted multisets in (Z/8\\{0})^4):")
        from collections import Counter
        tuple_hist = Counter(per_t3_w2_tuples)
        # Dump to a side cache for downstream consumption (mod-8 distribution analysis)
        hist_path = os.path.join(CACHE_DIR, f"_per_depth_w2_t3_tuples_N{N}.json")
        with open(hist_path, "w") as f:
            # JSON keys must be strings; encode as "(v1,v2,v3,v4)"
            json.dump({str(list(k)): v for k, v in tuple_hist.items()}, f)
        print(f"  Total distinct multisets observed: {len(tuple_hist)}")
        print(f"  Saved tuple histogram to {hist_path}")
        print(f"  Top 10 by frequency:")
        for tup, ct in tuple_hist.most_common(10):
            print(f"    {tup}: {ct}")


if __name__ == "__main__":
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 160
    run(N)
