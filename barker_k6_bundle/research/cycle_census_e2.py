#!/usr/bin/env python3
"""
cycle_census_e2.py — E2: extend the chordless-cycle census in G_x[V_x] across
universe sizes and settle the odd-cycle deficit claimed in finding N2.

Two objects per universe size N:
  EMPIRICAL: number of chordless directed ℓ-cycles in G_x[V_x], summed over all
             hubs x (counted as (hub, cycle) incidences), for ℓ = 2..6.
  NULL (reciprocity-corrected, Monte Carlo): the same count under the model
             - each unordered pair {p,q} ⊆ V_x carries a shared fair Legendre
               coin S ∈ {+1,-1} (quadratic reciprocity ties (p/q)=(q/p) for
               p,q ≡ 1 mod 4, so it is ONE coin per pair);
             - if S = -1 the pair carries NO edge either way (verified below as
               a hard empirical constraint);
             - if S = +1 then p→q is present w.p. 2^{-(t_p-1)} and q→p w.p.
               2^{-(t_q-1)}, independently (the higher 2-adic bits matching the
               edge target -χ_p(x), uniform under Chebotarev).
The independence null (no reciprocity) would instead make each directed edge
present w.p. 2^{-t_p} independently. The reciprocity coupling is the only
difference; N2 claims it makes the null exact at EVEN ℓ and leaves a deficit at
ODD ℓ. E2 asks whether that odd deficit grows or washes out as N increases.

Per-length z = (empirical - null_mean)/null_sd is the decisive statistic:
a real odd-length deficit hardens (|z| grows with N); noise does not.
"""
from __future__ import annotations
import sys, os, math
from itertools import combinations

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "code"))
from barker.two_primary import build_two_primary_table, quotient_class, legendre_layer
from barker.sweep import find_hard_primes

# deterministic PRNG (no Math.random equivalent needed; seedable for reproducibility)
import random

MAXLEN = 6
SIZES = [80, 120, 160]
TRIALS = 300
SEED = 2026


def chordless_cycle_counts(adj: dict, verts: list, max_len: int) -> dict:
    """Count chordless simple directed cycles by length in the digraph `adj`
    (adj[v] = set of out-neighbours). A length-ℓ directed cycle is chordless
    iff the induced subgraph on its ℓ vertices has exactly the ℓ cycle edges."""
    counts = {l: 0 for l in range(2, max_len + 1)}
    seen: set = set()
    vert_index = {v: i for i, v in enumerate(verts)}

    def dfs(start, path, pathset):
        last = path[-1]
        for nxt in adj.get(last, ()):  # extend
            if nxt == start and len(path) >= 2:
                key = canon(path)
                if key not in seen:
                    seen.add(key)
                    if is_chordless(path):
                        counts[len(path)] += 1
            elif (nxt not in pathset and len(path) < max_len
                  and vert_index[nxt] > vert_index[start]):
                # only extend to vertices indexed above start → each cycle's
                # minimal-index vertex is the unique start, killing rotations
                path.append(nxt); pathset.add(nxt)
                dfs(start, path, pathset)
                path.pop(); pathset.discard(nxt)

    def canon(path):
        # cycle already rooted at its min-index vertex (the start); fix direction
        n = len(path)
        fwd = tuple(path)
        return fwd

    def is_chordless(path):
        s = set(path)
        cyc_edges = set((path[i], path[(i + 1) % len(path)]) for i in range(len(path)))
        for v in path:
            for u in adj.get(v, ()):
                if u in s and (v, u) not in cyc_edges:
                    return False
        return True

    for start in verts:
        dfs(start, [start], {start})
    return counts


def build_empirical(primes):
    """Return (table, hub_data) where hub_data[x] = (verts, adj, pair_coin,
    depth) for every hub with >= 2 V_x vertices. Also returns invariants."""
    table = build_two_primary_table(primes)
    hub_data = {}
    n_pairs = 0
    n_neg_pairs = 0
    n_neg_with_edge = 0
    n_px_not_plus = 0
    for x in primes:
        verts = [p for p in primes if p != x and table.chi[(p, x)] == 0]
        if len(verts) < 2:
            continue
        # reciprocity invariant: (p/x) = +1 for all p in V_x
        for p in verts:
            if legendre_layer(p, x) != 1:
                n_px_not_plus += 1
        adj = {v: set() for v in verts}
        for pi in verts:
            t_i = table.depth[pi]
            neg_a = (-table.chi[(x, pi)]) % (2 ** t_i)
            for pj in verts:
                if pj != pi and table.chi[(pj, pi)] == neg_a:
                    adj[pi].add(pj)
        pair_coin = {}
        for p, q in combinations(verts, 2):
            s = legendre_layer(p, q)  # (p/q); equals (q/p) by reciprocity
            pair_coin[frozenset((p, q))] = s
            n_pairs += 1
            if s == -1:
                n_neg_pairs += 1
                if (q in adj[p]) or (p in adj[q]):
                    n_neg_with_edge += 1
        hub_data[x] = (verts, adj, pair_coin)
    invariants = dict(n_pairs=n_pairs, n_neg_pairs=n_neg_pairs,
                      n_neg_with_edge=n_neg_with_edge, n_px_not_plus=n_px_not_plus)
    return table, hub_data, invariants


def null_trial(table, hub_data, rng):
    counts = {l: 0 for l in range(2, MAXLEN + 1)}
    for x, (verts, _adj, _coin) in hub_data.items():
        adj = {v: set() for v in verts}
        for p, q in combinations(verts, 2):
            if rng.random() < 0.5:  # shared fair Legendre coin = +1
                tp = table.depth[p]; tq = table.depth[q]
                if rng.random() < 2.0 ** (-(tp - 1)):
                    adj[p].add(q)
                if rng.random() < 2.0 ** (-(tq - 1)):
                    adj[q].add(p)
        c = chordless_cycle_counts(adj, verts, MAXLEN)
        for l in counts:
            counts[l] += c[l]
    return counts


def main():
    for N in SIZES:
        primes = [r["prime"] for r in find_hard_primes(2_000_000)[:N]]
        if len(primes) < N:
            print(f"N={N}: only {len(primes)} hard primes available; skipping")
            continue
        table, hub_data, inv = build_empirical(primes)
        emp = {l: 0 for l in range(2, MAXLEN + 1)}
        for x, (verts, adj, _coin) in hub_data.items():
            c = chordless_cycle_counts(adj, verts, MAXLEN)
            for l in emp:
                emp[l] += c[l]

        rng = random.Random(SEED + N)
        trials = [null_trial(table, hub_data, rng) for _ in range(TRIALS)]
        null_mean = {l: sum(t[l] for t in trials) / TRIALS for l in emp}
        null_sd = {l: math.sqrt(sum((t[l] - null_mean[l]) ** 2 for t in trials) / TRIALS)
                   for l in emp}

        print(f"\n{'='*70}\nN = {N}   hubs with |V_x|>=2: {len(hub_data)}   "
              f"range {primes[0]}..{primes[-1]}")
        print(f"  reciprocity invariants: (p/x)=+1 violations = {inv['n_px_not_plus']}; "
              f"S=-1 pairs = {inv['n_neg_pairs']}/{inv['n_pairs']}, "
              f"of which carry an edge = {inv['n_neg_with_edge']}")
        print(f"  {'ℓ':>2} {'parity':>6} {'empirical':>10} {'null_mean':>10} "
              f"{'null_sd':>8} {'z':>7}")
        for l in range(2, MAXLEN + 1):
            sd = null_sd[l] if null_sd[l] > 1e-9 else float('nan')
            z = (emp[l] - null_mean[l]) / sd if sd == sd else float('nan')
            par = "even" if l % 2 == 0 else "ODD"
            print(f"  {l:>2} {par:>6} {emp[l]:>10} {null_mean[l]:>10.2f} "
                  f"{null_sd[l]:>8.2f} {z:>7.2f}")


if __name__ == "__main__":
    main()
