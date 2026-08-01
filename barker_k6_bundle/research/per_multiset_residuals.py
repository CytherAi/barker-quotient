#!/usr/bin/env python3
"""
per_multiset_residuals.py — full per-multiset breakdown of σ=0 mass at
(t=3, w=2) on the N=160 enumeration, with residuals against the
iid-empirical-marginal null. Tests two specific predictions:

  (1) Does the tail's σ=0 mass sit on EVEN-containing negation-closed
      multisets (the {1,2,6,7}, {2,3,5,6} structure)?
  (2) Do EVEN-containing collisions (σ≠0 w=2 multisets with a doubled
      even value) appear empirically AT ALL? Their absence is the
      falsifiable signature of "QR primes enter only in negation pairs."

Inputs: _per_depth_w2_t3_tuples_N160.json (the empirical histogram)
        _marginal_test_summary.json (the empirical χ-marginal)

Output: _per_multiset_residuals.json plus a printed summary
"""

from __future__ import annotations
import json
import os
import sys
from collections import Counter, defaultdict
from itertools import product
from math import factorial


def _check(cond, msg):
    """assert that survives python -O: invariant violations must fail loudly."""
    if not cond:
        raise ValueError(msg)

CACHE_DIR = os.path.dirname(os.path.abspath(__file__))


def load_hist(N: int) -> Counter:
    path = os.path.join(CACHE_DIR, f"_per_depth_w2_t3_tuples_N{N}.json")
    with open(path) as f:
        raw = json.load(f)
    return Counter({tuple(json.loads(k)): v for k, v in raw.items()})


def load_marginal() -> dict:
    path = os.path.join(CACHE_DIR, "_marginal_test_summary.json")
    with open(path) as f:
        s = json.load(f)
    return {int(k): v for k, v in s["empirical_marginal"].items()}


def w_and_sigma(values, mod=8):
    n = len(values)
    w = 0
    for i in range(n):
        for j in range(i + 1, n):
            if (values[i] + values[j]) % mod == 0:
                w += 1
    sigma = sum(values) % mod
    return w, sigma


def multiset_orderings(multiset):
    """Number of distinct ordered tuples with this multiset."""
    counter = Counter(multiset)
    n = sum(counter.values())
    denom = 1
    for c in counter.values():
        denom *= factorial(c)
    return factorial(n) // denom


def is_negation_closed(multiset, mod=8):
    """A multiset is negation-closed iff for every value v, the count of v
    equals the count of -v mod m. Equivalent to σ=0 at w=2."""
    c = Counter(multiset)
    for v in range(1, mod):
        if c[v] != c[(-v) % mod]:
            return False
    return True


def count_evens(multiset):
    return sum(1 for v in multiset if v % 2 == 0)


def main():
    N = 160
    mod = 8
    hist = load_hist(N)
    marginal = load_marginal()
    n_emp_total = sum(hist.values())

    # Enumerate all w=2 multisets in (Z/8\{0})^4, compute expected counts
    # under iid-empirical-marginal.
    all_w2_multisets = []
    p_w2 = 0.0
    for tup in product(range(1, mod), repeat=4):
        w, sigma = w_and_sigma(tup, mod)
        if w == 2:
            prob = 1.0
            for v in tup:
                prob *= marginal[v]
            p_w2 += prob
            all_w2_multisets.append((tuple(sorted(tup)), prob))

    # Conditional probability per multiset = sum over orderings / P(w=2)
    multiset_prob_cond = defaultdict(float)
    for ms, prob in all_w2_multisets:
        multiset_prob_cond[ms] += prob / p_w2

    # Sanity: probabilities sum to 1
    total = sum(multiset_prob_cond.values())
    _check(abs(total - 1.0) < 1e-9, f"prob sum {total}")

    # Build records
    records = []
    for ms in sorted(multiset_prob_cond.keys()):
        emp = hist.get(ms, 0)
        expected = multiset_prob_cond[ms] * n_emp_total
        residual = emp - expected
        residual_pp_of_total = residual / n_emp_total * 100
        w, sigma = w_and_sigma(list(ms), mod)
        records.append({
            "multiset": list(ms),
            "sigma": sigma,
            "sigma0": sigma == 0,
            "n_evens": count_evens(ms),
            "negation_closed": is_negation_closed(ms, mod),
            "is_all_odd": count_evens(ms) == 0,
            "empirical": emp,
            "expected_iid_emp_marg": round(expected, 2),
            "residual": round(residual, 2),
            "residual_pp_of_1590": round(residual_pp_of_total, 3),
            "ratio_emp_over_expected": round(emp / expected, 3) if expected > 0 else None,
        })

    # Sort by empirical count descending
    records.sort(key=lambda r: -r["empirical"])

    # Categorize
    def cat(r):
        even = "even-containing" if r["n_evens"] > 0 else "all-odd"
        sig = "σ=0" if r["sigma0"] else "σ≠0"
        return f"{even} {sig}"

    # Aggregate
    agg = defaultdict(lambda: {"empirical": 0, "expected": 0.0, "n_multisets": 0})
    for r in records:
        k = cat(r)
        agg[k]["empirical"] += r["empirical"]
        agg[k]["expected"] += r["expected_iid_emp_marg"]
        agg[k]["n_multisets"] += 1

    # Top-10 vs tail
    top10 = records[:10]
    tail = records[10:]
    top10_residual = sum(r["residual"] for r in top10)
    tail_residual = sum(r["residual"] for r in tail)
    top10_sigma0_residual = sum(r["residual"] for r in top10 if r["sigma0"])
    tail_sigma0_residual = sum(r["residual"] for r in tail if r["sigma0"])

    print("=" * 92)
    print(f"Per-multiset residuals at (t=3, w=2), N={N}, total empirical w=2 cases: {n_emp_total}")
    print(f"Null model: iid χ-values with empirical marginal (odd-skewed)")
    print("=" * 92)
    print()
    print(f"{'multiset':>16}  {'σ':>2}  {'evens':>5}  {'neg-closed':>10}  {'emp':>5}  {'expected':>9}  {'residual':>9}  {'ratio':>6}")
    print("-" * 92)
    for r in records:
        ms_str = "(" + ",".join(str(v) for v in r["multiset"]) + ")"
        nc = "Y" if r["negation_closed"] else "."
        sig = "0" if r["sigma0"] else "≠0"
        print(
            f"{ms_str:>16}  {sig:>2}  {r['n_evens']:>5}  {nc:>10}  "
            f"{r['empirical']:>5}  {r['expected_iid_emp_marg']:>9}  "
            f"{r['residual']:>+9.2f}  {r['ratio_emp_over_expected'] or 0:>6.2f}"
        )

    print()
    print("=" * 92)
    print("Category aggregates (empirical, expected under iid-emp-marg, residual)")
    print("=" * 92)
    for k in sorted(agg.keys()):
        emp = agg[k]["empirical"]
        exp = agg[k]["expected"]
        res = emp - exp
        nm = agg[k]["n_multisets"]
        print(f"  {k:<26}: n_multisets={nm:>2}  emp={emp:>5}  exp={exp:>7.2f}  residual={res:>+7.2f}  pp_of_1590={res / n_emp_total * 100:+.2f}")

    print()
    print("=" * 92)
    print("Top-10 vs tail σ=0 residual breakdown")
    print("=" * 92)
    print(f"  top-10 total residual:        {top10_residual:>+7.2f}  ({top10_residual / n_emp_total * 100:+.2f} pp of 1590)")
    print(f"  top-10 σ=0 residual:          {top10_sigma0_residual:>+7.2f}  ({top10_sigma0_residual / n_emp_total * 100:+.2f} pp)")
    print(f"  tail (26 multisets) residual: {tail_residual:>+7.2f}  ({tail_residual / n_emp_total * 100:+.2f} pp)")
    print(f"  tail σ=0 residual:            {tail_sigma0_residual:>+7.2f}  ({tail_sigma0_residual / n_emp_total * 100:+.2f} pp)")

    print()
    print("=" * 92)
    print("PREDICTION (1) — Tail σ=0 mass on EVEN-containing negation-closed multisets:")
    print("=" * 92)
    tail_sigma0_even = [r for r in tail if r["sigma0"] and r["n_evens"] > 0]
    for r in tail_sigma0_even:
        ms_str = "(" + ",".join(str(v) for v in r["multiset"]) + ")"
        print(f"  {ms_str}: emp={r['empirical']}, expected={r['expected_iid_emp_marg']:.2f}, residual={r['residual']:+.2f}, ratio={r['ratio_emp_over_expected'] or 0:.2f}")
    tail_sigma0_even_res = sum(r["residual"] for r in tail_sigma0_even)
    print(f"  TOTAL tail σ=0 even-containing residual: {tail_sigma0_even_res:+.2f}  ({tail_sigma0_even_res / n_emp_total * 100:+.2f} pp)")

    print()
    print("=" * 92)
    print("PREDICTION (2) — EVEN-containing COLLISIONS (σ≠0 w=2 with a doubled even value):")
    print("=" * 92)
    even_collisions = [r for r in records if not r["sigma0"] and r["n_evens"] > 0]
    print(f"  {len(even_collisions)} such multisets exist combinatorially.")
    print(f"  Total empirical occurrences: {sum(r['empirical'] for r in even_collisions)}")
    print(f"  Total expected under iid-emp-marg: {sum(r['expected_iid_emp_marg'] for r in even_collisions):.2f}")
    print()
    # Show top examples
    even_collisions.sort(key=lambda r: -r["expected_iid_emp_marg"])
    for r in even_collisions[:10]:
        ms_str = "(" + ",".join(str(v) for v in r["multiset"]) + ")"
        print(f"  {ms_str}: emp={r['empirical']}, expected={r['expected_iid_emp_marg']:.2f}, residual={r['residual']:+.2f}")
    if len(even_collisions) > 10:
        n_zero = sum(1 for r in even_collisions if r['empirical'] == 0)
        n_pos = sum(1 for r in even_collisions if r['empirical'] > 0)
        print(f"  ... {len(even_collisions) - 10} more.")
        print(f"  Multisets with zero empirical occurrences: {n_zero} / {len(even_collisions)}")
        print(f"  Multisets with at least one occurrence:    {n_pos} / {len(even_collisions)}")

    out = {
        "N": N,
        "total_w2_empirical": n_emp_total,
        "category_aggregates": dict(agg),
        "top10_residual": top10_residual,
        "top10_sigma0_residual": top10_sigma0_residual,
        "tail_residual": tail_residual,
        "tail_sigma0_residual": tail_sigma0_residual,
        "tail_sigma0_even_residual": tail_sigma0_even_res,
        "even_collisions": {
            "n_multisets": len(even_collisions),
            "total_empirical": sum(r['empirical'] for r in even_collisions),
            "total_expected": sum(r['expected_iid_emp_marg'] for r in even_collisions),
            "n_with_zero_empirical": sum(1 for r in even_collisions if r['empirical'] == 0),
            "details": even_collisions,
        },
        "records": records,
    }
    out_path = os.path.join(CACHE_DIR, "_per_multiset_residuals.json")
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2, default=str)
    print(f"\nSaved {out_path}")


if __name__ == "__main__":
    main()
