"""Regression tests for the Weisfeiler-Lehman signatures.

Two properties are pinned:

1. A signature is an isomorphism invariant — relabelling the vertices of a
   graph must not change it.

2. A signature carries the stable COLOURS, not merely their class sizes.  The
   previous implementation renumbered colours per graph and returned the sorted
   ids, which collapsed to the colour-class size profile; at k = 6 that gave all
   61 enumerated configurations one identical signature, so the invariant
   separated nothing and the I_6-vs-1-WL comparison built on it was wrong.
"""
import json
import os
import random
import sys

import pytest

_RESEARCH = os.path.join(
    os.path.dirname(__file__), "..", "barker_k6_bundle", "research"
)
sys.path.insert(0, _RESEARCH)

from _common import build_labeled_graph, two_fwl_signature  # noqa: E402
from discrimination_depth import i6_invariant, one_wl_signature  # noqa: E402


def _relabel(cancels, member, vertex_types, n, perm):
    """Present the same graph with vertex i renamed to perm[i]."""
    new_types = [None] * n
    for i, t in enumerate(vertex_types):
        new_types[perm[i]] = t
    return (
        {(perm[u], perm[v]) for u, v in cancels},
        {(perm[u], perm[v]) for u, v in member},
        new_types,
        n,
    )


@pytest.fixture(scope="module")
def table():
    sys.path.insert(
        0, os.path.join(os.path.dirname(__file__), "..", "barker_k6_bundle", "code")
    )
    from barker.sweep import find_hard_primes
    from barker.two_primary import build_two_primary_table

    return build_two_primary_table([h["prime"] for h in find_hard_primes(80000)][:80])


@pytest.fixture(scope="module")
def by_k():
    with open(os.path.join(_RESEARCH, "_enumeration_cache.json")) as f:
        raw = json.load(f)
    return {k: [tuple(cfg) for _k, _c, _p, cfg in raw if _k == k] for k in (3, 4, 5, 6)}


class TestRelabellingInvariance:
    @pytest.mark.parametrize("seed", [1, 2, 3])
    def test_signatures_survive_vertex_relabelling(self, table, by_k, seed):
        rng = random.Random(seed)
        wl1_reg, fwl2_reg = {}, {}
        for k in (3, 4, 5, 6):
            for cfg in by_k[k][:4]:
                g = build_labeled_graph(cfg, table)
                perm = list(range(g[3]))
                rng.shuffle(perm)
                relabelled = _relabel(*g, perm)
                assert one_wl_signature(*g, wl1_reg) == \
                    one_wl_signature(*relabelled, wl1_reg), \
                    f"1-WL signature changed under relabelling for {cfg}"
                assert two_fwl_signature(*g, fwl2_reg) == \
                    two_fwl_signature(*relabelled, fwl2_reg), \
                    f"2-FWL signature changed under relabelling for {cfg}"


class TestSignatureCarriesColours:
    """The signature must distinguish configurations that genuinely differ.

    A size-profile-only signature passes the relabelling test above while
    separating nothing, so invariance alone is not enough to pin correctness.
    """

    def test_k6_configurations_are_not_all_collapsed(self, table, by_k):
        wl1_reg, fwl2_reg = {}, {}
        cfgs = by_k[6]
        wl1 = {one_wl_signature(*build_labeled_graph(c, table), wl1_reg) for c in cfgs}
        fwl2 = {two_fwl_signature(*build_labeled_graph(c, table), fwl2_reg) for c in cfgs}
        assert len(wl1) > 1, "1-WL collapsed every k=6 configuration to one signature"
        assert len(fwl2) > 1, "2-FWL collapsed every k=6 configuration to one signature"

    def test_one_wl_refines_i6_at_k6(self, table, by_k):
        """Equal 1-WL signature must imply equal I_6 — the containment that the
        earlier size-profile signature violated in 3500 pairs."""
        from itertools import combinations

        wl1_reg = {}
        rows = [
            (one_wl_signature(*build_labeled_graph(c, table), wl1_reg),
             i6_invariant(c, table))
            for c in by_k[6]
        ]
        offenders = [
            (a, b) for (a, b) in combinations(rows, 2)
            if a[0] == b[0] and a[1] != b[1]
        ]
        assert not offenders, \
            f"{len(offenders)} pairs share a 1-WL signature but differ in I_6"


class TestRegistryIsStable:
    def test_rescoring_against_the_same_registry_is_idempotent(self, table, by_k):
        """Re-encountering a colour must reuse its id, not mint a new one —
        otherwise signatures would depend on how many graphs preceded them."""
        a, b = by_k[6][0], by_k[6][1]
        shared = {}
        first = one_wl_signature(*build_labeled_graph(a, table), shared)
        one_wl_signature(*build_labeled_graph(b, table), shared)
        assert one_wl_signature(*build_labeled_graph(a, table), shared) == first

    @staticmethod
    def _partition(cfgs, table, sign):
        """Group configurations by signature equality, scoring in the order given."""
        registry = {}
        groups = {}
        for cfg in cfgs:
            groups.setdefault(sign(*build_labeled_graph(cfg, table), registry),
                              []).append(cfg)
        return frozenset(frozenset(g) for g in groups.values())

    @pytest.mark.parametrize("sign", [one_wl_signature, two_fwl_signature])
    def test_partition_does_not_depend_on_processing_order(self, table, by_k, sign):
        """Registry ids are assigned in first-encounter order, so they shift when
        the configurations are scored in a different order.  The ids are never
        the claim — the induced partition is — and THAT must be order-free.

        This is what makes within-census comparison sound.  It is also why a
        signature must not be serialised or compared against a different run:
        the ids are run-local even though the partition is not.
        """
        cfgs = by_k[6]
        forward = self._partition(cfgs, table, sign)
        reverse = self._partition(list(reversed(cfgs)), table, sign)
        shuffled = list(cfgs)
        random.Random(99).shuffle(shuffled)
        assert forward == reverse == self._partition(shuffled, table, sign)

    def test_ids_really_do_shift_with_order(self, table, by_k):
        """Guards the test above against being vacuous: if ids happened to be
        order-independent, order-invariance of the partition would be trivial."""
        cfgs = by_k[6]
        first_forward = one_wl_signature(*build_labeled_graph(cfgs[0], table), {})
        registry = {}
        for cfg in reversed(cfgs):
            one_wl_signature(*build_labeled_graph(cfg, table), registry)
        first_after = one_wl_signature(*build_labeled_graph(cfgs[0], table), registry)
        assert first_forward != first_after
