#!/usr/bin/env python3
"""
null_control.py — exploratory probe #3 (research/, post-v1.0).

Null control for the "pair-dominant target concentration" invariant

    c(C) := 1 - max_x |pairs cancelled at x| / C(k, 2)

discovered in witness_complex.py. Observed:
  c(Type A configs, k >= 4)  in  [0.33, 0.40]
  c(Type B configs, k >= 4)  in  [0.67, 0.70]

But c could be measuring two very different things:
  (a) Type-B-ness — failure of a covering configuration to admit
      a pair-dominant target;
  (b) generic dispersion — failure of *any* random k-subset to
      admit a pair-dominant target.

These have completely different mathematical content.
(a) implies c carries genuine compatibility-obstruction information.
(b) implies c just measures absence of structure; in which case the
real signal is that Type A is unusually structured (low c) while
both Type B and random spread are simply the default (high c).

This script samples random k-subsets of the first 80 hard primes,
computes c(C) for each, and partitions by whether the subset happens
to be a covering (every pair has an internal witness in C).

Reads the distributions of c against the known Type A / Type B values.

Default seed = 42, N = 2000 per k. Reproducible.

Run from repo root:
    python3 barker_k6_bundle/research/null_control.py
"""

import os
import random
import sys
from itertools import combinations
from statistics import mean, median, stdev

sys.path.insert(
    0,
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "code"),
)

from barker.cofactor_analysis import classify_all_known  # noqa: E402
from barker.sweep import find_hard_primes  # noqa: E402
from barker.two_primary import build_two_primary_table  # noqa: E402


SEED = 42
N_SAMPLES_PER_K = 2000


def compute_c(C, target_primes, table):
    """c(C) = 1 - max_x |pairs cancelled at x| / C(k, 2)."""
    pairs = list(combinations(sorted(C), 2))
    n_pairs = len(pairs)
    if n_pairs == 0:
        return 1.0
    best = 0
    for x in target_primes:
        if x not in table.depth:
            continue
        mod = 2 ** table.depth[x]
        count = 0
        for (p, q) in pairs:
            if p == x or q == x:
                continue
            s = (table.chi[(p, x)] + table.chi[(q, x)]) % mod
            if s == 0:
                count += 1
        if count > best:
            best = count
    return 1.0 - best / n_pairs


def is_covering_internal(C, table):
    """Every pair in C has an internal witness in C (the paper's def)."""
    Cs = sorted(C)
    for (a, b) in combinations(Cs, 2):
        found = False
        for c in Cs:
            if c == a or c == b:
                continue
            mod = 2 ** table.depth[c]
            if (table.chi[(a, c)] + table.chi[(b, c)]) % mod == 0:
                found = True
                break
        if not found:
            return False
    return True


def percentiles(values, ps=(0.05, 0.25, 0.50, 0.75, 0.95)):
    if not values:
        return {p: float("nan") for p in ps}
    sv = sorted(values)
    out = {}
    for p in ps:
        idx = min(int(p * len(sv)), len(sv) - 1)
        out[p] = sv[idx]
    return out


def quantile_of(value, sample):
    if not sample:
        return float("nan")
    return sum(1 for v in sample if v <= value) / len(sample)


def fmt_dist(values):
    if not values:
        return "  (empty)"
    pct = percentiles(values)
    return (
        f"n={len(values)}  min={min(values):.3f}  "
        f"p05={pct[0.05]:.3f}  p25={pct[0.25]:.3f}  "
        f"med={pct[0.50]:.3f}  p75={pct[0.75]:.3f}  "
        f"p95={pct[0.95]:.3f}  max={max(values):.3f}  "
        f"mean={mean(values):.3f}  "
        f"sd={(stdev(values) if len(values) > 1 else 0):.3f}"
    )


def main():
    print(f"Building target system: first 80 hard primes (seed={SEED})")
    hp = find_hard_primes(80000)
    target_primes = [d["prime"] for d in hp[:80]]
    print(f"  target system: |X|={len(target_primes)}, max={target_primes[-1]}")
    print(f"Building character table on {len(target_primes)} primes...")
    table = build_two_primary_table(target_primes)

    print("Computing c(C) for known minimal coverings...")
    cls = classify_all_known()

    known = []  # (k, type_label, config, c)
    for r in cls.type_a + cls.type_b:
        Cs = tuple(sorted(r.config))
        # Skip k=6 here — handled separately because it lives in the same
        # table as a covering. Wait, actually classify_all_known includes k=6.
        label = "B" if r.is_genuine else "A"
        c = compute_c(Cs, target_primes, table)
        known.append((len(Cs), label, Cs, c))

    known.sort(key=lambda r: (r[1], r[0]))

    print()
    print("=" * 78)
    print("  KNOWN minimal coverings (Type A and Type B)")
    print("=" * 78)
    for k, lab, Cs, c in known:
        cfg_str = str(Cs)
        if len(cfg_str) > 36:
            cfg_str = cfg_str[:33] + "..."
        print(f"  k={k}  Type {lab}  c={c:.3f}   {cfg_str}")

    # ----- random sampling -----
    print()
    print("=" * 78)
    print(f"  RANDOM NULL CONTROL — N={N_SAMPLES_PER_K} samples per k")
    print("=" * 78)

    rng = random.Random(SEED)

    for k in (3, 4, 5, 6):
        coverings_c = []
        noncoverings_c = []
        for _ in range(N_SAMPLES_PER_K):
            sample = tuple(sorted(rng.sample(target_primes, k)))
            c_val = compute_c(sample, target_primes, table)
            if is_covering_internal(sample, table):
                coverings_c.append(c_val)
            else:
                noncoverings_c.append(c_val)

        print()
        print(f"-- k = {k} --")
        print(f"  random coverings:     {fmt_dist(coverings_c)}")
        print(f"  random non-coverings: {fmt_dist(noncoverings_c)}")
        print(
            f"  covering frequency:   "
            f"{len(coverings_c)}/{N_SAMPLES_PER_K} "
            f"= {len(coverings_c) / N_SAMPLES_PER_K:.4f}"
        )

        # Known at this k, with quantiles against the random non-coverings
        ks_at_this_k = [(lab, Cs, c) for (kk, lab, Cs, c) in known if kk == k]
        if ks_at_this_k:
            print(f"  KNOWN k={k} positions:")
            for (lab, Cs, c) in ks_at_this_k:
                q_nc = quantile_of(c, noncoverings_c)
                q_c = quantile_of(c, coverings_c) if coverings_c else float("nan")
                cfg_str = str(Cs)
                if len(cfg_str) > 36:
                    cfg_str = cfg_str[:33] + "..."
                print(
                    f"    Type {lab}  c={c:.3f}   "
                    f"quantile vs random non-cov = {q_nc:.3f}   "
                    f"vs random cov = {q_c if q_c == q_c else 'n/a'}   "
                    f"{cfg_str}"
                )

    print()
    print("=" * 78)
    print("READING:")
    print("  - If random non-coverings concentrate near Type B c values (high),")
    print("    c is a generic dispersion measure. Then the *real* signal is that")
    print("    Type A is structurally unusual, not that Type B is.")
    print("  - If random non-coverings span a broad c range and Type B occupies a")
    print("    specific extreme, c carries Type-B-specific compatibility content.")
    print("  - Random coverings (if any appear) provide the most informative")
    print("    comparison: do covering configurations generically concentrate")
    print("    (Type-A-like) or generically distribute (Type-B-like)?")
    print("=" * 78)


if __name__ == "__main__":
    main()
