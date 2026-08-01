#!/usr/bin/env python3
"""
discrimination_depth.py — exhaustive census of the marginal
discrimination contribution of each level of a fixed invariant ladder
on cross-class pairs in the 421-configuration enumeration.

For each pair (S, T) of configurations in different strata of the
six primary strata of §4, the discrimination-depth function is

    λ(S, T) = min{ r : level-r invariant of S differs from that of T }.

The ladder of structural invariants:

    level 1 — δ-profile          (sorted multiset of |V_x ∩ (S \\ {x})|)
    level 2 — V-graph canonical  (min-lex permutation of V_x adjacency)
    level 3 — I_6                (joint (target_load, pair_witness) multiset
                                  at each 1-cell of the incidence matrix)
    level 4 — 1-WL               (stable color signature from 1-dimensional
                                  Weisfeiler–Lehman refinement on the labeled
                                  bipartite cancellation+membership graph)
    level 5 — 2-FWL              (stable signature from 2-dimensional folklore
                                  Weisfeiler–Lehman refinement on the same
                                  labeled bipartite graph)

Reports the marginal contribution at each level (how many cross-class
pairs are FIRST separated at level r), and lists pairs at each depth.

SCOPE. The output is an exhaustive census of cross-class pairs over
the 421 enumerated configurations at k ∈ {3, 4, 5, 6} in the first
80 hard primes. The distribution shape is reported as a fact about
this enumeration; no claim is made that it persists at larger k or
a wider prime universe.

REFINEMENT STRENGTH vs MARGINAL CONTRIBUTION. These are two distinct
notions and a level may score differently on each. On this census the
1-WL stable color signature (level 4) strictly refines I_6 (level 3):
no pair of configurations shares a 1-WL signature while differing in
I_6, and 89 pairs share I_6 while differing in 1-WL (`i6_vs_1wl.py`).
Level 4 nevertheless has zero MARGINAL contribution, because every
cross-class pair it separates is already separated by the δ-profile,
the V-graph or I_6. Zero marginal contribution is therefore a
statement about this census and this ladder ordering, not a statement
that level 4 is a weaker invariant than level 3.
"""

import json
import os
import sys
import time
from collections import Counter, defaultdict
from itertools import combinations, permutations

sys.path.insert(
    0,
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "code"),
)

from barker.sweep import find_hard_primes  # noqa: E402
from barker.two_primary import build_two_primary_table  # noqa: E402

from _common import build_labeled_graph, two_fwl_signature  # noqa: E402


CACHE_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "_enumeration_cache.json"
)


def primary_stratum(cls):
    """Collapse a cache label to its PRIMARY stratum.

    The taxonomy of §4 has six mutually exclusive primary strata —
    A1, A2, A3, B0, B1, B_int — and the cache spells interior-B labels with
    their δ_max annotation attached ("B(δ=1)", "B(δ=2)", "B(δ=3)").  Those are
    one stratum, not three: δ_max is a secondary annotation on B_int, and
    A_blocked is an overlapping refinement flag rather than a seventh stratum.

    Comparing raw labels therefore counted within-B_int pairs as cross-stratum.
    At k = 6 the B_int groups have sizes 3, 7, 3, contributing
    3·7 + 3·3 + 7·3 = 51 spurious "cross-class" pairs, all of which separate at
    the δ-profile level — which is exactly why the error inflated λ = 1 and the
    total by 51 while leaving every other level untouched.
    """
    return "B_int" if cls.startswith("B(") else cls


# ---------------------------------------------------------------------------
# Level 1: δ-profile
# ---------------------------------------------------------------------------

def delta_profile(C, table):
    Cs = sorted(C)
    deltas = [sum(1 for q in Cs if q != p and table.chi[(q, p)] == 0) for p in Cs]
    return tuple(sorted(deltas, reverse=True))


# ---------------------------------------------------------------------------
# Level 2: V-graph canonical isomorphism class
# ---------------------------------------------------------------------------

def vgraph_canonical(C, table):
    """Min-lex flattened adjacency matrix of the directed V-graph on S."""
    Cs = sorted(C)
    k = len(Cs)
    adj = [
        [1 if (i != j and table.chi[(Cs[j], Cs[i])] == 0) else 0
         for j in range(k)]
        for i in range(k)
    ]
    best = None
    for perm in permutations(range(k)):
        flat = tuple(adj[perm[i]][perm[j]] for i in range(k) for j in range(k))
        if best is None or flat < best:
            best = flat
    return best


# ---------------------------------------------------------------------------
# Level 3: I_6 — joint (target_load, pair_witness) multiset
# ---------------------------------------------------------------------------

def i6_invariant(C, table):
    Cs = sorted(C)
    k = len(Cs)
    pairs = list(combinations(range(k), 2))
    n_pairs = len(pairs)
    M = [[0] * n_pairs for _ in range(k)]
    for i in range(k):
        x = Cs[i]
        mod = 2 ** table.depth[x]
        for pi, (a, b) in enumerate(pairs):
            if a == i or b == i:
                M[i][pi] = -1
                continue
            s = (table.chi[(Cs[a], x)] + table.chi[(Cs[b], x)]) % mod
            M[i][pi] = 1 if s == 0 else 0
    target_loads = [sum(1 for p in range(n_pairs) if M[i][p] == 1) for i in range(k)]
    pair_witnesses = [
        sum(1 for i in range(k) if M[i][p] == 1) for p in range(n_pairs)
    ]
    joint = []
    for i in range(k):
        for p in range(n_pairs):
            if M[i][p] == 1:
                joint.append((target_loads[i], pair_witnesses[p]))
    return tuple(sorted(joint))


# ---------------------------------------------------------------------------
# Level 4: 1-WL on the labeled bipartite graph
# ---------------------------------------------------------------------------

def one_wl_signature(cancels, member, vertex_types, n, registry, max_iter=100):
    """1-WL color refinement; per-node colors stabilised under labeled
    neighborhood multisets.

    Returns the sorted tuple of stable colour ids.  `registry` maps colour key
    -> int id and is SHARED (and mutated in place) across every graph whose
    signatures will be compared — see `_common.two_fwl_signature` for why the
    shared registry, rather than per-graph renumbering, is what makes the
    colours part of the signature.
    """
    colors = {}
    for u in range(n):
        c_deg = sum(1 for v in range(n) if (u, v) in cancels)
        m_deg = sum(1 for v in range(n) if (u, v) in member)
        colors[u] = registry.setdefault(
            (vertex_types[u], c_deg, m_deg), len(registry)
        )

    n_classes = len(set(colors.values()))
    for _ in range(max_iter):
        new_colors = {}
        for u in range(n):
            c_nbrs = tuple(sorted(colors[v] for v in range(n) if (u, v) in cancels))
            m_nbrs = tuple(sorted(colors[v] for v in range(n) if (u, v) in member))
            new_colors[u] = registry.setdefault(
                (colors[u], c_nbrs, m_nbrs), len(registry)
            )
        colors = new_colors
        new_n_classes = len(set(colors.values()))
        # Monotone refinement: no growth in class count means stable.
        if new_n_classes == n_classes:
            break
        n_classes = new_n_classes
    return tuple(sorted(colors.values()))


# ---------------------------------------------------------------------------
# Main experiment
# ---------------------------------------------------------------------------

LEVEL_NAMES = {1: "δ-profile", 2: "V-graph", 3: "I_6", 4: "1-WL", 5: "2-FWL"}


def main():
    print("Loading first 80 hard primes...", flush=True)
    hp = find_hard_primes(80000)
    target_primes = [d["prime"] for d in hp[:80]]
    print("Building character table...", flush=True)
    t0 = time.time()
    table = build_two_primary_table(target_primes)
    print(f"  setup: {time.time() - t0:.1f}s", flush=True)

    print(f"Loading cache from {os.path.basename(CACHE_FILE)}...", flush=True)
    with open(CACHE_FILE) as f:
        raw = json.load(f)
    records = [(k, cls, tuple(prof), tuple(cfg)) for (k, cls, prof, cfg) in raw]
    print(f"  loaded {len(records)} configurations", flush=True)

    print("\nComputing 5-level signatures per configuration...", flush=True)
    t0 = time.time()
    # One registry per WL level, shared across all configurations so that the
    # colour ids of different configurations are comparable.
    wl1_registry, fwl2_registry = {}, {}
    sigs = []
    for idx, (k, cls, _prof, cfg) in enumerate(records):
        cancels, member, vt, n = build_labeled_graph(cfg, table)
        sigs.append({
            # `cls` is the PRIMARY stratum and decides cross-stratum pairing;
            # `raw_cls` keeps the δ_max annotation for display only.
            "k": k, "cls": primary_stratum(cls), "raw_cls": cls, "cfg": cfg,
            "L1": delta_profile(cfg, table),
            "L2": vgraph_canonical(cfg, table),
            "L3": i6_invariant(cfg, table),
            "L4": one_wl_signature(cancels, member, vt, n, wl1_registry),
            "L5": two_fwl_signature(cancels, member, vt, n, fwl2_registry),
        })
        if (idx + 1) % 50 == 0:
            print(f"  {idx + 1}/{len(records)}  elapsed {time.time() - t0:.1f}s", flush=True)
    print(f"  signatures: {time.time() - t0:.1f}s", flush=True)

    # Compute λ for every cross-class pair within each k.
    by_k_hist = defaultdict(Counter)
    by_k_examples = defaultdict(lambda: defaultdict(list))
    overall_hist = Counter()

    print("\n=== DISCRIMINATION-DEPTH HISTOGRAMS ===", flush=True)
    for k in (3, 4, 5, 6):
        sigs_k = [s for s in sigs if s["k"] == k]
        cross = 0
        for i, j in combinations(range(len(sigs_k)), 2):
            sA, sB = sigs_k[i], sigs_k[j]
            if sA["cls"] == sB["cls"]:
                continue
            cross += 1
            lam = None
            for level_idx in (1, 2, 3, 4, 5):
                if sA[f"L{level_idx}"] != sB[f"L{level_idx}"]:
                    lam = level_idx
                    break
            if lam is None:
                lam = "inf"
            by_k_hist[k][lam] += 1
            overall_hist[lam] += 1
            if len(by_k_examples[k][lam]) < 5:
                by_k_examples[k][lam].append(
                    (sA["raw_cls"], sB["raw_cls"], sA["cfg"], sB["cfg"])
                )

        print(f"\n  k={k}  ({len(sigs_k)} configs, {cross} cross-class pairs)", flush=True)
        for lam in (1, 2, 3, 4, 5, "inf"):
            c = by_k_hist[k].get(lam, 0)
            if c == 0 and lam != "inf":
                continue
            pct = 100 * c / cross if cross else 0
            label = LEVEL_NAMES.get(lam, lam) if lam != "inf" else "UNRESOLVED"
            tag = f"λ={lam}" if lam != "inf" else "λ=∞"
            print(f"    {tag:>6} ({label:>10}): {c:>6}  ({pct:5.1f}%)")

    total_cross = sum(overall_hist.values())
    print(f"\n=== OVERALL  ({total_cross} cross-class pairs) ===", flush=True)
    for lam in (1, 2, 3, 4, 5, "inf"):
        c = overall_hist.get(lam, 0)
        pct = 100 * c / total_cross if total_cross else 0
        label = LEVEL_NAMES.get(lam, lam) if lam != "inf" else "UNRESOLVED"
        tag = f"λ={lam}" if lam != "inf" else "λ=∞"
        print(f"  {tag:>6} ({label:>10}): {c:>6}  ({pct:5.1f}%)")

    print("\n=== CROSS-CLASS PAIRS AT λ=5 (separated only by 2-FWL on this census) ===", flush=True)
    print("  Each pair listed agrees on every lower level (δ-profile, V-graph, I_6, 1-WL).")
    print("  These pairs are reported as a fact about the enumeration; a singleton is")
    print("  not evidence of a structural class.\n")
    any_l5 = False
    for k in (3, 4, 5, 6):
        examples = by_k_examples[k].get(5, [])
        if not examples:
            continue
        any_l5 = True
        n_at_k = by_k_hist[k].get(5, 0)
        print(f"  k={k}  ({n_at_k} such pair(s); showing up to {len(examples)}):")
        for cls_A, cls_B, cfg_A, cfg_B in examples:
            print(f"    [{cls_A}]  {cfg_A}")
            print(f"    [{cls_B}]  {cfg_B}")
            print()
    if not any_l5:
        print("  No cross-class pairs at λ=5 on this census.")
        print("  (Re-run with a wider parameter range to test whether this persists.)")

    print("\n=== λ=4 PAIRS (1-WL needed but 2-FWL not required)  ===", flush=True)
    for k in (3, 4, 5, 6):
        examples = by_k_examples[k].get(4, [])
        if not examples:
            continue
        n_at_k = by_k_hist[k].get(4, 0)
        print(f"  k={k}  ({n_at_k} such pairs; showing up to 2):")
        for cls_A, cls_B, cfg_A, cfg_B in examples[:2]:
            print(f"    [{cls_A}]  {cfg_A}")
            print(f"    [{cls_B}]  {cfg_B}")
            print()

    inf_count = overall_hist.get("inf", 0)
    print(f"\n=== SANITY CHECK ===")
    print(f"  unresolved cross-class pairs (λ=∞) on this census: {inf_count}")
    print(f"  expected: 0 on this enumeration (every cross-class pair is separated")
    print(f"  by some level of the ladder; persistence at larger k is not claimed)")


if __name__ == "__main__":
    main()
