"""Fast regressions for the realization-theorem guardrail."""

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "barker_k6_bundle" / "research" / "realization_checks.py"
SPEC = importlib.util.spec_from_file_location("realization_checks", PATH)
assert SPEC and SPEC.loader
RC = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RC)


def test_affine_commutator_and_derived_subgroup():
    for t in range(2, 6):
        row = RC.check_affine_depth(t)
        assert row["commutator_formula"]
        assert row["delta_mod_4"] == 2
        assert row["derived_subgroup_exact"]


def test_spurious_right_translation_factor_is_detected():
    n = 8
    correct = RC.check_affine_depth(3)["delta_3_5"]
    wrong = correct * pow(3 * 5, -1, n) % n
    assert correct == 6
    assert wrong == 2
    assert wrong != correct


def test_exact_depth_conjugacy_is_common_row_gauge():
    for t in range(2, 6):
        assert RC.check_affine_depth(t)["exact_depth_conjugacy_is_row_gauge"]


def test_slice_density_is_prefix_independent():
    rows = RC.check_slice_counts()
    assert rows
    assert all(row["equals_2_over_4t"] for row in rows)


def test_character_coordinate_matches_kummer_residue_nonvacuously():
    row = RC.check_character_coordinates(5)
    assert row["kummer_coordinate_identity"]
    assert row["quadratic_parity_identity"]
    assert row["nonzero_coordinates"] > 0
    assert row["odd_coordinates"] > 0


def test_depth_two_hard_slice_is_empty_small_range():
    row = RC.check_density_slices(20_000)
    assert row["depth_2_zero"]
    assert row["hard_count_p_1_mod_4"] > 0
