"""Fast invariants for exact_dp.py. The heavy acceptance checks (k=4 brute
force, 64^5 predicate sampling, MC agreement, orbit constancy) run in the CLI
and are recorded in _exact_results.json; these tests pin the cheap algebra."""
import os
import sys
from fractions import Fraction

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from exact_dp import (BITPOS, COF, PAIRS, POPCNT, S_LUT, beta_perm,
                      mask_perm_lut, predicate_reference, row_controls,
                      row_tables)


def test_row_mass_sums():
    for t in (3, 4):
        tabs = row_tables(t)
        half = 1 << (t - 1)
        for s in range(16):
            zeros = sum((s >> i) & 1 == 0 for i in range(4))
            assert tabs["all"][s].sum() == (half - 1) ** zeros * half ** (4 - zeros)


def test_structural_controls():
    assert row_controls(row_tables(3)) == []
    assert row_controls(row_tables(4)) == []


def test_unconditioned_baselines_match_e1_docstring():
    tabs = row_tables(3)
    qnr = Fraction(int((tabs["sig0"][15] * (POPCNT == 2)).sum()),
                   int((tabs["all"][15] * (POPCNT == 2)).sum()))
    allt = Fraction(int((tabs["sig0"] * (POPCNT == 2)).sum()),
                    int((tabs["all"] * (POPCNT == 2)).sum()))
    assert qnr == Fraction(1, 5)
    assert allt == Fraction(3, 13)


def test_beta_perm_transpositions_are_involutions():
    for pi in ([1, 0, 2, 3, 4], [4, 1, 2, 3, 0], [0, 3, 2, 1, 4]):
        pb = beta_perm(pi)
        assert np.array_equal(pb[pb], np.arange(1024))


def test_mask_perm_roundtrip():
    pi = [2, 0, 4, 1, 3]
    inv = [pi.index(v) for v in range(5)]
    lut, lut_inv = mask_perm_lut(pi), mask_perm_lut(inv)
    for v in range(5):
        w = pi[v]
        assert np.array_equal(lut_inv[w][lut[v]], np.arange(64))


def test_s_lut_definition():
    rng = np.random.default_rng(7)
    for beta in rng.integers(0, 1024, 20):
        for v in range(5):
            for i, u in enumerate(COF[v]):
                e = PAIRS.index((min(v, u), max(v, u)))
                assert ((S_LUT[beta, v] >> i) & 1) == ((int(beta) >> e) & 1)


def _code(masks):
    c = 0
    for v, m in enumerate(masks):
        c |= m << (6 * v)
    return c


def test_predicate_reference_all_witness_fails_minimality():
    assert predicate_reference(_code([63] * 5)) is False


def test_predicate_reference_cyclic_single_witness_survives():
    # w({i,i+1}) = i-1, w({i,i+2}) = i+1 (mod 5): full set covers; every
    # 4-subset V\{y} misses the witness of {y+1,y+2}; every triple contains a
    # pair whose sole witness lies outside. Hand-verified minimal covering.
    masks = [0] * 5
    for i in range(5):
        p1 = tuple(sorted(((i + 1) % 5, (i + 2) % 5)))       # witness i
        masks[i] |= 1 << BITPOS[i][p1]
        p2 = tuple(sorted(((i - 1) % 5, (i + 1) % 5)))       # witness i
        masks[i] |= 1 << BITPOS[i][p2]
    assert predicate_reference(_code(masks)) is True
