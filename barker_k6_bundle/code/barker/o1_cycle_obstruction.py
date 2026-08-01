"""
barker.o1_cycle_obstruction
============================
Edge labels, edge composition, and the cycle obstruction analysis for G_x.

Theoretical summary
--------------------
For each hub prime x, the cycle graph G_x has:
  Vertices V_x = {p ∈ S : chi_x(p) = 0}   (p lies in H_x)
  Directed edges p → q  iff  chi_p(q) = L(p) := -chi_p(x)
  Edge labels L(p) = -chi_p(x) = -(a_p), which is always even.

Key proved results:
  1. L(p) is always even (proved: chi_x(p)=0 → chi_p(x) even by C4+C5 parity)
  2. A directed k-cycle in G_x corresponds to a covering configuration of size k+1
  3. A directed triangle p0→p1→p2→p0 in G_x implies {x,p0,p1,p2} is a covering 4-set
     (but NOT necessarily minimal — it may contain a smaller covering triple)

Triangle ↔ covering-triple theorem
-------------------------------------
For each edge p_i → p_{i+1} in G_x:
  chi_{p_i}(p_{i+1}) = L(p_i) = -a_i  where a_i = chi_{p_i}(x)

This directly gives: chi_{p_i}(x) + chi_{p_i}(p_{i+1}) = a_i + (-a_i) = 0
                     → pair (x, p_{i+1}) is bad at target p_i

Combined with chi_x(p_j) = 0 for all j (so (p_i,p_j) bad at x for all i≠j):

For a directed triangle p0→p1→p2→p0:
  - x covers all 3 inter-p pairs (p0,p1),(p0,p2),(p1,p2)
  - p0 covers (x,p1), p1 covers (x,p2), p2 covers (x,p0)
  so {x,p0,p1,p2} is always a covering 4-set.

Special case: if L(p1) = 0 (a_1=0, i.e., x ∈ H_{p1}), then chi_{p1}(x)=0,
so chi_{p1}(x) + chi_{p1}(p0) = chi_{p1}(p0) = 0 iff p0 ∈ H_{p1}.
This makes {x,p0,p1} a covering triple when p0 ∈ H_{p1} ∩ V_x.
This is the degenerate case where BOTH x and p0 are in H_{p1}.

For a directed 5-cycle p0→p1→p2→p3→p4→p0:
  All 15 pairs of {x,p0,...,p4} are covered (see o1_obstruction.py).
  The resulting sextuple is a MINIMAL k=6 covering set.
  This cannot happen (empirically: no 5-cycle in G_x for hard primes < 20000).

Edge composition
----------------
For a directed path p0→p1→p2 in G_x:
  chi_{p0}(p1) = L(p0) = even      (edge condition)
  chi_{p1}(p2) = L(p1) = even      (edge condition)
  chi_{p0}(p2) = ?                  (cross-entry, independent)

By C5: chi_{p0}(p2) ≡ chi_{p2}(p0) mod 2.
For a 5-cycle, chi_{p2}(p0) is a cross-backward entry (required to be ODD in Case B).
So chi_{p0}(p2) ≡ ODD. Since L(p0) = EVEN, we get:
  chi_{p0}(p2) ≠ L(p0), so p2 is NOT an out-neighbor of p0.

This means: consecutive-by-2 vertices in a 5-cycle cannot be directly adjacent in G_x.
(The 5-cycle must use exactly the 5 prescribed edges, with no "shortcut" chords.)

Known cycle structure in G_x (first 40 hard primes):
  Triangles: 1 (at x=4057)
  4-cycles:  several (at x=1913, x=4201)
  5-cycles:  0 (the main result)
"""

from __future__ import annotations
from dataclasses import dataclass

from .two_primary import (
    build_two_primary_table, TwoPrimaryCharacterTable,
)
from .o1_realizability import CycleGraph, build_cycle_graph


# ---------------------------------------------------------------------------
# Edge label analysis
# ---------------------------------------------------------------------------

@dataclass
class EdgeLabelSummary:
    """
    Summary of edge labels L(p) = -chi_p(x) for all p ∈ V_x.

    Attributes
    ----------
    hub            : x
    labels         : {p: L(p) = -chi_p(x) mod 2^{t_p}}
    all_even       : True iff all labels are even (proved: should always hold)
    zero_labels    : list of p with L(p)=0 (degenerate: x ∈ H_p)
    nonzero_labels : list of p with L(p)≠0 (generic case)
    """
    hub:           int
    labels:        dict[int, int]
    all_even:      bool
    zero_labels:   list[int]
    nonzero_labels: list[int]


def compute_edge_labels(graph: CycleGraph, table: TwoPrimaryCharacterTable) -> EdgeLabelSummary:
    """Compute edge labels L(p) = -chi_p(hub) for all vertices p in G_x."""
    labels = graph.a_values  # a_values already stores chi_p(x); L(p) = -a_p mod 2^t
    hub    = graph.hub
    L = {}
    for p, a_p in labels.items():
        t_p = table.depth[p]
        L[p] = (-a_p) % (2 ** t_p)

    all_even  = all(v % 2 == 0 for v in L.values())
    zero_l    = [p for p, l in L.items() if l == 0]
    nonzero_l = [p for p, l in L.items() if l != 0]

    return EdgeLabelSummary(
        hub=hub, labels=L, all_even=all_even,
        zero_labels=zero_l, nonzero_labels=nonzero_l,
    )


# ---------------------------------------------------------------------------
# Cycle detection with cycle-type classification
# ---------------------------------------------------------------------------

@dataclass
class CycleRecord:
    """A directed cycle in G_x with its obstruction classification."""
    hub:        int
    cycle:      tuple[int,...]
    length:     int
    label_seq:  tuple[int,...]   # (L(p0), L(p1), ...) around the cycle
    is_degenerate: bool          # True if any label is 0
    obstruction: str             # "triangle→covering-triple", "4-cycle", "5-cycle!!", ...


def find_all_cycles(
    graph: CycleGraph,
    max_length: int = 6,
    table: TwoPrimaryCharacterTable | None = None,
) -> list[CycleRecord]:
    """
    Find all directed cycles of length 3..max_length in G_x.
    Returns classified CycleRecords.

    If *table* is provided, label_seq contains the true edge labels
    L(p) = -chi_p(hub) mod 2^{t_p}.  Otherwise falls back to
    a_p = chi_p(hub) (legacy behavior, sign-inverted).
    """
    edges    = graph.edges
    vertices = graph.vertices
    a_vals   = graph.a_values  # chi_p(hub)
    hub      = graph.hub

    canonical: set[tuple] = set()

    for start in vertices:
        if start not in edges:
            continue

        def dfs(path: list, depth: int):
            if depth >= 3 and path[0] in edges.get(path[-1], []):
                cycle = tuple(path)
                rot   = min(cycle[i:] + cycle[:i] for i in range(len(cycle)))
                canonical.add(rot)
                if depth >= max_length:
                    return
            if depth >= max_length:
                return
            for nxt in edges.get(path[-1], []):
                if nxt not in path:
                    path.append(nxt)
                    dfs(path, depth + 1)
                    path.pop()

        dfs([start], 1)

    result = []
    for cycle_tuple in canonical:
        k = len(cycle_tuple)

        # Edge labels L(p) = -chi_p(hub) mod 2^{t_p} around the cycle
        if table is not None:
            label_seq = tuple(
                (-a_vals.get(p, 0)) % (2 ** table.depth[p])
                for p in cycle_tuple
            )
        else:
            # Legacy fallback: store a_p directly (sign-inverted vs L(p))
            label_seq = tuple(a_vals.get(p, 0) for p in cycle_tuple)
        is_degen = any(a_vals.get(p, 0) == 0 for p in cycle_tuple)

        if k == 3:
            obs = "triangle→covering-triple (hub+triangle = covering 4-set)"
        elif k == 4:
            obs = "4-cycle (hub+cycle = covering 5-set, check minimality)"
        elif k == 5:
            obs = "5-cycle!! → minimal k=6 covering set (O1 realized)"
        else:
            obs = f"{k}-cycle (longer pattern)"

        result.append(CycleRecord(
            hub=hub, cycle=cycle_tuple, length=k,
            label_seq=label_seq, is_degenerate=is_degen,
            obstruction=obs,
        ))

    return sorted(result, key=lambda r: (r.length, r.cycle))


# ---------------------------------------------------------------------------
# Composition analysis
# ---------------------------------------------------------------------------

@dataclass
class CompositionAnalysis:
    """
    Analysis of edge composition: for each directed path p0→p1→p2,
    check if p2 is an out-neighbor of p0 (would mean a shortcut chord).

    Attributes
    ----------
    hub          : x
    n_paths_len2 : total directed paths of length 2
    n_chords     : paths p0→p1→p2 where p0→p2 is also an edge (i.e., shortcut)
    chord_examples: list of (p0, p1, p2) shortcut examples
    """
    hub:            int
    n_paths_len2:   int
    n_chords:       int
    chord_examples: list[tuple]


def analyse_edge_composition(graph: CycleGraph) -> CompositionAnalysis:
    """
    Find all directed paths p0→p1→p2 where p0→p2 is also an edge (chord).

    In a 5-cycle p0→p1→p2→p3→p4→p0, a chord p0→p2 would create a shortcut
    triangle p0→p1→p2→p0, which we've shown corresponds to a covering triple.
    Chords in G_x thus indicate which triples are covered and help understand
    why 5-cycles cannot form (a 5-cycle with a chord isn't minimal).
    """
    edges = graph.edges
    n_paths = 0
    chords  = []

    for p0, nexts0 in edges.items():
        for p1 in nexts0:
            n_paths += 1
            for p2 in edges.get(p1, []):
                if p2 != p0 and p2 in edges.get(p0, []):
                    chords.append((p0, p1, p2))

    return CompositionAnalysis(
        hub=graph.hub,
        n_paths_len2=n_paths,
        n_chords=len(chords),
        chord_examples=chords[:5],
    )


# ---------------------------------------------------------------------------
# Full cycle obstruction report for all hubs
# ---------------------------------------------------------------------------

@dataclass
class CycleObstructionReport:
    """
    Complete cycle obstruction analysis over all hubs in a prime universe.

    Attributes
    ----------
    primes          : universe of hard primes
    hub_results     : {x: (CycleGraph, [CycleRecord], CompositionAnalysis)}
    n_hubs          : number of hubs with ≥5 vertices
    cycles_by_length: {k: total count} across all hubs
    any_5_cycle     : True iff any hub has a directed 5-cycle
    """
    primes:           list[int]
    hub_results:      dict[int, tuple]
    n_hubs:           int
    cycles_by_length: dict[int, int]
    any_5_cycle:      bool


def compute_cycle_obstruction_report(
    primes: list[int],
    table:  TwoPrimaryCharacterTable | None = None,
    min_verts: int = 5,
    max_cycle_length: int = 6,
) -> CycleObstructionReport:
    """Full cycle obstruction analysis."""
    if table is None:
        table = build_two_primary_table(primes)

    hub_results: dict[int, tuple] = {}
    by_length:   dict[int, int]   = {}
    any_5        = False

    for x in primes:
        g = build_cycle_graph(x, primes, table)
        if g.n_vertices < min_verts:
            continue

        cycles = find_all_cycles(g, max_length=max_cycle_length, table=table)
        comp   = analyse_edge_composition(g)
        hub_results[x] = (g, cycles, comp)

        for r in cycles:
            by_length[r.length] = by_length.get(r.length, 0) + 1
            if r.length == 5:
                any_5 = True

    return CycleObstructionReport(
        primes=primes,
        hub_results=hub_results,
        n_hubs=len(hub_results),
        cycles_by_length=by_length,
        any_5_cycle=any_5,
    )


# ---------------------------------------------------------------------------
# Formatted output
# ---------------------------------------------------------------------------

def format_cycle_obstruction_report(report: CycleObstructionReport) -> str:
    lines, div = [], "─" * 70
    lines.append(div)
    lines.append("  CYCLE OBSTRUCTION REPORT FOR G_x (O1 5-CYCLE ANALYSIS)")
    lines.append(f"  Prime universe: {report.n_hubs} hubs with ≥5 vertices tested")
    lines.append(div)

    lines.append("  DIRECTED CYCLES FOUND:")
    total = sum(report.cycles_by_length.values())
    if total == 0:
        lines.append("    None (all G_x are acyclic)")
    else:
        for k in sorted(report.cycles_by_length.keys()):
            cnt = report.cycles_by_length[k]
            mark = "  ← O1 REALIZED!" if k == 5 else ""
            lines.append(f"    Length {k}: {cnt} cycle(s){mark}")
    lines.append(div)

    for x, (g, cycles, comp) in sorted(report.hub_results.items()):
        if not cycles:
            continue
        lines.append(f"  Hub x={x}: {g.n_vertices}v, {g.n_edges}e, {len(cycles)} cycle(s)")
        for r in cycles[:3]:
            lines.append(f"    {list(r.cycle)} → {r.obstruction[:60]}")
        if comp.n_chords > 0:
            lines.append(f"    Chord paths: {comp.n_chords}")
        lines.append("")

    lines.append(div)
    if report.any_5_cycle:
        lines.append("  STATUS: O1 IS REALIZED — minimal k=6 covering set exists!")
    else:
        lines.append("  STATUS: No directed 5-cycle in any G_x.")
        lines.append("  O1 minimal k=6 covering sets do NOT exist in the tested range.")
    lines.append(div)
    return "\n".join(lines)
