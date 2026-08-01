# research/ — census experiments and companion-theorem guardrails

Scripts here support the census paper and its registered experiments. The
`realization_checks.py` harness supplies finite adversarial checks for the
companion theorem in `../realization/`; it does not replace that paper's proof.
The complete registered closure is verified by `verify_all.sh` at the
repository root.

Shared helpers (`delta_x`, `chi_sum`, `classify`, `build_labeled_graph`,
`two_fwl_signature`) live in `_common.py`. The class label format for interior-B
configurations is `B(δ=X)`, matching the JSON caches written by `profile_analysis.py`.

## Execution order

1. **`profile_analysis.py`** — first run builds `_enumeration_cache.json` (the
   421 minimal coverings at k = 3..6 over the first 80 hard primes; ~50 min on
   first run, instant thereafter from cache).
2. **Any of the refinement-check scripts** — read the cache and report on the
   refinement ladder:
   - `v_graph_check.py`
   - `pair_cancellation_check.py`
   - `compact_invariants_check.py`
   - `wl_refinement.py`
   - `wl2_v2.py`
3. **Census-scoped discrimination analysis** — also read-only on the cache:
   - `discrimination_depth.py` — exhaustive census of the marginal discrimination
     contribution at each level of the ordered ladder (δ-profile, V-graph, I_6,
     1-WL, 2-FWL) on cross-class pairs in the 421-configuration enumeration.
     Reports the discrimination-depth histogram λ(s, t). All numbers are
     exhaustive counts on the enumeration; the distribution shape is **not**
     claimed to persist outside the enumerated parameters.
   - `i6_vs_1wl.py` — pairwise partition-agreement matrix of I_6 and 1-WL.
     Establishes that 1-WL **strictly refines** I_6 on this graph class
     (89 same-I_6 / diff-1-WL pairs, 0 diff-I_6 / same-1-WL) and clarifies that the empty
     marginal contribution at λ=4 is a co-occurrence pattern across the lower
     levels of the ladder, not a structural containment of 1-WL by I_6.
4. **Structural-baseline reproductions** — independent of the cache, both
   following the size-matched-random-subset pattern:
   - `substructure_baseline.py` (~30 s) — V-substructure permutation test of
     Remark 5.6. Compares the 21 featured primes' internal V-density against
     5,000 random 21-subsets of the universe (seed = 42). Reports the empirical
     percentile (99.7) and swap-control densities. Backs §5.8.
   - `independence_validation.py` (~2 min) — empirical validation of the
     independence model underlying N_k. Compares per-subset N(S) against
     "any σ_x = 0" fractions on 200,000 random zero-δ k-subsets at k = 4, 5, 6
     (seed = 2026). Reports Wilson 95% CIs; at k = 5, 6 the CI encloses N_k,
     at k = 4 there is a small (≈1 pp, −3% relative) systematic offset
     characterised by `independence_diagnostic.py`. Backs §6.2 Defence (ii).
   - `independence_diagnostic.py` (~2 min) — characterisation of the k=4
     offset as the m=3 summand-count approximation effect at depth t=3.
     Computes the exact P(sum of m i.i.d. uniform-nonzero values mod 2^t = 0)
     by convolution; substitutes the corrected rate to give an exact_N_k that
     closes the all-depth-3 bin to ~0 residual. Confirms the offset is
     model-approximation, not target correlation. Documented in §7.6.
   - `per_depth_w2.py [N]` (~5 min at N=160, instant from cache) —
     per-depth conditional rate P(σ=0 | w=2) at k=5 zero-δ. Enumerates
     minimal coverings via a zero-δ-clique fast search (library's
     `search_minimal_covering_k` walks all C(N,k) and is too slow at
     N=160), then uses `_common.chi_sum` for per-target invariants.
     Reports the empirical rate per depth class against the closed-form
     iid-uniform-values null `(2^(t-1)-1)/(5·2^(t-1)-7)` and isolates
     the surviving arithmetic residue. Caches to `_per_depth_w2_cache_N<N>.json`.
5. **`audit_verify.py`** (in `barker_k6_bundle/`) — independent numerical
   audit of the main paper's claims.
6. **`audit_cleanroom.py`** (in `barker_k6_bundle/`) — clean-room
   reimplementation; the strongest independence check.

Steps 5 and 6 are the main-paper audit gates and should pass before and after
any change to `_common.py` or to the library modules under
`barker_k6_bundle/code/barker/`.

## Realization-theorem guardrail

- `realization_checks.py` — deterministic checks of the affine commutator and
  derived subgroup through depths 2--6, 20 exact Frobenius-slice counts,
  conjugacy as common row gauge, 56 non-vacuous implementation/Kummer
  coordinate identities, and the exact-depth prime counts below 20,000,000.
  It writes `_realization_checks.json` and is registered as
  `realization_theorem`. Its scope is falsification of finite algebra and
  conventions; the number-field argument in `../realization/realization_paper.tex`
  is the source of the theorem.

## k=7 robustness probes

- `k7_extension.py` — enumerates k=7 on the first 50 hard primes
  (~17 min, caches to `_k7_enumeration_cache.json`; 2 configs found, no
  multi-class profile).
- `k7_60primes.py` — same probe on the first 60 hard primes (~65 min,
  caches to `_k7_60primes_cache.json`; 8 configs, still no multi-class).

Both write their own caches and are skipped on subsequent runs. Robustness of
the 2-FWL classifier at k ≥ 7 is empirically open — see follow-on §1.6.

## Standalone diagnostic scripts

These do not depend on the enumeration cache and can be run in any order:

- `defect_signature.py`, `witness_complex.py`, `internal_witness_graph.py` —
  intuition probes on the known configurations.
- `null_control.py`, `_sanity_check.py` — null-model and validation checks.
- `delta_profile.py` — re-derives the {A1, A2, A3, B0, B1} census on the 13
  known minimal coverings; fast (<5 s).
- `wl2_refinement.py` — diagnostic 2-FWL run *without* membership edges
  (kept for historical comparison; the labelled-graph version in
  `wl2_v2.py` is the canonical one).
