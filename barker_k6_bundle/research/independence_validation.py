#!/usr/bin/env python3
"""
independence_validation.py — empirical validation of the independence
model underlying the null A3 fraction N_k of §6.2.

The null formula

    N(S) = 1 - prod_{x in S} (1 - 1/2^{t_x})

is the probability that at least one target's chi-sum vanishes under
two assumptions:
  (i)  each target's chi-sum is approximately uniform over its residue
       class C_{2^{t_x}};
  (ii) the chi-sums at different targets are approximately independent.

Assumption (ii) is non-trivial: chi-sums at different targets share
the same underlying primes evaluated under different characters. This
script tests (i) + (ii) jointly by comparing the per-config N(S)
formula against the empirical "any chi-sum vanishes" fraction on
UNCONSTRAINED random zero-delta k-subsets (no covering constraint
imposed) of the first 80 hard primes.

If the independence model is approximately valid in the unconstrained
case, the deviation measured in §6.2 between empirical A3 fractions
on minimal *covering* zero-delta configurations and N_k is genuinely
attributable to the covering constraint, not to mis-specification of
the independence model.

Result reported by this script is the empirical validation of N_k
referenced in §6.2 (Defence (ii)) and in empirical_observations.md
item 5.

Run from repo root:
    python3 barker_k6_bundle/research/independence_validation.py
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

N_SAMPLES = 200000
SEED = 2026


def is_zero_delta(S, table):
    for a in S:
        for b in S:
            if a == b:
                continue
            if table.chi[(b, a)] == 0:
                return False
    return True


def has_elim_target(S, table):
    for x in S:
        mod = 2 ** table.depth[x]
        if sum(table.chi[(q, x)] for q in S if q != x) % mod == 0:
            return True
    return False


def per_config_null(S, table):
    p_no = 1.0
    for x in S:
        p_no *= (1 - 1 / 2 ** table.depth[x])
    return 1 - p_no


def wilson_ci(x, n, z=1.96):
    if n == 0:
        return (0.0, 1.0)
    p = x / n
    z2 = z * z
    denom = 1 + z2 / n
    center = (p + z2 / (2 * n)) / denom
    half = (z * (p * (1 - p) / n + z2 / (4 * n * n)) ** 0.5) / denom
    return (max(0.0, center - half), min(1.0, center + half))


def main():
    print("Loading first 80 hard primes...", flush=True)
    hp = find_hard_primes(80000)
    target_primes = [d["prime"] for d in hp[:80]]
    print("Building character table...", flush=True)
    table = build_two_primary_table(target_primes)

    print()
    print("=" * 78)
    print(f"Independence-model validation  [{N_SAMPLES} random samples, seed={SEED}]")
    print("=" * 78)
    print()
    print("For each k, sample uniformly random k-subsets from C(80, k),")
    print("filter to zero-delta, and compare:")
    print("  empirical 'any chi-sum = 0' fraction")
    print("  vs N_k = mean over subsets of (1 - prod_x (1 - 1/2^{t_x}))")
    print()

    random.seed(SEED)
    for k in (4, 5, 6):
        n_zd = 0
        n_with_elim = 0
        sum_null = 0.0
        for _ in range(N_SAMPLES):
            S = tuple(random.sample(target_primes, k))
            if not is_zero_delta(S, table):
                continue
            n_zd += 1
            sum_null += per_config_null(S, table)
            if has_elim_target(S, table):
                n_with_elim += 1
        if n_zd == 0:
            continue
        emp = n_with_elim / n_zd
        null = sum_null / n_zd
        lo, hi = wilson_ci(n_with_elim, n_zd)
        rel_dev = (emp - null) / null * 100 if null else 0
        print(f"  k = {k}:  {n_zd:>6} zero-δ samples")
        print(f"    empirical:    {emp*100:>5.2f}%  [Wilson 95% CI {lo*100:.2f}-{hi*100:.2f}%]")
        print(f"    N_k (theory): {null*100:>5.2f}%")
        print(f"    discrepancy:  {(emp-null)*100:+.2f} pp  ({rel_dev:+.2f}% relative)")
        if lo <= null <= hi:
            print(f"    CI encloses N_k: independence model approximately valid.")
        else:
            print(f"    CI does NOT enclose N_k: independence assumption may be violated.")
        print()

    print("Reading:")
    print("  Match (Wilson CI encloses N_k, relative deviation ~few %) -> the")
    print("  independence model is approximately valid in the unconstrained")
    print("  zero-delta case, so the deviation between N_k and empirical")
    print("  behaviour on minimal covering zero-delta configurations is")
    print("  attributable to the covering constraint, not to model error.")
    print()
    print("  See §6.2 (Defence (ii)) and empirical_observations.md item 5.")


if __name__ == "__main__":
    main()
