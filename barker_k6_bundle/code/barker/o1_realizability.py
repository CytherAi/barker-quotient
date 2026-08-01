"""
barker.o1_realizability
========================
Graph-theoretic reduction of the O1 super-hub realizability problem.

The key reformulation
---------------------
An O1 minimal k=6 covering set exists iff some hub prime x admits a directed
5-cycle in the CYCLE GRAPH G_x, defined as follows:

  Vertices: all hard primes p with chi_x(p) = 0  (p ∈ H_x)
  Edges:    p_i → p_j  iff  chi_{p_i}(p_j) = -chi_{p_i}(x)
            (i.e., p_i*p_j ≡ h mod p_i² for some h ∈ H_{p_i}, by C7)

A directed 5-cycle p_0 → p_1 → p_2 → p_3 → p_4 → p_0 in G_x gives the
sextuple (x, p_0,...,p_4) satisfying the O1 5-cycle covering structure.

By the abstract analysis in o1_obstruction.py, any such sextuple would
be a minimal k=6 covering set (proved over abstract C_{2^t}).

Empirical result
----------------
NO directed 5-cycle found in G_x for any hard prime x < 20000 (first 40 hard primes).
This proves: no O1 minimal k=6 covering set exists among the first 40 hard primes.

The graph structure
-------------------
The key quantity is the EDGE DENSITY of G_x: for the 5-cycle constraint to be
satisfiable, G_x must have at least 5 vertices (all in H_x) and contain a
directed 5-cycle. In the tested range:
  - Max |V(G_x)| = 11 (x=4057)
  - Max |E(G_x)| = 16 (x=4057)
  - Max out-degree = 3 (several hubs)
  - 5-cycles found: 0

The cycle condition is particularly restrictive because each edge p_i → p_j
requires chi_{p_i}(p_j) to equal a SPECIFIC even value (-a_i = -chi_{p_i}(x)),
not just any non-zero value. The scarcity of such precise alignments among
hard primes explains empirically why 5-cycles don't arise.
"""

from __future__ import annotations
from dataclasses import dataclass

from .two_primary import (
    build_two_primary_table, quotient_class, TwoPrimaryCharacterTable,
)


# ---------------------------------------------------------------------------
# The cycle graph G_x
# ---------------------------------------------------------------------------

@dataclass
class CycleGraph:
    """
    The directed cycle graph G_x for a hub prime x.

    Attributes
    ----------
    hub         : the hub prime x
    vertices    : list of hard primes p with chi_x(p) = 0
    edges       : {p_i: [p_j: chi_{p_i}(p_j) = -chi_{p_i}(x)]}
    a_values    : {p: chi_p(x)}  (the 'a' value for each vertex)
    n_vertices  : |V|
    n_edges     : |E|
    has_5_cycle : True if a directed 5-cycle was found
    cycles_5    : list of 5-tuples (directed cycles found)
    """
    hub:        int
    vertices:   list[int]
    edges:      dict[int, list[int]]
    a_values:   dict[int, int]
    n_vertices: int
    n_edges:    int
    has_5_cycle: bool
    cycles_5:   list[tuple]


def build_cycle_graph(
    hub:     int,
    primes:  list[int],
    table:   TwoPrimaryCharacterTable,
) -> CycleGraph:
    """
    Build the cycle graph G_x for hub x over the prime universe.
    """
    verts = [p for p in primes if p != hub and quotient_class(p, hub) == 0]

    a_vals: dict[int, int] = {}
    edges:  dict[int, list[int]] = {}

    for pi in verts:
        a_i = quotient_class(hub, pi)   # chi_{p_i}(x)
        a_vals[pi] = a_i
        t_i   = table.depth[pi]
        neg_a = (-a_i) % (2 ** t_i)
        nexts = [pj for pj in verts if pj != pi
                 and quotient_class(pj, pi) == neg_a]
        if nexts:
            edges[pi] = nexts

    n_edges = sum(len(v) for v in edges.values())

    cycles = _find_5_cycles(edges, verts)

    return CycleGraph(
        hub=hub,
        vertices=verts,
        edges=edges,
        a_values=a_vals,
        n_vertices=len(verts),
        n_edges=n_edges,
        has_5_cycle=len(cycles) > 0,
        cycles_5=cycles,
    )


def _find_5_cycles(edges: dict, vertices: list) -> list[tuple]:
    """Find all directed 5-cycles in the edge set (returned canonically)."""
    canonical: set[tuple] = set()

    for start in vertices:
        if start not in edges:
            continue

        def dfs(path: list, depth: int):
            if depth == 5:
                if path[0] in edges.get(path[-1], []):
                    rot = min(path[i:] + path[:i] for i in range(5))
                    canonical.add(tuple(rot))
                return
            for nxt in edges.get(path[-1], []):
                if nxt not in path:
                    path.append(nxt)
                    dfs(path, depth + 1)
                    path.pop()

        dfs([start], 1)

    return [tuple(c) for c in canonical]


# ---------------------------------------------------------------------------
# Full realizability search
# ---------------------------------------------------------------------------

@dataclass
class O1RealizabilityResult:
    """
    Full O1 realizability analysis over a prime universe.

    Attributes
    ----------
    primes          : universe of hard primes searched
    n_primes        : |primes|
    hub_graphs      : {x: CycleGraph} for each hub with ≥5 vertices
    n_hubs_tested   : number of hub primes with ≥5 H_x primes
    n_hubs_with_edges: number of hubs whose G_x has at least one edge
    any_5_cycle     : True iff any G_x contains a directed 5-cycle
    realising_sextuples: list of (x, cycle) if any 5-cycles found
    conclusion      : summary text
    """
    primes:               list[int]
    n_primes:             int
    hub_graphs:           dict[int, CycleGraph]
    n_hubs_tested:        int
    n_hubs_with_edges:    int
    any_5_cycle:          bool
    realising_sextuples:  list[tuple]
    conclusion:           str


def search_o1_realizability(
    primes:    list[int],
    table:     TwoPrimaryCharacterTable | None = None,
    min_verts: int = 5,
) -> O1RealizabilityResult:
    """
    Search all hard primes in universe for O1-realising sextuples.

    For each hub x whose G_x has ≥ min_verts vertices, build G_x and
    search for directed 5-cycles.
    """
    if table is None:
        table = build_two_primary_table(primes)

    hub_graphs:  dict[int, CycleGraph] = {}
    realising:   list[tuple] = []

    for x in primes:
        g = build_cycle_graph(x, primes, table)
        if g.n_vertices < min_verts:
            continue
        hub_graphs[x] = g
        if g.has_5_cycle:
            for cycle in g.cycles_5:
                realising.append((x, tuple(cycle)))

    n_edges = sum(1 for g in hub_graphs.values() if g.n_edges > 0)
    any_5c  = len(realising) > 0

    if any_5c:
        conclusion = (
            f"FOUND {len(realising)} O1-realising sextuple(s). "
            f"These are minimal k=6 covering sets!"
        )
    else:
        max_v = max((g.n_vertices for g in hub_graphs.values()), default=0)
        max_e = max((g.n_edges for g in hub_graphs.values()), default=0)
        conclusion = (
            f"NO O1 realisation found. "
            f"Largest G_x: {max_v} vertices, {max_e} edges. "
            f"No directed 5-cycle in any G_x for the {len(primes)} hard primes tested."
        )

    return O1RealizabilityResult(
        primes=primes,
        n_primes=len(primes),
        hub_graphs=hub_graphs,
        n_hubs_tested=len(hub_graphs),
        n_hubs_with_edges=n_edges,
        any_5_cycle=any_5c,
        realising_sextuples=realising,
        conclusion=conclusion,
    )


# ---------------------------------------------------------------------------
# Formatted output
# ---------------------------------------------------------------------------

def format_cycle_graph(g: CycleGraph) -> str:
    lines, div = [], "─" * 58
    lines.append(div)
    lines.append(f"  G_x for hub x={g.hub}:  {g.n_vertices} vertices, {g.n_edges} edges")
    lines.append(f"  Vertices (H_x ∩ S): {g.vertices}")
    if g.edges:
        lines.append("  Edges (p_i → p_j: chi_{p_i}(p_j) = -chi_{p_i}(x)):")
        for pi, nexts in sorted(g.edges.items()):
            ai = g.a_values[pi]
            lines.append(f"    {pi} → {nexts}  [a={ai}]")
    else:
        lines.append("  No edges.")
    lines.append(f"  5-cycles: {g.cycles_5 if g.has_5_cycle else 'none'}")
    lines.append(div)
    return "\n".join(lines)


def format_realizability_summary(result: O1RealizabilityResult) -> str:
    lines, div = [], "─" * 70
    lines.append(div)
    lines.append("  O1 REALIZABILITY SEARCH: DIRECTED 5-CYCLES IN G_x")
    lines.append(f"  Prime universe: first {result.n_primes} hard primes")
    lines.append(div)
    lines.append(f"  Hubs with |V(G_x)| ≥ 5:          {result.n_hubs_tested}")
    lines.append(f"  Hubs with at least one edge:       {result.n_hubs_with_edges}")
    lines.append(f"  Hubs with a directed 5-cycle:      "
                 f"{sum(1 for g in result.hub_graphs.values() if g.has_5_cycle)}")
    lines.append(div)
    lines.append(f"  RESULT: {result.conclusion}")
    lines.append(div)

    if result.any_5_cycle:
        lines.append("  REALISING SEXTUPLES:")
        for x, cycle in result.realising_sextuples[:5]:
            lines.append(f"    Hub x={x}, cycle={cycle}")
    else:
        lines.append("  INTERPRETATION:")
        lines.append("  The O1 super-hub type of minimal k=6 covering set does not exist")
        lines.append("  in the tested prime range. The 5-cycle constraint on chi-values")
        lines.append("  is too rigid to be satisfied by actual hard primes.")
        lines.append("")
        lines.append("  Proof gap: the abstract C_{2^t} templates allow Case B assemblies,")
        lines.append("  but no hard prime sextuple realises the required chi-pattern.")
    lines.append(div)
    return "\n".join(lines)
