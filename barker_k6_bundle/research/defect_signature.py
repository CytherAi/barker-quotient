#!/usr/bin/env python3
"""
defect_signature.py — exploratory probe (post-v1.0, not part of the
verified pipeline; no tests; intentionally outside the audited stack).

For each known minimal covering configuration C (12 prior + the k=6
witness), evaluate the 0-cochain

    s(x, C) = sum_{p in C, p != x} chi_x(p)   mod 2^{t_x}

at every target x in the standard target system (first 80 hard primes).
Aggregate into a "defect signature" per configuration:

  * zero-support size and partition into internal (x in C) vs external
    (x not in C) zeros;
  * witness-richness at each zero target (how many p in C lie in V_x);
  * depth-from-zero distribution: for each nonzero s, the quantity
    v_2(s) + 1, which runs over [1, t_x]:
        depth = 1    iff s is odd            (maximally far from 0)
        depth = t_x  iff s = 2^{t_x - 1}     (one bit below 0, "almost-hub")
    NOTE: this was previously computed as t_x - v_2(s), which reverses the
    scale — it is largest for odd s and smallest for near-zero s.  Under that
    formula `almost_hub_count` (depth >= 3) counted the targets FURTHEST from
    a hub rather than the closest.  Numbers emitted by this probe before the
    correction are not comparable with the ones it emits now.
  * Shannon entropy of the depth-from-zero distribution.

This probes whether Type B configurations exhibit "distributed
near-triviality" (many targets with structurally small but nonzero s,
indicating an obstruction-class shadow visible already at the 0-cochain
level) versus Type A's expected sharply-concentrated single zero.

If Type B separates here, the cocycle upgrade collapses into a
computable defect invariant. If not, the obstruction genuinely lives
at the 1-cochain level on the witness-incidence complex.

Run from repo root:
    python3 barker_k6_bundle/research/defect_signature.py
"""

import os
import sys
from collections import Counter
from math import log2

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


def v2(n: int) -> int:
    if n == 0:
        return -1
    v = 0
    while n % 2 == 0:
        v += 1
        n //= 2
    return v


def shannon_entropy(counts: Counter) -> float:
    total = sum(counts.values())
    if total == 0:
        return 0.0
    h = 0.0
    for c in counts.values():
        if c:
            p = c / total
            h -= p * log2(p)
    return h


def signature(config, target_primes, table):
    C = tuple(sorted(config))
    in_C = set(C)

    rows = []
    for x in target_primes:
        t = table.depth[x]
        mod = 2 ** t
        s = 0
        witness = 0
        for p in C:
            if p == x:
                continue
            c = table.chi[(p, x)]
            s = (s + c) % mod
            if c == 0:
                witness += 1
        rows.append((x, s, t, witness))

    zeros_internal = [(x, w) for (x, s, t, w) in rows if s == 0 and x in in_C]
    zeros_external = [(x, w) for (x, s, t, w) in rows if s == 0 and x not in in_C]
    nonzero = [(x, s, t, w) for (x, s, t, w) in rows if s != 0]

    depth_from_zero = Counter()
    for x, s, t, w in nonzero:
        depth_from_zero[v2(s) + 1] += 1

    return {
        "config": C,
        "n_targets": len(rows),
        "n_internal_zeros": len(zeros_internal),
        "n_external_zeros": len(zeros_external),
        "zeros_internal": zeros_internal,
        "zeros_external": zeros_external,
        "depth_dist": dict(sorted(depth_from_zero.items())),
        "entropy_bits": shannon_entropy(depth_from_zero),
        "max_depth_seen": max(depth_from_zero) if depth_from_zero else 0,
        "almost_hub_count": sum(c for d, c in depth_from_zero.items() if d >= 3),
    }


def main():
    print("Building target system: first 80 hard primes...")
    hp = find_hard_primes(80000)
    target_primes = [d["prime"] for d in hp[:80]]
    print(f"  target system size = {len(target_primes)}, max = {target_primes[-1]}")

    configs = (
        list(KNOWN_MINIMAL_COVERING_TRIPLES)
        + list(KNOWN_MINIMAL_COVERING_4SETS)
        + list(KNOWN_MINIMAL_COVERING_5SETS)
        + [K6_WITNESS]
    )

    all_primes = sorted(set(target_primes) | {p for C in configs for p in C})
    print(f"Building character table on {len(all_primes)} primes...")
    table = build_two_primary_table(all_primes)

    print("Computing Type A/B classification...")
    cls = classify_all_known()
    type_b = {tuple(sorted(r.config)) for r in cls.type_b}

    print()
    print("=" * 78)
    print("  DEFECT SIGNATURE  —  s(x, C) = sum_{p in C, p != x} chi_x(p)")
    print("  Target system: first 80 hard primes")
    print("=" * 78)

    summary_rows = []
    for C in configs:
        Cs = tuple(sorted(C))
        label = "B" if Cs in type_b else "A"
        sig = signature(C, target_primes, table)

        print()
        print(f"k={len(Cs)}  [Type {label}]  {Cs}")
        print(
            f"  zeros: total={sig['n_internal_zeros'] + sig['n_external_zeros']:>2} "
            f"(internal={sig['n_internal_zeros']}, external={sig['n_external_zeros']})"
        )
        if sig["zeros_internal"]:
            tag = ", ".join(f"{x}/w={w}" for x, w in sig["zeros_internal"])
            print(f"    internal [x in C]:  {tag}")
        if sig["zeros_external"]:
            display = sig["zeros_external"][:8]
            tag = ", ".join(f"{x}/w={w}" for x, w in display)
            tail = " ..." if len(sig["zeros_external"]) > 8 else ""
            print(f"    external [x not in C]:  {tag}{tail}")
        print(f"  depth-from-zero dist (v_2(s) + 1): {sig['depth_dist']}")
        print(
            f"  entropy = {sig['entropy_bits']:.3f} bits | "
            f"max depth = {sig['max_depth_seen']} | "
            f"almost-hub (depth >= 3) = {sig['almost_hub_count']}"
        )

        summary_rows.append((label, len(Cs), Cs, sig))

    # Comparative summary
    print()
    print("=" * 78)
    print("  SUMMARY  (sorted by Type, then by k)")
    print("=" * 78)
    print(
        f"{'Type':4} {'k':>2}  {'config':36}  "
        f"{'int0':>4} {'ext0':>4} {'almost':>6}  {'entropy':>7}"
    )
    for label, k, Cs, sig in sorted(summary_rows, key=lambda r: (r[0], r[1])):
        cfg_str = str(Cs)
        if len(cfg_str) > 34:
            cfg_str = cfg_str[:31] + "..."
        print(
            f"{label:4} {k:>2}  {cfg_str:36}  "
            f"{sig['n_internal_zeros']:>4} "
            f"{sig['n_external_zeros']:>4} "
            f"{sig['almost_hub_count']:>6}  "
            f"{sig['entropy_bits']:>7.3f}"
        )


if __name__ == "__main__":
    main()
