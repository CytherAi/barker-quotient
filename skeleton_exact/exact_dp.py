#!/usr/bin/env python3
"""
exact_dp.py — exact replacement for the E1 reciprocity-skeleton Monte Carlo.

Model (identical to research/skeleton_model_e1{,_mixed}.py at fixed depth
vector d): 10 unordered pairs carry fair shared parity coins b_ij; directed
high bits are independent, χ_i(j) = 2u + b_ij with u uniform on [0, 2^{d_i-1});
witnessing at k is (χ_k(i) + χ_k(j)) ≡ 0 mod 2^{d_k}; conditioning is zero-δ
(all off-diagonal entries nonzero) AND covering AND true minimality (none of
the 15 proper subsets of size 3 or 4 covers, matching the census convention
that covering is defined for sets of size ≥ 3).

Key reduction: conditional on the parity graph the 5 rows are independent, and
every conditioning event and observable is a function of the per-row witness
bit-vector (6 bits) plus a per-row σ=0 flag.  The whole model is therefore one
fixed {0,1} tensor F over 64^5 mask tuples contracted against per-(depth,
parity-star) integer row tables.  All contractions are integer-exact (counts
bounded by 2^44 < 2^53, verified) and results are emitted as exact fractions.

Outputs (skeleton_exact/):
  _exact_results.json   exact fractions, controls, acceptance checks
  _per_graph.npz        per-labeled-parity-graph survivor mass and cell counts
  _support.npz          conditioned support: labeled codes, orbit reps,
                        orbit sizes, exact integer weights per depth profile

Run:  python3 skeleton_exact/exact_dp.py [--skip-support]
"""
from __future__ import annotations

import json
import os
import sys
from fractions import Fraction
from itertools import combinations, permutations

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
RESEARCH = os.path.join(os.path.dirname(HERE), "barker_k6_bundle", "research")

K = 5
PAIRS = list(combinations(range(K), 2))                    # global lex order
NPAIR = len(PAIRS)                                         # 10
SUBSETS = [t for r in (3, 4) for t in combinations(range(K), r)]  # 15
NMASK = 64                                                 # 2^C(4,2)
COF = {v: [u for u in range(K) if u != v] for v in range(K)}
COF_PAIRS = {v: [i for i, p in enumerate(PAIRS) if v not in p] for v in range(K)}
BITPOS = {v: {PAIRS[p]: j for j, p in enumerate(COF_PAIRS[v])} for v in range(K)}
PROFILE_A = (3, 3, 3, 3, 3)
PROFILE_B = (3, 3, 3, 3, 4)                                # deep vertex LAST


# ---------------------------------------------------------------- row tables
def row_tables(t):
    """Exact per-row tables at depth t for each parity star s in [0,16).

    Returns dict with integer arrays over (16 stars, 64 masks):
      all  — zero-δ-clean assignment counts by witness mask
      sig0 — same restricted to σ ≡ 0 mod 2^t
    Cofactor slots are in ascending-vertex order; mask bits follow the global
    pair order restricted to the cofactor (same convention as build_F).
    """
    half = 1 << (t - 1)
    mod = 1 << t
    u = np.indices((half,) * 4).reshape(4, -1).T           # (half^4, 4)
    q_all = np.zeros((16, NMASK), dtype=np.int64)
    q_sig0 = np.zeros((16, NMASK), dtype=np.int64)
    slot_pairs = list(combinations(range(4), 2))           # 6, lex = mask order
    for s in range(16):
        b = np.array([(s >> i) & 1 for i in range(4)])
        e = 2 * u + b                                      # entries in [0, mod)
        clean = np.all(e != 0, axis=1)
        e = e[clean]
        mask = np.zeros(e.shape[0], dtype=np.int64)
        for j, (a, c) in enumerate(slot_pairs):
            mask |= (((e[:, a] + e[:, c]) % mod == 0).astype(np.int64) << j)
        sig0 = (e.sum(axis=1) % mod == 0)
        np.add.at(q_all[s], mask, 1)
        np.add.at(q_sig0[s], mask, sig0.astype(np.int64))
    return {"all": q_all, "sig0": q_sig0, "t": t}


def row_controls(tabs):
    """Structural positive controls on a row table; returns list of failures."""
    t = tabs["t"]
    half, mod = 1 << (t - 1), 1 << t
    u = np.indices((half,) * 4).reshape(4, -1).T
    fails = []
    for s in range(16):
        b = np.array([(s >> i) & 1 for i in range(4)])
        e = 2 * u + b
        e = e[np.all(e != 0, axis=1)]
        w = np.zeros(e.shape[0], dtype=np.int64)
        for a, c in combinations(range(4), 2):
            w += ((e[:, a] + e[:, c]) % mod == 0)
        sig0 = (e.sum(axis=1) % mod == 0)
        if (w == 5).any():
            fails.append(f"t={t} s={s}: w=5 occurs")
        if (~sig0[w == 4]).any():
            fails.append(f"t={t} s={s}: w=4 without σ=0")
        if (sig0 & (w % 2 == 1)).any():
            fails.append(f"t={t} s={s}: σ=0 with odd w")
    return fails



def check(cond, msg):
    """assert that survives python -O: acceptance checks must fail closed."""
    if not cond:
        raise SystemExit(f"EXACT-DP CHECK FAILED: {msg}")

POPCNT = np.array([bin(m).count("1") for m in range(NMASK)], dtype=np.int64)


# ------------------------------------------------------------- predicate F
def build_F():
    """F over 64^5 mask tuples: covering AND no proper subset covers.

    Returns (packed, popcount): packed is a (64, 64^4/8) uint8 bit array,
    chunked over axis m0, bits in C-order over (m1, m2, m3, m4).
    """
    bit = {v: {p: ((np.arange(NMASK) >> BITPOS[v][PAIRS[p]]) & 1).astype(bool)
               for p in range(NPAIR) if v not in PAIRS[p]} for v in range(K)}
    shape = {1: (NMASK, 1, 1, 1), 2: (1, NMASK, 1, 1),
             3: (1, 1, NMASK, 1), 4: (1, 1, 1, NMASK)}

    def wit_arr(v, p, m0):
        if v == 0:
            return bit[0][p][m0]                           # python bool
        return bit[v][p].reshape(shape[v])

    packed = np.zeros((NMASK, NMASK ** 4 // 8), dtype=np.uint8)
    total = 0
    for m0 in range(NMASK):
        def covered(members):
            out = np.ones((), dtype=bool)
            for pi, p in enumerate(PAIRS):
                if not (set(p) <= set(members)):
                    continue
                acc = np.zeros((), dtype=bool)
                for v in members:
                    if v in p:
                        continue
                    acc = acc | wit_arr(v, pi, m0)
                out = out & acc
            return np.broadcast_to(out, (NMASK,) * 4)

        f = covered(range(K)).copy()
        for T in SUBSETS:
            f &= ~covered(T)
        total += int(f.sum())
        packed[m0] = np.packbits(f.reshape(-1))
    return packed, total


def unpack_chunk(packed, m0):
    return np.unpackbits(packed[m0]).reshape((NMASK,) * 4).astype(bool)


def predicate_reference(code):
    """Independent Boolean re-implementation for one 30-bit code (slow path)."""
    masks = [(code >> (6 * v)) & 63 for v in range(K)]
    wit = {p: {v for v in range(K) if v not in PAIRS[p]
               and (masks[v] >> BITPOS[v][PAIRS[p]]) & 1} for p in range(NPAIR)}

    def covers(members):
        ms = set(members)
        return all(wit[p] & ms for p in range(NPAIR) if set(PAIRS[p]) <= ms)

    return covers(range(K)) and not any(covers(T) for T in SUBSETS)


# ------------------------------------------------------------- contraction
S_LUT = np.zeros((1024, K), dtype=np.int64)                # β -> per-vertex star
for beta in range(1024):
    for v in range(K):
        s = 0
        for i, u in enumerate(COF[v]):
            e = PAIRS.index((min(v, u), max(v, u)))
            s |= ((beta >> e) & 1) << i
        S_LUT[beta, v] = s


def beta_perm(pi):
    """Index array: relabeled graph. Edge {i,j} of output = edge {pi(i),pi(j)}."""
    out = np.zeros(1024, dtype=np.int64)
    for beta in range(1024):
        nb = 0
        for e, (i, j) in enumerate(PAIRS):
            a, b = pi[i], pi[j]
            src = PAIRS.index((min(a, b), max(a, b)))
            nb |= ((beta >> src) & 1) << e
        out[beta] = nb
    return out


def contract(packed, depths, tab3, tab4):
    """Per-graph exact counts for one depth vector (axes = vertices 0..4).

    Returns dict of int64 arrays over the 1024 labeled parity graphs:
      D        — survivor count (zero-δ ∧ covering ∧ minimal), u-assignment units
      cell/num — per hub x with d_x = 3: (all-QNR, w=2) cells and their σ=0 part
    Hubs 2..4 are derived from hub 0 by vertex transposition on β (valid when
    d_x = d_0; cross-checked against the directly computed hub 1).
    """
    tab = {3: tab3, 4: tab4}
    q = [tab[depths[v]] for v in range(K)]
    Q4 = q[4]["all"].T.astype(np.float32)                  # (64, 16)

    G = np.empty((NMASK, NMASK ** 3, 16), dtype=np.float32)
    for m0 in range(NMASK):
        f = unpack_chunk(packed, m0).reshape(NMASK ** 3, NMASK).astype(np.float32)
        G[m0] = f @ Q4                                     # ≤ 2^12, f32-exact
    G = G.reshape(NMASK, NMASK, NMASK, NMASK, 16)          # (m0,m1,m2,m3,s4)

    Q3 = q[3]["all"].T.astype(np.float32)
    H = (G.transpose(0, 1, 2, 4, 3).reshape(-1, NMASK) @ Q3)   # ≤ 2^20
    H = H.reshape(NMASK, NMASK, NMASK, 16, 16)             # (m0,m1,m2,s4,s3)
    del G

    Q2 = q[2]["all"].T.astype(np.float64)
    Kt = (H.transpose(0, 1, 3, 4, 2).reshape(-1, NMASK).astype(np.float64) @ Q2)
    Kt = Kt.reshape(NMASK, NMASK, 16, 16, 16)              # (m0,m1,s4,s3,s2)
    del H

    s = S_LUT                                              # (1024, 5)
    Ksub = Kt[:, :, s[:, 4], s[:, 3], s[:, 2]]             # (64, 64, 1024)
    Ksub = np.ascontiguousarray(Ksub.transpose(2, 0, 1))   # (1024, 64, 64)
    del Kt

    def load(v, kind, gate_w2=False, gate_qnr=False):
        vec = q[v][kind].astype(np.float64)                # (16, 64)
        if gate_w2:
            vec = vec * (POPCNT == 2)
        arr = vec[s[:, v]]                                 # (1024, 64)
        if gate_qnr:
            arr = arr * (s[:, v] == 15)[:, None]
        return arr

    def pair_contract(L0, L1):
        val = np.einsum("bij,bi,bj->b", Ksub, L0, L1)
        check(np.all(np.abs(val - np.round(val)) == 0) and val.max() < 2 ** 53,
              "contraction result non-integral or exceeds 2^53")
        return np.round(val).astype(np.int64)

    out = {"D": pair_contract(load(0, "all"), load(1, "all"))}
    out["cell0"] = pair_contract(load(0, "all", True, True), load(1, "all"))
    out["num0"] = pair_contract(load(0, "sig0", True, True), load(1, "all"))
    out["cell1"] = pair_contract(load(0, "all"), load(1, "all", True, True))
    out["num1"] = pair_contract(load(0, "all"), load(1, "sig0", True, True))
    return out


def hub_totals(res, depths):
    """Pooled (num, cell) over all depth-3 hubs, via β-transposition for x ≥ 2;
    also returns the hub-1 consistency check."""
    ids = list(range(K))
    num = res["num0"].copy()
    cell = res["cell0"].copy()
    perm01 = beta_perm([1, 0] + ids[2:])
    check = (np.array_equal(res["num1"], res["num0"][perm01])
             and np.array_equal(res["cell1"], res["cell0"][perm01]))
    num += res["num1"]
    cell += res["cell1"]
    for x in range(2, K):
        if depths[x] != 3:
            continue
        pi = ids.copy()
        pi[0], pi[x] = pi[x], pi[0]
        pb = beta_perm(pi)
        num += res["num0"][pb]
        cell += res["cell0"][pb]
    return num, cell, check


# ------------------------------------------------------- small-k cross-checks
def brute_force_k4(t=3):
    """Direct enumeration of the full k=4 model (no row factorization):
    per parity graph, all 64^4 u-assignments evaluated from raw entries.
    Returns per-graph survivor counts (int64, 64 graphs)."""
    k = 4
    pairs = list(combinations(range(k), 2))
    subsets = list(combinations(range(k), 3))
    half, mod = 1 << (t - 1), 1 << t
    n_per_row = half ** (k - 1)                            # 64
    idx = np.arange(n_per_row ** k, dtype=np.int64)
    rows_u = [(idx // (n_per_row ** v)) % n_per_row for v in range(k)]
    D = np.zeros(64, dtype=np.int64)
    for beta in range(64):
        E = {}
        ok = np.ones(idx.shape[0], dtype=bool)
        for v in range(k):
            cof = [u for u in range(k) if u != v]
            for slot, u_ in enumerate(cof):
                e_idx = pairs.index((min(v, u_), max(v, u_)))
                b = (beta >> e_idx) & 1
                u_dig = (rows_u[v] // (half ** slot)) % half
                E[(v, u_)] = 2 * u_dig + b
                ok &= E[(v, u_)] != 0
        def covd(members, alive):
            got = alive.copy()
            for (a, b2) in combinations(sorted(members), 2):
                acc = np.zeros(idx.shape[0], dtype=bool)
                for w_ in members:
                    if w_ in (a, b2):
                        continue
                    acc |= ((E[(w_, a)] + E[(w_, b2)]) % mod == 0)
                got &= acc
            return got
        surv = covd(range(k), ok)
        for T in subsets:
            surv &= ~covd(T, ok)
        D[beta] = int(surv.sum())
    return D


def exact_k4(t=3):
    """Row-factorized exact k=4 counts per parity graph (engine path)."""
    k = 4
    pairs = list(combinations(range(k), 2))
    subsets = list(combinations(range(k), 3))
    cof_pairs = {v: [i for i, p in enumerate(pairs) if v not in p] for v in range(k)}
    bitpos = {v: {pairs[p]: j for j, p in enumerate(cof_pairs[v])} for v in range(k)}
    half, mod = 1 << (t - 1), 1 << t
    # per-row tables over 8 stars, 8 masks
    q = np.zeros((k, 8, 8), dtype=np.int64)
    for v in range(k):
        cof = [u for u in range(k) if u != v]
        slot_pairs = list(combinations(range(k - 1), 2))
        for s in range(8):
            b = np.array([(s >> i) & 1 for i in range(k - 1)])
            u = np.indices((half,) * (k - 1)).reshape(k - 1, -1).T
            e = 2 * u + b
            e = e[np.all(e != 0, axis=1)]
            mask = np.zeros(e.shape[0], dtype=np.int64)
            for j, (a, c) in enumerate(slot_pairs):
                gp = (min(cof[a], cof[c]), max(cof[a], cof[c]))
                mask |= (((e[:, a] + e[:, c]) % mod == 0).astype(np.int64)
                         << bitpos[v][gp])
            np.add.at(q[v][s], mask, 1)
    # predicate over 8^4
    grids = np.indices((8,) * k)
    def covd(members):
        out = np.ones((8,) * k, dtype=bool)
        for p_i, p in enumerate(pairs):
            if not set(p) <= set(members):
                continue
            acc = np.zeros((8,) * k, dtype=bool)
            for v in members:
                if v in p:
                    continue
                acc |= ((grids[v] >> bitpos[v][p]) & 1).astype(bool)
            out &= acc
        return out
    F = covd(range(k)).copy()
    for T in subsets:
        F &= ~covd(T)
    # per-graph contraction
    D = np.zeros(64, dtype=np.int64)
    for beta in range(64):
        stars = []
        for v in range(k):
            s = 0
            for i, u_ in enumerate([u for u in range(k) if u != v]):
                e_i = pairs.index((min(v, u_), max(v, u_)))
                s |= ((beta >> e_i) & 1) << i
            stars.append(s)
        val = np.einsum("abcd,a,b,c,d->", F.astype(np.float64),
                        *[q[v][stars[v]].astype(np.float64) for v in range(k)])
        D[beta] = int(round(val))
    return D


# ------------------------------------------------------------------ support
def mask_perm_lut(pi):
    """For permutation pi: LUT[v] maps row-v masks to row-pi(v) masks."""
    lut = np.zeros((K, NMASK), dtype=np.int64)
    for v in range(K):
        for m in range(NMASK):
            nm = 0
            for p in range(NPAIR):
                if v in PAIRS[p]:
                    continue
                if (m >> BITPOS[v][PAIRS[p]]) & 1:
                    a, b = sorted(pi[i] for i in PAIRS[p])
                    nm |= 1 << BITPOS[pi[v]][(a, b)]
            lut[v, m] = nm
    return lut


def support_codes(packed):
    """All labeled mask tuples with F = 1, as codes = Σ_v mask_v << 6v."""
    out = []
    for m0 in range(NMASK):
        f = unpack_chunk(packed, m0).reshape(-1)
        w = np.nonzero(f)[0].astype(np.int64)      # flat C-order (m1,m2,m3,m4)
        code = (((w >> 18) & 63) << 6) | (((w >> 12) & 63) << 12) \
            | (((w >> 6) & 63) << 18) | ((w & 63) << 24) | m0
        out.append(code)
    return np.concatenate(out)


def canonicalize(codes, group):
    """Minimum code over the orbit of each labeled structure under `group`.
    Valid only for depth profiles fixed by every permutation in `group`."""
    luts = [mask_perm_lut(pi) for pi in group]
    ms = [(codes >> (6 * v)) & 63 for v in range(K)]
    canon = None
    for pi, lut in zip(group, luts):
        nc = np.zeros_like(codes)
        for v in range(K):
            nc |= lut[v][ms[v]] << (6 * pi[v])
        canon = nc if canon is None else np.minimum(canon, nc)
    return canon


def support_weights(reps, depths, tab3, tab4):
    """Exact integer weight N(m) = Σ_β Π_v q_all[s_v(β)][m_v] per rep.
    Per-β products ≤ 2^44 and the β-sum ≤ 2^54, so accumulate in int64."""
    tab = {3: tab3, 4: tab4}
    rm = [(reps >> (6 * v)) & 63 for v in range(K)]
    acc = np.zeros(reps.shape[0], dtype=np.int64)
    for beta in range(1024):
        term = np.ones(reps.shape[0], dtype=np.int64)
        for v in range(K):
            term *= tab[depths[v]]["all"][S_LUT[beta, v]][rm[v]]
        acc += term
    return acc


# --------------------------------------------------------------- MC checks
def mc_rate_e1():
    files = [os.path.join(RESEARCH, f"_e1_survivors_s{s}.npy")
             for s in list(range(1, 9)) + list(range(11, 17))]
    files = [f for f in files if os.path.exists(f)]
    if not files:
        return None
    M = np.concatenate([np.load(f) for f in files])
    hit = tot = 0
    for x in range(K):
        cof = [p for p in range(K) if p != x]
        vals = M[:, x, cof]
        sigma = vals.sum(axis=1) % 8
        w = np.zeros(M.shape[0], np.int64)
        for a, b in combinations(range(4), 2):
            w += ((vals[:, a] + vals[:, b]) % 8 == 0)
        sel = np.all(vals % 2 == 1, axis=1) & (w == 2)
        hit += int((sigma[sel] == 0).sum())
        tot += int(sel.sum())
    return hit, tot, len(M)


def mc_rate_e1deep():
    files = [os.path.join(RESEARCH, f"_e1deep_s{s}.npz") for s in range(401, 411)]
    files = [f for f in files if os.path.exists(f)]
    if not files:
        return None
    Ms, ts = [], []
    for f in files:
        d = np.load(f)
        Ms.append(d["M"]); ts.append(d["t"])
    M, t = np.concatenate(Ms), np.concatenate(ts)
    hit = tot = 0
    for x in range(K):
        cof = [p for p in range(K) if p != x]
        vals = M[:, x, cof]
        sigma = vals.sum(axis=1) % 8
        w = np.zeros(M.shape[0], np.int64)
        for a, b in combinations(range(4), 2):
            w += ((vals[:, a] + vals[:, b]) % 8 == 0)
        sel = (t[:, x] == 3) & np.all(vals % 2 == 1, axis=1) & (w == 2)
        prof_ok = np.sort(t[:, cof], axis=1)[:, -1] == 4
        sel &= prof_ok & (np.sort(t[:, cof], axis=1)[:, :3] == 3).all(axis=1)
        hit += int((sigma[sel] == 0).sum())
        tot += int(sel.sum())
    return hit, tot, len(M)


# --------------------------------------------------------------------- main
def main():
    skip_support = "--skip-support" in sys.argv
    checks = {}
    log = lambda s: print(s, flush=True)

    log("[1/7] row tables + structural controls")
    tab3, tab4 = row_tables(3), row_tables(4)
    fails = row_controls(tab3) + row_controls(tab4)
    check(not fails, "structural row controls failed: " + "; ".join(fails))
    checks["row_controls_w5_w4_parity"] = "PASS"
    for t, tabs in ((3, tab3), (4, tab4)):
        half = 1 << (t - 1)
        for s in range(16):
            zeros = sum((s >> i) & 1 == 0 for i in range(4))
            expect = ((half - 1) ** zeros) * (half ** (4 - zeros))
            check(tabs["all"][s].sum() == expect, f"row mass sum t={t} s={s}")
    checks["row_mass_sums"] = "PASS"
    qnr_num = int((tab3["sig0"][15] * (POPCNT == 2)).sum())
    qnr_den = int((tab3["all"][15] * (POPCNT == 2)).sum())
    check(Fraction(qnr_num, qnr_den) == Fraction(1, 5),
          f"unconditioned all-QNR w=2 baseline {qnr_num}/{qnr_den} != 1/5")
    checks["baseline_qnr_w2"] = f"{qnr_num}/{qnr_den} = {Fraction(qnr_num, qnr_den)}"
    a_num = int((tab3["sig0"] * (POPCNT == 2)).sum())
    a_den = int((tab3["all"] * (POPCNT == 2)).sum())
    check(Fraction(a_num, a_den) == Fraction(3, 13),
          f"unconditioned all-t3 w=2 baseline {a_num}/{a_den} != 3/13")
    checks["baseline_all_t3_w2"] = f"{a_num}/{a_den} = {Fraction(a_num, a_den)}"

    log("[2/7] k=4 engine vs direct matrix enumeration")
    bf = brute_force_k4()
    en = exact_k4()
    check(np.array_equal(bf, en), "k=4 brute force mismatch")
    checks["k4_brute_force_agreement"] = f"PASS (64 graphs, total={int(bf.sum())})"

    log("[3/7] build 64^5 predicate (covering ∧ 15-subset non-coverage)")
    packed, fpop = build_F()
    checks["predicate_popcount"] = fpop
    rng = np.random.default_rng(20260726)
    sample = rng.integers(0, 2 ** 30, size=20000)
    for c in sample:
        m0 = int(c) & 63
        rest = int(c) >> 6
        w = (((rest >> 0) & 63) << 18) | (((rest >> 6) & 63) << 12) \
            | (((rest >> 12) & 63) << 6) | ((rest >> 18) & 63)
        got = bool((packed[m0][w >> 3] >> (7 - (w & 7))) & 1)
        want = predicate_reference((int(c) & 63)
                                   | (((rest >> 0) & 63) << 6)
                                   | (((rest >> 6) & 63) << 12)
                                   | (((rest >> 12) & 63) << 18)
                                   | (((rest >> 18) & 63) << 24))
        check(got == want, f"predicate mismatch at code {c}")
    checks["predicate_boolean_reference_20k"] = "PASS"

    log("[4/7] exact contraction, profile A = (3,3,3,3,3)")
    resA = contract(packed, PROFILE_A, tab3, tab4)
    numA, cellA, chkA = hub_totals(resA, PROFILE_A)
    log("[4/7] exact contraction, profile B = (3,3,3,3,4)")
    resB = contract(packed, PROFILE_B, tab3, tab4)
    numB, cellB, chkB = hub_totals(resB, PROFILE_B)
    check(chkA and chkB, f"hub-1 counts != transposed hub-0 counts "
                         f"(profile A ok={chkA}, profile B ok={chkB})")
    checks["hub1_equals_permuted_hub0"] = "PASS"

    R_A = Fraction(int(numA.sum()), int(cellA.sum()))
    R_B = Fraction(int(numB.sum()), int(cellB.sum()))

    # labeled-vs-orbit: survivor mass constant on iso classes of parity graphs
    perms = list(permutations(range(K)))
    pb_all = [beta_perm(pi) for pi in perms]
    canon_beta = np.min(np.stack([np.arange(1024)[pb] for pb in pb_all]), axis=0)
    ncls = len(np.unique(canon_beta))
    okA = all(len(set(resA["D"][canon_beta == c])) == 1
              for c in np.unique(canon_beta))
    perms4 = [pi for pi in perms if pi[4] == 4]
    canon4 = np.min(np.stack([np.arange(1024)[beta_perm(pi)] for pi in perms4]),
                    axis=0)
    okB = all(len(set(resB["D"][canon4 == c])) == 1 for c in np.unique(canon4))
    checks["labeled_vs_orbit"] = (
        f"PASS ({ncls} unlabeled classes; A constant on S5 classes: {okA}; "
        f"B constant on vertex-4-marked classes: {okB})")
    check(ncls == 34 and okA and okB, "labeled-vs-orbit constancy failed")

    # depth-vector permutation invariance: deep vertex moved 4 -> 0
    resB0 = contract(packed, (4, 3, 3, 3, 3), tab3, tab4)
    swap = beta_perm([4, 1, 2, 3, 0])
    checks["depth_perm_invariance"] = (
        "PASS" if np.array_equal(resB0["D"], resB["D"][swap]) else "FAIL")
    check(checks["depth_perm_invariance"] == "PASS", "depth permutation invariance failed")

    log("[5/7] Monte Carlo agreement")
    e1 = mc_rate_e1()
    if e1:
        h, n, nm = e1
        diff = abs(h / n - float(R_A))
        checks["mc_e1"] = (f"MC {h}/{n} = {h/n:.4f} over {nm} matrices; "
                           f"exact {float(R_A):.6f}; |diff| = {diff:.4f}")
        check(diff < 0.02, f"e1 MC disagreement {diff}")
    deep = mc_rate_e1deep()
    if deep:
        h, n, nm = deep
        diff = abs(h / n - float(R_B))
        checks["mc_e1deep"] = (f"MC {h}/{n} = {h/n:.4f} over {nm} matrices; "
                               f"exact {float(R_B):.6f}; |diff| = {diff:.4f}")
        check(diff < 0.015, f"e1deep MC disagreement {diff}")

    surv_A = int(resA["D"].sum())
    surv_B = int(resB["D"].sum())
    p_A = Fraction(surv_A, 1024 * (4 ** 4) ** 5)
    p_B = Fraction(surv_B, 1024 * (4 ** 4) ** 4 * (8 ** 4))

    log(f"[6/7] conditioned support + orbits ({fpop} labeled structures)")
    support = {}
    if not skip_support and fpop > 5 * 10 ** 7:
        support = {"skipped": f"{fpop} labeled structures exceed the 5e7 "
                              "emission bound; rerun with a coarser plan"}
        log("  ! support emission skipped: " + support["skipped"])
    elif not skip_support:
        codes = support_codes(packed)
        check(codes.shape[0] == fpop, "support code count != predicate popcount")
        # profile A: weights are S5-invariant -> S5 orbits
        canon_A = canonicalize(codes, perms)
        reps_A, counts_A = np.unique(canon_A, return_counts=True)
        wA = support_weights(reps_A, PROFILE_A, tab3, tab4)
        # profile B: depth marks vertex 4 -> orbits under its stabilizer S4
        canon_B = canonicalize(codes, perms4)
        reps_B, counts_B = np.unique(canon_B, return_counts=True)
        wB = support_weights(reps_B, PROFILE_B, tab3, tab4)
        support = {
            "labeled_structures": int(codes.shape[0]),
            "s5_orbits": int(reps_A.shape[0]),
            "s4_marked_orbits": int(reps_B.shape[0]),
            "s5_orbits_realizable_A": int((wA > 0).sum()),
            "s4_orbits_realizable_B": int((wB > 0).sum()),
        }
        np.savez_compressed(
            os.path.join(HERE, "_support.npz"),
            codes=codes, canon_A=canon_A, canon_B=canon_B,
            reps_A=reps_A, orbit_size_A=counts_A, weight_A=wA,
            reps_B=reps_B, orbit_size_B=counts_B, weight_B=wB,
            note=np.array([
                "code = sum(mask_v << 6v); weight = sum_beta prod_v "
                "q_all[s_v(beta)][m_v]; P(structure & survive | profile) = "
                "weight / (1024 * prod_v 2^{4(d_v-1)})"]))
        # sanity: orbit-weighted mass equals the contraction's survivor mass
        check(int((wA * counts_A).sum()) == surv_A, "profile-A orbit mass != survivor mass")
        check(int((wB * counts_B).sum()) == surv_B, "profile-B orbit mass != survivor mass")
        checks["support_mass_equals_survivor_mass"] = "PASS"

    log("[7/7] emit artifacts")
    np.savez_compressed(
        os.path.join(HERE, "_per_graph.npz"),
        D_A=resA["D"], D_B=resB["D"],
        cell0_A=resA["cell0"], num0_A=resA["num0"],
        cell0_B=resB["cell0"], num0_B=resB["num0"],
        pooled_cell_A=cellA, pooled_num_A=numA,
        pooled_cell_B=cellB, pooled_num_B=numB)

    results = {
        "model": "reciprocity-symmetric skeleton, exact (no Monte Carlo)",
        "estimand": "P(σ_x = 0 | all-QNR cofactor, w_x = 2, hub depth 3) on "
                    "zero-δ minimal coverings; cells pooled over depth-3 hubs "
                    "and all 1024 labeled parity graphs",
        "R_A_3333": {"fraction": f"{R_A.numerator}/{R_A.denominator}",
                     "decimal": float(R_A)},
        "R_B_3334": {"fraction": f"{R_B.numerator}/{R_B.denominator}",
                     "decimal": float(R_B)},
        "cells": {"A": [int(numA.sum()), int(cellA.sum())],
                  "B": [int(numB.sum()), int(cellB.sum())]},
        "survivor_mass": {"A": surv_A, "B": surv_B},
        "acceptance_probability": {
            "A": {"fraction": f"{p_A.numerator}/{p_A.denominator}",
                  "decimal": float(p_A)},
            "B": {"fraction": f"{p_B.numerator}/{p_B.denominator}",
                  "decimal": float(p_B)}},
        "support": support,
        "checks": checks,
    }
    out = os.path.join(HERE, "_exact_results.json")
    with open(out, "w") as fh:
        json.dump(results, fh, indent=2)
    log(f"\nR(3,3,3,3) = {R_A} = {float(R_A):.6f}")
    log(f"R(3,3,3,4) = {R_B} = {float(R_B):.6f}")
    log(f"acceptance A = {float(p_A):.3e}   B = {float(p_B):.3e}")
    log(f"wrote {out}")


if __name__ == "__main__":
    main()
