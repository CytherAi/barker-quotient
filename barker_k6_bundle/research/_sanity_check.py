#!/usr/bin/env python3
"""
_sanity_check.py — verify null_control.py results against known facts
before interpreting them as evidence.

Checks:
 1. The "first 80 hard primes" universe actually contains every prime
    appearing in any known minimal covering configuration.
 2. is_covering_internal returns True for every known minimal covering.
 3. is_covering_internal returns False for a hand-built non-covering.
 4. compute_c values match the witness_complex.py results exactly
    for every known config.
 5. The full c-histogram of random non-coverings (per k) — not just
    percentiles — so we see whether Type B sits at a structural ceiling
    or in a sparsely populated tail.
 6. Sample inspection: print 5 random non-coverings per k with their
    c values, for manual verification.
"""

import os
import random
import sys
from collections import Counter
from itertools import combinations

sys.path.insert(
    0,
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "code"),
)

from barker.cofactor_analysis import classify_all_known  # noqa: E402
from barker.known_configs import (  # noqa: E402
    KNOWN_MINIMAL_COVERING_4SETS,
    KNOWN_MINIMAL_COVERING_5SETS,
    KNOWN_MINIMAL_COVERING_TRIPLES,
)
from barker.sweep import find_hard_primes  # noqa: E402
from barker.two_primary import build_two_primary_table  # noqa: E402

K6_WITNESS = (1801, 13417, 14537, 17881, 18121, 18521)
SEED = 42


def compute_c(C, target_primes, table):
    pairs = list(combinations(sorted(C), 2))
    n_pairs = len(pairs)
    if n_pairs == 0:
        return 1.0
    best = 0
    best_x = None
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
            best_x = x
    return 1.0 - best / n_pairs, best, best_x


def is_covering_internal(C, table):
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


def main():
    print("Loading first 80 hard primes...")
    hp = find_hard_primes(80000)
    target_primes = [d["prime"] for d in hp[:80]]
    print(f"  count={len(target_primes)}, min={target_primes[0]}, max={target_primes[-1]}")
    print(f"  first 10: {target_primes[:10]}")
    print(f"  last 10:  {target_primes[-10:]}")

    target_set = set(target_primes)

    # ---- Check 1: known config primes are inside target universe ----
    all_known = (
        list(KNOWN_MINIMAL_COVERING_TRIPLES)
        + list(KNOWN_MINIMAL_COVERING_4SETS)
        + list(KNOWN_MINIMAL_COVERING_5SETS)
        + [K6_WITNESS]
    )
    print()
    print("Check 1: known config primes subset-of first 80 hard primes")
    all_ok = True
    for C in all_known:
        missing = [p for p in C if p not in target_set]
        if missing:
            print(f"  FAIL  {C}  missing from target universe: {missing}")
            all_ok = False
    if all_ok:
        print(f"  PASS  all {len(all_known)} known configs are subsets of the first 80")

    # ---- Build table ----
    print()
    print("Building character table...")
    table = build_two_primary_table(target_primes)

    # ---- Check 2: is_covering_internal True on known coverings ----
    print()
    print("Check 2: is_covering_internal returns True for known minimal coverings")
    for C in all_known:
        ok = is_covering_internal(C, table)
        print(f"  {'PASS' if ok else 'FAIL'}  is_covering={ok}  {tuple(sorted(C))}")

    # ---- Check 3: is_covering_internal returns False on a constructed non-covering ----
    print()
    print("Check 3: is_covering_internal returns False on first 4 hard primes (non-covering)")
    test_nc = tuple(target_primes[:4])
    ok = is_covering_internal(test_nc, table)
    print(f"  {'PASS' if not ok else 'FAIL'}  is_covering={ok}  {test_nc}")

    # ---- Check 4: c values match witness_complex.py ----
    expected = {
        (73, 233, 1721):     (0.667, 1),
        (73, 1609, 1801):    (0.667, 1),
        (89, 601, 2969):     (0.667, 1),
        (233, 337, 2969):    (0.333, 2),
        (937, 1609, 4057):   (0.333, 2),
        (1289, 1433, 1609):  (0.333, 2),
        (1913, 2089, 3257):  (0.333, 2),
        (337, 937, 1433, 1721):                 (0.667, 2),
        (89, 1721, 4177, 6553, 7529):           (0.400, 6),
        (233, 881, 4201, 6553, 6857):           (0.400, 6),
        (1913, 4057, 6089, 6353, 7753):         (0.400, 6),
        (4297, 4409, 5689, 6553, 7753):         (0.700, 3),
        (1801, 13417, 14537, 17881, 18121, 18521): (0.333, 10),
    }
    print()
    print("Check 4: compute_c matches witness_complex.py")
    for C, (exp_c, exp_max) in expected.items():
        c_val, best, best_x = compute_c(C, target_primes, table)
        ok = abs(c_val - exp_c) < 0.001 and best == exp_max
        print(
            f"  {'PASS' if ok else 'FAIL'}  c={c_val:.3f} (exp {exp_c:.3f}), "
            f"maxPC={best} (exp {exp_max}), best_x={best_x}  {C}"
        )

    # ---- Check 5: c histogram for random non-coverings (full distribution) ----
    rng = random.Random(SEED)
    print()
    print("Check 5: full c histogram for 2000 random non-coverings per k")
    for k in (3, 4, 5, 6):
        hist = Counter()
        non_cov_count = 0
        cov_count = 0
        for _ in range(2000):
            sample = tuple(sorted(rng.sample(target_primes, k)))
            c_val, _, _ = compute_c(sample, target_primes, table)
            covering = is_covering_internal(sample, table)
            if covering:
                cov_count += 1
            else:
                non_cov_count += 1
                # round c to 3 decimals for histogram bucketing
                bucket = round(c_val, 3)
                hist[bucket] += 1
        print(f"\n  k={k}: {non_cov_count} non-coverings, {cov_count} coverings")
        items = sorted(hist.items())
        max_count = max(hist.values()) if hist else 1
        for c_val, count in items:
            bar = "#" * int(40 * count / max_count)
            pct = 100 * count / non_cov_count
            print(f"    c={c_val:.3f}  n={count:>4}  ({pct:>5.2f}%)  {bar}")

    # ---- Check 6: print 5 sample random non-coverings per k ----
    rng2 = random.Random(SEED + 1)
    print()
    print("Check 6: 5 sample random non-coverings per k (for manual spot-check)")
    for k in (3, 4, 5, 6):
        print(f"\n  k={k}:")
        n_shown = 0
        attempts = 0
        while n_shown < 5 and attempts < 200:
            attempts += 1
            sample = tuple(sorted(rng2.sample(target_primes, k)))
            if is_covering_internal(sample, table):
                continue
            c_val, best, best_x = compute_c(sample, target_primes, table)
            print(
                f"    {sample}  c={c_val:.3f}  maxPC={best}/"
                f"{k * (k - 1) // 2}  best_x={best_x}"
            )
            n_shown += 1


if __name__ == "__main__":
    main()
