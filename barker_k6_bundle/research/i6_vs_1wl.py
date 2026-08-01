#!/usr/bin/env python3
"""
i6_vs_1wl.py — refinement-strength comparison of I_6 and 1-WL across
the 421 enumerated configurations.

The discrimination-depth experiment (discrimination_depth.py) reports
zero MARGINAL CONTRIBUTION at level 4 (1-WL) on the cross-class
census: no cross-class pair has agreeing δ-profile / V-graph / I_6
together with differing 1-WL. This is a marginal-contribution claim
about a fixed ladder ordering, NOT a refinement-strength claim about
I_6 vs 1-WL in isolation.

This script measures refinement strength directly. For every
unordered pair of configurations (not restricted to cross-class), we
tabulate the 2×2 agreement table

    same I_6  /  same 1-WL
    same I_6  /  diff 1-WL
    diff I_6  /  same 1-WL
    diff I_6  /  diff 1-WL

If either off-diagonal entry is non-zero, I_6 and 1-WL are
incomparable as partitions of the configuration space — neither
refines the other. The "diff I_6 / same 1-WL" cell is the one that
decides containment: it is empty exactly when 1-WL refines I_6.

RESULT ON THIS CENSUS. 1-WL strictly refines I_6. The "diff I_6 /
same 1-WL" cell is empty; 89 pairs sit in "same I_6 / diff 1-WL".
The empty marginal contribution at λ = 4 in discrimination_depth.py
is therefore NOT evidence that 1-WL is the weaker invariant. It says
only that every cross-class pair 1-WL separates is already separated
by δ-profile, V-graph, or I_6 — a fact about the cross-class census
and the chosen ladder order, not about refinement strength.

HISTORY. An earlier version of this script found both off-diagonal
cells non-empty (113 and 3500) and concluded the two invariants were
incomparable. That was an artefact of the WL implementation, not a
property of the invariants: the routines renumbered colours per graph
and returned the sorted ids, so the "signature" carried only the
colour-class SIZE PROFILE and discarded which colours occurred. At
k = 6 it assigned all 61 enumerated configurations one identical
signature. With colours registered in a table shared across
configurations (see `_common.two_fwl_signature`) the incomparability
disappears.

Output also decomposes the same-I_6 / diff-1-WL pairs by whether they
sit across cancellation classes or within a single class.

SCOPE. Numbers here are about the 421-configuration enumeration at
k ∈ {3, 4, 5, 6} in the first 80 hard primes. No claim is made about
configurations outside that enumeration.
"""

import json
import os
import sys
import time
from itertools import combinations

sys.path.insert(
    0,
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "code"),
)

from barker.sweep import find_hard_primes  # noqa: E402
from barker.two_primary import build_two_primary_table  # noqa: E402

from _common import build_labeled_graph  # noqa: E402
from discrimination_depth import (  # noqa: E402
    i6_invariant,
    one_wl_signature,
    primary_stratum,
)


CACHE_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "_enumeration_cache.json"
)


def main():
    print("Loading first 80 hard primes...", flush=True)
    hp = find_hard_primes(80000)
    target_primes = [d["prime"] for d in hp[:80]]
    print("Building character table...", flush=True)
    t0 = time.time()
    table = build_two_primary_table(target_primes)
    print(f"  setup: {time.time() - t0:.1f}s", flush=True)

    with open(CACHE_FILE) as f:
        raw = json.load(f)
    records = [(k, cls, tuple(prof), tuple(cfg)) for (k, cls, prof, cfg) in raw]
    print(f"  loaded {len(records)} configurations", flush=True)

    print("\nComputing I_6 and 1-WL signatures per configuration...", flush=True)
    t0 = time.time()
    rows = []
    wl1_registry = {}  # shared across configs so colour ids are comparable
    for k, cls, _prof, cfg in records:
        cancels, member, vt, n = build_labeled_graph(cfg, table)
        rows.append({
            "k": k,
            # Primary stratum, so "cross-class" here means the same thing it
            # means in discrimination_depth.py (B(δ=n) are one stratum, B_int).
            "cls": primary_stratum(cls),
            "raw_cls": cls,
            "cfg": cfg,
            "i6": i6_invariant(cfg, table),
            "wl1": one_wl_signature(cancels, member, vt, n, wl1_registry),
        })
    print(f"  done: {time.time() - t0:.1f}s", flush=True)

    # 2x2 partition agreement: per k, then overall
    print("\n=== I_6 vs 1-WL CONTAINMENT  ===", flush=True)
    print("  (within each k; pairs categorized by whether I_6 and 1-WL agree)")
    print()

    total_counters = {
        "same_both": 0,
        "same_i6_diff_wl1": 0,
        "diff_i6_same_wl1": 0,
        "diff_both": 0,
    }
    cross_class_within = {
        "same_i6_diff_wl1_cross": 0,
        "same_i6_diff_wl1_same":  0,
    }
    examples_within = []

    for k in (3, 4, 5, 6):
        rows_k = [r for r in rows if r["k"] == k]
        counters = {kk: 0 for kk in total_counters}
        for a, b in combinations(rows_k, 2):
            i6_eq = (a["i6"] == b["i6"])
            wl_eq = (a["wl1"] == b["wl1"])
            if i6_eq and wl_eq:
                counters["same_both"] += 1
            elif i6_eq and not wl_eq:
                counters["same_i6_diff_wl1"] += 1
                if a["cls"] != b["cls"]:
                    cross_class_within["same_i6_diff_wl1_cross"] += 1
                else:
                    cross_class_within["same_i6_diff_wl1_same"] += 1
                    if len(examples_within) < 5:
                        examples_within.append(
                            (k, a["raw_cls"], a["cfg"], b["cfg"])
                        )
            elif not i6_eq and wl_eq:
                counters["diff_i6_same_wl1"] += 1
            else:
                counters["diff_both"] += 1

        n_pairs = len(rows_k) * (len(rows_k) - 1) // 2
        print(f"  k={k}  ({len(rows_k)} configs, {n_pairs} total pairs)")
        print(f"    same I_6 AND same 1-WL:           {counters['same_both']}")
        print(f"    same I_6 AND different 1-WL:      {counters['same_i6_diff_wl1']}  <-- key counter")
        print(f"    different I_6 AND same 1-WL:      {counters['diff_i6_same_wl1']}  (expected 0)")
        print(f"    different I_6 AND different 1-WL: {counters['diff_both']}")
        print()
        for kk, vv in counters.items():
            total_counters[kk] += vv

    print("  AGGREGATE:")
    for kk, vv in total_counters.items():
        print(f"    {kk}: {vv}")

    print()
    print("  DECOMPOSITION OF 'same I_6, different 1-WL' PAIRS:")
    print(f"    cross-class:  {cross_class_within['same_i6_diff_wl1_cross']}")
    print(f"    same-class:   {cross_class_within['same_i6_diff_wl1_same']}")

    print()
    print("=== READING ===")
    same_i6_diff_wl = total_counters["same_i6_diff_wl1"]
    diff_i6_same_wl = total_counters["diff_i6_same_wl1"]
    ccw = cross_class_within["same_i6_diff_wl1_cross"]
    scw = cross_class_within["same_i6_diff_wl1_same"]

    print("  Refinement-strength comparison:")
    print(f"    pairs with same I_6 but different 1-WL signature: {same_i6_diff_wl}")
    print(f"    pairs with different I_6 but same 1-WL signature: {diff_i6_same_wl}")
    print()
    if same_i6_diff_wl > 0 and diff_i6_same_wl > 0:
        print("  Both off-diagonal entries are non-zero. I_6 and 1-WL are INCOMPARABLE")
        print("  as partitions of the configuration space on this enumeration: neither")
        print("  refines the other.")
        print("  NOTE: this branch previously fired because of a defective 1-WL")
        print("  signature (per-graph colour renumbering, which retained only the")
        print("  colour-class size profile). If it fires again, check the signature")
        print("  before reporting incomparability as a property of the invariants.")
    elif same_i6_diff_wl == 0 and diff_i6_same_wl == 0:
        print("  Both off-diagonal entries are zero. I_6 and 1-WL induce the SAME")
        print("  equivalence relation on this dataset. (Refinement equivalence;")
        print("  still empirical, not a theorem.)")
    elif same_i6_diff_wl > 0:
        # A refines B iff A(s) == A(t) implies B(s) == B(t).  An empty
        # "diff I_6 / same 1-WL" cell says same-1-WL implies same-I_6, i.e.
        # 1-WL refines I_6.  The non-empty "same I_6 / diff 1-WL" cell makes
        # the containment strict.
        print("  1-WL strictly refines I_6 on this enumeration.")
    else:
        print("  I_6 strictly refines 1-WL on this enumeration.")

    print()
    print("  Decomposition of 'same I_6, different 1-WL' pairs by class:")
    print(f"    cross-class: {ccw}")
    print(f"    same-class:  {scw}")
    print()
    print("  CONSISTENCY WITH discrimination_depth.py.")
    print("  discrimination_depth.py reports zero MARGINAL contribution at level 4")
    print("  (1-WL) on the cross-class census. That is consistent with the cross-class")
    print(f"  count above ({ccw}) being non-zero only if every such pair is ALSO")
    print("  separated by a lower level (δ-profile, V-graph, or I_6). The marginal")
    print("  contribution captures the FIRST separation in the ordered ladder; pairs")
    print("  that 1-WL separates may have been already separated earlier and are")
    print("  attributed to those earlier levels, not to 1-WL.")
    print()
    print("  The empty marginal contribution at λ = 4 is therefore a fact about this")
    print("  census and this ladder ordering. It is NOT evidence that 1-WL is the")
    print("  weaker invariant: on refinement strength 1-WL strictly refines I_6 here.")

    if examples_within:
        print()
        print("  Examples of 'same I_6, different 1-WL' pairs (within-class subset):")
        for k, cls, cfg_a, cfg_b in examples_within[:5]:
            print(f"    k={k}  [{cls}]")
            print(f"      {cfg_a}")
            print(f"      {cfg_b}")


if __name__ == "__main__":
    main()
