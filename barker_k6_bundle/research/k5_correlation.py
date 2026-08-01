#!/usr/bin/env python3
"""
k5_correlation.py — cross-target conditional α-profile decomposition at
k = 5 zero-δ (manuscript §6.2 (i)-(iii)).

RECONSTRUCTED. The original script of this name was referenced by §8.7 but was
absent from the repository, leaving the §6.2 cross-target numbers without
provenance. This is a reimplementation from the manuscript's own definitions
(6.2.α, 6.2.β); it is validated by reproducing the published tables exactly —
see `--check`, which asserts against the N = 160 figures printed in §6.2.

What it computes
----------------
For each k = 5 zero-δ minimal covering S and each unordered target pair
(x, y) ⊆ S (Definition 6.2.α):

    inner cofactor        C_xy = S \\ {x, y}                    (3 primes)
    inner candidate pairs {a, b} ⊆ C_xy                        (3 pairs)

Each inner candidate pair is witnessed by x, by y, by both, or by neither,
where "x witnesses {a, b}" means χ_x(a) + χ_x(b) ≡ 0 (mod 2^{t_x}). Counting
those four states gives the α-profile (Definition 6.2.β)

    (α_both, α_x_only, α_y_only, α_none),   summing to 3,

collapsed to the unordered (α_both, α_asymm, α_none) with
α_asymm = α_x_only + α_y_only.

Elimination at a target is σ_x(S) = Σ_{p ∈ S, p ≠ x} χ_x(p) ≡ 0 (mod 2^{t_x}),
computed with the library primitive `_common.chi_sum`.

The pair (x, y) is ordered as x < y so that the two marginal columns
P(σ_x = 0) and P(σ_y = 0) are well defined per cell.

SCOPE / STATUS OF THE OUTPUT
----------------------------
Every quantity here is a descriptive statistic of a finite enumerated census.
The "P(iid | α)" column is the product of the two marginals measured IN THE
SAME CELL: it is a fitted in-sample baseline, not a calibrated null. The
`ratio` column is therefore a descriptive contrast, and no significance,
σ-value, or population extrapolation is attached to it or should be inferred
from it. Cells are reported with their counts so the reader can see which are
thin (the α_both = 2 cell holds 16 pairs at N = 160).

Run from repo root:
    python3 barker_k6_bundle/research/k5_correlation.py [N=160] [--check]

Emits a structured result to `_k5_correlation_N<N>.json`.
"""

from __future__ import annotations

import json
import os
import sys
from collections import defaultdict
from itertools import combinations

sys.path.insert(
    0,
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "code"),
)

from barker.sweep import find_hard_primes  # noqa: E402
from barker.two_primary import build_two_primary_table  # noqa: E402

from _common import chi_sum, delta_x  # noqa: E402
from per_depth_w2 import cache_path, enumerate_k5_zero_delta  # noqa: E402


HERE = os.path.dirname(os.path.abspath(__file__))


def witnesses(x, a, b, table):
    """True iff target x witnesses the pair {a, b}: χ_x(a) + χ_x(b) ≡ 0."""
    mod = 2 ** table.depth[x]
    return (table.chi[(a, x)] + table.chi[(b, x)]) % mod == 0


def alpha_profile(S, x, y, table):
    """(α_both, α_x_only, α_y_only, α_none) over the 3 inner candidate pairs."""
    inner = [p for p in S if p != x and p != y]
    both = x_only = y_only = none = 0
    for a, b in combinations(inner, 2):
        wx = witnesses(x, a, b, table)
        wy = witnesses(y, a, b, table)
        if wx and wy:
            both += 1
        elif wx:
            x_only += 1
        elif wy:
            y_only += 1
        else:
            none += 1
    return both, x_only, y_only, none


def collect(configs, table):
    """One record per unordered target pair, ordered x < y."""
    rows = []
    for S in configs:
        Ss = sorted(S)
        elim = {p: chi_sum(p, Ss, table) == 0 for p in Ss}
        for x, y in combinations(Ss, 2):
            both, xo, yo, none = alpha_profile(Ss, x, y, table)
            rows.append({
                "alpha_both": both,
                "alpha_asymm": xo + yo,
                "alpha_none": none,
                "elim_x": elim[x],
                "elim_y": elim[y],
            })
    return rows


def _cell(rows):
    n = len(rows)
    if n == 0:
        return None
    px = sum(r["elim_x"] for r in rows) / n
    py = sum(r["elim_y"] for r in rows) / n
    both = sum(r["elim_x"] and r["elim_y"] for r in rows) / n
    iid = px * py
    return {
        "n": n,
        "p_elim_x": px,
        "p_elim_y": py,
        "p_both_emp": both,
        "p_iid_given_cell": iid,
        "excess": both - iid,
        "ratio": (both / iid) if iid > 0 else None,
    }


def summarise(rows):
    pooled = (
        sum(r["elim_x"] for r in rows) + sum(r["elim_y"] for r in rows)
    ) / (2 * len(rows))
    by_both = {}
    for ab in sorted({r["alpha_both"] for r in rows}):
        by_both[ab] = _cell([r for r in rows if r["alpha_both"] == ab])
    by_profile = {}
    keyed = defaultdict(list)
    for r in rows:
        keyed[(r["alpha_both"], r["alpha_asymm"], r["alpha_none"])].append(r)
    for key in sorted(keyed):
        by_profile[key] = _cell(keyed[key])
    agg = _cell(rows)
    agg["p_pooled"] = pooled
    agg["p_pooled_squared"] = pooled ** 2
    agg["ratio_vs_pooled"] = agg["p_both_emp"] / (pooled ** 2)
    return agg, by_both, by_profile


# Published §6.2 figures at N = 160, used to validate this reconstruction.
_PUBLISHED_N160 = {
    "n_configs": 661,
    "n_pairs": 6610,
    "p_both_emp": 0.1086,
    "p_pooled_squared": 0.1084,
    "by_both": {  # alpha_both -> (n, p_x, p_y, p_both, p_iid, ratio)
        0: (5798, 0.302, 0.314, 0.0952, 0.0947, 1.005),
        1: (796, 0.464, 0.494, 0.2010, 0.2289, 0.878),
        2: (16, 0.688, 0.625, 0.3750, 0.4297, 0.873),
    },
    "by_profile": {  # (both, asymm, none) -> (n, p_x, p_y, p_both, p_iid, ratio)
        (0, 1, 2): (1308, 0.136, 0.161, 0.0000, 0.0218, 0.000),
        (0, 2, 1): (2783, 0.297, 0.305, 0.0679, 0.0905, 0.750),
        (0, 3, 0): (1707, 0.437, 0.445, 0.2127, 0.1946, 1.093),
        (1, 0, 2): (42, 0.452, 0.500, 0.3095, 0.2262, 1.368),
        (1, 1, 1): (375, 0.477, 0.507, 0.1733, 0.2418, 0.717),
        (1, 2, 0): (379, 0.451, 0.480, 0.2164, 0.2167, 0.999),
    },
}


def check_against_published(n_configs, agg, by_both, by_profile):
    """Assert this reconstruction reproduces the §6.2 N=160 tables."""
    pub = _PUBLISHED_N160
    fails = []

    def near(got, want, tol, what):
        if got is None or abs(got - want) > tol:
            fails.append(f"{what}: got {got}, published {want}")

    if n_configs != pub["n_configs"]:
        fails.append(f"n_configs: got {n_configs}, published {pub['n_configs']}")
    if agg["n"] != pub["n_pairs"]:
        fails.append(f"n_pairs: got {agg['n']}, published {pub['n_pairs']}")
    near(agg["p_both_emp"], pub["p_both_emp"], 5e-5, "aggregate P(both)")
    near(agg["p_pooled_squared"], pub["p_pooled_squared"], 5e-5, "pooled p^2")

    for ab, (n, px, py, pb, pi, ratio) in pub["by_both"].items():
        c = by_both.get(ab)
        if c is None:
            fails.append(f"alpha_both={ab}: cell missing")
            continue
        if c["n"] != n:
            fails.append(f"alpha_both={ab} n: got {c['n']}, published {n}")
        near(c["p_elim_x"], px, 5e-4, f"alpha_both={ab} P(elim_x)")
        near(c["p_elim_y"], py, 5e-4, f"alpha_both={ab} P(elim_y)")
        near(c["p_both_emp"], pb, 5e-5, f"alpha_both={ab} P(both)")
        near(c["p_iid_given_cell"], pi, 5e-4, f"alpha_both={ab} P(iid)")
        near(c["ratio"], ratio, 5e-3, f"alpha_both={ab} ratio")

    for key, (n, px, py, pb, pi, ratio) in pub["by_profile"].items():
        c = by_profile.get(key)
        if c is None:
            fails.append(f"profile {key}: cell missing")
            continue
        if c["n"] != n:
            fails.append(f"profile {key} n: got {c['n']}, published {n}")
        near(c["p_elim_x"], px, 5e-4, f"profile {key} P(elim_x)")
        near(c["p_elim_y"], py, 5e-4, f"profile {key} P(elim_y)")
        near(c["p_both_emp"], pb, 5e-5, f"profile {key} P(both)")
        near(c["p_iid_given_cell"], pi, 5e-4, f"profile {key} P(iid)")
        near(c["ratio"], ratio, 5e-3, f"profile {key} ratio")
    return fails


def run(N: int, do_check: bool):
    hp = find_hard_primes(60000 if N <= 160 else 100000)
    primes = [d["prime"] for d in hp[:N]]
    print(f"Universe: first {N} hard primes (max p_{N} = {primes[-1]})", flush=True)
    table = build_two_primary_table(primes)

    cp = cache_path(N)
    if os.path.exists(cp):
        print(f"Loading k=5 zero-δ enumeration from {os.path.basename(cp)}", flush=True)
        with open(cp) as f:
            configs = [tuple(s) for s in json.load(f)]
    else:
        print("Enumerating k=5 zero-δ minimal coverings...", flush=True)
        configs = [tuple(primes[i] for i in S)
                   for S in enumerate_k5_zero_delta(primes, table)]
        with open(cp, "w") as f:
            json.dump([list(s) for s in configs], f)
    print(f"  {len(configs)} configurations", flush=True)

    for S in configs[:5]:
        for x in S:
            if delta_x(x, sorted(S), table) != 0:
                raise SystemExit(f"CHECK FAILED: non-zero-δ at {x} in {S}")

    rows = collect(configs, table)
    agg, by_both, by_profile = summarise(rows)

    print()
    print(f"=== Aggregate over {agg['n']} unordered target pairs ===")
    print(f"  P(σ_x = 0 ∧ σ_y = 0) empirical : {agg['p_both_emp']:.4f}")
    print(f"  pooled p^2 (in-sample)        : {agg['p_pooled_squared']:.4f}")
    print(f"  ratio                         : {agg['ratio_vs_pooled']:.3f}")
    print()
    print("=== Conditional on α_both ===")
    print(f"{'α_both':>6} {'n':>6} {'P(elim_x)':>10} {'P(elim_y)':>10} "
          f"{'P(both)':>9} {'P(iid|α)':>9} {'excess':>9} {'ratio':>7}")
    for ab, c in sorted(by_both.items()):
        print(f"{ab:>6} {c['n']:>6} {c['p_elim_x']:>10.3f} {c['p_elim_y']:>10.3f} "
              f"{c['p_both_emp']:>9.4f} {c['p_iid_given_cell']:>9.4f} "
              f"{c['excess']:>+9.4f} {c['ratio']:>7.3f}")
    print()
    print("=== Conditional on (α_both, α_asymm, α_none) ===")
    print(f"{'profile':>12} {'n':>6} {'P(elim_x)':>10} {'P(elim_y)':>10} "
          f"{'P(both)':>9} {'P(iid|prof)':>11} {'ratio':>7}")
    for key, c in sorted(by_profile.items()):
        r = "  n/a" if c["ratio"] is None else f"{c['ratio']:>7.3f}"
        print(f"{str(key):>12} {c['n']:>6} {c['p_elim_x']:>10.3f} "
              f"{c['p_elim_y']:>10.3f} {c['p_both_emp']:>9.4f} "
              f"{c['p_iid_given_cell']:>11.4f} {r}")
    print()
    print("  These are descriptive statistics of a finite census. 'P(iid | ·)' is")
    print("  the product of the two marginals measured in the SAME cell — a fitted")
    print("  in-sample baseline, not a calibrated null. No significance or")
    print("  population claim attaches to the excess or ratio columns.")

    out = os.path.join(HERE, f"_k5_correlation_N{N}.json")
    with open(out, "w") as f:
        json.dump({
            "N": N,
            "universe_max_prime": primes[-1],
            "n_configs": len(configs),
            "aggregate": agg,
            "by_alpha_both": {str(k): v for k, v in by_both.items()},
            "by_alpha_profile": {str(list(k)): v for k, v in by_profile.items()},
        }, f, indent=2, sort_keys=True)
    print(f"\n  wrote {os.path.basename(out)}")

    if do_check:
        if N != 160:
            print("\n  --check only validates against the published N=160 tables.")
            return 1
        fails = check_against_published(len(configs), agg, by_both, by_profile)
        print()
        if fails:
            print("CHECK FAILED — reconstruction does not match published §6.2:")
            for f_ in fails:
                print(f"    {f_}")
            return 1
        print("CHECK PASSED — reproduces every published §6.2 N=160 figure.")
    return 0


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--check"]
    N = int(args[0]) if args else 160
    sys.exit(run(N, "--check" in sys.argv))
