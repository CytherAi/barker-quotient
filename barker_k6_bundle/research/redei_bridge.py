#!/usr/bin/env python3
"""
redei_bridge.py — falsification of the Rédei bridge lemma for Question 6.2.G.

Q6.2.G asks whether hard-prime tuples realize the exact conditioned support of
the reciprocity skeleton. Rédei symbols were the natural first suspect for an
arithmetic constraint above quadratic reciprocity, but "Rédei-compatible" was a
*hypothesis about the skeleton bits*, not an established constraint: it needs a
bridge lemma translating χ-data into a Rédei symbol. This script settles that
lemma in the negative, so the targeted all-QR enumeration it would have
justified is not worth its compute.

Three structural facts (checked here, not assumed)
--------------------------------------------------
1. NORMALISATION. χ_x is the discrete log w.r.t. the smallest primitive root
   mod x² — an arbitrary convention. A different primitive root rescales χ_x by
   a fixed odd unit of Z/2^t. Units act transitively on each valuation level, so
   the ONLY normalisation-invariant content of the pair (x, p) is v₂(χ_x(p)).
   "The high bit of χ_x(p)" is therefore not a well-defined quantity.
   (The paper's observables — σ_x = 0, the witness relation, the transversal
   multiset — survive precisely because units permute them.)

2. LINEARITY. χ_x is a group homomorphism factoring through (Z/x)*, so every
   multi-prime condition at a fixed hub collapses to a power-residue condition
   on one product: χ_x(a) + χ_x(b) = χ_x(ab). The 2-primary data at a hub
   carries no trilinear content, while a Rédei symbol is genuinely trilinear.
   Any candidate bridge must therefore be cross-hub.

3. SIDE CONDITIONS. Rédei's classical side conditions are pairwise-trivial
   Hilbert symbols, i.e. an all-QR triangle. The deciding observable is the
   all-QNR cofactor at a depth-3 hub, where (p/x) = −1 for all four cofactor
   primes, so every hub-cofactor triple violates them. Only cofactor-internal
   triangles can qualify, and most cofactor parity patterns have none.

The symbol
----------
For primes p₁,p₂,p₃ ≡ 1 (mod 4) with all pairwise Legendre symbols +1: take a
primitive solution of x² − p₁y² − p₂z² = 0, set α = x + y√p₁, and evaluate
[p₁,p₂,p₃] = ((x + y·s) / p₃) with s² ≡ p₁ (mod p₃). Both square roots give the
same value, since the conjugate product is p₂z² and (p₂/p₃) = 1.

Validation before use: value independent of which primitive solution is taken,
and symmetric under all six orderings of the triple — Rédei's defining
property, and the check that the normalisation is right.

The test
--------
The full invariant at hub x is the orbit of (χ_x(y), χ_x(z)) under the
SIMULTANEOUS unit action — everything the census can see there. A triangle's
invariant is the three hub invariants. Only invariant classes holding ≥ 2
triangles can falsify determination, so that is the denominator reported.

This is a falsification harness. A pass would not prove the lemma; the observed
failure does refute it.

Run:  python3 barker_k6_bundle/research/redei_bridge.py
"""
from __future__ import annotations

import itertools
import json
import os
import sys
from collections import defaultdict
from math import gcd, isqrt

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "code"))

from barker.two_primary import quotient_class, two_primary_depth
from barker.arithmetic import is_prime, multiplicative_order, jacobi_symbol

HERE = os.path.dirname(os.path.abspath(__file__))
N_PRIMES = 44                     # universe size for the harness


def check(cond, msg):
    """assert that survives python -O: acceptance checks must fail closed."""
    if not cond:
        raise SystemExit(f"REDEI-BRIDGE CHECK FAILED: {msg}")


def hard_primes(n):
    """The repo's hard primes: p ≡ 1 (mod 4) with ord_p(2) odd."""
    out, p = [], 5
    while len(out) < n:
        if is_prime(p) and p % 4 == 1 and multiplicative_order(2, p) % 2 == 1:
            out.append(p)
        p += 2
    return out


def sqrt_mod(a, p):
    """One square root of a mod p, or None. Tonelli–Shanks."""
    a %= p
    if a == 0:
        return 0
    if pow(a, (p - 1) // 2, p) != 1:
        return None
    q, s = p - 1, 0
    while q % 2 == 0:
        q //= 2
        s += 1
    z = 2
    while pow(z, (p - 1) // 2, p) != p - 1:
        z += 1
    m, c, t, r = s, pow(z, q, p), pow(a, q, p), pow(a, (q + 1) // 2, p)
    while t != 1:
        i, t2 = 0, t
        while t2 != 1:
            t2 = t2 * t2 % p
            i += 1
        b = pow(c, 1 << (m - i - 1), p)
        m, c = i, b * b % p
        t = t * c % p
        r = r * b % p
    return r


def conic_solutions(p1, p2, zmax=60, xmax_mult=400, want=6):
    """Primitive positive solutions of x² − p1·y² − p2·z² = 0.

    Needs (p2/p1) = 1. For each z, x ≡ ±z·√p2 (mod p1), so x runs over two
    arithmetic progressions rather than an interval.
    """
    u = sqrt_mod(p2, p1)
    if u is None:
        return []
    out, xmax = [], xmax_mult * isqrt(p1 * p2)
    for z in range(1, zmax + 1):
        for r in sorted({(u * z) % p1, (-u * z) % p1}):
            x = r if r else p1
            while x <= xmax:
                num = x * x - p2 * z * z
                if num > 0 and num % p1 == 0:
                    yy = num // p1
                    y = isqrt(yy)
                    if y * y == yy and y > 0 and gcd(gcd(x, y), z) == 1:
                        out.append((x, y, z))
                        if len(out) >= want:
                            return out
                x += p1
    return out


def redei_from(p1, p2, p3, sol):
    """[p1,p2,p3] from one primitive solution of the (p1,p2) conic."""
    x, y, _ = sol
    s = sqrt_mod(p1, p3)
    if s is None:
        return None
    v = (x + y * s) % p3
    return None if v == 0 else jacobi_symbol(v, p3)


def redei(p1, p2, p3):
    """The symbol, or None if the primitive solutions disagree."""
    sols = conic_solutions(p1, p2)
    if not sols:
        return None
    vals = {redei_from(p1, p2, p3, s) for s in sols} - {None}
    return vals.pop() if len(vals) == 1 else None


def hub_invariant(x, y, z):
    """Orbit of (χ_x(y), χ_x(z)) under the simultaneous odd-unit action.

    χ_x is defined only up to multiplication by an odd unit of Z/2^t, applied
    to both entries at once, so the canonical representative is the smallest
    such rescaling. This is the complete invariant content of hub x within the
    triangle.
    """
    t = two_primary_depth(x)
    m = 1 << t
    a, b = quotient_class(y, x), quotient_class(z, x)
    return (t,) + min(((a * u) % m, (b * u) % m) for u in range(1, m, 2))


def triangle_invariant(tri):
    p, q, r = tri
    return (hub_invariant(p, q, r), hub_invariant(q, p, r), hub_invariant(r, p, q))


# --------------------------------------------------------------- validations
def verify_generator_rescaling(x=73):
    """Fact 1: another primitive root rescales χ_x by ONE odd unit."""
    t = two_primary_depth(x)
    m, x2 = x * (x - 1), x * x
    odd, mask = m >> t, 1 << t

    def order(a, n):
        k, v = 1, a % n
        while v != 1:
            v = v * a % n
            k += 1
        return k

    gens = [g for g in range(2, 400)
            if gcd(g, x2) == 1 and order(g, x2) == m][:4]

    def chi(p, g):
        s, pm, v = pow(g, odd, x2), pow(p % x2, odd, x2), 1
        for k in range(mask):
            if v == pm:
                return k
            v = v * s % x2
        return None

    units = {}
    for g in gens[1:]:
        us = {(chi(p, g) * pow(chi(p, gens[0]), -1, mask)) % mask
              for p in range(2, x) if chi(p, gens[0]) % 2}
        check(len(us) == 1, f"generator {g} does not rescale χ by a single unit")
        units[g] = us.pop()
    return {"x": x, "generators": gens, "rescaling_units": units}


def verify_chi_structure(x=73):
    """Fact 2: χ_x is a homomorphism factoring through (Z/x)*, bit 0 = Legendre."""
    t = two_primary_depth(x)
    m = 1 << t
    hom = all((quotient_class(a, x) + quotient_class(b, x)) % m
              == quotient_class(a * b, x)
              for a in range(2, 30) for b in range(2, 30)
              if a % x and b % x and (a * b) % x)
    factors = all(quotient_class(a, x) == quotient_class(a + x * k, x)
                  for a in range(2, min(x, 40)) if a % x for k in (1, 2, 3))
    bit0 = all((quotient_class(a, x) % 2 == 0) == (jacobi_symbol(a % x, x) == 1)
               for a in range(2, x) if a % x)
    check(hom, "χ_x is not a homomorphism")
    check(factors, "χ_x does not factor through (Z/x)*")
    check(bit0, "bit 0 of χ_x is not the Legendre symbol")
    return {"homomorphism": hom, "factors_through_Zx": factors,
            "bit0_is_legendre": bit0}


def parity_applicability():
    """Fact 3: all-QR triangles available inside a deciding-cell cofactor.

    The gate forces the hub's four edges odd, so no hub-cofactor triple can
    satisfy Rédei's side conditions. Only the cofactor K4's 6 edges are free.
    """
    V = [0, 1, 2, 3]
    E = list(itertools.combinations(V, 2))
    T = list(itertools.combinations(V, 3))
    hist = defaultdict(int)
    for b in range(1 << len(E)):
        par = {e: (b >> i) & 1 for i, e in enumerate(E)}
        n = sum(1 for t in T
                if all(par[e] == 0 for e in itertools.combinations(t, 2)))
        hist[n] += 1
    return {"patterns_by_all_QR_triangles": {str(k): v for k, v in sorted(hist.items())},
            "patterns_with_at_least_one": sum(v for k, v in hist.items() if k),
            "patterns_total": 1 << len(E),
            "hub_cofactor_triples_applicable": 0,
            "hub_cofactor_triples_total": 6}


# ---------------------------------------------------------------- the sweep
def main():
    log = lambda m: print(m, flush=True)
    log("[1/4] structural facts about χ")
    resc = verify_generator_rescaling()
    struct = verify_chi_structure()
    log(f"      χ homomorphism/factors/bit0 = Legendre: all True")
    log(f"      at x=73 the generators {resc['generators'][1:]} rescale χ by "
        f"{list(resc['rescaling_units'].values())} — so only v₂(χ) is invariant")

    hp = hard_primes(N_PRIMES)
    tris = [t for t in itertools.combinations(hp, 3)
            if all(jacobi_symbol(a % b, b) == 1
                   for a, b in itertools.combinations(t, 2))]
    log(f"[2/4] {len(hp)} hard primes (max {hp[-1]}); "
        f"{len(tris)} all-QR triangles")

    log("[3/4] validating the symbol (solution-independence, S₃-symmetry)")
    indep_ok = indep_n = 0
    for tri in tris[:120]:
        sols = conic_solutions(*tri[:2])
        vals = {redei_from(tri[0], tri[1], tri[2], s) for s in sols} - {None}
        indep_n += 1
        indep_ok += (len(vals) == 1)
    check(indep_ok == indep_n,
          f"symbol depends on which primitive solution is taken "
          f"({indep_ok}/{indep_n})")
    sym_ok = sym_n = 0
    for tri in tris[:120]:
        vals = {redei(*o) for o in itertools.permutations(tri)} - {None}
        sym_n += 1
        sym_ok += (len(vals) == 1)
    check(sym_ok == sym_n,
          f"symbol is not S₃-symmetric ({sym_ok}/{sym_n}) — Rédei's defining "
          f"property fails, so the implementation or normalisation is wrong")
    log(f"      solution-independent {indep_ok}/{indep_n}; "
        f"S₃-symmetric {sym_ok}/{sym_n}")

    log("[4/4] is the symbol a function of the invariant χ data?")
    values = {}
    for i, tri in enumerate(tris):
        v = redei(*tri)
        if v is not None:
            values[tri] = v
        if (i + 1) % 400 == 0:
            log(f"      {i + 1}/{len(tris)}")
    dist = defaultdict(int)
    for v in values.values():
        dist[v] += 1

    buckets = defaultdict(list)
    for tri, v in values.items():
        buckets[triangle_invariant(tri)].append((tri, v))
    multi = {k: b for k, b in buckets.items() if len(b) >= 2}
    split = {k: b for k, b in multi.items() if len({v for _, v in b}) > 1}
    check(split, "no split class found — the lemma is NOT falsified at this "
                 "size, and this script's registered claim would be wrong")

    # deterministic counterexample: smallest split class, its two extreme signs
    key = min(split)
    members = sorted(split[key])
    neg = next(t for t, v in members if v == -1)
    pos = next(t for t, v in members if v == +1)

    result = {
        "universe": {"n_hard_primes": len(hp), "max_prime": hp[-1],
                     "all_QR_triangles": len(tris)},
        "chi_structure": struct,
        "generator_rescaling": {"x": resc["x"],
                                "units": {str(k): v for k, v in
                                          resc["rescaling_units"].items()}},
        "symbol_validation": {"solution_independent": [indep_ok, indep_n],
                              "s3_symmetric": [sym_ok, sym_n]},
        "distribution": {"+1": dist[1], "-1": dist[-1]},
        "determination": {"invariant_classes": len(buckets),
                          "testable_classes": len(multi),
                          "mixed_sign_classes": len(split)},
        "counterexample": {"invariant_class": str(key),
                           "minus": list(neg), "plus": list(pos)},
        "applicability": parity_applicability(),
        "verdict": "falsified: the Redei symbol is not a function of the "
                   "normalisation-invariant chi data, and is undefined on the "
                   "hub triangles carrying the deciding all-QNR observable",
    }
    out = os.path.join(HERE, "_redei_bridge.json")
    with open(out, "w") as fh:
        json.dump(result, fh, indent=2)

    log("")
    log(f"  symbol distribution: +1 {dist[1]}, −1 {dist[-1]}")
    log(f"  invariant classes {len(buckets)}; testable (≥2 triangles) "
        f"{len(multi)}; mixed-sign {len(split)}")
    log(f"  counterexample: {neg} → −1 and {pos} → +1 share invariant class")
    ap = result["applicability"]
    log(f"  applicability in the deciding cell: "
        f"{ap['patterns_with_at_least_one']}/{ap['patterns_total']} cofactor "
        f"parity patterns carry an all-QR triangle; "
        f"{ap['hub_cofactor_triples_applicable']}/6 hub-cofactor triples do")
    log(f"  wrote {out}")
    log("")
    log("  VERDICT — bridge lemma falsified. Classical Rédei symbols are "
        "neither functions of the invariant χ-data nor defined on the hub "
        "triangles carrying the deciding observable.")


if __name__ == "__main__":
    main()
