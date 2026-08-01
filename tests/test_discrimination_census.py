"""The discrimination census must use the PRIMARY taxonomy of §4.

The taxonomy has six mutually exclusive primary strata — A1, A2, A3, B0, B1,
B_int — with δ_max a secondary annotation on B_int and A_blocked an overlapping
refinement flag, not a seventh stratum.  The enumeration cache spells interior-B
labels as "B(δ=1)", "B(δ=2)", "B(δ=3)"; comparing those raw labels treats one
stratum as three and counts within-B_int pairs as cross-stratum.

At k = 6 the B_int groups have sizes 3, 7, 3, so the error admitted
3·7 + 3·3 + 7·3 = 51 spurious pairs, every one of them separating at the
δ-profile level — inflating the total and λ = 1 by 51 apiece and leaving the
other levels untouched.
"""
import json
import os
import sys
from collections import Counter
from itertools import combinations

import pytest

_RESEARCH = os.path.join(
    os.path.dirname(__file__), "..", "barker_k6_bundle", "research"
)
sys.path.insert(0, _RESEARCH)

from _common import build_labeled_graph, two_fwl_signature  # noqa: E402
from discrimination_depth import (  # noqa: E402
    delta_profile,
    i6_invariant,
    one_wl_signature,
    primary_stratum,
    vgraph_canonical,
)

EXPECTED_TOTAL = 14857
EXPECTED_HISTOGRAM = [14719, 26, 111, 0, 1]
EXPECTED_PER_K = {3: 10676, 4: 1577, 5: 1193, 6: 1411}
SPURIOUS_PAIRS = 51


@pytest.fixture(scope="module")
def cache():
    with open(os.path.join(_RESEARCH, "_enumeration_cache.json")) as f:
        return [(k, cls, tuple(cfg)) for k, cls, _p, cfg in json.load(f)]


@pytest.fixture(scope="module")
def signatures(cache):
    sys.path.insert(
        0, os.path.join(os.path.dirname(__file__), "..", "barker_k6_bundle", "code")
    )
    from barker.sweep import find_hard_primes
    from barker.two_primary import build_two_primary_table

    table = build_two_primary_table(
        [h["prime"] for h in find_hard_primes(80000)][:80]
    )
    wl1, fwl2 = {}, {}
    rows = []
    for k, cls, cfg in cache:
        g = build_labeled_graph(cfg, table)
        rows.append({
            "k": k,
            "cls": primary_stratum(cls),
            "raw": cls,
            "L1": delta_profile(cfg, table),
            "L2": vgraph_canonical(cfg, table),
            "L3": i6_invariant(cfg, table),
            "L4": one_wl_signature(*g, wl1),
            "L5": two_fwl_signature(*g, fwl2),
        })
    return rows


class TestPrimaryStratum:
    def test_interior_b_labels_collapse(self):
        for raw in ("B(δ=1)", "B(δ=2)", "B(δ=3)"):
            assert primary_stratum(raw) == "B_int"

    def test_other_strata_are_untouched(self):
        for raw in ("A1", "A2", "A3", "B0", "B1"):
            assert primary_stratum(raw) == raw

    def test_exactly_six_primary_strata_occur(self, cache):
        strata = {primary_stratum(cls) for _k, cls, _c in cache}
        assert strata == {"A1", "A2", "A3", "B0", "B1", "B_int"}


class TestCensus:
    def test_total_and_per_k(self, signatures):
        per_k = Counter()
        for k in (3, 4, 5, 6):
            rows = [r for r in signatures if r["k"] == k]
            per_k[k] = sum(1 for a, b in combinations(rows, 2)
                           if a["cls"] != b["cls"])
        assert dict(per_k) == EXPECTED_PER_K
        assert sum(per_k.values()) == EXPECTED_TOTAL

    def test_histogram(self, signatures):
        hist = Counter()
        for k in (3, 4, 5, 6):
            rows = [r for r in signatures if r["k"] == k]
            for a, b in combinations(rows, 2):
                if a["cls"] == b["cls"]:
                    continue
                lam = next((l for l in (1, 2, 3, 4, 5)
                            if a[f"L{l}"] != b[f"L{l}"]), None)
                assert lam is not None, "unresolved cross-stratum pair"
                hist[lam] += 1
        assert [hist.get(l, 0) for l in (1, 2, 3, 4, 5)] == EXPECTED_HISTOGRAM

    def test_raw_labels_would_inflate_by_exactly_51_at_lambda_1(self, signatures):
        """Pins the defect itself, so the fix cannot silently regress: the
        within-B_int pairs are real pairs that must NOT count as cross-stratum,
        and every one of them separates at the δ-profile."""
        levels = Counter()
        for k in (3, 4, 5, 6):
            rows = [r for r in signatures if r["k"] == k]
            for a, b in combinations(rows, 2):
                if a["raw"] != b["raw"] and a["cls"] == b["cls"]:
                    lam = next((l for l in (1, 2, 3, 4, 5)
                                if a[f"L{l}"] != b[f"L{l}"]), None)
                    levels[lam] += 1
        assert sum(levels.values()) == SPURIOUS_PAIRS
        assert levels == Counter({1: SPURIOUS_PAIRS})

    def test_b_int_group_sizes_at_k6(self, cache):
        sizes = Counter(cls for k, cls, _c in cache
                        if k == 6 and cls.startswith("B("))
        assert sorted(sizes.values()) == [3, 3, 7]
        assert sum(a * b for a, b in combinations(sizes.values(), 2)) == SPURIOUS_PAIRS

    def test_lambda_5_singleton_survives(self, signatures):
        found = []
        for k in (3, 4, 5, 6):
            rows = [r for r in signatures if r["k"] == k]
            for a, b in combinations(rows, 2):
                if a["cls"] == b["cls"]:
                    continue
                if all(a[f"L{l}"] == b[f"L{l}"] for l in (1, 2, 3, 4)) \
                        and a["L5"] != b["L5"]:
                    found.append((k, a["cls"], b["cls"]))
        assert len(found) == 1
        assert found[0][0] == 5
        assert {found[0][1], found[0][2]} == {"B_int", "A3"}
