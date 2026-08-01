"""Fast invariants for burde_pair_law.py.

The full sweep runs in the CLI and is recorded in _burde_pair_law.json; these
tests pin the pieces the calibration rests on, and — importantly — the claim
boundary: that the identity is non-vacuous, that the four displayed forms are
equivalent rather than independent, and that the law is undefined on the odd
hub-cofactor edges carrying sigma_x.
"""
import itertools
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "barker_k6_bundle", "research"))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "barker_k6_bundle", "code"))

from burde_pair_law import quartic, two_squares, variants
from redei_bridge import hard_primes
from barker.two_primary import quotient_class, two_primary_depth
from barker.arithmetic import jacobi_symbol

HP = hard_primes(40)
D3 = [p for p in HP if two_primary_depth(p) == 3]
PAIRS = [(p, q) for p, q in itertools.combinations(D3, 2)
         if jacobi_symbol(p % q, q) == 1
         and quotient_class(q, p) and quotient_class(p, q)][:250]


def test_two_squares_normalised():
    for p in D3:
        a, b = two_squares(p)
        assert a * a + b * b == p and a % 2 == 1 and b % 2 == 0 and a > 0 < b


def test_quartic_symbol_is_the_v2_statement():
    """(q/p)_4 = +1 iff v2(chi_p(q)) >= 2 — this is why it is well-defined."""
    for p, q in PAIRS:
        assert quartic(q, p) == (1 if quotient_class(q, p) % 4 == 0 else -1)


def test_quartic_undefined_on_the_odd_sector():
    """The all-QNR gate makes every hub-cofactor pair odd, so the law cannot
    reach the edges carrying sigma_x."""
    odd = [(p, q) for p, q in itertools.combinations(D3, 2)
           if jacobi_symbol(p % q, q) == -1][:50]
    assert odd
    for p, q in odd:
        assert quartic(q, p) is None and quartic(p, q) is None


def test_identity_holds():
    for p, q in PAIRS:
        (a, b), (c, d) = two_squares(p), two_squares(q)
        assert quartic(q, p) * quartic(p, q) == variants(a, b, c, d, q)["ad-bc"]


def test_identity_is_not_vacuous():
    """Both signs must occur, or the identity would assert nothing."""
    seen = {variants(*two_squares(p), *two_squares(q), q)["ad-bc"]
            for p, q in PAIRS}
    assert seen == {1, -1}


def test_four_forms_are_one_identity_not_four():
    """On hard primes (all 1 mod 8) the four displayed forms coincide, so
    agreement across them is not independent corroboration."""
    for p, q in PAIRS:
        assert len(set(variants(*two_squares(p), *two_squares(q), q).values())) == 1


def test_rhs_invariant_under_sign_choices():
    for p, q in PAIRS[:60]:
        (a, b), (c, d) = two_squares(p), two_squares(q)
        vals = {variants(sa * a, sb * b, sc * c, sd * d, q)["ad-bc"]
                for sa in (1, -1) for sb in (1, -1)
                for sc in (1, -1) for sd in (1, -1)}
        assert len(vals) == 1


def test_negative_control_perturbed_rhs_fails():
    """Bumping the RHS by one must destroy the match, or the identity test
    would have no teeth."""
    hit = 0
    for p, q in PAIRS:
        (a, b), (c, d) = two_squares(p), two_squares(q)
        hit += (quartic(q, p) * quartic(p, q)
                == jacobi_symbol((a * d - b * c + 1) % q, q))
    assert hit < 0.6 * len(PAIRS)
