"""Regression for the hub pooling in maxpair_exact.py.

The estimand pools all four depth-3 hubs (`skeleton_model_maxpair.measure`
does the same). Each hub is evaluated on the vertex-0-gated fast path by the
transposition (0 v), which transposes the joint on every (3,3) edge whose
endpoint order it reverses. A released version pooled by multiplying hub 0 by
four instead — exact only when the joints are symmetric, which is precisely
what the uniform-digit validation makes them. Every test here therefore uses
deliberately asymmetric joints.
"""
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from exact_dp import PAIRS, beta_perm, build_F
import maxpair_exact as MX

MOD = MX.MODULI[0]
# no entry equals its transpose partner, in either sector
WE = np.array([[2, 3, 5], [7, 11, 13], [17, 19, 23]], dtype=np.int64)
WO = np.array([[2, 3, 5, 7], [11, 13, 17, 19],
               [23, 29, 31, 37], [41, 43, 47, 53]], dtype=np.int64)


@pytest.fixture(scope="module")
def F4():
    """The covering/minimality predicate, contracted over vertex 4."""
    packed, pop = build_F()
    MX._F_CACHE["packed"], MX._F_CACHE["pop"] = packed, pop
    return lambda beta: MX.build_F4([(beta >> e) & 1
                                     for e in range(len(PAIRS))]) % MOD


def test_joints_are_asymmetric():
    assert not (WE == WE.T).all() and not (WO == WO.T).all()


def test_hub_relabelling_matches_direct_contraction(F4):
    """Gating hub v directly equals gating vertex 0 on the relabelled parity
    graph with the joints transposed on the reversed edges. Any wrong flip set
    — including the empty one the retracted `* 4` shortcut assumed — breaks it.
    """
    rng = np.random.default_rng(20260728)
    seen_nonzero = False
    for v in (1, 2, 3):
        q = list(range(5))
        q[0], q[v] = q[v], q[0]
        pb = beta_perm(q)
        # the all-QNR gate forces hub v's four edges odd; anything else is the
        # empty cell and would compare 0 with 0
        live = sum(1 << PAIRS.index((min(v, u), max(v, u)))
                   for u in range(5) if u != v)
        for beta in (1023,) + tuple(int(b) | live for b in rng.integers(0, 1024, 3)):
            direct = MX.contract_beta(beta, F4(beta), WE, WO, [()],
                                      MOD, gate_hub=v)[0]
            relab = MX.contract_beta(int(pb[beta]), F4(int(pb[beta])), WE, WO,
                                     [MX.flips_for(v)], MOD)[0]
            assert direct == relab, (v, beta, direct, relab)
            seen_nonzero |= direct[0] != 0
    assert seen_nonzero, "every comparison was the empty cell — test is vacuous"


def test_pooled_cell_is_orientation_independent(F4):
    """Transposing both joints IS the vertex-reversal relabelling, which sends
    hub v to hub 3 - v. So it must leave the pooled cell unchanged while moving
    the individual hubs — the property that makes the pool, and no single hub,
    the estimand.
    """
    rev = [3, 2, 1, 0, 4]
    pb = beta_perm(rev)
    beta = 1023
    lhs = [MX.contract_beta(beta, F4(beta), WE, WO, [()], MOD, gate_hub=v)[0]
           for v in range(4)]
    b2 = int(pb[beta])
    rhs = [MX.contract_beta(b2, F4(b2), WE.T.copy(), WO.T.copy(), [()],
                            MOD, gate_hub=v)[0] for v in range(4)]
    assert lhs == rhs[::-1]
    assert len(set(lhs)) > 1, "asymmetric joints must separate the hubs"
