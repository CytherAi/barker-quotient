#!/usr/bin/env python3
"""
k7_60primes.py — same probe as k7_extension.py but on the first 60
hard primes instead of 50.

C(60, 7) = 386,206,920 subsets, estimated ~65 min wall time at the
rate measured in k7_extension (≈100K checks/sec including pruning).

The first-50 run found only 2 minimal coverings — too few to surface
multi-class δ-profiles for the 2-FWL robustness check. Increasing to
60 primes is the smallest expansion likely to yield enough k=7
minimal coverings to find at least one multi-class profile.

If 2-FWL still resolves every multi-class profile at k=7, the
structural-completeness pattern from k=3..6 extends. If 2-FWL
fails on any multi-class profile, we've found the first genuine
arithmetic residue at higher k with the proper encoding.
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

from _common import (  # noqa: E402
    build_labeled_graph,
    classify,
    two_fwl_signature,
)


CACHE_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "_k7_60primes_cache.json"
)


def main():
    print("Loading first 60 hard primes...", flush=True)
    hp = find_hard_primes(20000)
    target_primes = [d["prime"] for d in hp[:60]]
    print(f"  count={len(target_primes)}, max={target_primes[-1]}", flush=True)

    print("Building character table and bad-pair index...", flush=True)
    t0 = time.time()
    table = build_two_primary_table(target_primes)
    index = BadPairIndex(target_primes, table)
    print(f"  setup: {time.time() - t0:.1f}s", flush=True)

    if os.path.exists(CACHE_FILE):
        print(f"Loading cached k=7 records from {CACHE_FILE}", flush=True)
        with open(CACHE_FILE) as f:
            records = json.load(f)
        records = [(k, cls, tuple(profile), tuple(config))
                   for k, cls, profile, config in records]
    else:
        print("\n=== k = 7 on first 60 hard primes ===", flush=True)
        t0 = time.time()
        result = search_minimal_covering_k(target_primes, 7, table, index)
        print(
            f"  total={result.n_subsets_total:,} "
            f"checked={result.n_subsets_checked:,} "
            f"covering={result.n_covering} "
            f"minimal={result.n_minimal} "
            f"elapsed={time.time() - t0:.1f}s",
            flush=True,
        )
        records = []
        for C in result.minimal_sets:
            c = classify(C, table)
            records.append((7, c.cls, c.profile, tuple(sorted(C))))
        with open(CACHE_FILE, "w") as f:
            json.dump([(k, cls, list(profile), list(config))
                       for k, cls, profile, config in records], f)
        print(f"\n  saved {len(records)} k=7 records to {CACHE_FILE}", flush=True)

    print()
    print("=" * 78)
    print(f"  k=7 minimal coverings found (first 60 primes): {len(records)}")
    print("=" * 78)
    class_counts = defaultdict(int)
    for k, cls, profile, config in records:
        class_counts[cls] += 1
    print(f"  classifications: {dict(sorted(class_counts.items()))}")

    by_profile = defaultdict(list)
    for k, cls, profile, config in records:
        by_profile[(k, profile)].append((cls, config))
    multi_profiles = {k: v for k, v in by_profile.items()
                      if len({c for c, _ in v}) > 1}

    print()
    print(f"  distinct (k, profile) pairs: {len(by_profile)}")
    print(f"  multi-class profiles:        {len(multi_profiles)}")

    # List all profiles with class counts
    print()
    print("  Profile inventory:")
    for (k, profile), rows in sorted(by_profile.items()):
        cls_count = defaultdict(int)
        for cls, _ in rows:
            cls_count[cls] += 1
        print(f"    profile={profile} → {dict(cls_count)}")

    if not multi_profiles:
        print()
        print("  No multi-class profiles at k=7 (first 60 primes).")
        print("  2-FWL robustness check is vacuous on this enumeration.")
        return

    print()
    print("=" * 78)
    print("  2-FWL RESOLUTION TEST ON k=7 MULTI-CLASS PROFILES")
    print("=" * 78)

    resolved = 0
    unresolved = 0
    unresolved_examples = []
    fwl2_registry = {}  # shared across all configs so signatures are comparable
    for (k, profile), rows in sorted(multi_profiles.items()):
        sigs_to_classes = defaultdict(set)
        sigs_to_rows = defaultdict(list)
        for cls, config in rows:
            cancels, member, vt, n = build_labeled_graph(config, table)
            sig = two_fwl_signature(cancels, member, vt, n, fwl2_registry)
            sig_hash = hash(sig)
            sigs_to_classes[sig_hash].add(cls)
            sigs_to_rows[sig_hash].append((cls, config))
        ambig = {s: cs for s, cs in sigs_to_classes.items() if len(cs) > 1}
        n_distinct = len(sigs_to_classes)
        n_ambig = len(ambig)
        status = "RESOLVED" if not ambig else "UNRESOLVED"
        print(
            f"  profile={profile} classes={sorted({c for c, _ in rows})} "
            f"n_configs={len(rows)} n_sigs={n_distinct} ambig={n_ambig} → {status}",
            flush=True,
        )
        if ambig:
            unresolved += 1
            for s, cs in ambig.items():
                unresolved_examples.append((profile, sorted(cs), sigs_to_rows[s]))
        else:
            resolved += 1

    print()
    print(f"Multi-class profiles total:           {len(multi_profiles)}")
    print(f"Resolved by 2-FWL (full edge types):  {resolved}")
    print(f"Unresolved (2-FWL-equivalent pairs):  {unresolved}")

    if unresolved_examples:
        print()
        print("=" * 78)
        print("  2-FWL-UNRESOLVED CONFIGURATIONS AT k=7 (genuine residue)")
        print("=" * 78)
        for profile, classes, rows in unresolved_examples:
            print(f"\n  profile={profile} classes={classes}")
            for cls, cfg in rows:
                print(f"    [{cls}] {cfg}")


if __name__ == "__main__":
    main()
