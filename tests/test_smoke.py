"""Phase 0 — Smoke tests that freeze current behavior before any changes."""
from itertools import combinations

import pytest


def _is_covering(sub, tbl, quotient_class):
    """True iff every pair in `sub` has a witness inside `sub`."""
    for a, b in combinations(sub, 2):
        if not any(
            (quotient_class(a, c) + quotient_class(b, c)) % (2 ** tbl.depth[c]) == 0
            for c in sub
            if c not in (a, b)
        ):
            return False
    return True


class TestImportAll:
    """Every module in barker/ imports without error."""

    def test_import_arithmetic(self):
        from barker import arithmetic  # noqa: F401

    def test_import_two_primary(self):
        from barker import two_primary  # noqa: F401

    def test_import_sweep(self):
        from barker import sweep  # noqa: F401

    def test_import_coverage_search(self):
        from barker import coverage_search  # noqa: F401

    def test_import_minimal_cover_search(self):
        from barker import minimal_cover_search  # noqa: F401

    def test_import_o1_realizability(self):
        from barker import o1_realizability  # noqa: F401

    def test_import_o1_cycle_obstruction(self):
        from barker import o1_cycle_obstruction  # noqa: F401

    def test_import_o1_cycle_classification(self):
        from barker import o1_cycle_classification  # noqa: F401

    def test_import_o1_final_result(self):
        from barker import o1_final_result  # noqa: F401

    def test_import_o1_structural_analysis(self):
        from barker import o1_structural_analysis  # noqa: F401

    def test_import_o1_program_retrospective(self):
        from barker import o1_program_retrospective  # noqa: F401


class TestHeadlineResult:
    """The minimal k=6 covering set verification — the gold regression check."""

    @pytest.fixture(scope="class")
    def table_and_primes(self):
        from barker.two_primary import build_two_primary_table, quotient_class
        from barker.sweep import find_hard_primes
        hard80 = [h["prime"] for h in find_hard_primes(80000)][:80]
        tbl = build_two_primary_table(hard80)
        return tbl, hard80, quotient_class

    def test_all_config_primes_are_hard(self, table_and_primes):
        tbl, hard80, _ = table_and_primes
        config = (17881, 1801, 14537, 13417, 18121, 18521)
        prime_set = set(hard80)
        for p in config:
            assert p in prime_set, f"{p} not in first 80 hard primes"
            assert tbl.depth[p] >= 3, f"{p} depth < 3"

    def test_cycle_vertices_in_Vx(self, table_and_primes):
        _, _, quotient_class = table_and_primes
        hub = 17881
        cycle = (1801, 14537, 13417, 18121, 18521)
        for p in cycle:
            assert quotient_class(p, hub) == 0, f"chi_{hub}({p}) != 0"

    def test_directed_5_cycle_edges(self, table_and_primes):
        tbl, hard80, quotient_class = table_and_primes
        hub = 17881
        cycle = (1801, 14537, 13417, 18121, 18521)
        vx = [p for p in hard80 if p != hub and quotient_class(p, hub) == 0]
        L_map = {p: (-quotient_class(hub, p)) % (2 ** tbl.depth[p]) for p in vx}
        for i in range(5):
            pi, pj = cycle[i], cycle[(i + 1) % 5]
            chi = quotient_class(pj, pi)
            L = L_map[pi]
            assert chi == L, f"Edge {pi}->{pj}: chi={chi} != L={L}"

    def test_all_15_pairs_covered(self, table_and_primes):
        from itertools import combinations
        tbl, _, quotient_class = table_and_primes
        config = (17881, 1801, 14537, 13417, 18121, 18521)
        for a, b in combinations(config, 2):
            found = False
            for c in config:
                if c in (a, b):
                    continue
                t = tbl.depth[c]
                if (quotient_class(a, c) + quotient_class(b, c)) % (2 ** t) == 0:
                    found = True
                    break
            assert found, f"Pair ({a}, {b}) not covered"

    def test_no_proper_subset_is_covering(self, table_and_primes):
        """Exhaustive minimality: every proper subset of size ≥ 3, not just the
        six single-element deletions (see the non-monotonicity test below)."""
        tbl, _, quotient_class = table_and_primes
        config = (17881, 1801, 14537, 13417, 18121, 18521)
        for r in range(3, len(config)):
            for sub in combinations(config, r):
                assert not _is_covering(sub, tbl, quotient_class), \
                    f"Proper subset {sub} is covering"

    def test_single_deletion_does_not_certify_minimality(self, table_and_primes):
        """Coverage is not monotone under deletion, so the one-deletion test
        admits false minimality certificates.  This set passes it and is not
        minimal."""
        tbl, _, quotient_class = table_and_primes
        S = (73, 233, 1721, 4057, 18121)
        assert _is_covering(S, tbl, quotient_class)
        for skip in S:
            sub = tuple(p for p in S if p != skip)
            assert not _is_covering(sub, tbl, quotient_class), \
                f"expected {sub} non-covering"
        assert _is_covering((73, 233, 1721), tbl, quotient_class), \
            "the size-3 covering subset that defeats the one-deletion test"
