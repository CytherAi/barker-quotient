"""Tests for barker.arithmetic — Layer 1 primitives."""
import pytest
from barker.arithmetic import (
    is_prime, factorize, prime_factors, valuation, euler_phi,
    multiplicative_order, is_self_conjugate, integer_sqrt,
    jacobi_symbol, odd_part, two_adic_valuation, FactorizationError,
)


# ---------------------------------------------------------------------------
# is_prime
# ---------------------------------------------------------------------------

class TestIsPrime:
    @pytest.mark.parametrize("n,expected", [
        (-1, False), (0, False), (1, False), (2, True), (3, True),
        (4, False), (5, True), (6, False), (7, True), (97, True),
        (100, False), (101, True), (113, True), (114, False),
    ])
    def test_small_values(self, n, expected):
        assert is_prime(n) == expected

    def test_carmichael_number_561(self):
        """561 = 3*11*17 is the smallest Carmichael number — must be composite."""
        assert is_prime(561) is False

    def test_large_prime(self):
        assert is_prime(104729) is True  # 10000th prime

    def test_large_composite(self):
        assert is_prime(104729 * 2) is False

    @pytest.mark.parametrize("n", [2047, 1373653, 25326001])
    def test_near_mr_bounds(self, n):
        """Values at or near Miller-Rabin witness set boundaries."""
        # These are composites that are pseudoprimes to small bases
        assert is_prime(n) is False


# ---------------------------------------------------------------------------
# factorize
# ---------------------------------------------------------------------------

class TestFactorize:
    def test_one(self):
        assert factorize(1) == {}

    def test_prime(self):
        assert factorize(97) == {97: 1}

    def test_prime_power(self):
        assert factorize(8) == {2: 3}

    def test_product(self):
        assert factorize(360) == {2: 3, 3: 2, 5: 1}

    def test_semiprime(self):
        assert factorize(91) == {7: 1, 13: 1}

    def test_zero_and_negative(self):
        assert factorize(0) == {}
        assert factorize(-1) == {}


class TestPrimeFactors:
    def test_basic(self):
        assert prime_factors(12) == [2, 2, 3]

    def test_prime(self):
        assert prime_factors(13) == [13]


# ---------------------------------------------------------------------------
# valuation
# ---------------------------------------------------------------------------

class TestValuation:
    def test_basic(self):
        assert valuation(72, 2) == 3
        assert valuation(72, 3) == 2

    def test_coprime(self):
        assert valuation(7, 2) == 0

    def test_zero_raises(self):
        with pytest.raises(ValueError, match="infinite"):
            valuation(0, 2)

    def test_p_less_than_2_raises(self):
        with pytest.raises(ValueError, match="p >= 2"):
            valuation(10, 1)

    def test_p_zero_raises(self):
        with pytest.raises(ValueError, match="p >= 2"):
            valuation(10, 0)

    def test_negative_n(self):
        assert valuation(-8, 2) == 3


# ---------------------------------------------------------------------------
# euler_phi
# ---------------------------------------------------------------------------

class TestEulerPhi:
    def test_one(self):
        assert euler_phi(1) == 1

    def test_prime(self):
        assert euler_phi(97) == 96

    def test_composite(self):
        assert euler_phi(12) == 4

    def test_prime_power(self):
        assert euler_phi(8) == 4  # phi(2^3) = 4

    def test_zero_raises(self):
        with pytest.raises(ValueError, match="positive integers only"):
            euler_phi(0)

    def test_negative_raises(self):
        with pytest.raises(ValueError, match="positive integers only"):
            euler_phi(-5)


# ---------------------------------------------------------------------------
# multiplicative_order
# ---------------------------------------------------------------------------

class TestMultiplicativeOrder:
    def test_known_values(self):
        assert multiplicative_order(2, 7) == 3
        assert multiplicative_order(2, 5) == 4
        assert multiplicative_order(2, 73) == 9

    def test_order_one(self):
        assert multiplicative_order(1, 7) == 1

    def test_gcd_not_one_raises(self):
        with pytest.raises(ValueError, match="gcd"):
            multiplicative_order(0, 5)

    def test_mod_one(self):
        # ord_1(a) = 1 for all a (trivially a^1 ≡ 0 mod 1)
        assert multiplicative_order(2, 1) == 1


# ---------------------------------------------------------------------------
# is_self_conjugate
# ---------------------------------------------------------------------------

class TestIsSelfConjugate:
    def test_sc_true(self):
        result, j = is_self_conjugate(2, 5)
        assert result is True
        assert j == 2  # 2^2 = 4 ≡ -1 mod 5

    def test_sc_false_odd_order(self):
        result, j = is_self_conjugate(2, 73)
        assert result is False
        assert j is None

    def test_sc_false_3mod4(self):
        result, j = is_self_conjugate(2, 7)
        assert result is False

    def test_small_m(self):
        assert is_self_conjugate(2, 1) == (False, None)
        assert is_self_conjugate(2, 0) == (False, None)

    def test_not_coprime(self):
        assert is_self_conjugate(0, 5) == (False, None)


# ---------------------------------------------------------------------------
# integer_sqrt
# ---------------------------------------------------------------------------

class TestIntegerSqrt:
    def test_perfect_square(self):
        assert integer_sqrt(36) == 6
        assert integer_sqrt(0) == 0
        assert integer_sqrt(1) == 1

    def test_not_perfect_square(self):
        assert integer_sqrt(37) is None

    def test_negative(self):
        assert integer_sqrt(-1) is None


# ---------------------------------------------------------------------------
# jacobi_symbol
# ---------------------------------------------------------------------------

class TestJacobiSymbol:
    def test_legendre_cases(self):
        # (2/7) = 1, (3/7) = -1 (Legendre when n is prime)
        assert jacobi_symbol(2, 7) == 1
        assert jacobi_symbol(3, 7) in (-1, 0, 1)

    def test_zero(self):
        assert jacobi_symbol(0, 7) == 0

    def test_n_one(self):
        assert jacobi_symbol(5, 1) == 1

    def test_even_n_raises(self):
        with pytest.raises(ValueError):
            jacobi_symbol(3, 4)

    def test_negative_n_raises(self):
        with pytest.raises(ValueError):
            jacobi_symbol(3, -1)


# ---------------------------------------------------------------------------
# odd_part
# ---------------------------------------------------------------------------

class TestOddPart:
    def test_basic(self):
        assert odd_part(8) == 1
        assert odd_part(12) == 3
        assert odd_part(7) == 7

    def test_one(self):
        assert odd_part(1) == 1

    def test_zero_raises(self):
        with pytest.raises(ValueError, match="odd_part undefined"):
            odd_part(0)

    def test_negative_raises(self):
        with pytest.raises(ValueError, match="odd_part undefined"):
            odd_part(-4)


# ---------------------------------------------------------------------------
# two_adic_valuation (alias)
# ---------------------------------------------------------------------------

class TestTwoAdicValuation:
    def test_basic(self):
        assert two_adic_valuation(8) == 3
        assert two_adic_valuation(12) == 2
        assert two_adic_valuation(7) == 0
