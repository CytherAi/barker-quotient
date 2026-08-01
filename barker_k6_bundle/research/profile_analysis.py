#!/usr/bin/env python3
"""
profile_analysis.py — re-enumerate and group all minimal coverings by
sorted δ-profile, then count how many (k, profile) pairs split across
multiple cells of the {A1, A2, A3, B0, B-interior, B1} partition.

The k=5 (3,2,0,0,0) cross-cell appearance (A2 vs B1) showed that the
δ-profile alone does not determine cancellation. This script asks
whether that profile-splitting is:

  - ISOLATED: only a few profiles split across cells → the realization
    map is *almost* structural, with a small ambiguous set where extra
    invariants are needed for the rest.
  - PERVASIVE: most profiles split → realization is fundamentally
    arithmetic across the interior; structural classification is out.

Saves an enumeration cache to research/_enumeration_cache.json on
first run; subsequent runs skip the ~50min k=6 search and only
re-do the analysis.

Run from repo root:
    python3 barker_k6_bundle/research/profile_analysis.py
"""

import json
import os
import sys
import time
from collections import defaultdict

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


CACHE_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "_enumeration_cache.json"
)


def enumerate_and_cache(target_primes, table):
    index = BadPairIndex(target_primes, table)
    records = []
    for k in (3, 4, 5, 6):
        print(f"\n=== k = {k} ===", flush=True)
        t0 = time.time()
        result = search_minimal_covering_k(target_primes, k, table, index)
        print(
            f"  total={result.n_subsets_total:,} checked={result.n_subsets_checked:,} "
            f"covering={result.n_covering} minimal={result.n_minimal} "
            f"elapsed={time.time() - t0:.1f}s",
            flush=True,
        )
        for C in result.minimal_sets:
            c = classify(C, table)
            records.append((k, c.cls, list(c.profile), list(sorted(C))))
    return records


def main():
    print("Loading first 80 hard primes...", flush=True)
    hp = find_hard_primes(80000)
    target_primes = [d["prime"] for d in hp[:80]]

    print("Building character table...", flush=True)
    table = build_two_primary_table(target_primes)

    if os.path.exists(CACHE_FILE):
        print(f"Loading cached enumeration from {CACHE_FILE}", flush=True)
        with open(CACHE_FILE) as f:
            records = json.load(f)
        print(f"  loaded {len(records)} minimal coverings", flush=True)
    else:
        print("Enumerating (no cache)...", flush=True)
        records = enumerate_and_cache(target_primes, table)
        with open(CACHE_FILE, "w") as f:
            json.dump(records, f)
        print(f"\nSaved cache to {CACHE_FILE} ({len(records)} records)", flush=True)

    # Convert lists back to tuples for use as dict keys
    records = [(k, cls, tuple(profile), tuple(config)) for (k, cls, profile, config) in records]

    # Group by (k, profile)
    by_profile = defaultdict(list)
    for k, cls, profile, config in records:
        by_profile[(k, profile)].append((cls, config))

    split = {key: rows for key, rows in by_profile.items()
             if len({cls for cls, _ in rows}) > 1}
    single = {key: rows for key, rows in by_profile.items()
              if len({cls for cls, _ in rows}) == 1}

    print()
    print("=" * 78)
    print("  δ-PROFILE / CLASS ANALYSIS")
    print("=" * 78)
    print(f"Total minimal coverings:        {len(records)}")
    print(f"Distinct (k, profile) pairs:    {len(by_profile)}")
    print(f"Single-class profiles:          {len(single)}")
    print(f"Multi-class profiles (SPLIT):   {len(split)}")

    print()
    print("Per-k breakdown:")
    print(f"{'k':>3}  {'#profiles':>10}  {'single-class':>13}  {'multi-class':>12}  {'%split':>7}")
    for k in (3, 4, 5, 6):
        profs_k = [key for key in by_profile if key[0] == k]
        single_k = [key for key in single if key[0] == k]
        multi_k = [key for key in split if key[0] == k]
        pct = 100 * len(multi_k) / len(profs_k) if profs_k else 0
        print(
            f"{k:>3}  {len(profs_k):>10}  {len(single_k):>13}  "
            f"{len(multi_k):>12}  {pct:>6.1f}%"
        )

    # Per-k: how many configs sit on a split profile vs a non-split one?
    print()
    print("Configurations on split vs single-class profiles (counts of configs, not profiles):")
    print(f"{'k':>3}  {'on-single':>10}  {'on-split':>10}  {'%on-split':>10}")
    for k in (3, 4, 5, 6):
        on_single = sum(len(rows) for key, rows in single.items() if key[0] == k)
        on_split = sum(len(rows) for key, rows in split.items() if key[0] == k)
        total_k = on_single + on_split
        pct = 100 * on_split / total_k if total_k else 0
        print(f"{k:>3}  {on_single:>10}  {on_split:>10}  {pct:>9.1f}%")

    print()
    print("=" * 78)
    print("  ALL MULTI-CLASS δ-PROFILES (same topology, different arithmetic)")
    print("=" * 78)
    if not split:
        print("  (none)")
    else:
        for (k, profile), rows in sorted(split.items()):
            classes_here = sorted({cls for cls, _ in rows})
            print(
                f"\n  k={k}  profile={profile}   "
                f"classes={classes_here}   n_configs={len(rows)}"
            )
            class_counts = defaultdict(int)
            for cls, _ in rows:
                class_counts[cls] += 1
            for cls in classes_here:
                ex = [cfg for c, cfg in rows if c == cls][:3]
                print(f"    [{cls}: {class_counts[cls]}]  example(s): {ex}")

    print()
    print("=" * 78)
    print("READING:")
    print("  if %split is low (<10%): isolated — most profiles map to a single")
    print("    class, structural classification almost works.")
    print("  if %split is moderate to high (>30%): pervasive — realization is")
    print("    fundamentally arithmetic across the interior, no structural")
    print("    invariant beyond δ-profile decides cancellation.")
    print("=" * 78)


if __name__ == "__main__":
    main()
