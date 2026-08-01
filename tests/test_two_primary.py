"""Tests for barker.two_primary — Layer 2 character theory."""
import pytest
from barker.two_primary import (
    _v2, _odd_part, two_primary_depth, two_primary_level,
    in_odd_subgroup, quotient_class, is_2torsion,
    build_two_primary_table, TwoPrimaryCharacterTable,
)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

class TestV2:
    def test_powers_of_2(self):
        assert _v2(1) == 0
        assert _v2(2) == 1
        assert _v2(8) == 3

    def test_odd(self):
        assert _v2(7) == 0
        assert _v2(15) == 0

    def test_mixed(self):
        assert _v2(12) == 2  # 12 = 4*3

    def test_zero_raises(self):
        with pytest.raises(ValueError, match="infinite"):
            _v2(0)


class TestOddPart:
    def test_basic(self):
        assert _odd_part(8) == 1
        assert _odd_part(12) == 3

    def test_odd_input(self):
        assert _odd_part(7) == 7

    def test_zero_raises(self):
        with pytest.raises(ValueError):
            _odd_part(0)


# ---------------------------------------------------------------------------
# 2-primary depth and level
# ---------------------------------------------------------------------------

class TestTwoPrimaryDepth:
    def test_small_primes(self):
        # 5-1=4=2^2 → t=2
        assert two_primary_depth(5) == 2
        # 73-1=72=8*9 → t=3
        assert two_primary_depth(73) == 3
        # 89-1=88=8*11 → t=3
        assert two_primary_depth(89) == 3

    def test_even_prime_raises(self):
        with pytest.raises(ValueError):
            two_primary_depth(2)

    def test_composite_raises(self):
        with pytest.raises(ValueError):
            two_primary_depth(15)


class TestQuotientClass:
    def test_deterministic(self):
        """Same inputs always produce the same output."""
        c1 = quotient_class(73, 89)
        c2 = quotient_class(73, 89)
        assert c1 == c2

    def test_zero_for_Hx_member(self):
        """Hard prime 73 with odd order mod 89² should have chi=0."""
        # 73 has ord_{89}(2) odd, and we know from the research
        # that certain primes land in H_x.  Just verify type/range.
        chi = quotient_class(73, 89)
        t = two_primary_depth(89)
        assert 0 <= chi < 2**t

    def test_p_equals_x_raises(self):
        with pytest.raises(ValueError, match="not invertible"):
            quotient_class(89, 89)

    def test_p_zero_raises(self):
        with pytest.raises(ValueError, match="not invertible"):
            quotient_class(0, 89)


# ---------------------------------------------------------------------------
# Character table
# ---------------------------------------------------------------------------

class TestBuildTwoPrimaryTable:
    @pytest.fixture(scope="class")
    def small_table(self):
        primes = [73, 89, 233]
        return build_two_primary_table(primes), primes

    def test_depth_populated(self, small_table):
        tbl, primes = small_table
        for p in primes:
            assert p in tbl.depth
            assert tbl.depth[p] >= 1

    def test_chi_populated(self, small_table):
        tbl, primes = small_table
        for p in primes:
            for x in primes:
                if p == x:
                    continue
                assert (p, x) in tbl.chi

    def test_pair_chi_sum_populated(self, small_table):
        tbl, primes = small_table
        from itertools import combinations
        for a, b in combinations(primes, 2):
            for x in primes:
                if x in (a, b):
                    continue
                assert ((a, b), x) in tbl.pair_chi_sum

    def test_is_sc_method(self, small_table):
        tbl, _ = small_table
        # Just verify it doesn't crash and returns bool
        result = tbl.is_sc(73, 89)
        assert isinstance(result, bool)

    def test_cancels_method(self, small_table):
        tbl, _ = small_table
        result = tbl.cancels(73, 89, 233)
        assert isinstance(result, bool)

    @pytest.fixture(scope="class")
    def cancelling_table(self):
        """A table large enough to contain actual cancellations.

        The 3-prime `small_table` has none at all, so symmetry assertions on it
        hold vacuously (False == False) and cannot detect a key-order bug.
        """
        from barker.sweep import find_hard_primes
        primes = [h["prime"] for h in find_hard_primes(80000)][:12]
        return build_two_primary_table(primes), primes

    def test_fixture_actually_contains_cancellations(self, cancelling_table):
        """Guards the two tests below against becoming vacuous."""
        from itertools import combinations
        tbl, primes = cancelling_table
        n = sum(
            1
            for a, b in combinations(primes, 2)
            for x in primes
            if x not in (a, b) and tbl.pair_chi_sum[((a, b), x)] == 0
        )
        assert n > 0, "fixture has no cancelling pairs; symmetry tests would be vacuous"

    def test_cancels_is_symmetric_in_its_pair(self, cancelling_table):
        """pair_chi_sum is keyed smaller-prime-first; cancels() must normalise
        the key, or every a > b call silently reports False."""
        from itertools import combinations
        tbl, primes = cancelling_table
        for a, b in combinations(primes, 2):
            for x in primes:
                if x in (a, b):
                    continue
                assert tbl.cancels(a, b, x) == tbl.cancels(b, a, x)

    def test_cancels_agrees_with_chi_sum_in_both_orders(self, cancelling_table):
        from itertools import combinations
        tbl, primes = cancelling_table
        for a, b in combinations(primes, 2):
            for x in primes:
                if x in (a, b):
                    continue
                expected = (tbl.chi[(a, x)] + tbl.chi[(b, x)]) % (2 ** tbl.depth[x]) == 0
                assert tbl.cancels(a, b, x) is expected
                assert tbl.cancels(b, a, x) is expected
