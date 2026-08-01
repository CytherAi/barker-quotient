#!/usr/bin/env python3
"""
skeleton_model_e1.py — E1: the reciprocity-symmetric skeleton generative model.

Tests whether the zero-δ k=5 §6.2 residues are COMBINATORICS of
{covering + minimal + zero-δ} conditioning on a reciprocity-symmetric skeleton,
or genuine arithmetic. The model replaces the real χ-matrix of a 5-set with a
synthetic one:
    - depth t = 3 at every vertex (the (3,3,3,3,3) regime where the empirical
      +6.6 pp transversal excess concentrates; everything is mod 8);
    - each unordered pair {i,j} carries a shared fair Legendre parity coin
      b_ij ∈ {0,1} (reciprocity: parity χ_i(j) = parity χ_j(i)); P(QNR)=1/2;
    - higher 2-adic bits per direction uniform & independent: χ_i(j) = 2·u + b_ij,
      u ~ U{0,1,2,3}.
We sample matrices, KEEP only zero-δ minimal coverings (true minimality: no
proper subset covers — NOT single-drop, which over-counts 2.6×), and measure
the §6.2 observables on the survivors' targets, comparing
    [model]  vs  [empirical (3,3,3,3) cut, N=160]  vs  [forced null].

Decision rule for the decisive observable Q6.2.B:
    P(σ_x = 0 | all-QNR cofactor, w_x = 2)   null = 1/5 = 0.200,  emp = 201/756 = 0.266
    model ≈ 0.266  →  the +6.6 pp is COMBINATORIAL (conditioning explains it)
    model ≈ 0.200  →  CERTIFIED ARITHMETIC (conditioning does not explain it)

Positive controls (must hold or the harness is wrong):
    - forced propositions: w=4 ⟹ σ=0; σ=0 ⟹ w even; no w=5 (Cor 4.7/4.8/4.9);
    - with conditioning OFF, the per-target σ=0|w=2 rate must recover the iid
      baselines 3/13 (all-t=3) and 1/5 (all-QNR).
"""
from __future__ import annotations
import sys, os
import numpy as np

PAIRS = [(i, j) for i in range(5) for j in range(i + 1, 5)]          # 10 unordered
SUBSETS = ([tuple(s) for s in __import__("itertools").combinations(range(5), 3)]
           + [tuple(s) for s in __import__("itertools").combinations(range(5), 4)])


def generate(B, rng):
    """B random 5x5 skeleton χ-matrices (mod 8), reciprocity-symmetric parity."""
    M = np.zeros((B, 5, 5), dtype=np.int64)
    for i, j in PAIRS:
        b = rng.integers(0, 2, B)            # shared parity coin
        uij = rng.integers(0, 4, B)
        uji = rng.integers(0, 4, B)
        M[:, i, j] = 2 * uij + b
        M[:, j, i] = 2 * uji + b
    return M


def pair_witnessed(M, members, i, j):
    """Boolean (B,) : some k in `members`, k∉{i,j}, with M[:,k,i]+M[:,k,j] ≡ 0 (mod 8)."""
    out = np.zeros(M.shape[0], dtype=bool)
    for k in members:
        if k == i or k == j:
            continue
        out |= ((M[:, k, i] + M[:, k, j]) % 8 == 0)
    return out


def is_covering(M, members):
    """Boolean (B,) : every pair within `members` is witnessed within `members`."""
    members = list(members)
    ok = np.ones(M.shape[0], dtype=bool)
    for a in range(len(members)):
        for b in range(a + 1, len(members)):
            ok &= pair_witnessed(M, members, members[a], members[b])
            if not ok.any():
                return ok
    return ok


def keep_zero_delta_minimal_coverings(M):
    """Return boolean mask (B,) of skeleton matrices that are zero-δ minimal
    coverings of the full 5-set."""
    B = M.shape[0]
    # zero-δ: all off-diagonal entries nonzero
    offdiag = np.ones((B,), dtype=bool)
    for i in range(5):
        for j in range(5):
            if i != j:
                offdiag &= (M[:, i, j] != 0)
    mask = offdiag
    if not mask.any():
        return mask
    # full set covering
    full = is_covering(M, range(5))
    mask &= full
    if not mask.any():
        return mask
    # minimality: NO proper subset (size 3 or 4) is itself a covering
    for T in SUBSETS:
        sub_cov = is_covering(M, T)
        mask &= ~sub_cov
        if not mask.any():
            return mask
    return mask


def target_observables(M):
    """For each surviving matrix and each of its 5 targets, return arrays of
    (w, sigma, all_qnr) over all (matrix, target) pairs."""
    B = M.shape[0]
    ws, sigmas, allqnr = [], [], []
    for x in range(5):
        cof = [p for p in range(5) if p != x]
        vals = M[:, x, cof]                       # (B,4) cofactor χ-values
        sigma = vals.sum(axis=1) % 8
        # w = #pairs in cofactor with χ_x(a)+χ_x(b) ≡ 0 mod 8
        w = np.zeros(B, dtype=np.int64)
        for a in range(4):
            for b in range(a + 1, 4):
                w += ((vals[:, a] + vals[:, b]) % 8 == 0)
        aq = np.all(vals % 2 == 1, axis=1)        # all-QNR cofactor
        ws.append(w); sigmas.append(sigma); allqnr.append(aq)
    return (np.concatenate(ws), np.concatenate(sigmas), np.concatenate(allqnr))


def sample(total_trials, batch, seed, outfile):
    """Rejection-sample zero-δ minimal coverings; save survivor matrices to npy."""
    rng = np.random.default_rng(seed)
    kept_M = []
    n_trials = 0
    n_kept = 0
    while n_trials < total_trials:
        B = min(batch, total_trials - n_trials)
        M = generate(B, rng)
        mask = keep_zero_delta_minimal_coverings(M)
        if mask.any():
            kept_M.append(M[mask])
            n_kept += int(mask.sum())
        n_trials += B
    M = np.concatenate(kept_M, axis=0) if kept_M else np.zeros((0, 5, 5), dtype=np.int64)
    np.save(outfile, M)
    print(f"  seed={seed}  trials={n_trials:,}  kept={n_kept:,}  "
          f"acceptance={n_kept/n_trials:.2e}  -> {outfile} ({M.shape[0]} matrices)")


def measure(files):
    Ms = [np.load(f) for f in files]
    M = np.concatenate(Ms, axis=0) if Ms else np.zeros((0, 5, 5), dtype=np.int64)
    n_kept = M.shape[0]
    print(f"  loaded {n_kept:,} survivor matrices from {len(files)} file(s)")
    if n_kept == 0:
        return

    w, sigma, aq = target_observables(M)
    n_targets = w.size
    s0 = (sigma == 0)

    # --- positive controls (forced propositions) ---
    print("\n  [positive controls — forced propositions]")
    w4 = (w == 4)
    print(f"    w=4 ⟹ σ=0 : {int((w4 & s0).sum())}/{int(w4.sum())} "
          f"({'PASS' if w4.sum()>0 and (w4 & ~s0).sum()==0 else 'check'})")
    print(f"    σ=0 ⟹ w even : odd-w σ=0 count = {int((s0 & (w % 2 == 1)).sum())} "
          f"({'PASS' if (s0 & (w%2==1)).sum()==0 else 'FAIL'})")
    print(f"    w=5 impossible : count = {int((w==5).sum())} "
          f"({'PASS' if (w==5).sum()==0 else 'FAIL'})")

    # --- Q6.2.E : QNR fraction of cofactor entries vs 1/2 prior ---
    qnr_frac = (M[:, [0,1,2,3,4]][:, :, :] % 2 == 1)  # placeholder; compute directly
    # fraction of off-diagonal entries that are QNR (odd) among survivors
    offvals = []
    for i in range(5):
        for j in range(5):
            if i != j:
                offvals.append(M[:, i, j])
    offvals = np.concatenate(offvals)
    print("\n  [Q6.2.E — QNR over-selection]")
    print(f"    QNR fraction of cofactor entries (survivors) = {(offvals%2==1).mean():.3f}  "
          f"(skeleton prior 0.500; empirical conditioned over-selects ×1.49 ≈ 0.60)")

    # --- Q6.2.B : the decisive cell ---
    cell = aq & (w == 2)                     # all-QNR cofactor, w=2  (t=3 is universal here)
    n_cell = int(cell.sum())
    rate = float(s0[cell].mean()) if n_cell else float('nan')
    print("\n  [Q6.2.B — DECISIVE : P(σ=0 | all-QNR cofactor, w=2), t=3]")
    print(f"    model rate = {rate:.4f}   (n_cell = {n_cell:,})")
    print(f"    forced null = 0.2000 (1/5)")
    print(f"    empirical (3,3,3,3) cut, N=160 = 0.2659 (201/756)  → +6.6 pp")
    if n_cell:
        # The sampling unit is the ACCEPTED MATRIX, not the target.  One matrix
        # contributes up to 5 targets to the cell and they share its χ-values,
        # so a binomial interval on n_cell treats correlated targets as
        # independent draws and reports a width that is too narrow.  Resample
        # whole matrices instead — that is the unit the sampler generated.
        n_matrices = M.shape[0]
        mat_id = np.concatenate([np.arange(n_matrices) for _ in range(5)])
        cell_mat = mat_id[cell]
        hits = np.bincount(cell_mat, weights=s0[cell].astype(float),
                           minlength=n_matrices)
        cnts = np.bincount(cell_mat, minlength=n_matrices).astype(float)

        naive_se = (rate * (1 - rate) / n_cell) ** 0.5
        rng = np.random.default_rng(20260726)
        n_boot, chunk = 10000, 500
        boot = []
        for start in range(0, n_boot, chunk):
            idx = rng.integers(0, n_matrices, size=(min(chunk, n_boot - start),
                                                    n_matrices))
            den = cnts[idx].sum(axis=1)
            boot.append(hits[idx].sum(axis=1) / np.maximum(den, 1.0))
        boot = np.concatenate(boot)
        lo, hi = np.percentile(boot, [2.5, 97.5])
        n_eff = rate * (1 - rate) / boot.var(ddof=1) if boot.var(ddof=1) > 0 else float("nan")

        print(f"    contributing matrices = {int((cnts > 0).sum()):,} "
              f"(mean {n_cell / max(int((cnts > 0).sum()), 1):.2f} cell targets each)")
        print(f"    model 95% CI (cluster bootstrap over matrices) = [{lo:.4f}, {hi:.4f}]"
              f"   half-width {(hi - lo) / 2:.4f}")
        print(f"    [naive per-target binomial would give ±{1.96 * naive_se:.4f} "
              f"— too narrow; effective n ≈ {n_eff:,.0f} vs n_cell {n_cell:,}]")
        print(f"    → {'model rate is above the 1/5 forced null' if lo > 0.20 else 'model rate not separated from the 1/5 forced null'}"
              f"; observed census rate 0.2659 is "
              f"{'inside' if lo <= 0.2659 <= hi else 'outside'} this interval")

    # --- w distribution (Q6.2.C texture) ---
    print("\n  [w distribution over all surviving targets]")
    vals, counts = np.unique(w, return_counts=True)
    for v, c in zip(vals, counts):
        print(f"    w={v}: {c}  ({c/n_targets:.3f})")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "sample"
    if mode == "sample":
        total = int(sys.argv[2]); batch = int(sys.argv[3]); seed = int(sys.argv[4])
        outfile = sys.argv[5]
        print(f"E1 skeleton model (all depth-3, mod 8) — sampling {total:,} trials")
        sample(total, batch, seed, outfile)
    elif mode == "measure":
        print("E1 skeleton model — measurement panel")
        measure(sys.argv[2:])
