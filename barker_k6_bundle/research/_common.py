"""
_common.py — shared helpers for the research scripts.

Centralises the structural invariants used across the enumeration and
refinement-check scripts:

    delta_x(x, S)  — |V_x ∩ (S \\ {x})| — local defect at x
    chi_sum(x, S)  — Σ_{p ∈ S, p ≠ x} χ_x(p) mod 2^{t_x}
    classify(S)    — five-class partition {A1, A2, A3, B0, B1} of the
                     follow-on paper §1.3, with "B(δ=X)" labels for
                     interior-B configurations (matches the format
                     written to `_enumeration_cache.json`)

Also provides the labeled bipartite (cancellation + membership) graph
construction and the 2-FWL color-refinement signature used by
`wl2_v2.py`, `k7_extension.py`, and `k7_60primes.py`.

Previously the helpers above were duplicated across delta_profile.py,
enumerate_classes.py, profile_analysis.py, k7_extension.py, and
k7_60primes.py with three different return signatures for `classify`
and three different B-label spellings. They are unified here.
"""

from dataclasses import dataclass
from itertools import combinations


def delta_x(x, C, table):
    """δ_x(S) = |V_x ∩ (S \\ {x})| — how many other primes lie in H_x."""
    return sum(1 for p in C if p != x and table.chi[(p, x)] == 0)


def chi_sum(x, C, table):
    """Σ_{p ∈ S, p ≠ x} χ_x(p) mod 2^{t_x} — cofactor chi-sum at x."""
    mod = 2 ** table.depth[x]
    return sum(table.chi[(p, x)] for p in C if p != x) % mod


@dataclass
class Classification:
    cls: str                # "A1" | "A2" | "A3" | "B0" | "B1" | "B(δ=N)"
    deltas: dict            # {prime: int}      δ-value at each target
    chi_sums: dict          # {prime: int}      chi-sum at each target
    elim: list              # primes with chi_sum == 0
    profile: tuple          # sorted-descending tuple of δ values


def classify(C, table):
    """
    Five-class partition (follow-on paper §1.3):

      A1     — max δ_x = k-1 among elim targets (full hub)
      A2     — max δ_x ≥ 2  among elim targets (partial hub)
      A3     — max δ_x ≤ 1  among elim targets (pure cancellation)
      B0     — no elim target, all δ_x = 0     (maximally diffuse)
      B1     — no elim target, max δ_x = k-2   (codimension-one blocked)
      B(δ=X) — no elim target, 0 < max δ_x < k-2 (interior B)
    """
    Cs = sorted(C)
    k = len(Cs)
    deltas = {x: delta_x(x, Cs, table) for x in Cs}
    chi_sums = {x: chi_sum(x, Cs, table) for x in Cs}
    elim = [x for x in Cs if chi_sums[x] == 0]
    profile = tuple(sorted(deltas.values(), reverse=True))

    if elim:
        max_elim_delta = max(deltas[x] for x in elim)
        if max_elim_delta == k - 1:
            cls = "A1"
        elif max_elim_delta >= 2:
            cls = "A2"
        else:
            cls = "A3"
    else:
        dmax = max(deltas.values())
        if dmax == k - 2:
            cls = "B1"
        elif dmax == 0:
            cls = "B0"
        else:
            cls = f"B(δ={dmax})"

    return Classification(
        cls=cls, deltas=deltas, chi_sums=chi_sums,
        elim=elim, profile=profile,
    )


def build_labeled_graph(C, table):
    """
    Bipartite (target, pair) graph used by 2-FWL with both cancellation
    and combinatorial-membership edges.

    Vertices: k targets (indices 0..k-1), then C(k,2) pair vertices.
    Edges:
      cancels — target ~ pair iff target's chi-sum on the pair is 0
                (arithmetic cancellation)
      member  — target ~ pair iff target is one of the pair's two indices
                (combinatorial membership)

    Returns (cancels, member, vertex_types, n_vertices) where
    vertex_types[i] ∈ {0, 1} (0 = target, 1 = pair).
    """
    Cs = sorted(C)
    k = len(Cs)
    pair_list = list(combinations(range(k), 2))
    n_pairs = len(pair_list)
    n_vertices = k + n_pairs
    cancels = set()
    member = set()
    for ti in range(k):
        x = Cs[ti]
        mod = 2 ** table.depth[x]
        for pi, (a, b) in enumerate(pair_list):
            pv = k + pi
            if a == ti or b == ti:
                member.add((ti, pv))
                member.add((pv, ti))
            else:
                s = (table.chi[(Cs[a], x)] + table.chi[(Cs[b], x)]) % mod
                if s == 0:
                    cancels.add((ti, pv))
                    cancels.add((pv, ti))
    vertex_types = [0] * k + [1] * n_pairs
    return cancels, member, vertex_types, n_vertices


def two_fwl_signature(cancels, member, vertex_types, n, registry,
                      max_iter=100, *, verbose=False):
    """
    2-FWL color refinement on ordered pairs of vertices, three edge types:
    C (cancellation), M (membership), N (none); D = diagonal.

    Returns the sorted tuple of stable colour ids — the multiset of 2-FWL
    stable colours of the graph.

    `registry` maps colour key -> int id and is SHARED (and mutated in place)
    across every graph whose signatures will be compared.  Ids mean nothing on
    their own: only equality of signatures computed against the same registry
    is meaningful.  Passing a fresh registry per graph makes every signature
    incomparable with every other.

    DO NOT SERIALISE A SIGNATURE, or compare one against a different run.  Ids
    are handed out in first-encounter order, so scoring the same census in a
    different order yields different ids for the same colours.  The PARTITION
    they induce is order-free (pinned by
    tests/test_wl_invariance.py::test_partition_does_not_depend_on_processing_order),
    and the partition is the only thing any result here rests on.  If a
    signature ever does need to outlive its run, persist the registry beside
    it, or key colours by a digest of the colour structure instead of a
    counter.

    The registry is what makes the colours themselves part of the signature.
    An earlier version instead renumbered colours per graph and returned the
    sorted ids, which reduced the signature to the colour-class SIZE PROFILE
    and discarded which colours occurred — at k = 6 that gave all 61 enumerated
    configurations one identical signature, so the invariant separated nothing.
    """
    colors = {}
    for u in range(n):
        for v in range(n):
            if u == v:
                key = ("D", vertex_types[u])
            else:
                if (u, v) in cancels:
                    et = "C"
                elif (u, v) in member:
                    et = "M"
                else:
                    et = "N"
                key = (et, vertex_types[u], vertex_types[v])
            colors[(u, v)] = registry.setdefault(key, len(registry))

    n_classes = len(set(colors.values()))
    converged = False
    for it in range(max_iter):
        new_colors = {}
        for u in range(n):
            for v in range(n):
                pair_mset = tuple(
                    sorted((colors[(u, w)], colors[(w, v)]) for w in range(n))
                )
                new_colors[(u, v)] = registry.setdefault(
                    (colors[(u, v)], pair_mset), len(registry)
                )
        colors = new_colors
        new_n_classes = len(set(colors.values()))
        # Each new colour determines its predecessor, so refinement is
        # monotone: a round that does not increase the class count is stable.
        if new_n_classes == n_classes:
            if verbose:
                print(f"  stable after {it + 1} iterations")
            converged = True
            break
        n_classes = new_n_classes
    if not converged and verbose:
        print(f"  did not stabilize in {max_iter} iterations")
    return tuple(sorted(colors.values()))
