#!/usr/bin/env python3
"""
burde_pair_law.py — Burde's rational biquadratic reciprocity on the census
population, as a theorem-level calibration of the §6.2 even-sector joint.

What this establishes, and nothing more
---------------------------------------
It IDENTIFIES the even-sector quartic-bit agreement with the sign of
(ad − bc)/q. On the exact population the manuscript measures — N = 320, both
primes of depth 3, even sector, zero-δ, which is 8,734 pairs and equals
We.sum() of the maximal-pairwise joint — the identity

    (q/p)_4 · (p/q)_4 = ((ad − bc) / q),     p = a²+b², q = c²+d², a,c odd, b,d even

holds on every pair. That converts an empirical observation into a classical
law plus one arithmetic question.

It does NOT:
  * explain why that sign is +1 in 4,994 of 8,734 pairs — the bias is exactly
    what remains unexplained, and is the content of the open question;
  * explain the ordered-joint asymmetry (1,100 at (2,6) against 953 at (6,2)),
    since Burde is symmetric in p and q;
  * constrain the odd hub–cofactor edges that carry σ_x — the all-QNR gate makes
    every hub–cofactor pair odd, and the quartic symbol is undefined there.

Why it is correctly typed (where the Rédei attempt was not, see redei_bridge.py)
-------------------------------------------------------------------------------
(q/p)_4 := q^((p−1)/4) is precisely the statement v₂(χ_p(q)) ≥ 2. Since χ_x is a
discrete log defined only up to an odd unit, v₂ is the ONLY invariant of a pair,
so the quartic symbol is well-defined where "the high bit of χ" is not. Its side
condition is a pair condition, (p/q) = 1, not a triangle.

A trap this harness pins
------------------------
On hard primes all four displayed formulas — (ad ± bc)/q and (ac ± bd)/q — give
the SAME Legendre symbol. Every hard prime is 1 mod 8, so (i/q) = +1, and
c ≡ ±i·d (mod q) turns each expression into the others times (i/q) or (−1/q).
Agreement across the four is therefore one identity tested four times, not four
independent confirmations, and the harness asserts the equivalence rather than
reporting it as corroboration.

Run:  python3 barker_k6_bundle/research/burde_pair_law.py
"""
from __future__ import annotations

import itertools
import json
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "code"))

from redei_bridge import check, hard_primes
from barker.two_primary import quotient_class, two_primary_depth
from barker.arithmetic import jacobi_symbol

N_UNIVERSE = 320          # the population §6.2 measures its joint on
WE_SUM = 8734             # We.sum() of the maximal-pairwise even joint
CE_SUM = 15564            # even-sector depth-3 pairs before zero-δ


def two_squares(p):
    """p = a² + b² with a odd > 0 and b even > 0. Unique for p ≡ 1 (mod 4)."""
    a = 1
    while a * a < p:
        b2 = p - a * a
        b = int(b2 ** 0.5)
        while b * b < b2:
            b += 1
        if b * b == b2 and b % 2 == 0 and b > 0:
            return a, b
        a += 2
    return None


def quartic(q, p):
    """(q/p)_4 ∈ {±1}; None when (q/p) ≠ 1. Equals v₂(χ_p(q)) ≥ 2."""
    r = pow(q % p, (p - 1) // 4, p)
    return 1 if r == 1 else (-1 if r == p - 1 else None)


def variants(a, b, c, d, q):
    """The four displayed right-hand sides, as Legendre symbols mod q."""
    return {"ad-bc": jacobi_symbol((a * d - b * c) % q, q),
            "ad+bc": jacobi_symbol((a * d + b * c) % q, q),
            "ac-bd": jacobi_symbol((a * c - b * d) % q, q),
            "ac+bd": jacobi_symbol((a * c + b * d) % q, q)}


def main():
    log = lambda m: print(m, flush=True)

    log("[1/5] population (must be the one §6.2 measures its joint on)")
    hp = hard_primes(N_UNIVERSE)
    check(all(p % 8 == 1 for p in hp),
          "a hard prime is not 1 mod 8 — the variant-equivalence argument fails")
    d3 = [p for p in hp if two_primary_depth(p) == 3]
    rep = {p: two_squares(p) for p in d3}
    check(all(r and r[0] % 2 == 1 and r[1] % 2 == 0 and r[0] > 0 and r[1] > 0
              and r[0] ** 2 + r[1] ** 2 == p for p, r in rep.items()),
          "two-squares representation missing or wrongly normalised")

    pairs, before_zero_delta = [], 0
    for p, q in itertools.combinations(d3, 2):
        if jacobi_symbol(p % q, q) != 1:
            continue
        before_zero_delta += 1
        cp, cq = quotient_class(q, p), quotient_class(p, q)
        if cp == 0 or cq == 0:
            continue
        pairs.append((p, q, cp, cq))
    check(before_zero_delta == CE_SUM,
          f"even-sector depth-3 pairs {before_zero_delta} != {CE_SUM}")
    check(len(pairs) == WE_SUM,
          f"population {len(pairs)} != We.sum() = {WE_SUM}; this harness is not "
          f"testing the joint the manuscript measures")
    log(f"      {len(d3)} depth-3 primes of {len(hp)}; even-sector pairs "
        f"{before_zero_delta} = Ce.sum(); after zero-δ {len(pairs)} = We.sum()")

    log("[2/5] domain checks on the quartic symbols")
    for p, q, cp, cq in pairs:
        check(quartic(q, p) is not None and quartic(p, q) is not None,
              f"quartic symbol undefined on the even sector at ({p},{q})")
        check(quartic(q, p) == (1 if cp % 4 == 0 else -1)
              and quartic(p, q) == (1 if cq % 4 == 0 else -1),
              f"quartic symbol disagrees with v₂(χ) at ({p},{q})")
    log("      all defined, and each equals the v₂(χ) ≥ 2 statement")

    log("[3/5] the identity, and the equivalence of the four displayed forms")
    ok = 0
    var_all_equal = 0
    rhs = Counter()
    joint = Counter()
    for p, q, cp, cq in pairs:
        (a, b), (c, d) = rep[p], rep[q]
        vs = variants(a, b, c, d, q)
        var_all_equal += (len(set(vs.values())) == 1)
        r = vs["ad-bc"]
        lhs = quartic(q, p) * quartic(p, q)
        ok += (lhs == r)
        rhs[r] += 1
        joint[(quartic(q, p), quartic(p, q))] += 1
    check(ok == len(pairs), f"identity fails: {ok}/{len(pairs)}")
    check(var_all_equal == len(pairs),
          "the four displayed forms are not equivalent on this population")
    log(f"      (q/p)_4 (p/q)_4 = ((ad-bc)/q) on {ok}/{len(pairs)} pairs")
    log(f"      all four displayed forms agree on {var_all_equal}/{len(pairs)} "
        f"— ONE identity tested four times, not four confirmations")

    log("[4/5] non-vacuity, marginals, and representation invariance")
    check(rhs[1] > 0 and rhs[-1] > 0, "RHS is constant — the identity is vacuous")
    n = len(pairs)
    agree = sum(v for k, v in joint.items() if k[0] == k[1])
    m_qp = sum(v for k, v in joint.items() if k[0] == 1) / n
    m_pq = sum(v for k, v in joint.items() if k[1] == 1) / n
    check(0.2 < m_qp < 0.5 and 0.2 < m_pq < 0.5,
          "a quartic marginal is degenerate")
    check(agree == rhs[1],
          "agreement count is not the count of RHS = +1 — the identification "
          "of the joint's agreement structure with Burde's RHS has broken")
    sign_inv = 0
    for p, q, _, _ in pairs:
        (a, b), (c, d) = rep[p], rep[q]
        vals = {variants(sa * a, sb * b, sc * c, sd * d, q)["ad-bc"]
                for sa in (1, -1) for sb in (1, -1)
                for sc in (1, -1) for sd in (1, -1)}
        sign_inv += (len(vals) == 1)
    check(sign_inv == n, "RHS depends on the sign choice in the representation")
    log(f"      RHS split +1 {rhs[1]} / -1 {rhs[-1]}; marginals "
        f"{m_qp:.4f}, {m_pq:.4f}; agreement {agree} = RHS(+1)")
    log(f"      invariant under all 16 sign choices of (a,b,c,d): {sign_inv}/{n}")

    log("[5/5] applicability, and live negative controls")
    V = [0, 1, 2, 3]
    E = list(itertools.combinations(V, 2))
    with_even = sum(1 for m in range(1 << len(E))
                    if any(not (m >> i) & 1 for i in range(len(E))))

    shifted = sum(1 for i, (p, q, _, _) in enumerate(pairs)
                  if quartic(q, p) * quartic(p, q)
                  == variants(*rep[pairs[(i + 1) % n][0]],
                              *rep[pairs[(i + 1) % n][1]],
                              pairs[(i + 1) % n][1])["ad-bc"]) / n
    bumped = sum(1 for p, q, _, _ in pairs
                 if quartic(q, p) * quartic(p, q)
                 == jacobi_symbol((rep[p][0] * rep[q][1]
                                   - rep[p][1] * rep[q][0] + 1) % q, q)) / n
    check(shifted < 0.60, f"scrambled-pairing control passes at {shifted:.3f} — "
                          f"the identity check has no teeth")
    check(bumped < 0.60, f"perturbed-RHS control passes at {bumped:.3f} — "
                         f"the identity check has no teeth")
    log(f"      cofactor parity patterns with ≥1 even edge: {with_even}/64; "
        f"hub-cofactor edges under the all-QNR gate: 0/4")
    log(f"      negative controls — scrambled pairing {shifted:.3f}, "
        f"perturbed RHS {bumped:.3f} (identity itself 1.000)")

    result = {
        "population": {"universe": N_UNIVERSE, "depth3_primes": len(d3),
                       "even_sector_pairs": before_zero_delta,
                       "pairs_after_zero_delta": n,
                       "equals_We_sum": n == WE_SUM},
        "identity": {"holds": ok, "of": n,
                     "four_forms_equivalent": var_all_equal,
                     "four_forms_are_one_identity": True},
        "rhs_split": {"+1": rhs[1], "-1": rhs[-1]},
        "joint": {str(k): v for k, v in sorted(joint.items())},
        "marginals": {"(q/p)_4=+1": round(m_qp, 4), "(p/q)_4=+1": round(m_pq, 4)},
        "agreement_count": agree,
        "sign_choice_invariant": sign_inv,
        "applicability": {"cofactor_patterns_with_even_edge": with_even,
                          "cofactor_patterns_total": 64,
                          "hub_cofactor_edges_applicable": 0,
                          "hub_cofactor_edges_total": 4},
        "negative_controls": {"scrambled_pairing": round(shifted, 4),
                              "perturbed_rhs": round(bumped, 4)},
        "boundary": "identifies the even-sector quartic-bit agreement with the "
                    "sign of (ad-bc)/q; does NOT explain the +1 bias, the "
                    "ordered-joint asymmetry, or anything about the odd "
                    "hub-cofactor edges carrying sigma_x",
    }
    out = os.path.join(HERE, "_burde_pair_law.json")
    with open(out, "w") as fh:
        json.dump(result, fh, indent=2)
    log(f"\n  wrote {out}")
    log("  BOUNDARY — the identity holds and is non-vacuous. The bias in its "
        "right-hand side is unexplained and is the open question; the odd "
        "sector carrying σ_x is untouched.")


if __name__ == "__main__":
    main()
