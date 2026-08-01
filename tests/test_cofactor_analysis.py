"""
Tests for the hub self-defeat theorem and pair-vs-cofactor decoupling.

These tests verify the central mathematical finding: the covering-set
concept (pair-level) and the Turyn elimination test (cofactor-level)
are not equivalent.  83% of known covering sets are false alarms at
the cofactor level.
"""
import pytest
from barker.cofactor_analysis import (
    cofactor_test, verify_hub_self_defeat, classify_all_known,
    CofactorAnalysis,
)
from barker.known_configs import (
    KNOWN_MINIMAL_COVERING_TRIPLES,
    KNOWN_MINIMAL_COVERING_4SETS,
    KNOWN_MINIMAL_COVERING_5SETS,
)


# ---------------------------------------------------------------------------
# Hub self-defeat theorem
# ---------------------------------------------------------------------------

class TestHubSelfDefeat:
    """The four-line theorem: every O1 hub covering set is self-defeating."""

    def test_k6_hub_self_defeat(self):
        """The headline k=6 configuration is self-defeating at its hub."""
        assert verify_hub_self_defeat(
            hub=17881,
            cycle=(1801, 14537, 13417, 18121, 18521),
        )

    def test_k6_cofactor_not_sc_at_hub(self):
        """Full cofactor at hub 17881 is NOT self-conjugate."""
        result = cofactor_test((17881, 1801, 14537, 13417, 18121, 18521))
        hub_target = next(t for t in result.targets if t.target == 17881)
        assert hub_target.cofactor_chi == 0
        assert hub_target.is_sc is False

    def test_k6_cofactor_is_sc_at_all_other_targets(self):
        """Full cofactor IS self-conjugate at all 5 non-hub targets."""
        result = cofactor_test((17881, 1801, 14537, 13417, 18121, 18521))
        non_hub = [t for t in result.targets if t.target != 17881]
        assert len(non_hub) == 5
        for t in non_hub:
            assert t.is_sc is True, f"Target {t.target}: expected SC"
            assert t.cofactor_chi != 0

    def test_k6_turyn_eliminates(self):
        """The Turyn test eliminates the k=6 configuration."""
        result = cofactor_test((17881, 1801, 14537, 13417, 18121, 18521))
        assert result.turyn_eliminates is True
        assert result.is_genuine is False
        assert result.obstruction_type == "A-self-defeating"

    def test_hub_self_defeat_structural(self):
        """The theorem holds for ANY hub where all cycle primes have chi=0."""
        from barker.two_primary import build_two_primary_table, quotient_class
        from barker.sweep import find_hard_primes

        # Use a smaller prime set for speed
        hard_primes = [h["prime"] for h in find_hard_primes(5000)]
        if len(hard_primes) < 10:
            pytest.skip("Not enough hard primes for structural test")

        table = build_two_primary_table(hard_primes)

        # For each prime x, find primes in V_x and check the theorem
        checked = 0
        for x in hard_primes[:15]:
            vx = [p for p in hard_primes if p != x
                  and quotient_class(p, x) == 0]
            if len(vx) < 3:
                continue
            # Pick any 3 primes from V_x
            cycle = tuple(vx[:3])
            assert verify_hub_self_defeat(x, cycle), (
                f"Hub self-defeat failed for hub={x}, cycle={cycle}"
            )
            checked += 1

        assert checked > 0, "No hubs tested"


# ---------------------------------------------------------------------------
# k=3 triples: cofactor = pair product, always NOT SC
# ---------------------------------------------------------------------------

class TestTripleCofactors:
    """For k=3 covering triples, cofactor = pair, so NOT SC everywhere."""

    @pytest.mark.parametrize("triple", KNOWN_MINIMAL_COVERING_TRIPLES)
    def test_triple_all_not_sc(self, triple):
        result = cofactor_test(triple)
        assert result.n_not_sc == 3, (
            f"Triple {triple}: expected 3 NOT-SC targets, got {result.n_not_sc}"
        )
        assert result.turyn_eliminates is True
        assert result.obstruction_type == "A-self-defeating"


# ---------------------------------------------------------------------------
# Genuine obstructions: k=4 quad and k=5 set #4
# ---------------------------------------------------------------------------

class TestGenuineObstructions:
    """The two Type B configurations where Turyn cannot eliminate."""

    def test_k4_quad_genuine(self):
        result = cofactor_test((337, 937, 1433, 1721))
        assert result.is_genuine is True
        assert result.turyn_eliminates is False
        assert result.obstruction_type == "B-genuine"
        assert result.n_sc == 4
        # Every cofactor chi-sum is nonzero
        for t in result.targets:
            assert t.cofactor_chi != 0, f"Target {t.target} has chi=0"
            assert t.is_sc is True

    def test_k5_set4_genuine(self):
        result = cofactor_test((4297, 4409, 5689, 6553, 7753))
        assert result.is_genuine is True
        assert result.turyn_eliminates is False
        assert result.obstruction_type == "B-genuine"
        assert result.n_sc == 5

    def test_genuine_has_no_hub(self):
        """Type B configs have no prime that puts all others in H_x."""
        for config in [(337, 937, 1433, 1721),
                       (4297, 4409, 5689, 6553, 7753)]:
            result = cofactor_test(config)
            assert result.hub_target is None, (
                f"Config {config} has unexpected hub at {result.hub_target}"
            )


# ---------------------------------------------------------------------------
# Full classification
# ---------------------------------------------------------------------------

class TestClassification:
    """The complete classification of all 13 known covering sets."""

    @pytest.fixture(scope="class")
    def classification(self):
        return classify_all_known()

    def test_total_count(self, classification):
        # 12 from known_configs + 1 k=6 = 13
        assert classification.n_total == 13

    def test_type_a_count(self, classification):
        assert classification.n_type_a == 11

    def test_type_b_count(self, classification):
        assert classification.n_type_b == 2

    def test_false_alarm_rate(self, classification):
        rate = classification.false_alarm_rate
        assert 0.84 < rate < 0.85  # 11/13 ≈ 84.6%

    def test_type_b_are_the_known_two(self, classification):
        type_b_configs = {r.config for r in classification.type_b}
        assert (337, 937, 1433, 1721) in type_b_configs
        assert (4297, 4409, 5689, 6553, 7753) in type_b_configs

    def test_k6_is_type_a(self, classification):
        k6_results = [r for r in classification.type_a if r.k == 6]
        assert len(k6_results) == 1
        assert k6_results[0].hub_target == 17881


# ---------------------------------------------------------------------------
# Consistency: chi-sum = 0 iff NOT SC (verified independently)
# ---------------------------------------------------------------------------

class TestConsistency:
    """The cofactor_test function cross-checks chi-sum vs is_self_conjugate."""

    def test_k6_consistency(self):
        """cofactor_test asserts internally that chi=0 iff NOT SC."""
        # This will raise AssertionError if the consistency check fails
        cofactor_test((17881, 1801, 14537, 13417, 18121, 18521))

    def test_k4_consistency(self):
        cofactor_test((337, 937, 1433, 1721))

    @pytest.mark.parametrize("triple", KNOWN_MINIMAL_COVERING_TRIPLES)
    def test_triple_consistency(self, triple):
        cofactor_test(triple)
