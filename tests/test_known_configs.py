"""Tests for known-config consistency and the canonical source of truth."""
import pytest


class TestKnownConfigsCanonical:
    """All modules see the same known-config list from known_configs.py."""

    def test_canonical_count(self):
        from barker.known_configs import ALL_KNOWN_MINIMAL_COVERING
        # 7 triples + 1 quad + 4 five-sets = 12
        assert len(ALL_KNOWN_MINIMAL_COVERING) == 12

    def test_coverage_search_reexport(self):
        from barker.known_configs import ALL_KNOWN_MINIMAL_COVERING as canonical
        from barker.coverage_search import KNOWN_MINIMAL_COVERING_SETS as cs_sets
        assert set(canonical) == set(cs_sets)

    def test_minimal_cover_search_reexport(self):
        from barker.known_configs import ALL_KNOWN_MINIMAL_COVERING as canonical
        from barker.minimal_cover_search import ALL_KNOWN_MINIMAL_COVERING as mc_sets
        assert set(canonical) == set(mc_sets)

    def test_all_elements_are_frozensets(self):
        from barker.known_configs import ALL_KNOWN_MINIMAL_COVERING
        for s in ALL_KNOWN_MINIMAL_COVERING:
            assert isinstance(s, frozenset)

    def test_sizes_correct(self):
        from barker.known_configs import (
            KNOWN_MINIMAL_COVERING_TRIPLES,
            KNOWN_MINIMAL_COVERING_4SETS,
            KNOWN_MINIMAL_COVERING_5SETS,
        )
        assert all(len(t) == 3 for t in KNOWN_MINIMAL_COVERING_TRIPLES)
        assert all(len(t) == 4 for t in KNOWN_MINIMAL_COVERING_4SETS)
        assert all(len(t) == 5 for t in KNOWN_MINIMAL_COVERING_5SETS)

    def test_no_duplicates(self):
        from barker.known_configs import ALL_KNOWN_MINIMAL_COVERING
        assert len(ALL_KNOWN_MINIMAL_COVERING) == len(set(ALL_KNOWN_MINIMAL_COVERING))

    def test_all_primes_are_hard(self):
        """Every prime in the known configs should be a hard prime."""
        from barker.known_configs import ALL_KNOWN_MINIMAL_COVERING
        from barker.arithmetic import is_prime, multiplicative_order
        all_primes = set()
        for s in ALL_KNOWN_MINIMAL_COVERING:
            all_primes |= s
        for p in all_primes:
            assert is_prime(p), f"{p} is not prime"
            assert p % 4 == 1, f"{p} is not 1 mod 4"
            d = multiplicative_order(2, p)
            assert d % 2 == 1, f"ord_{p}(2) = {d} is even; {p} is not a hard prime"


class TestRunSweepGuard:
    """run_sweep raises NotImplementedError instead of ModuleNotFoundError."""

    def test_run_sweep_raises_not_implemented(self):
        from barker.sweep import run_sweep
        with pytest.raises(NotImplementedError, match="admissibility"):
            run_sweep(10)
