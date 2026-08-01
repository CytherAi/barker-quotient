"""Fast invariants for redei_bridge.py.

The full sweep runs in the CLI and is recorded in _redei_bridge.json; these
tests pin the pieces the falsification rests on — that the symbol is a genuine
Rédei symbol (solution-independent and S3-symmetric), that the conic solutions
are real solutions, and the two structural facts about chi that make the
lemma unstatable in its original form.
"""
import itertools
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "barker_k6_bundle", "research"))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "barker_k6_bundle", "code"))

from redei_bridge import (conic_solutions, hard_primes, hub_invariant, redei,
                          redei_from, sqrt_mod, verify_chi_structure,
                          verify_generator_rescaling, triangle_invariant)
from barker.arithmetic import jacobi_symbol
from barker.two_primary import quotient_class, two_primary_depth

TRIS = [(73, 89, 937), (73, 89, 1801), (73, 937, 1433), (89, 233, 4201)]


def test_sqrt_mod_roundtrip():
    for p in (73, 89, 233, 937):
        for a in range(1, 40):
            s = sqrt_mod(a, p)
            if s is not None:
                assert s * s % p == a % p


def test_conic_solutions_are_solutions():
    for p1, p2, _ in TRIS:
        sols = conic_solutions(p1, p2)
        assert sols
        for x, y, z in sols:
            assert x * x - p1 * y * y - p2 * z * z == 0


def test_symbol_independent_of_solution():
    """Both square roots and every primitive solution must agree."""
    for p1, p2, p3 in TRIS:
        vals = {redei_from(p1, p2, p3, s) for s in conic_solutions(p1, p2)}
        assert len(vals - {None}) == 1


def test_symbol_is_s3_symmetric():
    """Redei's defining property — this is what validates the normalisation."""
    for tri in TRIS:
        vals = {redei(*o) for o in itertools.permutations(tri)} - {None}
        assert len(vals) == 1, tri


def test_chi_is_a_homomorphism_through_Zx():
    """Fact 2: no trilinear content can live in chi at a single hub."""
    got = verify_chi_structure()
    assert got == {"homomorphism": True, "factors_through_Zx": True,
                   "bit0_is_legendre": True}


def test_generator_choice_rescales_chi_by_one_unit():
    """Fact 1: only v2(chi) is normalisation-invariant."""
    got = verify_generator_rescaling()
    assert set(got["rescaling_units"].values()) <= {1, 3, 5, 7}
    assert len(got["generators"]) >= 2


def test_hub_invariant_is_constant_on_the_unit_orbit():
    """The canonical form must be constant on the simultaneous unit orbit —
    the property that makes it the complete invariant of a hub in a triangle."""
    x, y, z = 73, 89, 937
    t = two_primary_depth(x)
    m = 1 << t
    a, b = quotient_class(y, x), quotient_class(z, x)
    orbit = {((a * u) % m, (b * u) % m) for u in range(1, m, 2)}
    assert len(orbit) > 1, "orbit is trivial — the test would prove nothing"
    assert hub_invariant(x, y, z) == (t,) + min(orbit)
    for u in range(1, m, 2):
        rescaled = {((a * u * w) % m, (b * u * w) % m) for w in range(1, m, 2)}
        assert rescaled == orbit


def test_known_mixed_sign_pair():
    """The registered counterexample: same invariant class, opposite symbols."""
    a, b = (4057, 4201, 6553), (4409, 5209, 5689)
    for t in (a, b):
        assert all(jacobi_symbol(u % v, v) == 1
                   for u, v in itertools.combinations(t, 2))
    assert triangle_invariant(a) == triangle_invariant(b)
    assert redei(*a) == -1 and redei(*b) == 1


def test_hard_primes_prefix():
    assert hard_primes(6) == [73, 89, 233, 337, 601, 881]
