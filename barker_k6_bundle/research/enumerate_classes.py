#!/usr/bin/env python3
"""
enumerate_classes.py — exhaustive enumeration of all minimal covering
k-sets in the first 80 hard primes (k = 3, 4, 5, 6), classified by the
follow-on paper's 5-class δ-profile partition.

The decisive question:

  A2 is the only mid-δ regime observed among the 13 known coverings.
  With one instance, A2 might be either a structural transition stratum
  or a classification artifact (a grid cell that exists because the
  axes exist but doesn't correspond to a natural class).

  Exhaustive enumeration answers this:
    - A2 count = 1 (no new instances): arithmetic contingency.
      The single example is an isolated coincidence.
    - A2 count >> 1: A2 is a populated stratum and the most interesting
      regime in the table, where topology and arithmetic interact
      nontrivially.

  The same enumeration also answers whether B0 generalizes (any new
  maximally-diffuse configurations at larger k) and whether B1 grows
  beyond the three instances the follow-on paper already reports.

Uses the existing BadPairIndex from barker.minimal_cover_search.

Run from repo root:
    python3 barker_k6_bundle/research/enumerate_classes.py
"""

import os
import sys
import time
from collections import Counter

sys.path.insert(
    0,
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "code"),
)

from barker.minimal_cover_search import (  # noqa: E402
    BadPairIndex,
    search_minimal_covering_k,
)
from barker.sweep import find_hard_primes  # noqa: E402
from barker.two_primary import build_two_primary_table  # noqa: E402

from _common import classify  # noqa: E402


def main():
    print("Loading first 80 hard primes...")
    hp = find_hard_primes(80000)
    target_primes = [d["prime"] for d in hp[:80]]

    print("Building character table and bad-pair index (one-time setup)...")
    t0 = time.time()
    table = build_two_primary_table(target_primes)
    index = BadPairIndex(target_primes, table)
    print(f"  setup elapsed: {time.time() - t0:.1f}s")

    cells_by_k = {}
    examples_by_class_k = {}

    for k in (3, 4, 5, 6):
        print()
        print(f"=== k = {k} ===")
        t0 = time.time()
        result = search_minimal_covering_k(target_primes, k, table, index)
        print(
            f"  C(80, {k}) = {result.n_subsets_total:,}   "
            f"checked = {result.n_subsets_checked:,}   "
            f"covering = {result.n_covering}   "
            f"minimal = {result.n_minimal}   "
            f"elapsed = {time.time() - t0:.1f}s"
        )

        counts = Counter()
        cells_by_k[k] = []
        for C in result.minimal_sets:
            c = classify(C, table)
            counts[c.cls] += 1
            cells_by_k[k].append((c.cls, c.profile, C, c.elim))
            examples_by_class_k.setdefault((c.cls, k), []).append(
                (c.profile, C, c.elim)
            )

        print(f"  classifications: {dict(sorted(counts.items()))}")

    print()
    print("=" * 78)
    print("  CROSS-k CLASS CENSUS")
    print("=" * 78)
    classes = ("A1", "A2", "A3", "B0", "B1")
    print(f"{'k':>3} | " + " ".join(f"{c:>4}" for c in classes) + " | total")
    print("-" * 50)
    for k in (3, 4, 5, 6):
        c = Counter(row[0] for row in cells_by_k[k])
        total = sum(c.values())
        print(
            f"{k:>3} | "
            + " ".join(f"{c.get(cls, 0):>4}" for cls in classes)
            + f" | {total}"
        )

    print()
    print("=" * 78)
    print("  NEW A2 INSTANCES (the decisive question)")
    print("=" * 78)
    a2_total = sum(len(examples_by_class_k.get(("A2", k), [])) for k in (3, 4, 5, 6))
    print(f"Total A2 across all enumerated k: {a2_total}")
    for k in (3, 4, 5, 6):
        rows = examples_by_class_k.get(("A2", k), [])
        if rows:
            print(f"\n  k={k}: {len(rows)} A2 instance(s)")
            for profile, C, elim in rows[:20]:
                print(f"    {C}   δ-profile={profile}   elim={elim}")

    print()
    print("=" * 78)
    print("  ALL B0 INSTANCES (maximally diffuse residual)")
    print("=" * 78)
    for k in (3, 4, 5, 6):
        rows = examples_by_class_k.get(("B0", k), [])
        if rows:
            print(f"\n  k={k}: {len(rows)} B0 instance(s)")
            for profile, C, elim in rows[:20]:
                print(f"    {C}   δ-profile={profile}")

    print()
    print("=" * 78)
    print("  ALL B1 INSTANCES (codimension-one blocked)")
    print("=" * 78)
    for k in (3, 4, 5, 6):
        rows = examples_by_class_k.get(("B1", k), [])
        if rows:
            print(f"\n  k={k}: {len(rows)} B1 instance(s)")
            for profile, C, elim in rows[:20]:
                print(f"    {C}   δ-profile={profile}")

    print()
    print("=" * 78)
    print("READING:")
    print("  A2 count 1 -> arithmetic contingency, A2 is a singleton coincidence.")
    print("  A2 count >> 1 -> A2 is a populated stratum where topology and")
    print("    arithmetic interact nontrivially; the most interesting open regime.")
    print("=" * 78)


if __name__ == "__main__":
    main()
