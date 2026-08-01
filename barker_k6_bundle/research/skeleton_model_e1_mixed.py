#!/usr/bin/env python3
"""
skeleton_model_e1_mixed.py — E1, mixed-depth: the decisive attenuation test.

Generalises skeleton_model_e1.py from all-depth-3 to per-vertex depths drawn
from the law P(t=j) = (3/4)·4^{-(j-3)}.  The hub-row values χ_x(p) are still
mod 2^{t_x}; what changes is that cofactor primes can have depth ≥ 4, which
alters their WITNESS behaviour (covering tests are mod 2^{t_k} at witness k) and
hence the conditioning — the second-order channel through which the empirical
transversal excess ATTENUATES as cofactor depth rises.

Decisive question: does the skeleton model reproduce the empirical attenuation
    cofactor profile   (3,3,3,3)   (3,3,3,4)   (3,3,3,5)
    empirical (N=160)    0.266       0.225       0.211      → null 0.200
If yes  → Q6.2.B is fully combinatorial (dissolves as arithmetic).
If the model stays elevated at depth≥4 while empirical drops → arithmetic is
real and LOCATED in the depth-dependence.

Reciprocity: shared parity coin per unordered pair (Legendre is mod 2, depth-
independent); higher 2-adic bits independent per direction with per-vertex range
2^{t_i-1}.  Conditioning: zero-δ + covering + true minimality (all proper
subsets), identical to the all-depth-3 model.
"""
from __future__ import annotations
import sys
import numpy as np
from itertools import combinations

PAIRS = [(i, j) for i in range(5) for j in range(i + 1, 5)]
SUBSETS = [tuple(s) for s in combinations(range(5), 3)] + [tuple(s) for s in combinations(range(5), 4)]
DEPTHS = np.array([3, 4, 5, 6])
DPROB = np.array([0.75 * 4.0 ** (-(j - 3)) for j in DEPTHS])
DPROB = DPROB / DPROB.sum()


def generate(B, rng, fixed_t=None):
    """B random skeleton matrices with per-vertex depths. Returns (M, t, mod)
    where M[b,i,j]=χ_i(j) ∈ Z/2^{t[b,i]}, mod[b,i]=2^{t[b,i]}.
    If fixed_t (length-5) is given, every matrix uses that depth vector — used
    to target a specific cofactor-depth-profile cell at full yield."""
    if fixed_t is not None:
        t = np.tile(np.asarray(fixed_t, dtype=np.int64), (B, 1))   # (B,5)
    else:
        t = DEPTHS[rng.choice(len(DEPTHS), size=(B, 5), p=DPROB)]  # (B,5)
    mod = (1 << t).astype(np.int64)                                # 2^{t}
    M = np.zeros((B, 5, 5), dtype=np.int64)
    for i, j in PAIRS:
        b = rng.integers(0, 2, B)                                  # shared parity coin
        hi_i = (rng.random(B) * (mod[:, i] >> 1)).astype(np.int64)  # u in [0,2^{t_i-1})
        hi_j = (rng.random(B) * (mod[:, j] >> 1)).astype(np.int64)
        M[:, i, j] = 2 * hi_i + b
        M[:, j, i] = 2 * hi_j + b
    return M, t, mod


def pair_witnessed(M, mod, members, i, j):
    out = np.zeros(M.shape[0], dtype=bool)
    for k in members:
        if k == i or k == j:
            continue
        out |= ((M[:, k, i] + M[:, k, j]) % mod[:, k] == 0)
    return out


def is_covering(M, mod, members):
    members = list(members)
    ok = np.ones(M.shape[0], dtype=bool)
    for a in range(len(members)):
        for b in range(a + 1, len(members)):
            ok &= pair_witnessed(M, mod, members, members[a], members[b])
            if not ok.any():
                return ok
    return ok


def keep(M, mod):
    B = M.shape[0]
    mask = np.ones(B, dtype=bool)
    for i in range(5):
        for j in range(5):
            if i != j:
                mask &= (M[:, i, j] != 0)               # zero-δ
    if not mask.any():
        return mask
    mask &= is_covering(M, mod, range(5))               # covering
    if not mask.any():
        return mask
    for T in SUBSETS:                                    # true minimality
        mask &= ~is_covering(M, mod, T)
        if not mask.any():
            return mask
    return mask


def sample(total, batch, seed, outfile, fixed_t=None):
    rng = np.random.default_rng(seed)
    keptM, keptt = [], []
    n_tr = n_kept = 0
    while n_tr < total:
        B = min(batch, total - n_tr)
        M, t, mod = generate(B, rng, fixed_t)
        m = keep(M, mod)
        if m.any():
            keptM.append(M[m]); keptt.append(t[m]); n_kept += int(m.sum())
        n_tr += B
    M = np.concatenate(keptM) if keptM else np.zeros((0, 5, 5), np.int64)
    t = np.concatenate(keptt) if keptt else np.zeros((0, 5), np.int64)
    np.savez(outfile, M=M, t=t)
    print(f"  seed={seed} trials={n_tr:,} kept={n_kept:,} acc={n_kept/n_tr:.2e} -> {outfile}.npz")


def measure(files):
    Ms, ts = [], []
    for f in files:
        d = np.load(f)
        Ms.append(d["M"]); ts.append(d["t"])
    M = np.concatenate(Ms); t = np.concatenate(ts)
    print(f"  loaded {M.shape[0]:,} survivor matrices")
    if M.shape[0] == 0:
        return
    EMP = {(3,3,3,3): (201,756,0.266), (3,3,3,4): (49,218,0.225), (3,3,3,5): (8,38,0.211)}
    # decisive cell, binned by cofactor depth profile, hub depth = 3
    bins = {}
    for x in range(5):
        cof = [p for p in range(5) if p != x]
        hubdepth3 = (t[:, x] == 3)
        vals = M[:, x, cof]                              # mod 8 (hub depth 3)
        sigma = vals.sum(axis=1) % 8
        w = np.zeros(M.shape[0], np.int64)
        for a in range(4):
            for b in range(a + 1, 4):
                w += ((vals[:, a] + vals[:, b]) % 8 == 0)
        aq = np.all(vals % 2 == 1, axis=1)
        cof_t = np.sort(t[:, cof], axis=1)               # cofactor depth profile
        sel = hubdepth3 & aq & (w == 2)
        idx = np.where(sel)[0]
        for r in idx:
            prof = tuple(int(v) for v in cof_t[r])
            d = bins.setdefault(prof, [0, 0])
            d[1] += 1
            if sigma[r] == 0:
                d[0] += 1
    print(f"\n  [Q6.2.B attenuation — P(σ=0 | hub t=3, all-QNR, w=2) by cofactor depth profile]")
    print(f"  {'profile':>14} {'model rate':>12} {'n':>7}   {'empirical':>10}   {'null':>5}")
    for prof in sorted(bins, key=lambda p: (sum(p), p)):
        s0, n = bins[prof]
        rate = s0 / n if n else float('nan')
        emp = EMP.get(prof)
        emps = f"{emp[2]:.3f} ({emp[0]}/{emp[1]})" if emp else "—"
        se = (rate * (1 - rate) / n) ** 0.5 if n else 0
        print(f"  {str(prof):>14} {rate:>12.4f} {n:>7}   {emps:>10}   0.200   "
              f"[{rate-1.96*se:.3f},{rate+1.96*se:.3f}]")


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "sample":
        # optional 6th arg: comma-separated fixed depth vector, e.g. "3,3,3,3,4"
        ft = None
        if len(sys.argv) > 6:
            ft = [int(x) for x in sys.argv[6].split(",")]
        sample(int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), sys.argv[5], ft)
    elif mode == "measure":
        measure(sys.argv[2:])
