"""
Pre-publication audit script — verifies all numerical and structural claims.
Run from barker_k6_bundle/ directory.
"""
from __future__ import annotations
import sys, os, time
from itertools import combinations
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "code"))

from barker.arithmetic import multiplicative_order, is_prime
from barker.two_primary import build_two_primary_table, quotient_class
from barker.sweep import find_hard_primes
from barker.o1_realizability import build_cycle_graph
from barker.o1_cycle_obstruction import find_all_cycles
from barker.minimal_cover_search import BadPairIndex

CONFIG = (17881, 1801, 14537, 13417, 18121, 18521)
HUB = 17881
CYCLE = (1801, 14537, 13417, 18121, 18521)


def check(cond, msg):
    """assert that survives python -O: setup failures must fail closed."""
    if not cond:
        raise SystemExit(f"AUDIT SETUP FAILED: {msg}")


results = []
def record(block, claim, computed, expected, status):
    results.append((block, claim, computed, expected, status))
    mark = "✓" if status == "PASS" else ("✗" if status == "FAIL" else "?")
    print(f"  [{mark}] {block} | {claim}: computed={computed} expected={expected}")

print("=" * 70)
print("AUDIT: Pre-publication verification")
print("=" * 70)

print("\n[Setup] Computing first 80 hard primes and 2-primary table...")
t0 = time.time()
hard_records = find_hard_primes(80000)
HARD80 = [r["prime"] for r in hard_records[:80]]
check(len(HARD80) >= 80, f"only got {len(HARD80)} hard primes")
HARD80 = HARD80[:80]
table = build_two_primary_table(HARD80)
print(f"  done in {time.time()-t0:.1f}s. range={HARD80[0]}..{HARD80[-1]}")

for p in CONFIG:
    check(p in HARD80, f"{p} not in first 80 hard primes")

# Block 3: directed-cycle counts in G_x[V_x] over first 80 hard primes
# This is a v1.0 sanity check on the per-hub cycle enumeration: it counts ALL
# directed cycles (not chordless single cycles) and aggregates over hubs without
# deduplicating to distinct A1 sets. The expected values 26/20/33/34 are from
# v1.0 §2 line 67. The §4.4 reconstruction in the current manuscript counts
# single chordless cycles at the distinct-A1-set level and is verified separately
# by Block 3b below.
print("\n[Block 3] All directed cycles in G_x[V_x] per hub (v1.0 §2 sanity check)...")
t0 = time.time()
prime_to_idx = {p: i for i, p in enumerate(HARD80)}
bpi = BadPairIndex(HARD80, table)

cycle_counts = {2: 0, 3: 0, 4: 0, 5: 0, 6: 0}
cycle_covering_counts = {2: 0, 3: 0, 4: 0, 5: 0, 6: 0}
mutual_edges_seen = set()

for hub in HARD80:
    g = build_cycle_graph(hub, HARD80, table)
    if g.n_vertices < 2:
        continue

    # k=2: mutual edges (p→q and q→p)
    for p, nexts in g.edges.items():
        for q in nexts:
            if q in g.edges and p in g.edges[q]:
                key = (hub, frozenset({p, q}))
                if key in mutual_edges_seen:
                    continue
                mutual_edges_seen.add(key)
                cycle_counts[2] += 1
                triple_idx = tuple(prime_to_idx[x] for x in (hub, p, q))
                if bpi.is_covering(triple_idx):
                    cycle_covering_counts[2] += 1

    cycles = find_all_cycles(g, max_length=6, table=table)
    for rec in cycles:
        k = rec.length
        cycle_counts[k] += 1
        full_set = (hub,) + rec.cycle
        idx = tuple(prime_to_idx[x] for x in full_set)
        if bpi.is_covering(idx):
            cycle_covering_counts[k] += 1

print(f"  done in {time.time()-t0:.1f}s")

# v1.0 §2 line 67 cycle counts: 26 triangles, 20 four-cycles, 33 five-cycles,
# 34 six-cycles. These are the (hub, cycle) totals from find_all_cycles over
# G_x[V_x] for all 80 hubs, without chordlessness filtering or A1-set dedup.
v10_k3 = 26
v10_k4 = 20
v10_k5 = 33
v10_k6 = 34
print(f"  Mutual edges (length 2): {cycle_counts[2]} (covering: {cycle_covering_counts[2]})")
print(f"  Triangles  (length 3): {cycle_counts[3]} (covering: {cycle_covering_counts[3]}) — v1.0: {v10_k3}")
print(f"  4-cycles   (length 4): {cycle_counts[4]} (covering: {cycle_covering_counts[4]}) — v1.0: {v10_k4}")
print(f"  5-cycles   (length 5): {cycle_counts[5]} (covering: {cycle_covering_counts[5]}) — v1.0: {v10_k5}")
print(f"  6-cycles   (length 6): {cycle_counts[6]} (covering: {cycle_covering_counts[6]}) — v1.0: {v10_k6}")

record("3", "k=3 triangle count", cycle_counts[3], v10_k3,
       "PASS" if cycle_counts[3] == v10_k3 else "FAIL")
record("3", "k=3 triangles all covering", cycle_covering_counts[3], cycle_counts[3],
       "PASS" if cycle_covering_counts[3] == cycle_counts[3] else "FAIL")
record("3", "k=4 four-cycle count", cycle_counts[4], v10_k4,
       "PASS" if cycle_counts[4] == v10_k4 else "FAIL")
record("3", "k=4 four-cycles all covering", cycle_covering_counts[4], cycle_counts[4],
       "PASS" if cycle_covering_counts[4] == cycle_counts[4] else "FAIL")
record("3", "k=5 five-cycle count", cycle_counts[5], v10_k5,
       "PASS" if cycle_counts[5] == v10_k5 else "FAIL")
record("3", "k=5 five-cycles all covering", cycle_covering_counts[5], cycle_counts[5],
       "PASS" if cycle_covering_counts[5] == cycle_counts[5] else "FAIL")
record("3", "k=6 six-cycle count", cycle_counts[6], v10_k6,
       "PASS" if cycle_counts[6] == v10_k6 else "FAIL")
record("3", "k=6 six-cycles all covering", cycle_covering_counts[6], cycle_counts[6],
       "PASS" if cycle_covering_counts[6] == cycle_counts[6] else "FAIL")

# Block 3b: §4.4 cofactor-cycle theorem reconstruction (INDEPENDENT path).
#
# Verifies the manuscript §4.4 table:
#     k | single chordless (k−1)-cycles | killed by containment | A1 (net) | A1 census
#     3 |  ?  |  ?  |  ?  |  68
#     4 |  ?  |  ?  |  ?  |   9
#     5 |  ?  |  ?  |  ?  |   7
#     6 |  ?  |  ?  |  ?  |   1
#     7 |  ?  |  ?  |  ?  | (predicted 1)
#
# Independent path: uses find_all_cycles (the v1.0 cycle enumerator) as the
# base enumerator, then layers on chordlessness filtering, A1-set dedup
# (collapse (hub, cycle) duplicates that produce the same set S = {x} ∪ C),
# and containment against the enumeration cache. The A1 census column is the
# anchor — it comes from profile_analysis.py's direct stratum enumeration on
# the cache, independent of any cycle counting. Disagreement between the
# reconstructed net and the census is the signal of a counting error in the
# manuscript's cycles or kills columns.
print("\n[Block 3b] §4.4 cofactor-cycle reconstruction (independent path)...")
t0 = time.time()

# Load cache for census A1 counts and containment filter
import json
cache_path = os.path.join(os.path.dirname(__file__), "research", "_enumeration_cache.json")
if not os.path.exists(cache_path):
    print(f"  [SKIP] Cache missing: {cache_path}")
    print(f"         Run profile_analysis.py to generate it (~50 min first time).")
else:
    with open(cache_path) as fh:
        cache = json.load(fh)
    a1_census = {3: 0, 4: 0, 5: 0, 6: 0}
    all_minimal_by_k: dict[int, list] = {3: [], 4: [], 5: [], 6: []}
    for rec in cache:
        k_rec, stratum, _profile, primes = rec
        all_minimal_by_k.setdefault(k_rec, []).append(frozenset(primes))
        if stratum == "A1" and k_rec in a1_census:
            a1_census[k_rec] += 1

    def is_chordless_cycle(cycle_tuple, edges_dict):
        """A directed cycle is chordless iff the induced subgraph on its vertex
        set contains exactly the cycle edges and no others."""
        n = len(cycle_tuple)
        cycle_edges = set((cycle_tuple[i], cycle_tuple[(i + 1) % n]) for i in range(n))
        vertices = set(cycle_tuple)
        for v in cycle_tuple:
            for u in edges_dict.get(v, []):
                if u in vertices and (v, u) not in cycle_edges:
                    return False
        return True

    # Enumerate candidate A1 sets at each size (deduped to distinct sets)
    candidate_a1_sets: dict[int, set] = {3: set(), 4: set(), 5: set(), 6: set(), 7: set()}
    for hub in HARD80:
        g = build_cycle_graph(hub, HARD80, table)
        if g.n_vertices < 2:
            continue
        # Length-2 (mutual edges): always chordless
        seen_pairs: set[frozenset] = set()
        for p, nexts in g.edges.items():
            for q in nexts:
                if q in g.edges and p in g.edges[q]:
                    pair = frozenset({p, q})
                    if pair in seen_pairs:
                        continue
                    seen_pairs.add(pair)
                    candidate_a1_sets[3].add(frozenset({hub} | pair))
        # Length 3-6: find_all_cycles + chordlessness filter
        for rec in find_all_cycles(g, max_length=6, table=table):
            k_set = rec.length + 1
            if k_set > 7:
                continue
            if is_chordless_cycle(rec.cycle, g.edges):
                candidate_a1_sets[k_set].add(frozenset({hub} | set(rec.cycle)))

    # Containment filter: kill S if any smaller minimal covering is strict subset
    print(f"  Reconstruction columns (distinct A1 sets after chordless filter and dedup):")
    print(f"  {'k':>3} {'cycles':>8} {'killed':>8} {'A1 (net)':>10} {'A1 census':>10} {'status':>8}")
    for k_size in (3, 4, 5, 6, 7):
        smaller = []
        for k_smaller in range(3, k_size):
            smaller.extend(all_minimal_by_k.get(k_smaller, []))
        killed = 0
        survivors = 0
        for S in candidate_a1_sets[k_size]:
            if any(M < S for M in smaller):
                killed += 1
            else:
                survivors += 1
        n_cycles = len(candidate_a1_sets[k_size])
        census = a1_census.get(k_size)
        if census is None:
            census_str = "(k=7 not in cache; predicted 1)"
            status = "PRED" if survivors == 1 else "FAIL-PRED"
        else:
            census_str = str(census)
            status = "PASS" if survivors == census else "FAIL"
        print(f"  {k_size:>3} {n_cycles:>8} {killed:>8} {survivors:>10} {census_str:>10} {status:>8}")
        if census is not None:
            record("3b", f"k={k_size} A1 reconstruction matches census",
                   survivors, census, status)
        else:
            # k=7 prediction — soft check
            record("3b", f"k=7 A1 prediction (net == 1)",
                   survivors, 1, "PASS" if survivors == 1 else "FAIL")

    print(f"  done in {time.time()-t0:.1f}s")

# Block 3c: §4.4 Theorem-A object column + disjoint-union split + cycle-pair count.
#
# Verifies the second and third columns of the §4.4 unified table:
#   cofactor m | single cycles | disjoint unions | total Theorem-A objects
#       2     |    68         |        0        |       68
#       3     |     9         |        0        |        9
#       4     |     7         |       27        |       34
#       5     |     1         |        3        |        4
#       6     |     1         |        5        |        6
#
# And reconciles the 32-vs-35 cycle-pair count from the disjoint-union frontier
# remark by enumerating each disjoint-union object's component count.
#
# Independent path: for each hub, enumerate all subsets C ⊆ V_x of size 2..6
# directly (no use of find_all_cycles), check whether the induced subgraph has
# in-deg=1 and out-deg=1 at every vertex (the Theorem A condition), and
# decompose into cycle components by following the unique out-edge from each
# vertex. This is the most-bookkeeping-dense object in the paper after the
# Layer-6 audit; it must be independently verified.
print("\n[Block 3c] §4.4 Theorem-A column + disjoint-union split + cycle-pair count...")
t0 = time.time()
# Map each DISTINCT Theorem-A object (set S = {hub} ∪ C) to its component count.
# Keying by the set deduplicates the case where one set arises under more than
# one hub role: at cofactor size 2 a 3-set {a,b,c} is a Theorem-A 2-cycle under
# each of its three vertices as hub, so 89 raw (hub, C) instances collapse to 68
# distinct sets. At sizes >= 3 no such collision occurs. The manuscript table
# columns count distinct sets, so dedup before splitting single vs union.
obj_components: dict[int, dict] = {2: {}, 3: {}, 4: {}, 5: {}, 6: {}}
for hub in HARD80:
    g = build_cycle_graph(hub, HARD80, table)
    if g.n_vertices < 2:
        continue
    Vx = g.vertices
    edges_set: set = set()
    for v, nexts in g.edges.items():
        for u in nexts:
            edges_set.add((v, u))
    for sz in range(2, 7):
        if sz > len(Vx):
            continue
        for C_tuple in combinations(Vx, sz):
            C = set(C_tuple)
            in_deg = {v: 0 for v in C}
            out_deg = {v: 0 for v in C}
            for v in C:
                for u in C:
                    if v != u and (v, u) in edges_set:
                        out_deg[v] += 1
                        in_deg[u] += 1
            if any(in_deg[v] != 1 or out_deg[v] != 1 for v in C):
                continue
            # Theorem-A object. Decompose into cycles via unique out-edges.
            unvisited = set(C)
            n_components = 0
            while unvisited:
                start = next(iter(unvisited))
                cur = start
                while cur in unvisited:
                    unvisited.discard(cur)
                    succ = None
                    for u in C:
                        if (cur, u) in edges_set:
                            succ = u
                            break
                    if succ is None:
                        break
                    cur = succ
                n_components += 1
            A1_set = frozenset({hub} | C)
            obj_components[sz][A1_set] = n_components
print(f"  done in {time.time()-t0:.1f}s")
print(f"  {'cofactor':>9} {'single':>7} {'unions':>7} {'Theorem-A total':>16}")
manuscript_table = {
    2: {"single": 68, "union": 0,  "total": 68},
    3: {"single":  9, "union": 0,  "total":  9},
    4: {"single":  7, "union": 27, "total": 34},
    5: {"single":  1, "union": 3,  "total":  4},
    6: {"single":  1, "union": 5,  "total":  6},
}
for sz in (2, 3, 4, 5, 6):
    comps = list(obj_components[sz].values())
    n_total = len(comps)
    n_single = sum(1 for nc in comps if nc == 1)
    n_union = sum(1 for nc in comps if nc >= 2)
    mb = manuscript_table[sz]
    status_single = "PASS" if n_single == mb["single"] else "FAIL"
    status_union  = "PASS" if n_union  == mb["union"]  else "FAIL"
    status_total  = "PASS" if n_total  == mb["total"]  else "FAIL"
    print(f"  {sz:>9} {n_single:>7} {n_union:>7} {n_total:>16}"
          f"  ({status_single}/{status_union}/{status_total} vs {mb['single']}/{mb['union']}/{mb['total']})")
    record("3c", f"cofactor m={sz}: single chordless cycles",
           n_single, mb["single"], status_single)
    record("3c", f"cofactor m={sz}: disjoint-union Theorem-A objects",
           n_union, mb["union"], status_union)
    record("3c", f"cofactor m={sz}: Theorem-A total",
           n_total, mb["total"], status_total)

# 32-vs-35 reconciliation. obj_components[sz] maps each distinct disjoint-union
# Theorem-A object to its component count. A 2-component object IS a cross-edge-free
# cycle pair; an n-component object (n >= 3) is NOT a "pair" but contributes C(n, 2)
# unordered pairs of cycles.
n_2_component = sum(1 for sz in (4, 5, 6) for nc in obj_components[sz].values() if nc == 2)
n_3_component = sum(1 for sz in (4, 5, 6) for nc in obj_components[sz].values() if nc == 3)
n_4plus_component = sum(1 for sz in (4, 5, 6) for nc in obj_components[sz].values() if nc >= 4)
total_unions = n_2_component + n_3_component + n_4plus_component
cycle_pair_count = sum((nc * (nc - 1)) // 2
                       for sz in (4, 5, 6) for nc in obj_components[sz].values() if nc >= 2)
print(f"  Disjoint-union breakdown across cofactor sizes 4-6:")
print(f"    2-component unions (= cross-edge-free cycle pairs): {n_2_component}")
print(f"    3-component unions: {n_3_component}")
print(f"    4+-component unions: {n_4plus_component}")
print(f"    total disjoint-union objects: {total_unions}  (manuscript: 27+3+5 = 35)")
print(f"  Total unordered cycle pairs (sum of C(n,2) over unions): {cycle_pair_count}")
# Reconciliation, stated in the closing direction: of the 35 disjoint-union
# Theorem-A objects, 32 are 2-component (a vertex-disjoint, cross-edge-free pair
# of chordless cycles) and 3 are 3-component. So the "32 cross-edge-free cycle
# pairs" are exactly the 2-component objects; 35 = 32 + 3, the 3 being the
# 3-component unions, which are not pairs. (Counted instead by C(n,2), the
# 3-component objects supply 3 pairs each, giving 32 + 9 = 41 unordered pairs.)
record("3c", "2-component disjoint-union objects (cross-edge-free cycle pairs)",
       n_2_component, 32, "PASS" if n_2_component == 32 else "FAIL")
record("3c", "total disjoint-union Theorem-A objects across m=4-6",
       total_unions, 35, "PASS" if total_unions == 35 else "FAIL")

# Named-example guard for the §4.4 frontier remark: x = 73 (smallest disjoint
# structure, four (2+2) objects) and x = 17209 (largest, (2+4) twice + (2+2+2)).
# Component-size partitions, not just counts, so the prose's "(2+4) and (2+2+2)"
# claim is locked against drift.
def _union_partitions(hub):
    g = build_cycle_graph(hub, HARD80, table)
    es = set((v, u) for v, nx in g.edges.items() for u in nx)
    parts: dict = {}
    for sz in range(2, 7):
        if sz > len(g.vertices):
            continue
        for C_tuple in combinations(g.vertices, sz):
            C = set(C_tuple)
            indeg = {v: 0 for v in C}; outdeg = {v: 0 for v in C}
            for v in C:
                for u in C:
                    if v != u and (v, u) in es:
                        outdeg[v] += 1; indeg[u] += 1
            if any(indeg[v] != 1 or outdeg[v] != 1 for v in C):
                continue
            unvisited = set(C); comp = []
            while unvisited:
                cur = next(iter(unvisited)); cnt = 0
                while cur in unvisited:
                    unvisited.discard(cur); cnt += 1
                    succ = next((u for u in C if (cur, u) in es), None)
                    if succ is None:
                        break
                    cur = succ
                comp.append(cnt)
            if len(comp) >= 2:
                key = tuple(sorted(comp))
                parts[key] = parts.get(key, 0) + 1
    return parts

p73 = _union_partitions(73)
p17209 = _union_partitions(17209)
print(f"  x=73 union partitions: {p73}")
print(f"  x=17209 union partitions: {p17209}")
record("3c", "x=73: four (2+2) disjoint-union objects",
       p73.get((2, 2), 0), 4, "PASS" if p73.get((2, 2), 0) == 4 else "FAIL")
record("3c", "x=17209: (2+4) and (2+2+2) present, no (3+3)",
       ((2, 4) in p17209 and (2, 2, 2) in p17209 and (3, 3) not in p17209),
       True, "PASS" if ((2, 4) in p17209 and (2, 2, 2) in p17209 and (3, 3) not in p17209) else "FAIL")

# Block 4: parity symmetry χ_p(q) ≡ χ_q(p) (mod 2)
print("\n[Block 4] Parity symmetry check...")
violations_parity = 0
n_pairs_checked = 0
for p, q in combinations(HARD80, 2):
    cp = quotient_class(q, p)
    cq = quotient_class(p, q)
    if (cp % 2) != (cq % 2):
        violations_parity += 1
    n_pairs_checked += 1
print(f"  unordered pairs checked: {n_pairs_checked} = C(80,2) = 3160")
record("4", "parity violations (unordered pairs)", violations_parity, 0,
       "PASS" if violations_parity == 0 else "FAIL")
record("4", "pair count (paper says 3160)", n_pairs_checked, 3160,
       "PASS" if n_pairs_checked == 3160 else "FAIL")

# L(p) even for all p in V_x for all x
print("[Block 4] L(p) even check for all p in V_x...")
total_Lp = 0
odd_Lp = 0
for hub in HARD80:
    t_hub = table.depth[hub]
    for p in HARD80:
        if p == hub:
            continue
        if quotient_class(p, hub) == 0:
            t_p = table.depth[p]
            L_p = (-quotient_class(hub, p)) % (2 ** t_p)
            total_Lp += 1
            if L_p % 2 != 0:
                odd_Lp += 1
print(f"  L(p) values checked: {total_Lp}, odd: {odd_Lp}")
record("4", "L(p) even violations", odd_Lp, 0,
       "PASS" if odd_Lp == 0 else "FAIL")

# Block 5: chi-values in the 5-cycle + degenerate + V_x membership
print("\n[Block 5] Chi-values in the 5-cycle...")

edges_expected = [
    (1801, 14537, 2),
    (14537, 13417, 4),
    (13417, 18121, 0),
    (18121, 18521, 0),
    (18521, 1801, 2),
]
for src, dst, expected_chi in edges_expected:
    chi = quotient_class(dst, src)
    t_src = table.depth[src]
    L_src = (-quotient_class(HUB, src)) % (2 ** t_src)
    status = "PASS" if (chi == expected_chi and chi == L_src) else "FAIL"
    print(f"  {src} → {dst}: chi_{src}({dst})={chi}, L({src})={L_src}, expected={expected_chi}")
    record("5", f"chi_{src}({dst}) = {expected_chi}", chi, expected_chi, status)

for p in (13417, 18121):
    chi_p_hub = quotient_class(HUB, p)
    t_p = table.depth[p]
    L_p = (-chi_p_hub) % (2 ** t_p)
    print(f"  {p}: chi_{p}({HUB}) = {chi_p_hub}, L({p}) = {L_p}")
    record("5", f"L({p}) = 0 (degenerate)", L_p, 0,
           "PASS" if L_p == 0 else "FAIL")
    record("5", f"chi_{p}({HUB}) = 0", chi_p_hub, 0,
           "PASS" if chi_p_hub == 0 else "FAIL")

for p in CYCLE:
    chi_x_p = quotient_class(p, HUB)
    record("5", f"V_x membership: chi_{HUB}({p}) = 0", chi_x_p, 0,
           "PASS" if chi_x_p == 0 else "FAIL")

# Block 6: sole-witness structure and exhaustive minimality (paper §4(iv))
print("\n[Block 6] Sole-witness structure and exhaustive minimality...")
idx_config = tuple(prime_to_idx[p] for p in CONFIG)

sole_witness = {
    1801:  (HUB, 14537),
    14537: (HUB, 13417),
    13417: (HUB, 18121),
    18121: (HUB, 18521),
    18521: (HUB, 1801),
}

def uncovered_pairs(prime_subset):
    """Return list of pairs in prime_subset that are not covered by anyone in subset."""
    uncov = []
    for a, b in combinations(prime_subset, 2):
        covered = False
        for x in prime_subset:
            if x == a or x == b:
                continue
            t_x = table.depth[x]
            if (quotient_class(a, x) + quotient_class(b, x)) % (2 ** t_x) == 0:
                covered = True
                break
        if not covered:
            uncov.append(frozenset({a, b}))
    return uncov

for removed in CYCLE:
    sub = tuple(p for p in CONFIG if p != removed)
    uncov = uncovered_pairs(sub)
    expected_pair = frozenset(sole_witness[removed])
    print(f"  Remove {removed}: uncovered={[set(u) for u in uncov]}, expected={set(expected_pair)}")
    status = "PASS" if (len(uncov) == 1 and uncov[0] == expected_pair) else "FAIL"
    record("6", f"Remove {removed} → uncovered = {set(expected_pair)}",
           [set(u) for u in uncov], [set(expected_pair)], status)

# The single deletions above describe the sole-witness structure; they do NOT
# certify minimality, because coverage is not monotone under deletion.  In this
# same universe (73, 233, 1721, 4057, 18121) is covering with all five of its
# 4-subsets non-covering, yet (73, 233, 1721) is covering.  Minimality needs
# every proper subset of size ≥ 3 (sizes ≤ 2 can never cover).
covering_proper = []
n_proper = 0
for r in range(3, len(CONFIG)):
    for sub in combinations(CONFIG, r):
        n_proper += 1
        if not uncovered_pairs(sub):
            covering_proper.append(sub)
record("6", f"No proper subset of size 3–5 is covering ({n_proper} checked)",
       covering_proper, [], "PASS" if not covering_proper else "FAIL")

# Non-monotonicity witness — pins the reason the exhaustive scan is required.
NONMONO = (73, 233, 1721, 4057, 18121)
nm_ok = (
    not uncovered_pairs(NONMONO)
    and all(uncovered_pairs(tuple(p for p in NONMONO if p != s)) for s in NONMONO)
    and not uncovered_pairs((73, 233, 1721))
)
record("6", f"Non-monotonicity witness {NONMONO}: one-deletion test is unsound",
       nm_ok, True, "PASS" if nm_ok else "FAIL")

sub_no_hub = CYCLE
uncov_nohub = uncovered_pairs(sub_no_hub)
print(f"  Remove {HUB} (hub): {len(uncov_nohub)} uncovered pairs")
record("6", f"Remove hub: 6 Type A pairs uncovered", len(uncov_nohub), 6,
       "PASS" if len(uncov_nohub) == 6 else "FAIL")

# Block 7: structural claims about hub x=17881 (§4(i))
print("\n[Block 7] Structural claims about x=17881...")

V_17881 = [p for p in HARD80 if p != HUB and quotient_class(p, HUB) == 0]
print(f"  |V_17881| = {len(V_17881)}, vertices = {V_17881}")
record("7a", "|V_17881|", len(V_17881), 11,
       "PASS" if len(V_17881) == 11 else "FAIL")

depths_V = [table.depth[p] for p in V_17881]
n_depth3_in_V = sum(1 for d in depths_V if d == 3)
record("7b", "|V_17881| primes with depth 3", n_depth3_in_V, len(V_17881),
       "PASS" if n_depth3_in_V == len(V_17881) else "FAIL")

# 7b: 84% of first 80 hard primes are depth 3
depths_all = [table.depth[p] for p in HARD80]
n_depth3 = sum(1 for d in depths_all if d == 3)
pct = round(100 * n_depth3 / 80)
print(f"  depth-3 count in HARD80: {n_depth3}/80 = {pct}%")
record("7b", "depth-3 fraction of first 80 hard primes", f"{n_depth3}/80 ({pct}%)",
       "~84%", "PASS" if 82 <= pct <= 86 else "FLAG")

H_18121_in_V = [q for q in V_17881 if q != 18121 and quotient_class(q, 18121) == 0]
print(f"  H_18121 ∩ V_17881 = {H_18121_in_V}")
record("7c", "H_18121 ∩ V_17881 = {4297, 18521}", set(H_18121_in_V), {4297, 18521},
       "PASS" if set(H_18121_in_V) == {4297, 18521} else "FAIL")

# Mutual edge 4297 ↔ 18121 in G_17881
t_4297 = table.depth[4297]
t_18121 = table.depth[18121]
L_4297  = (-quotient_class(HUB, 4297))  % (2 ** t_4297)
L_18121 = (-quotient_class(HUB, 18121)) % (2 ** t_18121)
chi_4297_18121 = quotient_class(18121, 4297)
chi_18121_4297 = quotient_class(4297, 18121)
print(f"  L(4297)={L_4297}, chi_4297(18121)={chi_4297_18121}")
print(f"  L(18121)={L_18121}, chi_18121(4297)={chi_18121_4297}")
edge_a = chi_4297_18121 == L_4297
edge_b = chi_18121_4297 == L_18121
record("7d", "4297 → 18121 (chi=L)", edge_a, True,
       "PASS" if edge_a else "FAIL")
record("7d", "18121 → 4297 (chi=L)", edge_b, True,
       "PASS" if edge_b else "FAIL")
triple_idx = tuple(prime_to_idx[p] for p in (HUB, 4297, 18121))
record("7d", "{17881, 4297, 18121} covering", bpi.is_covering(triple_idx), True,
       "PASS" if bpi.is_covering(triple_idx) else "FAIL")

def coverage_degrees(config):
    """For each prime, count pairs in config that it covers."""
    deg = {p: 0 for p in config}
    for a, b in combinations(config, 2):
        for x in config:
            if x == a or x == b:
                continue
            t_x = table.depth[x]
            if (quotient_class(a, x) + quotient_class(b, x)) % (2 ** t_x) == 0:
                deg[x] += 1
    return deg

deg = coverage_degrees(CONFIG)
deg_sorted = sorted(deg.values(), reverse=True)
print(f"  degree sequence (sorted): {deg_sorted}")
print(f"  per prime: {deg}")
record("7e", "Hub 17881 covers all 10 inter-cycle pairs", deg[HUB], 10,
       "PASS" if deg[HUB] == 10 else "FAIL")
record("7e", "Degree sequence (10,2,2,2,2,1)", tuple(deg_sorted), (10,2,2,2,2,1),
       "PASS" if tuple(deg_sorted) == (10,2,2,2,2,1) else "FAIL")

# Block 8: hard-prime properties of CONFIG (paper §1)
print("\n[Block 8] Hard-prime properties of CONFIG...")
for p in CONFIG:
    cond1 = (p % 4 == 1)
    ord_p = multiplicative_order(2, p)
    cond2 = (ord_p % 2 == 1)
    cond3 = (p in HARD80)
    print(f"  {p}: ≡1 mod 4 → {cond1}, ord_p(2)={ord_p} odd → {cond2}, in HARD80 → {cond3}")
    record("8", f"{p} ≡ 1 (mod 4)", cond1, True, "PASS" if cond1 else "FAIL")
    record("8", f"{p} ord_p(2) is odd", cond2, True, "PASS" if cond2 else "FAIL")
    record("8", f"{p} in first 80 hard primes", cond3, True, "PASS" if cond3 else "FAIL")

record("8d", f"depth[17881] = 3", table.depth[HUB], 3,
       "PASS" if table.depth[HUB] == 3 else "FAIL")

# LS2012 Example 3.6 primes — should be even-order (not hard)
for p in (13, 41, 2953):
    ord_p = multiplicative_order(2, p)
    even = (ord_p % 2 == 0)
    print(f"  LS2012 prime {p}: ord_p(2)={ord_p}, even={even}")
    record("8e", f"{p}: ord_p(2) even (so not hard)", ord_p, "even",
           "PASS" if even else "FAIL")

# Block 9d: degenerate-direction consistency
# V_x membership: χ_x(p) = quotient_class(p, x) = 0
# Degenerate:     L(p) = -χ_p(x) = 0, i.e. quotient_class(x, p) = 0
# These are DIFFERENT conditions; both hold here.
print("\n[Block 9d] Degenerate-direction consistency check...")

both_for = {}
for p in (13417, 18121):
    v_x_membership = quotient_class(p, HUB)
    L_condition    = quotient_class(HUB, p)
    both_for[p] = (v_x_membership, L_condition)
    print(f"  {p}: chi_x(p) = {v_x_membership} (V_x: 0 means in)")
    print(f"  {p}: chi_p(x) = {L_condition}  (L=0 means degenerate)")

both_zero_13417 = both_for[13417][0] == 0 and both_for[13417][1] == 0
both_zero_18121 = both_for[18121][0] == 0 and both_for[18121][1] == 0
print(f"  13417: V_x AND degenerate both hold: {both_zero_13417}")
print(f"  18121: V_x AND degenerate both hold: {both_zero_18121}")
record("9d", "13417 in V_x AND L=0 (both directions zero)", both_zero_13417, True,
       "PASS" if both_zero_13417 else "FAIL")
record("9d", "18121 in V_x AND L=0 (both directions zero)", both_zero_18121, True,
       "PASS" if both_zero_18121 else "FAIL")

import math
record("4", "C(80,2) formula", math.comb(80, 2), 3160,
       "PASS" if math.comb(80, 2) == 3160 else "FAIL")

print("\n" + "=" * 70)
print("AUDIT RESULTS")
print("=" * 70)
n_pass = sum(1 for r in results if r[4] == "PASS")
n_fail = sum(1 for r in results if r[4] == "FAIL")
n_flag = sum(1 for r in results if r[4] == "FLAG")
print(f"Total checks: {len(results)}")
print(f"  PASS: {n_pass}")
print(f"  FAIL: {n_fail}")
print(f"  FLAG: {n_flag}")
if n_fail > 0:
    print("\nFAILURES:")
    for r in results:
        if r[4] == "FAIL":
            print(f"  [{r[0]}] {r[1]}: computed={r[2]} expected={r[3]}")
if n_flag > 0:
    print("\nFLAGS:")
    for r in results:
        if r[4] == "FLAG":
            print(f"  [{r[0]}] {r[1]}: computed={r[2]} expected={r[3]}")
print("=" * 70)
sys.exit(0 if n_fail == 0 else 1)
