#!/usr/bin/env python3
"""
maxpair_exact.py — exact evaluation of the maximal-pairwise model.

The Monte-Carlo pool leaves the sign of the maximal-pairwise movement
unresolved (§6.2: point 0.2600, cluster 95% [0.2516, 0.2685], which contains
the independent-digit constant 1123/4215). This removes the sampling error
entirely by computing the model's rate as an exact rational.

Why it is harder than `exact_dp.py`. There the higher digits were independent
given the parity coins, so the five rows factorized and each parity graph was
one product of row tables. Here the six depth-(3,3) edges carry a *measured
joint* over both directions, so the rows no longer factorize.

The structure that rescues it: the sector of a (3,3) pair (even/odd) IS the
shared parity, so conditioning on the parity graph β already selects which
joint applies to each edge. Within a sector the joint is a small matrix
(3×3 on the nonzero even values after zero-δ, 4×4 on the odd values), and
letting each edge's *bond* carry one endpoint's value restores factorization:
the model becomes a tensor network on K4 (the four depth-3 vertices) with bond
dimension 3 or 4, free mask indices of size 64, contracted against the same
covering-and-minimality predicate F that `exact_dp.py` builds. Vertex 4 carries
no (3,3) bond — its (3,4) edges are independent given parity — so F is
contracted down to a 64^4 tensor once per (3,4) parity pattern.

Arithmetic is integer throughout: the joints are kept as raw counts, so the
result is an exact rational in those counts. "Exact" therefore means free of
Monte-Carlo error, given the measured joints; it does not remove the empirical
uncertainty of the joint tables themselves, which were measured at N = 320.

The estimand pools all four depth-3 hubs, as `skeleton_model_maxpair.measure`
does. The vertex labels are the primes in increasing order, and the measured
joint is indexed in that order and is not symmetric, so the four hubs are four
genuinely different contractions and must be summed rather than counted once.
Only the pool is independent of the indexing convention: transposing both
joints is the vertex-reversal relabelling, which exchanges hub v with hub 3 - v.

Run:  python3 skeleton_exact/maxpair_exact.py [--validate-only]
"""
from __future__ import annotations

import json
import os
import sys
import time
from fractions import Fraction
from itertools import combinations

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(REPO, "barker_k6_bundle", "code"))
sys.path.insert(0, os.path.join(REPO, "barker_k6_bundle", "research"))

from exact_dp import BITPOS, PAIRS, POPCNT, K, build_F, check, unpack_chunk

NMASK = 64
# Contraction runs modulo these primes (the seven largest below 2^18) and is
# reconstructed by CRT. Each is < 2^18, so products are < 2^36 and a sum of
# 2^24 terms stays inside int64. Six carry ~108 bits (ample for totals near
# 10^30); the seventh is a check modulus, reconstructed-then-verified.
MODULI = [262139, 262133, 262127, 262121, 262111, 262109, 262103]
PAIRS33 = [(i, j) for i in range(4) for j in range(i + 1, 4)]      # 6 edges
PAIRS34 = [(i, 4) for i in range(4)]                              # 4 edges
EVEN_NZ = [2, 4, 6]                       # zero-δ removes 0 from the even sector
ODD_NZ = [1, 3, 5, 7]
DEEP_EVEN_NZ = [2, 4, 6, 8, 10, 12, 14]   # vertex 4 is mod 16
DEEP_ODD_NZ = [1, 3, 5, 7, 9, 11, 13, 15]


def measured_joints(N=320):
    """Integer count matrices for the depth-(3,3) universe joints, by sector.

    Same measurement as `skeleton_model_maxpair.measure_joints`, but counts are
    kept unnormalised so the whole computation stays in exact integers.
    """
    from barker.two_primary import build_two_primary_table
    from barker.arithmetic import is_prime, multiplicative_order, jacobi_symbol

    primes, p = [], 5
    while len(primes) < N:
        if is_prime(p) and p % 4 == 1 and multiplicative_order(2, p) % 2 == 1:
            primes.append(p)
        p += 2
    table = build_two_primary_table(primes)
    ie = {v: k for k, v in enumerate([0, 2, 4, 6])}
    io = {v: k for k, v in enumerate([1, 3, 5, 7])}
    Ce = np.zeros((4, 4), dtype=np.int64)
    Co = np.zeros((4, 4), dtype=np.int64)
    for a, b in combinations(primes, 2):
        if table.depth[a] != 3 or table.depth[b] != 3:
            continue
        if a > b:
            a, b = b, a
        va, vb = table.chi[(b, a)] % 8, table.chi[(a, b)] % 8
        if jacobi_symbol(a % b, b) == 1:
            Ce[ie[va], ie[vb]] += 1
        else:
            Co[io[va], io[vb]] += 1
    return Ce, Co


def edge_matrices(Ce, Co, mode):
    """Per-sector weight matrices on the zero-δ-surviving values.

    mode='measured'   — the measured joint (this is the model under test)
    mode='uniform'    — uniform independent digits, i.e. the exact_dp model;
                        used to validate the machinery against 1123/4215
    """
    ie = {v: k for k, v in enumerate([0, 2, 4, 6])}
    io = {v: k for k, v in enumerate([1, 3, 5, 7])}
    if mode == "measured":
        We = np.array([[Ce[ie[a], ie[b]] for b in EVEN_NZ] for a in EVEN_NZ],
                      dtype=np.int64)
        Wo = np.array([[Co[io[a], io[b]] for b in ODD_NZ] for a in ODD_NZ],
                      dtype=np.int64)
        # R is invariant under scaling BOTH sectors by one constant (every
        # parity graph carries exactly six (3,3) edges), so strip the common
        # factor to keep the modular arithmetic comfortable.
        from math import gcd
        g = 0
        for x in list(We.ravel()) + list(Wo.ravel()):
            g = gcd(g, int(x))
        if g > 1:
            We, Wo = We // g, Wo // g
    elif mode == "uniform":
        We = np.ones((len(EVEN_NZ), len(EVEN_NZ)), dtype=np.int64)
        Wo = np.ones((len(ODD_NZ), len(ODD_NZ)), dtype=np.int64)
    else:
        raise ValueError(mode)
    return We, Wo


def deep_row_table(parities):
    """Vertex 4's row: values to 0..3 are mod 16, nonzero, uniform given parity.

    Returns an object-dtype vector over its 64 possible witness masks.
    """
    slots = [DEEP_EVEN_NZ if b == 0 else DEEP_ODD_NZ for b in parities]
    cof = [0, 1, 2, 3]
    slot_pairs = list(combinations(range(4), 2))
    out = np.zeros(NMASK, dtype=np.int64)
    for v0 in slots[0]:
        for v1 in slots[1]:
            for v2 in slots[2]:
                for v3 in slots[3]:
                    vals = (v0, v1, v2, v3)
                    m = 0
                    for a, b in slot_pairs:
                        if (vals[a] + vals[b]) % 16 == 0:
                            m |= 1 << BITPOS[4][(cof[a], cof[b])]
                    out[m] += 1
    return out


def flips_for(v):
    """(3,3) edges whose joint transposes when hub v is relabelled to vertex 0.

    Sending hub v to vertex 0 by the transposition (0 v) is a symmetry of the
    predicate and of the sum over parity graphs, so every hub can be evaluated
    on the fast vertex-0-gated path. It is NOT a symmetry of the weights: the
    joint matrix is indexed [value of the lower-labelled endpoint, value of the
    higher-labelled endpoint], so an edge whose endpoint order the transposition
    reverses carries the transposed matrix. That is a no-op only when the joints
    are symmetric — which is exactly the uniform-digit case, and not the
    measured one.
    """
    q = list(range(4))
    q[0], q[v] = q[v], q[0]
    return tuple(e for e in PAIRS33 if q[e[0]] > q[e[1]])


def shallow_row_tensor(v, beta_bits, gate=None):
    """Vertex v (depth 3) as a tensor over (mask, bonds of its three (3,3) edges).

    The bond of edge {v,u} carries v's own outgoing value χ_v(u); the partner
    applies the joint weight, so exactly one endpoint per edge must own it.
    Ownership: the lower-numbered endpoint owns the bond, and the higher-numbered
    endpoint carries the weight matrix — so each joint is applied once.

    gate=None   → plain counting tensor
    gate='cell' → restrict to all-QNR cofactor with witness count exactly 2
    gate='num'  → same, and additionally σ_v ≡ 0 (mod 8)
    """
    cof = [u for u in range(K) if u != v]                 # ascending, includes 4
    slot_pairs = list(combinations(range(4), 2))
    edges33 = [(min(v, u), max(v, u)) for u in cof if u != 4]
    dims = []
    for e in edges33:
        b = beta_bits[PAIRS.index(e)]
        dims.append(len(EVEN_NZ) if b == 0 else len(ODD_NZ))
    shape = (NMASK,) + tuple(dims)
    T = np.zeros(shape, dtype=np.int64)

    # value ranges for each cofactor slot
    ranges = []
    for u in cof:
        b = beta_bits[PAIRS.index((min(v, u), max(v, u)))]
        if u == 4:
            ranges.append(EVEN_NZ if b == 0 else ODD_NZ)   # v's value is mod 8
        else:
            ranges.append(EVEN_NZ if b == 0 else ODD_NZ)
    idx_of = [{val: k for k, val in enumerate(r)} for r in ranges]

    for vals in np.ndindex(*[len(r) for r in ranges]):
        value = [ranges[s][vals[s]] for s in range(4)]
        if gate is not None:
            if any(x % 2 == 0 for x in value):
                continue
            w = sum(1 for a, b in slot_pairs if (value[a] + value[b]) % 8 == 0)
            if w != 2:
                continue
            if gate == "num" and sum(value) % 8 != 0:
                continue
        m = 0
        for a, b in slot_pairs:
            if (value[a] + value[b]) % 8 == 0:
                m |= 1 << BITPOS[v][(cof[a], cof[b])]
        # weight: the (3,4) slot is a free uniform digit (weight 1); the (3,3)
        # slots contribute the joint weight when v is the higher endpoint
        w = 1
        bond = []
        for s, u in enumerate(cof):
            if u == 4:
                continue
            e = (min(v, u), max(v, u))
            k_v = idx_of[s][value[s]]
            bond.append(k_v)
        T[(m,) + tuple(bond)] += w
    return T, edges33


def weighted_pair(beta_bits, We, Wo, flip):
    """Weight matrices W[e] indexed by (value of lower endpoint, of higher)."""
    out = {}
    for e in PAIRS33:
        M = We if beta_bits[PAIRS.index(e)] == 0 else Wo
        out[e] = M.T if e in flip else M
    return out


def contract_beta(beta, F4, We, Wo, flips, mod, gate_hub=0):
    """Exact contraction for one parity graph, modulo `mod`.

    Returns one (cell, num) pair per entry of `flips`: the (all-QNR, w = 2)
    cell mass gated at `gate_hub` and its σ = 0 part, under that weight
    orientation. The counting tensors do not depend on the orientation, so
    they are built once and the joints are applied per entry.

    The production path always gates vertex 0, where the tensor is sparse;
    `gate_hub` exists so the regression test can contract a hub directly and
    confront it with the relabelled fast path under asymmetric joints.
    """
    beta_bits = [(beta >> e) & 1 for e in range(len(PAIRS))]
    raw = {(g, v): shallow_row_tensor(v, beta_bits, g if v == gate_hub else None)
           for g in ("cell", "num") for v in range(4)}

    out = []
    for flip in flips:
        W = weighted_pair(beta_bits, We, Wo, flip)
        got = []
        for gate in ("cell", "num"):
            Ts = {}
            for v in range(4):
                T, edges = raw[gate, v]
                T = T % mod
                # each edge's joint weight is applied once, at the higher endpoint
                for pos, e in enumerate(edges):
                    if v == e[1]:
                        M = np.asarray(W[e], dtype=np.int64) % mod
                        T = np.moveaxis(T, pos + 1, -1)
                        T = np.tensordot(T, M, axes=([-1], [1])) % mod
                        T = np.moveaxis(T, -1, pos + 1)
                Ts[v] = (T, edges)
            got.append(_contract_k4(Ts, F4, mod))
        out.append((got[0], got[1]))
    return out


def _contract_k4(Ts, F4, mod):
    """Contract the four depth-3 vertex tensors against F4, modulo `mod`.

    Vertex 0 meets F4 FIRST: on the production path it carries the gate, and a
    gated tensor is sparse in its mask index — all-QNR with witness count
    exactly 2 leaves few masks — so the 64-wide m0 axis collapses before the
    other vertices enter. The contraction order is arbitrary otherwise, so a
    gate elsewhere is still correct, only slower.
    """
    def axes_for(v):
        return {e: pos + 1 for pos, e in enumerate(Ts[v][1])}

    T0 = Ts[0][0]
    live = np.nonzero(T0.reshape(T0.shape[0], -1).any(axis=1))[0]
    if live.size == 0:
        return 0
    G = np.tensordot(T0[live], F4[live] % mod, axes=([0], [0])) % mod
    # G axes: [(0,1),(0,2),(0,3), m1, m2, m3]
    T1, a1 = Ts[1][0], axes_for(1)
    G = np.tensordot(G, T1, axes=([0, 3], [a1[(0, 1)], 0])) % mod
    # G axes: [(0,2),(0,3), m2, m3, (1,2),(1,3)]
    T2, a2 = Ts[2][0], axes_for(2)
    G = np.tensordot(G, T2, axes=([0, 4, 2], [a2[(0, 2)], a2[(1, 2)], 0])) % mod
    # G axes: [(0,3), m3, (1,3), (2,3)]
    T3, a3 = Ts[3][0], axes_for(3)
    G = np.tensordot(G, T3, axes=([0, 2, 3, 1],
                                  [a3[(0, 3)], a3[(1, 3)], a3[(2, 3)], 0])) % mod
    return int(G)


def crt(residues, moduli):
    """The unique non-negative integer below prod(moduli) with these residues."""
    M = 1
    for m in moduli:
        M *= m
    total = 0
    for r, m in zip(residues, moduli):
        Mi = M // m
        total += r * Mi * pow(Mi, -1, m)
    return total % M


def build_F4(beta_bits):
    """F contracted over vertex 4's mask with its row table → 64^4 tensor.

    Depends only on the four (3,4) parities, so there are 16 distinct tensors
    rather than one per parity graph; they are cached.
    """
    parities = tuple(beta_bits[PAIRS.index((i, 4))] for i in range(4))
    hit = _F_CACHE.get(("F4", parities))
    if hit is not None:
        return hit
    q4 = deep_row_table(parities)
    packed = _F_CACHE["packed"]
    acc = np.zeros((NMASK,) * 4, dtype=np.int64)
    for m0 in range(NMASK):
        f = unpack_chunk(packed, m0)          # (m1,m2,m3,m4) booleans
        acc[m0] = f.astype(np.int64) @ q4
    _F_CACHE[("F4", parities)] = acc
    return acc


_F_CACHE = {}


def run_pass(We, Wo, label, log=print):
    """Exact per-hub (num, cell) over all 1,024 parity graphs, by CRT.

    Every hub is evaluated: hub v is relabelled onto vertex 0 by the
    transposition (0 v), which transposes the joints on the edges whose
    endpoint order it reverses (`flips_for`). The four hubs coincide only when
    the joints are symmetric, so they are accumulated separately and pooled by
    the caller — the estimand, matching the Monte-Carlo pool, is the sum.
    """
    flips = [flips_for(v) for v in range(4)]
    t0 = time.time()
    cells = [[] for _ in range(4)]
    nums = [[] for _ in range(4)]
    for mi, mod in enumerate(MODULI):
        cell = [0] * 4
        num = [0] * 4
        for beta in range(1 << len(PAIRS)):
            bits = [(beta >> e) & 1 for e in range(len(PAIRS))]
            F4 = build_F4(bits) % mod
            for v, (c, n) in enumerate(contract_beta(beta, F4, We, Wo, flips, mod)):
                cell[v] = (cell[v] + c) % mod
                num[v] = (num[v] + n) % mod
        for v in range(4):
            cells[v].append(cell[v]); nums[v].append(num[v])
        log(f"      [{label}] modulus {mi + 1}/{len(MODULI)} done "
            f"({time.time() - t0:.0f}s)")
    # reconstruct from all but the last modulus; the last one verifies
    out = []
    for v in range(4):
        cell = crt(cells[v][:-1], MODULI[:-1])
        num = crt(nums[v][:-1], MODULI[:-1])
        check(cell % MODULI[-1] == cells[v][-1] and num % MODULI[-1] == nums[v][-1],
              f"[{label}] hub {v}: CRT check modulus disagrees — overflow")
        out.append((num, cell))
    return out


def main():
    t0 = time.time()
    validate_only = "--validate-only" in sys.argv
    log = lambda m: print(m, flush=True)

    log("[1/5] building the covering/minimality predicate")
    packed, pop = build_F()
    _F_CACHE["packed"], _F_CACHE["pop"] = packed, pop
    log(f"      {pop:,} labeled structures satisfy it")

    log("[2/5] validating the machinery against exact_dp (uniform digits)")
    We_u, Wo_u = edge_matrices(None, None, "uniform")
    hubs_u = run_pass(We_u, Wo_u, "uniform", log)
    # positive control on the pooling: symmetric joints make the relabelling a
    # true symmetry, so the four hubs must come out identical.
    hubs_identical = len(set(hubs_u)) == 1
    check(hubs_identical,
          f"uniform digits must give four identical hubs, got {hubs_u}")
    num_u = sum(n for n, _ in hubs_u)
    cell_u = sum(c for _, c in hubs_u)
    R_uniform = Fraction(num_u, cell_u)
    log(f"      uniform-digit R(3,3,3,4) = {R_uniform} = {float(R_uniform):.6f}")
    check(R_uniform == Fraction(1123, 4215),
          f"machinery validation failed: {R_uniform} != 1123/4215")
    log("      MATCHES the exact_dp constant 1123/4215 — the tensor network, "
        "the modular arithmetic and the CRT reconstruction are all sound")

    result = {"validation_uniform": str(R_uniform),
              "validation_passed": True,
              "uniform_hubs_identical": hubs_identical}
    if not validate_only:
        log("[3/5] measuring the universe (3,3) joints (N = 320)")
        Ce, Co = measured_joints()
        We, Wo = edge_matrices(Ce, Co, "measured")
        log(f"      even-sector counts {Ce.sum():,}, odd-sector {Co.sum():,}")
        log("[4/5] exact contraction under the measured joints")
        hubs = run_pass(We, Wo, "measured", log)
        num = sum(n for n, _ in hubs)
        cell = sum(c for _, c in hubs)
        R = Fraction(num, cell)
        const, obs = Fraction(1123, 4215), Fraction(844, 3379)
        per_hub = [float(Fraction(n, c)) for n, c in hubs]
        result.update({
            "R_maxpair_exact": str(R), "R_decimal": float(R),
            "R_per_hub": [round(x, 6) for x in per_hub],
            # the pooling itself, in a form a reader can re-add
            "hub_num_cell": [[str(n), str(c)] for n, c in hubs],
            "independent_digit_constant": str(const),
            "observed_census": str(obs),
            "movement_pp": round(100 * float(R - const), 4),
            "gap_fraction": round(float((const - R) / (const - obs)), 4),
            "monte_carlo_point": 0.2600,
        })
        log(f"\nexact maximal-pairwise R(3,3,3,4) = {R}")
        log(f"                                 = {float(R):.6f}")
        log(f"  independent-digit constant 1123/4215 = {float(const):.6f}")
        log(f"  observed census 844/3379             = {float(obs):.6f}")
        log(f"  movement from the constant: {100*float(R-const):+.4f} pp "
            f"({100*float((const-R)/(const-obs)):.1f}% of the gap)")
        log(f"  Monte-Carlo point estimate was 0.2600 (interval [0.2516, 0.2685])")
        log("  per-hub rates " + ", ".join(f"{x:.6f}" for x in per_hub)
            + " — pooled above. Individual hubs are not estimands: transposing"
              " both joints exchanges hub v with hub 3 - v, so only the pool is"
              " independent of the endpoint-order convention.")

        # Symmetrized-joint sensitivity. W + W^T removes the joint's
        # orientation-antisymmetric component, which is what separates the four
        # hubs. It is NOT a decomposition of the rate into association and
        # order dependence: symmetrizing also averages the two endpoint
        # marginals, and the conditioned rate is a nonlinear functional of the
        # joint. Read the difference as how far the result moves when the
        # measured orientation is removed, nothing finer. (R is invariant under
        # scaling both sectors, so the doubling is free.)
        log("[5/5] sensitivity: the same contraction on the symmetrized joints")
        hubs_s = run_pass(We + We.T, Wo + Wo.T, "symmetrized", log)
        check(len(set(hubs_s)) == 1,
              f"symmetrized joints must give four identical hubs, got {hubs_s}")
        R_sym = Fraction(sum(n for n, _ in hubs_s), sum(c for _, c in hubs_s))
        result.update({
            "R_symmetrized": str(R_sym), "R_symmetrized_decimal": float(R_sym),
            "symmetrized_movement_pp": round(100 * float(R_sym - const), 4),
        })
        log(f"  symmetrized-joint R(3,3,3,4) = {R_sym} = {float(R_sym):.6f}")
        log(f"  movement from the constant: {100*float(R_sym-const):+.4f} pp "
            f"— sensitivity only: this is the rate under a different (orientation-"
            f"free) joint, not a decomposition of the measured one")

    with open(os.path.join(HERE, "_maxpair_exact.json"), "w") as fh:
        json.dump(result, fh, indent=2)
    log(f"\nelapsed {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
