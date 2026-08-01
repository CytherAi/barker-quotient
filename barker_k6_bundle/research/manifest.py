#!/usr/bin/env python3
"""
manifest.py — provenance manifests for the research layer.

Two tiers, per the release policy:

  RELEASE manifest (`_manifest/release.json`)
      pins the repository tree, the environment, the ordered prime universe,
      and the set of registered experiments.

  EXPERIMENT manifest (`_manifest/<name>.json`), one per experiment
      pins that experiment's command, parameters, seeds, source files, input
      and output hashes, and the manuscript claims it supplies.

The split is deliberate: §6.2 can fail provenance without invalidating the
verified §3–§5 artifacts, while the release manifest still makes the paper a
single coherent snapshot.

Usage
-----
    python3 barker_k6_bundle/research/manifest.py build [name ...]
    python3 barker_k6_bundle/research/manifest.py verify [name ...]
    python3 barker_k6_bundle/research/manifest.py list

`verify` exits non-zero if any registered artifact is MISSING (never recorded,
or recorded and since deleted) or STALE (present but its hash no longer matches
what was recorded). It also enforces the release snapshot itself:

  - the **release inventory** — per-file hashes of every manuscript, PDF,
    README, script, test and figure the claims depend on, plus one combined
    tree hash. This is the actual tree pin; a `tree_dirty` boolean is not one,
    because arbitrary edits leave it unchanged. Drift is reported by filename.
  - the recorded commit, tolerating drift that touches only `_manifest/`;
  - **environment capability**, not the exact recorded build: the documented
    Python floor and a NumPy major line with no breaking API change (pinning a
    patch version would red-gate every machine but the author's);
  - the exact registered experiment set and the hash of every per-experiment
    manifest;
  - for `skeleton_exact` and `maxpair_exact`, the emitted exact fractions
    against the registered constants.

All conditions are release blockers; a passing verify is what the §6.2 release
gate requires.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
MANIFEST_DIR = os.path.join(HERE, "_manifest")
SCHEMA_VERSION = 1


# ---------------------------------------------------------------------------
# Experiment registry
#
# `claims` names what the manuscript takes from the experiment, so a provenance
# failure points at the prose it invalidates rather than at a bare filename.
# ---------------------------------------------------------------------------

REGISTRY = {
    "k5_correlation": {
        "command": ["python3", "barker_k6_bundle/research/k5_correlation.py",
                    "{N}", "--check"],
        "parameters": {"N": [100, 120, 140, 160]},
        "seeds": [],
        "sources": ["k5_correlation.py", "per_depth_w2.py", "_common.py"],
        "inputs": ["_per_depth_w2_cache_N{N}.json"],
        "outputs": ["_k5_correlation_N{N}.json"],
        "claims": [
            "§6.2 (i) aggregate joint-elimination table",
            "§6.2 (ii) conditional α_both table",
            "§6.2 (ii) conditional (α_both, α_asymm, α_none) table",
            "§6.2 (iii) cofactor-sharing reading",
            "Proposition 6.2.1 empirical check (profile (0,1,2) → 0)",
        ],
    },
    "per_depth_w2": {
        "command": ["python3", "barker_k6_bundle/research/per_depth_w2.py", "{N}"],
        "parameters": {"N": [80, 100, 120, 140, 160, 200, 240, 280]},
        "seeds": [],
        "sources": ["per_depth_w2.py", "_common.py"],
        "inputs": [],
        "outputs": ["_per_depth_w2_cache_N{N}.json"],
        "claims": [
            "Corollary 4.9 per-(t, w) conditional rate table",
            "§6.2 w_x = 2 rate trajectory across N = 100..160",
            "k = 5 zero-δ enumeration counts per universe",
        ],
    },
    "discrimination_depth": {
        "command": ["python3", "barker_k6_bundle/research/discrimination_depth.py"],
        "parameters": {},
        "seeds": [],
        "sources": ["discrimination_depth.py", "_common.py"],
        "inputs": ["_enumeration_cache.json"],
        "outputs": [],
        "claims": [
            "§5.4 marginal contribution histogram (14719 / 26 / 111 / 0 / 1)",
            "§5.7 the unique λ = 5 cross-class pair",
        ],
    },
    "i6_vs_1wl": {
        "command": ["python3", "barker_k6_bundle/research/i6_vs_1wl.py"],
        "parameters": {},
        "seeds": [],
        "sources": ["i6_vs_1wl.py", "discrimination_depth.py", "_common.py"],
        "inputs": ["_enumeration_cache.json"],
        "outputs": [],
        "claims": [
            "§5.6 agreement table (26094 / 89 / 0 / 5426)",
            "§5.6 Observation 5.4 (1-WL strictly refines I_6)",
        ],
    },
    "skeleton_e1": {
        "command": ["python3", "barker_k6_bundle/research/skeleton_model_e1.py",
                    "sample", "300000000", "2000000", "{seed}",
                    "_e1_survivors_s{seed}.npy"],
        "parameters": {
            "trials_per_seed": 300_000_000,
            # seed 1 predates the standard depth and was run at 1e8 trials.
            "trials_seed_1": 100_000_000,
            "batch": 2_000_000,
            "total_trials": 4_000_000_000,
        },
        "seeds": [1, 2, 3, 4, 5, 6, 7, 8, 11, 12, 13, 14, 15, 16],
        "sources": ["skeleton_model_e1.py"],
        "inputs": [],
        "outputs": ["_e1_survivors_s{seed}.npy"],
        "claims": [
            "§6.2 Monte-Carlo validation pool for the exact constant "
            "R(3,3,3,3) = 1373/5300: 2395/9267 = 0.2584, |Δ| = 0.06 pp",
        ],
    },
    # Distinct estimand from skeleton_e1: the mixed-depth (3,3,3,4) profile.
    # Kept as its own experiment because conflating the two is exactly the
    # error the §6.2 reconciliation corrects — 0.2661 is this benchmark, not
    # the all-depth-3 one.
    "skeleton_e1_mixed": {
        "command": ["python3",
                    "barker_k6_bundle/research/skeleton_model_e1_mixed.py",
                    "measure", "_e1deep_s{seed}.npz"],
        "parameters": {"profile": "(3,3,3,4)", "n_cell": 11821,
                       "locked_benchmark": 0.2661},
        "seeds": [401, 402, 403, 404, 405, 406, 407, 408, 409, 410],
        "sources": ["skeleton_model_e1_mixed.py"],
        "inputs": [],
        "outputs": ["_e1deep_s{seed}.npz"],
        "claims": [
            "§6.2 Monte-Carlo validation pool for the exact constant "
            "R(3,3,3,4) = 1123/4215: 3146/11821 = 0.2661, |Δ| = 0.03 pp — "
            "the preregistration-locked value earlier drafts mistakenly "
            "compared against the all-depth-3 census rate",
        ],
    },
    # The maximal-pairwise run: the skeleton with the measured universe (3,3)
    # joints injected. It supplies §6.2's *unresolved* maximal-pairwise
    # estimate — a point estimate between the independent-digit constant and
    # the census, whose cluster interval still contains the constant — so its
    # pool must be gated like any other claim.
    "skeleton_maxpair": {
        # One runnable command that aggregates ALL ten pools and asserts the
        # published counts; a per-seed `measure` would not reproduce the
        # aggregate the manuscript quotes.
        "command": ["python3",
                    "barker_k6_bundle/research/skeleton_model_maxpair.py",
                    "check"],
        "parameters": {
            "profile": "(3,3,3,4)",
            "N_universe": 320,
            "trials_per_seed": 1_500_000_000,
            "batch": 2_000_000,
            "survivors": 9205, "contributors": 5732,
            "successes": 3003, "targets": 11550, "R_point": 0.2600,
            "cluster_se": 0.00434, "cluster_ci95": [0.2516, 0.2685],
        },
        "seeds": [501, 502, 503, 504, 505, 506, 507, 508, 509, 510],
        "sources": ["skeleton_model_maxpair.py"],
        "inputs": [],
        "outputs": ["_maxpair_s{seed}.npz", "_maxpair_summary.json"],
        "claims": [
            "§6.2 maximal-pairwise point estimate R(3,3,3,4) = 3003/11550 = "
            "0.2600 from 5,732 contributing survivor matrices, cluster "
            "bootstrap interval [0.2516, 0.2685]. The pool no longer sources a "
            "claim: the exact engine supersedes it, and the pool is its "
            "sampling validation — the interval covers the exact pooled value "
            "0.2663959 with the point estimate 1.47 SE below it",
            "§6.2 per-hub Monte-Carlo counts 785/2921, 745/2885, 727/2835, "
            "746/2909 — an apparent spread of 0.0123 at ~0.009 sampling error "
            "per hub, against a true spread of 3.4e-5, so the pool cannot "
            "resolve the hubs it pools",
        ],
    },
    # Branch-pruning for Question 6.2.G: the Rédei bridge lemma, falsified.
    # Registered because it decides where enumeration compute does NOT go. Its
    # claim is deliberately narrow — a negative about classical Rédei symbols,
    # not about arithmetic constraints in general, and not a manuscript claim.
    "redei_bridge": {
        "command": ["python3", "barker_k6_bundle/research/redei_bridge.py"],
        "parameters": {
            "n_hard_primes": 44, "max_prime": 10937,
            "all_QR_triangles": 1696,
            "solution_independent": [120, 120],
            "s3_symmetric": [120, 120],
            "distribution": {"+1": 847, "-1": 849},
            "invariant_classes": 1225,
            "testable_classes": 270,
            "mixed_sign_classes": 167,
            "counterexample_minus": [4057, 4201, 6553],
            "counterexample_plus": [4409, 5209, 5689],
            "cofactor_patterns_with_all_QR_triangle": 23,
            "cofactor_patterns_total": 64,
            "hub_cofactor_triples_applicable": 0,
        },
        "seeds": [],
        "sources": ["redei_bridge.py", "../../tests/test_redei_bridge.py"],
        "inputs": [],
        "outputs": ["_redei_bridge.json"],
        "claims": [
            "Q6.2.G branch-pruning: classical Rédei symbols are NOT functions "
            "of the normalisation-invariant χ-data — 167 of the 270 invariant "
            "classes holding at least two of the 1,696 all-QR triangles carry "
            "both signs, e.g. (4057, 4201, 6553) and (4409, 5209, 5689) share "
            "an invariant class with opposite symbols",
            "Q6.2.G branch-pruning: classical Rédei symbols are NOT defined on "
            "the hub triangles carrying the deciding all-QNR observable — the "
            "gate forces the hub's four edges odd, so 0 of 6 hub-cofactor "
            "triples meet the pairwise-trivial Hilbert side conditions, and "
            "only 23 of 64 cofactor parity patterns contain any all-QR triangle",
            "symbol validation: the computed symbol is independent of which "
            "primitive conic solution is used and is S₃-symmetric (120/120 "
            "each) — Rédei's defining property, so the normalisation is right",
            "χ_x is a homomorphism factoring through (Z/x)*, and a different "
            "primitive root rescales χ_x by one odd unit, so the only "
            "normalisation-invariant content of a pair is v₂(χ_x(p))",
        ],
    },
    # Theorem-level calibration of the §6.2 even-sector joint. Registered with
    # a deliberately narrow boundary: it IDENTIFIES the quartic-bit agreement
    # with a classical Legendre symbol, and explains neither that symbol's bias
    # nor the ordered asymmetry, nor anything in the odd sector.
    "burde_pair_law": {
        "command": ["python3", "barker_k6_bundle/research/burde_pair_law.py"],
        "parameters": {
            "universe": 320, "depth3_primes": 250,
            "even_sector_pairs": 15564, "pairs_after_zero_delta": 8734,
            "equals_We_sum": True,
            "identity_holds": 8734, "identity_of": 8734,
            "four_forms_equivalent": 8734,
            "rhs_split": {"+1": 4994, "-1": 3740},
            "marginals": {"(q/p)_4=+1": 0.3401, "(p/q)_4=+1": 0.3295},
            "agreement_count": 4994,
            "sign_choice_invariant": 8734,
            "cofactor_patterns_with_even_edge": 63,
            "hub_cofactor_edges_applicable": 0,
            "negative_control_scrambled": 0.5065,
            "negative_control_perturbed": 0.5,
        },
        "seeds": [],
        "sources": ["burde_pair_law.py", "../../tests/test_burde_pair_law.py"],
        "inputs": [],
        "outputs": ["_burde_pair_law.json"],
        "claims": [
            "§6.2 calibration: on the exact population the manuscript measures "
            "its even joint on — 8,734 depth-3 even-sector zero-δ pairs at "
            "N = 320, equal to We.sum() — Burde's law "
            "(q/p)_4 (p/q)_4 = ((ad-bc)/q) holds on 8734/8734 pairs, with the "
            "right-hand side non-constant (+1 4,994, -1 3,740)",
            "§6.2 calibration: the even-sector quartic-bit agreement count is "
            "identically the count of (ad-bc)/q = +1, both 4,994 of 8,734, so "
            "the joint's agreement structure at the quartic layer IS Burde's "
            "right-hand side; marginals 0.3401 and 0.3295 sit near the "
            "skeleton's 1/3, so the departure is in the joint, not the marginals",
            "BOUNDARY (registered as a limit, not a result): the law does NOT "
            "explain why (ad-bc)/q = +1 in 4,994 of 8,734 pairs, does NOT "
            "explain the ordered-joint asymmetry since it is symmetric in p "
            "and q, and does NOT constrain the odd hub-cofactor edges carrying "
            "σ_x — the all-QNR gate makes all 4 of them odd, where the quartic "
            "symbol is undefined; it reaches only cofactor-internal even "
            "edges, present in 63 of 64 parity patterns",
            "the four displayed forms (ad±bc, ac±bd)/q are equivalent on hard "
            "primes, which are all 1 mod 8: agreement across them is one "
            "identity tested four times, not four independent confirmations",
        ],
    },
    # The exact maximal-pairwise evaluation: the same conditioning with the
    # measured universe (3,3) joints injected, computed as an exact rational
    # by tensor-network contraction rather than sampled. It supersedes the
    # Monte-Carlo pool as the source of §6.2's maximal-pairwise statement; the
    # pool remains registered as the sampling it corrects.
    "maxpair_exact": {
        "command": ["python3", "skeleton_exact/maxpair_exact.py"],
        "parameters": {
            "R_maxpair_exact": "28345526604025309972212577/"
                               "106403745905832904560284283",
            "R_decimal": 0.2663959,
            "R_per_hub": [0.266375, 0.2664, 0.266409, 0.2664],
            # the pooling itself, exactly: the published rational must be the
            # sum of these numerators over the sum of these denominators
            "hub_num_cell": [
                ["793579310981401918655295144",
                 "2979178828758837096066728720"],
                ["793688214923654921912609040",
                 "2979307934294575503038954792"],
                ["793729892510340708017355488",
                 "2979370227836382531447744680"],
                ["793701561235437168302548952",
                 "2979362550563490180198411504"],
            ],
            "movement_pp": -0.0033,
            "gap_fraction": 0.002,
            "R_symmetrized": "1058377805268200408975721387/"
                             "3972832326551851183042320130",
            "symmetrized_movement_pp": -0.0026,
            "validation_uniform": "1123/4215",
            "uniform_hubs_identical": True,
            "joints_measured_at_N": 320,
            "moduli_bits": 18, "n_moduli": 7,
            "live_parity_graphs_per_hub": 64,
        },
        "seeds": [],
        "sources": ["../../skeleton_exact/maxpair_exact.py",
                    "../../skeleton_exact/test_maxpair_exact.py"],
        "inputs": [],
        "outputs": ["../../skeleton_exact/_maxpair_exact.json"],
        "claims": [
            "§6.2 exact maximal-pairwise rate R(3,3,3,4) = 0.2663959, pooled "
            "over the four depth-3 hubs as the census rate is — injecting the "
            "measured universe (3,3) joints moves the modelled rate only "
            "-0.0033 pp from the independent-digit constant 1123/4215, i.e. "
            "0.2% of the distance to the observed 0.2498, so the pair-level "
            "law is consequence-free for this observable",
            "§6.2 exact per-hub rates 0.266375, 0.266400, 0.266409, 0.266400 "
            "— a spread of 3.4e-5, against the Monte-Carlo pool's apparent "
            "0.0123 at ~0.009 sampling error per hub",
            "§6.2 symmetrized-joint sensitivity R(3,3,3,4) = 0.2664038 "
            "(-0.0026 pp): removing the joint's orientation-antisymmetric "
            "component moves the observable no further than the measured "
            "joint does. Not a decomposition — symmetrizing also averages the "
            "endpoint marginals and the rate is nonlinear in the joint",
            "§6.2 machinery validation: the same tensor network with uniform "
            "digits reproduces exact_dp's constant 1123/4215, and uniform "
            "digits produce four identical hubs (the positive control on the "
            "pooling that a symmetric-input validation alone cannot supply)",
        ],
    },
    # The exact engine supersedes both pools as the source of the constants;
    # the pools above remain registered as its independent validation.
    # Paths are relative to research/ (the engine lives at the repo root).
    "skeleton_exact": {
        "command": ["python3", "skeleton_exact/exact_dp.py"],
        "parameters": {
            "R_3333": "1373/5300",
            "R_3334": "1123/4215",
            "flatness_gap": "32941/4467900",
            "labeled_structures": 5445769,
            "s5_orbits": 45580,
            "s4_marked_orbits": 227200,
            "s5_orbits_realizable_A": 1833,
            "s4_orbits_realizable_B": 9013,
        },
        "seeds": [],
        "sources": ["../../skeleton_exact/exact_dp.py",
                    "../../skeleton_exact/test_exact_dp.py"],
        "inputs": [],
        "outputs": ["../../skeleton_exact/_exact_results.json",
                    "../../skeleton_exact/_per_graph.npz",
                    "../../skeleton_exact/_support.npz"],
        "claims": [
            "§6.2 exact skeleton constants R(3,3,3,3) = 1373/5300 and "
            "R(3,3,3,4) = 1123/4215 (Question 6.2.B′, resolved)",
            "§6.2 depth-flatness exactly false: +32941/4467900 = +0.7373 pp",
            "§6.2 Question 6.2.G conditioned support: 5,445,769 labeled "
            "structures; 45,580 S5 orbits; 1,833 / 9,013 parity-realizable",
        ],
    },
    # Finite adversarial guardrails for the realization theorem.  This is not
    # a computational proof of the number-field statements: it independently
    # checks the affine commutator, exact-slice count, row-gauge action and
    # Kummer-coordinate convention, and supplies the numerical density check
    # quoted in the companion paper.
    "realization_theorem": {
        "command": ["python3",
                    "barker_k6_bundle/research/realization_checks.py"],
        "parameters": {
            "prime_bound_exclusive": 20_000_000,
            "prime_count": 1_270_607,
            "hard_count_p_1_mod_4": 53_008,
            "depth_2_count": 0,
            "depth_3_count": 39_711,
            "depth_4_count": 9_939,
            "depth_5_count": 2_536,
            "depth_6_count": 619,
            "depth_7_count": 156,
            "affine_depths_passed": [2, 3, 4, 5, 6],
            "slice_count_cases": 20,
            "coordinate_pair_checks": 56,
            "all_checks_passed": True,
        },
        "seeds": [],
        "sources": ["realization_checks.py",
                    "../../tests/test_realization_checks.py"],
        "inputs": [],
        "outputs": ["_realization_checks.json"],
        "claims": [
            "Companion realization paper, finite guardrail only: affine "
            "commutator and derived-subgroup identities through depths 2..6, "
            "20 exact Frobenius-slice counts, and 56 non-vacuous Kummer/chi "
            "coordinate checks. These falsify finite algebra or convention "
            "errors but do not replace the number-field proof",
            "Companion realization paper, numerical validation of Proposition "
            "B below 20,000,000: 1,270,607 primes, 53,008 primes in the "
            "p == 1 (mod 4), ord_p(2) odd family, no exact-depth-2 member, "
            "and depth-3..7 counts 39,711 / 9,939 / 2,536 / 619 / 156",
        ],
    },
}

# Cross-check `skeleton_exact/_exact_results.json` against the registered
# fractions, so a regenerated engine result that drifts from the manuscript's
# numbers fails provenance by name rather than only by hash.
EXACT_RESULTS_KEYS = {
    "R_3333": ("R_A_3333", "fraction"),
    "R_3334": ("R_B_3334", "fraction"),
}

# The Rédei branch-pruning result. Registry keys are flat, the emitted artifact
# is nested, so these are dotted paths. The gate covers the validation outcomes
# (solution-independence and S₃-symmetry) as well as the counts, because a
# symbol that failed those would not be a Rédei symbol and the negative result
# would not follow from it.
REDEI_RESULTS_KEYS = {
    "all_QR_triangles": "universe.all_QR_triangles",
    "solution_independent": "symbol_validation.solution_independent",
    "s3_symmetric": "symbol_validation.s3_symmetric",
    "distribution": "distribution",
    "invariant_classes": "determination.invariant_classes",
    "testable_classes": "determination.testable_classes",
    "mixed_sign_classes": "determination.mixed_sign_classes",
    "counterexample_minus": "counterexample.minus",
    "counterexample_plus": "counterexample.plus",
    "cofactor_patterns_with_all_QR_triangle":
        "applicability.patterns_with_at_least_one",
    "hub_cofactor_triples_applicable":
        "applicability.hub_cofactor_triples_applicable",
}


# Burde: the gate pins the population identity (so the harness cannot silently
# drift off the joint the manuscript measures), the identity and its
# non-vacuity, the agreement/RHS coincidence, and BOTH negative controls — a
# control that stopped discriminating would make the identity check toothless.
BURDE_RESULTS_KEYS = {
    "even_sector_pairs": "population.even_sector_pairs",
    "pairs_after_zero_delta": "population.pairs_after_zero_delta",
    "equals_We_sum": "population.equals_We_sum",
    "identity_holds": "identity.holds",
    "identity_of": "identity.of",
    "four_forms_equivalent": "identity.four_forms_equivalent",
    "rhs_split": "rhs_split",
    "marginals": "marginals",
    "agreement_count": "agreement_count",
    "sign_choice_invariant": "sign_choice_invariant",
    "cofactor_patterns_with_even_edge":
        "applicability.cofactor_patterns_with_even_edge",
    "hub_cofactor_edges_applicable":
        "applicability.hub_cofactor_edges_applicable",
    "negative_control_scrambled": "negative_controls.scrambled_pairing",
    "negative_control_perturbed": "negative_controls.perturbed_rhs",
}


def dig(d, path):
    """Follow a dotted path into nested dicts; None if any step is missing."""
    for part in path.split("."):
        if not isinstance(d, dict) or part not in d:
            return None
        d = d[part]
    return d


# Same idea for the exact maximal-pairwise result. The gate covers the pooled
# rational, the four per-hub rates, the symmetrized-joint sensitivity and both
# validation outcomes: a released version pooled the hubs by multiplying one of
# them by four, which the uniform-digit validation cannot catch because uniform
# joints are symmetric. Gating the per-hub vector and the four-identical-hubs
# control makes that failure mode fail provenance by name.
MAXPAIR_RESULTS_KEYS = {
    "R_maxpair_exact": "R_maxpair_exact",
    "R_per_hub": "R_per_hub",
    "hub_num_cell": "hub_num_cell",
    "R_symmetrized": "R_symmetrized",
    "validation_uniform": "validation_uniform",
    "uniform_hubs_identical": "uniform_hubs_identical",
}


# The realization harness is intentionally gated at the decomposition level:
# an all-green aggregate would not catch the wrong affine coefficient or a
# coordinate convention that silently became vacuous.
REALIZATION_RESULTS_KEYS = {
    "prime_bound_exclusive": "density_slices.prime_bound_exclusive",
    "prime_count": "density_slices.prime_count",
    "hard_count_p_1_mod_4": "density_slices.hard_count_p_1_mod_4",
    "depth_2_count": "density_slices.by_depth.2.count",
    "depth_3_count": "density_slices.by_depth.3.count",
    "depth_4_count": "density_slices.by_depth.4.count",
    "depth_5_count": "density_slices.by_depth.5.count",
    "depth_6_count": "density_slices.by_depth.6.count",
    "depth_7_count": "density_slices.by_depth.7.count",
    "affine_depths_passed": "affine_depths_passed",
    "slice_count_cases": "slice_count_cases",
    "coordinate_pair_checks": "coordinate_pair_checks",
    "all_checks_passed": "all_checks_passed",
}


# ---------------------------------------------------------------------------
# Hashing
# ---------------------------------------------------------------------------

def sha256_file(path: str) -> str | None:
    if not os.path.exists(path):
        return None
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def expand(templates, params, seeds):
    """Expand {N}/{seed} templates over the registered parameter values."""
    out = []
    for t in templates:
        if "{N}" in t:
            out.extend(t.replace("{N}", str(n)) for n in params.get("N", []))
        elif "{seed}" in t:
            out.extend(t.replace("{seed}", str(s)) for s in seeds)
        else:
            out.append(t)
    return out


def git(*args) -> str:
    try:
        return subprocess.run(["git", "-C", REPO, *args], capture_output=True,
                              text=True, check=True).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""


def tracked_dirty() -> bool:
    """Tracked-file drift outside _manifest/.

    Untracked files are generated artifacts and are hashed by the experiment
    manifests; _manifest/ itself is excluded because building manifests must
    not count as dirtying the snapshot they describe."""
    for line in git("status", "--porcelain").splitlines():
        if not line.strip() or line.startswith("??"):
            continue
        if "research/_manifest/" in line:
            continue
        return True
    return False


def environment() -> dict:
    """Observed environment. Recorded for provenance; NOT gated on equality —
    see REQUIREMENTS and check_environment()."""
    try:
        import numpy
        numpy_version = numpy.__version__
    except ImportError:
        numpy_version = None
    return {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "machine": platform.machine(),
        "numpy": numpy_version,
    }


# Capability floors, not the exact build that happened to record the manifest.
# Pinning an exact patch version would red-gate every machine that is not the
# author's; what the results actually depend on is the documented Python floor
# and a NumPy major line with no breaking API change.
REQUIREMENTS = {
    "python_min": (3, 9),
    "numpy_min": (1, 24),      # np.random.default_rng + the integer dtypes used
}


def _ver_tuple(s):
    out = []
    for part in str(s).split(".")[:2]:
        digits = "".join(c for c in part if c.isdigit())
        out.append(int(digits) if digits else 0)
    return tuple(out) or (0, 0)


def check_environment(recorded: dict) -> list[str]:
    """Compatibility problems with the recorded environment, as messages."""
    problems = []
    py = sys.version_info[:2]
    if py < REQUIREMENTS["python_min"]:
        problems.append(f"python {py[0]}.{py[1]} below floor "
                        f"{'.'.join(map(str, REQUIREMENTS['python_min']))}")
    try:
        import numpy
    except ImportError:
        return problems + ["numpy not importable"]
    now = _ver_tuple(numpy.__version__)
    if now < REQUIREMENTS["numpy_min"]:
        problems.append(f"numpy {numpy.__version__} below floor "
                        f"{'.'.join(map(str, REQUIREMENTS['numpy_min']))}")
    rec = recorded.get("numpy")
    if rec and _ver_tuple(rec)[0] != now[0]:
        problems.append(f"numpy major line {now[0]} != recorded {_ver_tuple(rec)[0]} "
                        f"(observed {numpy.__version__}, recorded {rec}); a major "
                        f"bump is untested against these artifacts")
    return problems


# The intended release inventory: every file whose content the paper's claims
# depend on. Hashing this is what "pins the repository tree" means here — a
# dirty-state boolean does not, since arbitrary edits leave it unchanged.
# Large generated data artifacts are deliberately absent: they are hashed by
# the per-experiment manifests instead.
RELEASE_INVENTORY = [
    "README.md",
    "verify_all.sh",
    # Public novelty and release claims live here too, so citation drift must
    # fail the gate exactly as manuscript drift does. RELEASE_NOTES carries the
    # per-version result list and the correction record, which is the same kind
    # of public claim.
    "CITATION.cff",
    "RELEASE_NOTES.md",
    "barker_k6_bundle/README.md",
    "barker_k6_bundle/manuscript.md",
    "barker_k6_bundle/manuscript.pdf",
    # The companion theorem paper and its explicit publication boundary.
    "barker_k6_bundle/realization/*.md",
    "barker_k6_bundle/realization/*.tex",
    "barker_k6_bundle/realization/*.pdf",
    # Claim-bearing prose: the manifests call results "preregistration-locked"
    # and the READMEs point at RESEARCH.md for execution order, so both must be
    # pinned — otherwise the document a claim rests on can change while the
    # gate stays green.
    "barker_k6_bundle/docs/*.md",
    "barker_k6_bundle/research/RESEARCH.md",
    # Root working documents: they carry claim language about the same results
    # and are tracked, so they must be pinned too — otherwise withdrawn
    # statistics can survive there without failing the gate.
    "docs/*.md",
    "barker_k6_bundle/pdf_math_filter.lua",
    "barker_k6_bundle/verify_minimal_k6.py",
    "barker_k6_bundle/audit_verify.py",
    "barker_k6_bundle/audit_cleanroom.py",
    "barker_k6_bundle/remark_4_5_1_dn_disconnection.py",
    "barker_k6_bundle/code/barker/*.py",
    "barker_k6_bundle/research/*.py",
    "skeleton_exact/*.py",
    "tests/*.py",
    "figures/*.png",
]


def inventory_record() -> dict:
    """Per-file hashes of the release inventory plus one combined tree hash."""
    import glob
    files = {}
    for pattern in RELEASE_INVENTORY:
        for path in sorted(glob.glob(os.path.join(REPO, pattern))):
            if os.path.isfile(path):
                files[os.path.relpath(path, REPO)] = sha256_file(path)
    combined = sha256_text("\n".join(f"{k} {v}" for k, v in sorted(files.items())))
    return {"n_files": len(files), "files": files, "tree_sha256": combined}


def tracked_files() -> set:
    """Paths in the git index, repo-relative. Empty set if git is unavailable."""
    out = git("ls-files")
    return {line.strip() for line in out.splitlines() if line.strip()}


def manifest_referenced_paths(names) -> set:
    """Every repo-relative path the manifests depend on: the release inventory
    plus each experiment's sources, inputs and outputs."""
    paths = set(inventory_record()["files"])
    for name in names:
        spec = REGISTRY[name]
        params, seeds = spec["parameters"], spec["seeds"]
        for kind in ("sources", "inputs", "outputs"):
            for rel in expand(spec[kind], params, seeds):
                abs_p = os.path.normpath(os.path.join(HERE, rel))
                paths.add(os.path.relpath(abs_p, REPO))
    return paths


def universe_record() -> dict:
    """Pin the ordered prime universe the whole paper is defined over."""
    sys.path.insert(0, os.path.join(REPO, "barker_k6_bundle", "code"))
    from barker.sweep import find_hard_primes
    primes = [d["prime"] for d in find_hard_primes(100000)][:280]
    return {
        "definition": "hard primes p ≡ 1 (mod 4) with ord_p(2) odd, ascending",
        "n_pinned": len(primes),
        "first_8": primes[:8],
        "p_80": primes[79],
        "p_160": primes[159],
        "p_280": primes[279],
        "ordered_universe_sha256": sha256_text(",".join(map(str, primes))),
    }


# ---------------------------------------------------------------------------
# Build / verify
# ---------------------------------------------------------------------------

def build_experiment(name: str) -> dict:
    spec = REGISTRY[name]
    params, seeds = spec["parameters"], spec["seeds"]
    sources = {p: sha256_file(os.path.join(HERE, p)) for p in spec["sources"]}
    inputs = {p: sha256_file(os.path.join(HERE, p))
              for p in expand(spec["inputs"], params, seeds)}
    outputs = {p: sha256_file(os.path.join(HERE, p))
               for p in expand(spec["outputs"], params, seeds)}
    return {
        "name": name,
        "schema_version": SCHEMA_VERSION,
        "command": spec["command"],
        "parameters": params,
        "seeds": seeds,
        "claims": spec["claims"],
        "sources": sources,
        "inputs": inputs,
        "outputs": outputs,
        "commit": git("rev-parse", "HEAD"),
        "tree_dirty": tracked_dirty(),
        "environment": environment(),
    }


def build(names) -> int:
    os.makedirs(MANIFEST_DIR, exist_ok=True)
    written = {}
    for name in names:
        rec = build_experiment(name)
        path = os.path.join(MANIFEST_DIR, f"{name}.json")
        with open(path, "w") as f:
            json.dump(rec, f, indent=2, sort_keys=True)
        missing = [p for p, h in {**rec["sources"], **rec["inputs"],
                                  **rec["outputs"]}.items() if h is None]
        written[name] = sha256_file(path)
        flag = f"  ({len(missing)} artifact(s) absent)" if missing else ""
        print(f"  wrote _manifest/{name}.json{flag}")
        for p in missing:
            print(f"      absent: {p}")

    release = {
        "schema_version": SCHEMA_VERSION,
        "commit": git("rev-parse", "HEAD"),
        "tree_dirty": tracked_dirty(),
        "environment": environment(),
        "requirements": {k: list(v) if isinstance(v, tuple) else v
                         for k, v in REQUIREMENTS.items()},
        "inventory": inventory_record(),
        "universe": universe_record(),
        "experiments": written,
    }
    with open(os.path.join(MANIFEST_DIR, "release.json"), "w") as f:
        json.dump(release, f, indent=2, sort_keys=True)
    print("  wrote _manifest/release.json")
    if release["tree_dirty"]:
        print("  NOTE: working tree is dirty; this manifest pins uncommitted state.")
    return 0


def verify(names) -> int:
    failures = []
    for name in names:
        path = os.path.join(MANIFEST_DIR, f"{name}.json")
        if not os.path.exists(path):
            failures.append((name, "MISSING MANIFEST", path))
            print(f"[MISSING] {name}: no manifest recorded")
            continue
        with open(path) as f:
            rec = json.load(f)
        bad = 0
        for kind in ("sources", "inputs", "outputs"):
            for rel, recorded in rec[kind].items():
                actual = sha256_file(os.path.join(HERE, rel))
                if recorded is None and actual is None:
                    continue
                if actual is None:
                    failures.append((name, "MISSING", rel))
                    print(f"[MISSING] {name}/{kind}: {rel}")
                    bad += 1
                elif recorded is None:
                    failures.append((name, "UNRECORDED", rel))
                    print(f"[UNRECORDED] {name}/{kind}: {rel} exists but was "
                          f"not recorded")
                    bad += 1
                elif actual != recorded:
                    failures.append((name, "STALE", rel))
                    print(f"[STALE] {name}/{kind}: {rel}")
                    bad += 1
        if bad == 0:
            print(f"[OK] {name}: {len(rec['sources'])} source(s), "
                  f"{len(rec['inputs'])} input(s), {len(rec['outputs'])} output(s)")

    # skeleton_exact: assert the emitted fractions against the registered ones,
    # so the release gate catches a numeric drift, not only a hash change.
    exact_json = os.path.join(HERE, "../../skeleton_exact/_exact_results.json")
    if "skeleton_exact" in names and os.path.exists(exact_json):
        with open(exact_json) as f:
            res = json.load(f)
        mismatched = False
        for param, (key, sub) in EXACT_RESULTS_KEYS.items():
            want = REGISTRY["skeleton_exact"]["parameters"][param]
            got = res.get(key, {}).get(sub)
            if got != want:
                mismatched = True
                failures.append(("skeleton_exact", "CLAIM MISMATCH", param))
                print(f"[CLAIM MISMATCH] skeleton_exact: {param} registered "
                      f"{want}, emitted {got}")
        if not mismatched:
            print("[OK] skeleton_exact: emitted fractions match the "
                  "registered constants")

    mp_json = os.path.join(HERE, "../../skeleton_exact/_maxpair_exact.json")
    if "maxpair_exact" in names and os.path.exists(mp_json):
        with open(mp_json) as f:
            res = json.load(f)
        mism = [k for k, key in MAXPAIR_RESULTS_KEYS.items()
                if res.get(key) != REGISTRY["maxpair_exact"]["parameters"][k]]
        for k in mism:
            failures.append(("maxpair_exact", "CLAIM MISMATCH", k))
            print(f"[CLAIM MISMATCH] maxpair_exact: {k} registered "
                  f"{REGISTRY['maxpair_exact']['parameters'][k]}, emitted "
                  f"{res.get(MAXPAIR_RESULTS_KEYS[k])}")
        if not mism:
            print("[OK] maxpair_exact: emitted rational, exact per-hub "
                  "decomposition, symmetrized sensitivity and both validation "
                  "outcomes match the registered values")

    rb_json = os.path.join(HERE, "_redei_bridge.json")
    if "redei_bridge" in names and os.path.exists(rb_json):
        with open(rb_json) as f:
            res = json.load(f)
        reg = REGISTRY["redei_bridge"]["parameters"]
        mism = [k for k, path in REDEI_RESULTS_KEYS.items()
                if dig(res, path) != reg[k]]
        for k in mism:
            failures.append(("redei_bridge", "CLAIM MISMATCH", k))
            print(f"[CLAIM MISMATCH] redei_bridge: {k} registered {reg[k]}, "
                  f"emitted {dig(res, REDEI_RESULTS_KEYS[k])}")
        if not mism:
            print("[OK] redei_bridge: symbol validation, mixed-sign class "
                  "counts, counterexample and applicability counts match the "
                  "registered values")

    bp_json = os.path.join(HERE, "_burde_pair_law.json")
    if "burde_pair_law" in names and os.path.exists(bp_json):
        with open(bp_json) as f:
            res = json.load(f)
        reg = REGISTRY["burde_pair_law"]["parameters"]
        mism = [k for k, path in BURDE_RESULTS_KEYS.items()
                if dig(res, path) != reg[k]]
        for k in mism:
            failures.append(("burde_pair_law", "CLAIM MISMATCH", k))
            print(f"[CLAIM MISMATCH] burde_pair_law: {k} registered {reg[k]}, "
                  f"emitted {dig(res, BURDE_RESULTS_KEYS[k])}")
        if not mism:
            print("[OK] burde_pair_law: population identity, the reciprocity "
                  "identity, its non-vacuity, the agreement/RHS coincidence "
                  "and both negative controls match the registered values")

    rt_json = os.path.join(HERE, "_realization_checks.json")
    if "realization_theorem" in names and os.path.exists(rt_json):
        with open(rt_json) as f:
            res = json.load(f)
        reg = REGISTRY["realization_theorem"]["parameters"]
        mism = [k for k, path in REALIZATION_RESULTS_KEYS.items()
                if dig(res, path) != reg[k]]
        for k in mism:
            failures.append(("realization_theorem", "CLAIM MISMATCH", k))
            print(f"[CLAIM MISMATCH] realization_theorem: {k} registered "
                  f"{reg[k]}, emitted {dig(res, REALIZATION_RESULTS_KEYS[k])}")
        if not mism:
            print("[OK] realization_theorem: affine decomposition, exact "
                  "slice counts, coordinate checks and finite density slices "
                  "match the registered values")

    rel_path = os.path.join(MANIFEST_DIR, "release.json")
    if not os.path.exists(rel_path):
        failures.append(("release", "MISSING MANIFEST", rel_path))
        print("[MISSING] release manifest")
    else:
        with open(rel_path) as f:
            release = json.load(f)
        now = universe_record()
        if now["ordered_universe_sha256"] != release["universe"]["ordered_universe_sha256"]:
            failures.append(("release", "STALE", "ordered universe"))
            print("[STALE] release: the ordered prime universe no longer matches")
        else:
            print("[OK] release: ordered universe matches")

        # Enforce the snapshot release.json claims to pin — commit, dirty
        # state, environment, experiment set, per-manifest hashes — instead of
        # merely recording them.
        head = git("rev-parse", "HEAD")
        if head and release.get("commit") and head != release["commit"]:
            # Tolerate exactly one kind of drift: commits that touch only the
            # manifests themselves (the provenance commit that follows a
            # build). Anything else is a stale snapshot.
            drift = [f for f in git("diff", "--name-only",
                                    f"{release['commit']}..HEAD").splitlines()
                     if f.strip()]
            if drift and all("research/_manifest/" in f for f in drift):
                print("[OK] release: HEAD differs from the recorded commit "
                      "only by manifest files")
            else:
                failures.append(("release", "STALE", "commit"))
                print(f"[STALE] release: HEAD {head[:12]} != recorded "
                      f"{release['commit'][:12]}")
        # Release inventory: the actual tree pin. Any edit to the manuscript,
        # PDF, READMEs, scripts, tests or figures changes a per-file hash and
        # is named here; the dirty-state boolean cannot see such edits.
        inv_rec = release.get("inventory")
        if not inv_rec:
            failures.append(("release", "MISSING", "inventory"))
            print("[MISSING] release: no inventory recorded — rebuild manifests")
        else:
            inv_now = inventory_record()
            if inv_now["tree_sha256"] != inv_rec["tree_sha256"]:
                rec_f, now_f = inv_rec["files"], inv_now["files"]
                changed = sorted(p for p in set(rec_f) & set(now_f)
                                 if rec_f[p] != now_f[p])
                added = sorted(set(now_f) - set(rec_f))
                removed = sorted(set(rec_f) - set(now_f))
                failures.append(("release", "STALE", "release inventory"))
                print(f"[STALE] release: inventory tree hash differs "
                      f"({len(changed)} changed, {len(added)} added, "
                      f"{len(removed)} removed)")
                for p in (changed + added + removed)[:12]:
                    kind = ("changed" if p in changed else
                            "added" if p in added else "removed")
                    print(f"           {kind}: {p}")
            else:
                print(f"[OK] release: inventory tree hash matches "
                      f"({inv_now['n_files']} files)")
        # Clean-checkout reproducibility: hashing files on this filesystem
        # proves nothing about a fresh clone unless those files are in the
        # index. Every manifest-referenced path must be git-tracked.
        tracked = tracked_files()
        if not tracked:
            failures.append(("release", "UNVERIFIABLE", "git index unavailable"))
            print("[UNVERIFIABLE] release: cannot read the git index, so "
                  "clean-checkout reproducibility is unproven")
        else:
            referenced = manifest_referenced_paths(names)
            untracked = sorted(p for p in referenced if p not in tracked)
            if untracked:
                failures.append(("release", "UNTRACKED", f"{len(untracked)} paths"))
                print(f"[UNTRACKED] release: {len(untracked)} of "
                      f"{len(referenced)} manifest-referenced paths are not in "
                      f"the git index — a fresh clone would not reproduce this "
                      f"result")
                for p_ in untracked[:12]:
                    print(f"           untracked: {p_}")
                if len(untracked) > 12:
                    print(f"           … and {len(untracked) - 12} more")
            else:
                print(f"[OK] release: all {len(referenced)} manifest-referenced "
                      f"paths are git-tracked")

        env_problems = check_environment(release.get("environment", {}))
        if env_problems:
            failures.append(("release", "INCOMPATIBLE", "environment"))
            for msg in env_problems:
                print(f"[INCOMPATIBLE] release/environment: {msg}")
        rec_exps = set(release.get("experiments", {}))
        if rec_exps != set(REGISTRY):
            failures.append(("release", "STALE", "experiment set"))
            print(f"[STALE] release: registered experiments "
                  f"{sorted(REGISTRY)} != recorded {sorted(rec_exps)}")
        else:
            for name, rec_hash in release["experiments"].items():
                actual = sha256_file(os.path.join(MANIFEST_DIR, f"{name}.json"))
                if actual != rec_hash:
                    failures.append(("release", "STALE", f"manifest {name}.json"))
                    print(f"[STALE] release: _manifest/{name}.json hash "
                          f"changed since release.json was built")
        if not any(f[0] == "release" for f in failures):
            print("[OK] release: commit, inventory, environment capability, "
                  "experiment set and manifest hashes all match")

    print()
    if failures:
        print(f"PROVENANCE FAILED — {len(failures)} problem(s).")
        print("Missing or stale provenance is a release blocker: the claims listed")
        print("in the affected manifests are not currently reproducible.")
        return 1
    print("PROVENANCE OK — every registered artifact matches its manifest.")
    return 0


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else "verify"
    names = sys.argv[2:] or sorted(REGISTRY)
    unknown = [n for n in names if n not in REGISTRY]
    if unknown:
        print(f"unknown experiment(s): {', '.join(unknown)}")
        print(f"registered: {', '.join(sorted(REGISTRY))}")
        return 2
    if mode == "build":
        return build(names)
    if mode == "verify":
        return verify(names)
    if mode == "list":
        for n in sorted(REGISTRY):
            print(f"{n}")
            for c in REGISTRY[n]["claims"]:
                print(f"    supplies: {c}")
        return 0
    print(f"usage: {os.path.basename(__file__)} [build|verify|list] [name ...]")
    return 2


if __name__ == "__main__":
    sys.exit(main())
