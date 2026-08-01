#!/usr/bin/env python3
"""
witness_complex.py — exploratory probe #2 (research/, post-v1.0).

The 0-cochain probe (defect_signature.py) showed that linear-sum
vanishing alone does not separate Type B beyond the definitional
split. The obstruction is relational: it should live in how
cancellation data on pairs (and higher subsets) glues across overlaps.

This script computes, for each known configuration C of hard primes
and the standard target system (first 80 hard primes augmented with
config-internal primes), three layers of structure:

  (V) V-witness complex K_V(C):
      simplices = subsets of {p in C : chi_x(p) = 0} for some target x.
      Type A has C itself as a top simplex (the hub provides it).
      For Type B no single target witnesses all of C; K_V(C) has lower
      dimension.

  (P) Pair-cancellation bipartite incidence:
      pairs {p, q} subset C  <->  targets x with chi_x(p)+chi_x(q)=0.
      Type A: the hub cancels all (k choose 2) pairs simultaneously.
      Type B prediction: pairs are covered, but no single target
      dominates; coverage is distributed.

  (T) Triple-cancellation count:
      (T, x) pairs with sum_{p in T} chi_x(p) = 0, |T| = 3.

For each configuration the report includes:
  - max V-simplex size                 (= k for Type A by definition)
  - number of maximal V-simplices
  - max pair-coverage at a single target (= C(k,2) iff a "pair-hub" exists)
  - minimum pair-cover number          (fewest targets touching all pairs;
                                        exact — the greedy value is reported
                                        alongside it as an upper bound)
  - triple-cancellation count
  - distribution of pair-coverage per target (concentration vs distribution)

Run from repo root:
    python3 barker_k6_bundle/research/witness_complex.py
"""

import os
import sys
from collections import Counter, defaultdict
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


def v_witness_complex(C, target_universe, table):
    """V_x ∩ C for every target x; return maximal simplices."""
    V_sets = {}
    for x in target_universe:
        if x not in table.depth:
            continue
        members = frozenset(p for p in C if p != x and table.chi[(p, x)] == 0)
        if members:
            V_sets.setdefault(members, []).append(x)

    distinct = list(V_sets.keys())
    maximal = []
    for s in distinct:
        if not any((s < t) for t in distinct):
            maximal.append(s)

    max_size = max((len(s) for s in distinct), default=0)
    return {
        "all_V_subsets": V_sets,
        "maximal_simplices": maximal,
        "max_simplex_size": max_size,
        "num_distinct_V_subsets": len(distinct),
    }


def pair_cancellation_incidence(C, target_universe, table):
    """Bipartite: pairs {p,q} in C <-> targets x where chi_x(p)+chi_x(q)=0."""
    pairs = list(combinations(C, 2))
    n_pairs = len(pairs)

    pair_to_targets = defaultdict(list)
    target_to_pairs = defaultdict(list)
    for x in target_universe:
        if x not in table.depth:
            continue
        mod = 2 ** table.depth[x]
        for (p, q) in pairs:
            if p == x or q == x:
                continue
            s = (table.chi[(p, x)] + table.chi[(q, x)]) % mod
            if s == 0:
                pair_to_targets[(p, q)].append(x)
                target_to_pairs[x].append((p, q))

    max_single = max((len(v) for v in target_to_pairs.values()), default=0)
    target_at_max = [x for x, v in target_to_pairs.items() if len(v) == max_single]

    # Greedy cover of pairs by targets.  Greedy is an UPPER BOUND on the
    # minimum cover, not the minimum itself.
    covers = {x: set(plist) for x, plist in target_to_pairs.items()}
    work = set(pairs)
    chosen = []
    while work:
        best_x, best_set = None, set()
        for x, pset in covers.items():
            covered_here = work & pset
            if len(covered_here) > len(best_set):
                best_x, best_set = x, covered_here
        if not best_set:
            break
        chosen.append((best_x, len(best_set)))
        work -= best_set

    uncovered_pairs = list(work)

    # Exact minimum: only sizes strictly below the greedy result need testing,
    # and each such search is over the targets that witness at least one pair.
    min_cover_size = len(chosen) if not uncovered_pairs else None
    if min_cover_size is not None:
        candidates = sorted(covers)
        target_pairs = set(pairs) - set(uncovered_pairs)
        for size in range(1, len(chosen)):
            if any(set().union(*(covers[x] for x in sub)) >= target_pairs
                   for sub in combinations(candidates, size)):
                min_cover_size = size
                break

    pair_coverage_dist = Counter(len(v) for v in pair_to_targets.values())

    return {
        "n_pairs": n_pairs,
        "n_pairs_covered": n_pairs - len(uncovered_pairs),
        "uncovered_pairs": uncovered_pairs,
        "max_single_target_coverage": max_single,
        "target_at_max": target_at_max[:3],
        "is_pair_hub_present": max_single == n_pairs,
        "min_cover_size": min_cover_size,
        "greedy_cover_size": len(chosen),
        "greedy_cover_targets": chosen,
        "pair_coverage_dist": dict(sorted(pair_coverage_dist.items())),
        "target_pair_count_dist": Counter(len(v) for v in target_to_pairs.values()),
    }


def triple_cancellation_count(C, target_universe, table):
    """Count (triple, target) cancellations: sum_{p in T} chi_x(p) = 0, |T|=3."""
    triples = list(combinations(C, 3))
    triple_to_targets = defaultdict(list)
    target_to_triples = defaultdict(list)
    for x in target_universe:
        if x not in table.depth:
            continue
        mod = 2 ** table.depth[x]
        for T in triples:
            if x in T:
                continue
            s = sum(table.chi[(p, x)] for p in T) % mod
            if s == 0:
                triple_to_targets[T].append(x)
                target_to_triples[x].append(T)

    return {
        "n_triples": len(triples),
        "n_triples_with_cancellation": sum(1 for v in triple_to_targets.values() if v),
        "max_triples_at_single_target": max(
            (len(v) for v in target_to_triples.values()), default=0
        ),
        "total_triple_cancellation_incidences": sum(
            len(v) for v in target_to_triples.values()
        ),
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

    cls = classify_all_known()
    type_b = {tuple(sorted(r.config)) for r in cls.type_b}

    target_universe = sorted(set(all_primes))  # internal + external

    print()
    print("=" * 78)
    print("  WITNESS OVERLAP COMPLEX — pair- and triple-cancellation structure")
    print("=" * 78)

    summary_rows = []
    for C in configs:
        Cs = tuple(sorted(C))
        label = "B" if Cs in type_b else "A"
        n_pairs = len(Cs) * (len(Cs) - 1) // 2

        V = v_witness_complex(Cs, target_universe, table)
        P = pair_cancellation_incidence(Cs, target_universe, table)
        T = triple_cancellation_count(Cs, target_universe, table)

        print()
        print(f"k={len(Cs)}  [Type {label}]  {Cs}")
        print(
            f"  V-complex:  max simplex size = {V['max_simplex_size']}/{len(Cs)}  "
            f"({len(V['maximal_simplices'])} maximal, "
            f"{V['num_distinct_V_subsets']} distinct V_x∩C subsets)"
        )
        # Show a few maximal simplices
        maxs = sorted(V["maximal_simplices"], key=lambda s: (-len(s), tuple(sorted(s))))
        for s in maxs[:4]:
            print(f"    maximal: {sorted(s)}")
        if len(maxs) > 4:
            print(f"    ... and {len(maxs) - 4} more")

        print(
            f"  pair-cancellation:  {n_pairs} pairs total, "
            f"{P['n_pairs_covered']} covered; "
            f"max single-target coverage = {P['max_single_target_coverage']}/{n_pairs} "
            f"{'[PAIR-HUB present]' if P['is_pair_hub_present'] else '[no pair-hub]'}"
        )
        if P["target_at_max"]:
            tag = ", ".join(
                f"{x}{'∈C' if x in Cs else ''}" for x in P["target_at_max"]
            )
            print(f"    target(s) at max: {tag}")
        print(
            f"    min-cover: {P['min_cover_size']} targets   "
            f"(greedy: {P['greedy_cover_size']}, steps: "
            f"{P['greedy_cover_targets'][:5]}"
            f"{'...' if len(P['greedy_cover_targets']) > 5 else ''})"
        )
        if P["uncovered_pairs"]:
            print(f"    uncovered pairs: {P['uncovered_pairs']}")
        print(
            f"    pair-coverage degree distribution: "
            f"{P['pair_coverage_dist']}"
        )
        print(
            f"  triple-cancellation:  "
            f"{T['n_triples_with_cancellation']}/{T['n_triples']} triples ever cancel; "
            f"total incidences = {T['total_triple_cancellation_incidences']}; "
            f"max triples at single target = {T['max_triples_at_single_target']}"
        )

        summary_rows.append((label, len(Cs), Cs, V, P, T, n_pairs))

    # Comparative summary
    print()
    print("=" * 78)
    print("  SUMMARY")
    print("=" * 78)
    print(
        f"{'Type':4} {'k':>2}  {'config':36}  "
        f"{'V-dim':5} {'maxPC':>5} {'pairs':>5} {'cover':>5} {'hub?':>4} {'#trip':>5}"
    )
    for label, k, Cs, V, P, T, n_pairs in sorted(summary_rows, key=lambda r: (r[0], r[1])):
        cfg_str = str(Cs)
        if len(cfg_str) > 34:
            cfg_str = cfg_str[:31] + "..."
        print(
            f"{label:4} {k:>2}  {cfg_str:36}  "
            f"{V['max_simplex_size']:>5} "
            f"{P['max_single_target_coverage']:>5} "
            f"{n_pairs:>5} "
            f"{P['min_cover_size']:>5} "
            f"{'Y' if P['is_pair_hub_present'] else 'N':>4} "
            f"{T['n_triples_with_cancellation']:>5}"
        )

    # Type-aggregated comparison
    print()
    print("-" * 78)
    print(
        "  Reading the columns:  V-dim = max |V_x ∩ C|;  "
        "maxPC = max pairs cancelled at a single target;"
    )
    print(
        "  pairs = (k choose 2);  cover = exact minimum cover size;  "
        "hub? = Y iff one target cancels all pairs;"
    )
    print(
        "  #trip = number of distinct triples that cancel at >= 1 target."
    )


if __name__ == "__main__":
    main()
