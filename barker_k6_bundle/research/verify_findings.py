#!/usr/bin/env python3
"""
verify_findings.py — independent re-derivation of the three cheap "single
picture" findings (N1, N3, N4) before any of the E-experiments are built on
top of them.  Each is checked from scratch against the library primitives and
the canonical enumeration cache; nothing is inherited from the analysis note
that proposed them.

Findings under test:
  (N1) The mod-x² apparatus is redundant: χ_x (built on the Sylow-2 quotient of
       (Z/x²Z)*) factors through (Z/xZ)*.  Tested two ways — (a) the reduction
       kernel ker((Z/x²Z)* → (Z/xZ)*) is cyclic of odd order x, so a character
       into a 2-group kills it; (b) χ_x is constant on kernel cosets, i.e.
       χ_x(p) = χ_x(p + x) = χ_x(p + 2x) for every ordered (p, x).
  (N3) Legendre polarization: every one of the 68 A1 k=3 configurations is
       totally mutually quadratic-residue — all three unordered Legendre
       symbols are +1.
  (N4) Hasse-baseline claims: (a) the density of primes with ord_p(2) odd, and
       the density of the *hard* primes (ord odd AND p ≡ 1 mod 4); the note
       claims 7/24 for the hard primes — we check whether that is the ord-odd
       density and whether the hard density is the halved 7/48 instead.
       (b) the depth composition of the first 80 hard primes against the
       proposed law P(t=j | hard) = (3/4)·4^{-(j-3)}.
"""
from __future__ import annotations
import sys, os, json
from itertools import combinations

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "code"))
from barker.arithmetic import multiplicative_order, is_prime, jacobi_symbol
from barker.two_primary import (
    two_primary_depth, quotient_class, legendre_layer, build_two_primary_table,
)
from barker.sweep import find_hard_primes

CACHE = os.path.join(os.path.dirname(__file__), "_enumeration_cache.json")

fails = 0
def check(name, ok, detail=""):
    global fails
    mark = "PASS" if ok else "FAIL"
    if not ok:
        fails += 1
    print(f"  [{mark}] {name}" + (f"  ({detail})" if detail else ""))

HARD80 = [r["prime"] for r in find_hard_primes(80000)[:80]]

# ---------------------------------------------------------------------------
print("\n[N1] χ_x factors through (Z/xZ)* — the mod-x² apparatus is redundant")
# (a) reduction kernel is cyclic of odd order x
kernel_ok = True
for x in HARD80:
    # 1 + x generates ker((Z/x²Z)* -> (Z/xZ)*); that kernel has order x.
    if multiplicative_order(1 + x, x * x) != x or x % 2 == 0:
        kernel_ok = False
        break
check("reduction kernel ≅ C_x has odd order x (so a 2-group character kills it)",
      kernel_ok, "checked all 80 hubs")

# (b) χ_x constant on kernel cosets: χ_x(p) = χ_x(p+x) = χ_x(p+2x)
coset_mismatches = 0
coset_tests = 0
for x in HARD80:
    for p in HARD80:
        if p == x:
            continue
        base = quotient_class(p, x)
        for j in (1, 2):
            coset_tests += 1
            if quotient_class(p + j * x, x) != base:
                coset_mismatches += 1
check("χ_x(p) = χ_x(p+x) = χ_x(p+2x) over all ordered (p,x)",
      coset_mismatches == 0, f"{coset_tests} tests, {coset_mismatches} mismatches")

# ---------------------------------------------------------------------------
print("\n[N3] Legendre polarization — all 68 A1 k=3 configs are totally mutual-QR")
cache = json.load(open(CACHE))
a1_triples = [r[3] for r in cache if r[0] == 3 and r[1] == "A1"]
check("cache yields 68 A1 k=3 configurations", len(a1_triples) == 68,
      f"{len(a1_triples)} found")
not_all_plus = []
for trip in a1_triples:
    a, b, c = trip
    syms = [jacobi_symbol(p % q, q) for p, q in [(a, b), (b, a), (a, c),
                                                 (c, a), (b, c), (c, b)]]
    if any(s != 1 for s in syms):
        not_all_plus.append((trip, syms))
check("every A1 triple has all six ordered Legendre symbols = +1",
      not_all_plus == [], f"{len(a1_triples) - len(not_all_plus)}/68 all-+1")
if not_all_plus:
    for trip, syms in not_all_plus[:5]:
        print(f"      counterexample {trip}: symbols {syms}")

# ---------------------------------------------------------------------------
print("\n[N4] Hasse-baseline density and depth composition")
# (a) densities: ord-odd vs hard, against 7/24 and 7/48
BOUND = 200000
n_primes = 0
n_ord_odd = 0
n_hard = 0
n = 2
# iterate primes up to BOUND
candidate = 2
while candidate < BOUND:
    if is_prime(candidate):
        n_primes += 1
        if candidate > 2:
            o = multiplicative_order(2, candidate)
            if o % 2 == 1:
                n_ord_odd += 1
                if candidate % 4 == 1:
                    n_hard += 1
    candidate += 1
dens_ord_odd = n_ord_odd / n_primes
dens_hard = n_hard / n_primes
print(f"      primes < {BOUND}: {n_primes}")
print(f"      ord_p(2) odd: {n_ord_odd}  density {dens_ord_odd:.4f}   (7/24 = {7/24:.4f})")
print(f"      hard (ord odd & p≡1 mod4): {n_hard}  density {dens_hard:.4f}   "
      f"(7/48 = {7/48:.4f}, 7/24 = {7/24:.4f})")
check("ord-odd density ≈ 7/24 (Hasse 1966 — the citable theorem)",
      abs(dens_ord_odd - 7/24) < 0.01,
      f"{dens_ord_odd:.4f} vs {7/24:.4f}")
# The note claims 7/24 IS the hard-prime density. It is not: hardness adds
# p ≡ 1 mod 8 (depth ≥ 3) on top of ord-odd, and the depth law 2^{-t}
# suppresses it by an order of magnitude. Disconfirm the conflation.
check("hard density is NOT 7/24 (the note's conflation) — it is ~1/24",
      abs(dens_hard - 7/24) > 0.20 and abs(dens_hard - 1/24) < 0.01,
      f"hard={dens_hard:.4f} ≈ 1/24={1/24:.4f}, far below ord-odd 7/24={7/24:.4f}")
print(f"      → only {n_hard}/{n_ord_odd} = {n_hard/n_ord_odd:.1%} of ord-odd "
      f"primes are p≡1 mod4 (NOT ~50%): the depth law's 2^{{-t}} skew, not equidistribution")

# (b) depth composition of HARD80 vs (3/4)·4^{-(j-3)}
obs = {3: 0, 4: 0, 5: 0, 6: 0}
for x in HARD80:
    t = two_primary_depth(x)
    obs[t] = obs.get(t, 0) + 1
pred = {j: 0.75 * 4 ** (-(j - 3)) * 80 for j in (3, 4, 5, 6)}
print("      depth | observed | predicted (3/4)·4^{-(j-3)}·80")
chi2 = 0.0
for j in (3, 4, 5, 6):
    print(f"        t={j} | {obs.get(j,0):>8} | {pred[j]:>8.2f}")
    if pred[j] > 0:
        chi2 += (obs.get(j, 0) - pred[j]) ** 2 / pred[j]
print(f"      χ² (3 df) = {chi2:.2f}   observed composition = "
      f"{obs[3]}/{obs[4]}/{obs[5]}/{obs[6]}")
check("depth composition consistent with law (χ² < 7.81, p>0.05, 3 df)",
      chi2 < 7.81, f"χ²={chi2:.2f}")

print(f"\n{'='*60}\nverify_findings: {'ALL PASS' if fails==0 else str(fails)+' FAIL'}\n{'='*60}")
sys.exit(1 if fails else 0)
