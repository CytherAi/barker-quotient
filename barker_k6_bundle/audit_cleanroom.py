"""
CLEAN-ROOM AUDIT.

Re-implements every primitive from first principles, with NO import from
barker.*. Then runs every chi-value/parity/Wieferich claim of the paper
through the clean-room implementation, and cross-checks against the
library implementation.

If the library has a bug, clean-room ≠ library and the audit FAILS.
"""
from __future__ import annotations
import sys, os, time
from itertools import combinations

# Imports limited to stdlib for clean-room side
from math import gcd, comb

# Library side — only used for comparison, never to compute clean-room values
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "code"))
from barker.arithmetic import (
    is_prime as lib_is_prime,
    multiplicative_order as lib_mult_order,
)
from barker.two_primary import (
    quotient_class as lib_quotient_class,
    build_two_primary_table,
)
from barker.sweep import find_hard_primes as lib_find_hard_primes


# Clean-room primitives (no imports from barker.*)

def cr_is_prime(n: int) -> bool:
    """Deterministic Miller-Rabin for n < 318,665,857,834,031,151,167,461
    (≈ 3.19e23, the Sorenson–Webster bound ψ₁₂ for the first 12 prime
    witnesses 2..37; the previously claimed 3.3e24 is ψ₁₃ and requires
    witness 41). The paper's universe is far below either bound."""
    if n < 2:
        return False
    for p in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37):
        if n == p:
            return True
        if n % p == 0:
            return False
    # Write n-1 = 2^s * d with d odd
    d = n - 1
    s = 0
    while d % 2 == 0:
        d //= 2
        s += 1
    for a in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37):
        x = pow(a, d, n)
        if x == 1 or x == n - 1:
            continue
        for _ in range(s - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                break
        else:
            return False
    return True


def cr_prime_factors(n: int) -> list[int]:
    """Trial-division prime factorization (n small here — fine)."""
    factors: set[int] = set()
    d = 2
    while d * d <= n:
        while n % d == 0:
            factors.add(d)
            n //= d
        d += 1
    if n > 1:
        factors.add(n)
    return sorted(factors)


def cr_mult_order(a: int, n: int) -> int:
    """Multiplicative order of a mod n. Requires gcd(a,n)=1."""
    if gcd(a, n) != 1:
        raise ValueError("not coprime")
    # Compute φ(n) for n = x or n = x² with x prime
    # We only need this for n prime or n = prime². Compute φ generically:
    # For correctness, factor n.
    n_orig = n
    phi = 1
    n_work = n
    for p in cr_prime_factors(n):
        cnt = 0
        while n_work % p == 0:
            n_work //= p
            cnt += 1
        phi *= (p - 1) * p ** (cnt - 1)
    # Now order divides phi
    order = phi
    for q in cr_prime_factors(phi):
        while order % q == 0 and pow(a, order // q, n_orig) == 1:
            order //= q
    return order


def cr_primitive_root_mod_xsq(x: int) -> int:
    """Smallest primitive root mod x² (x odd prime)."""
    phi = x * (x - 1)            # φ(x²)
    x2 = x * x
    for g in range(2, x2):
        if gcd(g, x2) != 1:
            continue
        # g is a primitive root iff g^(phi/q) ≢ 1 mod x² for all prime q | phi
        ok = True
        for q in cr_prime_factors(phi):
            if pow(g, phi // q, x2) == 1:
                ok = False
                break
        if ok:
            return g
    raise RuntimeError(f"no primitive root found mod {x}^2")


def cr_v2(n: int) -> int:
    """2-adic valuation of n (n > 0)."""
    if n == 0:
        raise ValueError("v2(0) undefined")
    v = 0
    while n % 2 == 0:
        n //= 2
        v += 1
    return v


def cr_quotient_class(p: int, x: int) -> int:
    """
    χ_x(p) from first principles.

    Definition: image of p in (Z/x²Z)* / H_x where H_x is the unique
    odd-order subgroup. The quotient is cyclic of order 2^t where
    t = v_2(φ(x²)) = v_2(x-1).

    Construction:
      - Find a primitive root g of (Z/x²Z)*.
      - Let M = φ(x²) = x(x-1), t = v_2(M), m = M / 2^t (odd part).
      - s = g^m mod x² generates the Sylow 2-subgroup (order 2^t).
      - p^m mod x² lies in the Sylow 2-subgroup.
      - χ_x(p) = the unique k ∈ [0, 2^t) with s^k ≡ p^m (mod x²).

    Raises if p ≡ 0 (mod x) (not invertible mod x²).
    """
    if p % x == 0:
        raise ValueError(f"p={p} ≡ 0 (mod x={x}); not invertible mod x²")
    x2 = x * x
    M = x * (x - 1)
    t = cr_v2(M)
    m = M >> t
    g = cr_primitive_root_mod_xsq(x)
    s = pow(g, m, x2)
    pm = pow(p % x2, m, x2)
    power = 1
    for k in range(2 ** t):
        if power == pm:
            return k
        power = power * s % x2
    raise RuntimeError(f"discrete log not found: p={p}, x={x}")


CONFIG = (17881, 1801, 14537, 13417, 18121, 18521)
HUB = 17881
CYCLE = (1801, 14537, 13417, 18121, 18521)

results = []
def record(block, claim, cr_val, lib_val, expected, status):
    results.append((block, claim, cr_val, lib_val, expected, status))
    mark = "✓" if status == "PASS" else ("✗" if status == "FAIL" else "?")
    print(f"  [{mark}] {block} | {claim}")
    print(f"        clean-room={cr_val}  library={lib_val}  paper={expected}")

print("=" * 70)
print("CLEAN-ROOM AUDIT — independent reimplementation vs library")
print("=" * 70)

# A. Primality + hard-prime list
print("\n[A] Hard-prime list re-derivation...")
t0 = time.time()
cr_hard = []
for p in range(5, 80000):
    if not cr_is_prime(p) or p % 4 != 1:
        continue
    ord_p = cr_mult_order(2, p)
    if ord_p % 2 == 1:
        cr_hard.append(p)
cr_hard80 = cr_hard[:80]
print(f"  clean-room found {len(cr_hard)} hard primes in [5, 80000); first 80 in {time.time()-t0:.1f}s")

lib_hard_recs = lib_find_hard_primes(80000)
lib_hard80 = [r["prime"] for r in lib_hard_recs[:80]]

list_match = (cr_hard80 == lib_hard80)
record("A", "First 80 hard primes match library", cr_hard80[:3] + ["..."] + cr_hard80[-3:],
       lib_hard80[:3] + ["..."] + lib_hard80[-3:],
       "match", "PASS" if list_match else "FAIL")

# All 6 CONFIG primes appear in clean-room list
for p in CONFIG:
    in_cr = p in cr_hard80
    record("A", f"{p} in clean-room hard-80", in_cr, p in lib_hard80, True,
           "PASS" if in_cr else "FAIL")

# Library primality matches clean-room on the CONFIG
for p in CONFIG:
    record("A", f"is_prime({p})", cr_is_prime(p), lib_is_prime(p), True,
           "PASS" if cr_is_prime(p) == lib_is_prime(p) == True else "FAIL")

# Multiplicative order ord_p(2) for each
expected_orders = {17881: 2235, 1801: 25, 14537: 1817, 13417: 1677, 18121: 151, 18521: 2315}
for p in CONFIG:
    cr_o = cr_mult_order(2, p)
    lib_o = lib_mult_order(2, p)
    exp_o = expected_orders[p]
    status = "PASS" if cr_o == lib_o == exp_o else "FAIL"
    record("A", f"ord_p(2) for p={p}", cr_o, lib_o, exp_o, status)

# B. 5-cycle chi-values
print("\n[B] 5-cycle chi-values (clean-room vs library vs paper)...")
edges_expected = [
    (1801, 14537, 2),
    (14537, 13417, 4),
    (13417, 18121, 0),
    (18121, 18521, 0),
    (18521, 1801, 2),
]
for src, dst, paper in edges_expected:
    cr = cr_quotient_class(dst, src)
    lib = lib_quotient_class(dst, src)
    status = "PASS" if cr == lib == paper else "FAIL"
    record("B", f"chi_{src}({dst})", cr, lib, paper, status)

# C. V_x membership: chi_x(p) = 0 for each cycle prime
print("\n[C] V_{17881} membership (chi_x(p)=0)...")
for p in CYCLE:
    cr = cr_quotient_class(p, HUB)
    lib = lib_quotient_class(p, HUB)
    status = "PASS" if cr == lib == 0 else "FAIL"
    record("C", f"chi_17881({p}) = 0", cr, lib, 0, status)

# D. Degenerate condition: L(p) = -chi_p(x) = 0 for p in {13417, 18121}
print("\n[D] Degenerate condition L(p) = 0...")
# t at the hub is determined by hub, but L(p) uses 2^{t_p}
for p in (13417, 18121):
    cr_chi_p_hub = cr_quotient_class(HUB, p)
    lib_chi_p_hub = lib_quotient_class(HUB, p)
    status = "PASS" if cr_chi_p_hub == lib_chi_p_hub == 0 else "FAIL"
    record("D", f"chi_{p}(17881) [= 0 means L({p})=0]",
           cr_chi_p_hub, lib_chi_p_hub, 0, status)

# E. The "degenerate predecessor" claims from §4.5 S* witness table
print("\n[E] Structural-trace chi-values (§4.5 S* witness table)...")
for (src, dst, paper) in [(13417, 14537, 2), (18121, 13417, 2)]:
    cr = cr_quotient_class(dst, src)
    lib = lib_quotient_class(dst, src)
    status = "PASS" if cr == lib == paper else "FAIL"
    record("E", f"chi_{src}({dst}) = {paper}", cr, lib, paper, status)

# F. Mutual edge 4297 ↔ 18121 in G_{17881}
print("\n[F] Mutual edge 4297 ↔ 18121...")
# chi_{17881}(4297) = 0   (V_x membership for 4297)
# chi_{17881}(18121) = 0  (V_x membership for 18121)
# L(4297) = -chi_{4297}(17881) mod 2^{t_4297}
# L(18121) = -chi_{18121}(17881) mod 2^{t_18121}
# 4297 → 18121:  chi_{4297}(18121) = L(4297)
# 18121 → 4297:  chi_{18121}(4297) = L(18121)
cr_4297_hub  = cr_quotient_class(HUB, 4297)
lib_4297_hub = lib_quotient_class(HUB, 4297)
cr_18121_hub = cr_quotient_class(HUB, 18121)
lib_18121_hub= lib_quotient_class(HUB, 18121)
# depths
def cr_depth(x):
    return cr_v2(x - 1)
t_4297 = cr_depth(4297); t_18121 = cr_depth(18121)
cr_L_4297  = (-cr_4297_hub)  % (2 ** t_4297)
cr_L_18121 = (-cr_18121_hub) % (2 ** t_18121)
cr_chi_4297_18121  = cr_quotient_class(18121, 4297)
lib_chi_4297_18121 = lib_quotient_class(18121, 4297)
cr_chi_18121_4297  = cr_quotient_class(4297, 18121)
lib_chi_18121_4297 = lib_quotient_class(4297, 18121)
record("F", "4297 → 18121 (chi=L)",
       cr_chi_4297_18121 == cr_L_4297,
       lib_chi_4297_18121 == cr_L_4297,
       True,
       "PASS" if cr_chi_4297_18121 == cr_L_4297 == lib_chi_4297_18121 else "FAIL")
record("F", "18121 → 4297 (chi=L)",
       cr_chi_18121_4297 == cr_L_18121,
       lib_chi_18121_4297 == cr_L_18121,
       True,
       "PASS" if cr_chi_18121_4297 == cr_L_18121 == lib_chi_18121_4297 else "FAIL")

# G. V_{17881} list (size 11)
print("\n[G] |V_{17881}| (clean-room)...")
cr_V = []
for p in cr_hard80:
    if p == HUB:
        continue
    if cr_quotient_class(p, HUB) == 0:
        cr_V.append(p)
record("G", "|V_17881|", len(cr_V), 11, 11, "PASS" if len(cr_V) == 11 else "FAIL")

# H_18121 ∩ V_17881 = {4297, 18521}
cr_H_18121 = set(q for q in cr_V if q != 18121 and cr_quotient_class(q, 18121) == 0)
record("G", "H_18121 ∩ V_17881",
       cr_H_18121, {4297, 18521}, {4297, 18521},
       "PASS" if cr_H_18121 == {4297, 18521} else "FAIL")

# H. Coverage of all 15 pairs in CONFIG (clean-room)
print("\n[H] Coverage check (all 15 pairs, clean-room)...")
def cr_pair_bad_at(a, b, x):
    """chi_x(a) + chi_x(b) ≡ 0 mod 2^{t_x}?"""
    if x == a or x == b:
        return False
    t_x = cr_v2(x - 1)
    return (cr_quotient_class(a, x) + cr_quotient_class(b, x)) % (2 ** t_x) == 0

uncovered = []
for a, b in combinations(CONFIG, 2):
    if not any(cr_pair_bad_at(a, b, x) for x in CONFIG):
        uncovered.append((a, b))
record("H", "All 15 pairs covered (clean-room)",
       len(uncovered), 0, 0, "PASS" if not uncovered else "FAIL")

def cr_is_covering(sub):
    """True iff every pair in sub has a witness inside sub (clean-room)."""
    return all(any(cr_pair_bad_at(a, b, x) for x in sub)
               for a, b in combinations(sub, 2))


# Sole-witness structure: removing each cycle prime leaves exactly one
# uncovered pair.  This is a description of the configuration, NOT a minimality
# certificate — see the exhaustive scan below.
sole_witness = {
    1801:  frozenset({HUB, 14537}),
    14537: frozenset({HUB, 13417}),
    13417: frozenset({HUB, 18121}),
    18121: frozenset({HUB, 18521}),
    18521: frozenset({HUB, 1801}),
}
for removed in CYCLE:
    sub = tuple(p for p in CONFIG if p != removed)
    sub_uncov = []
    for a, b in combinations(sub, 2):
        if not any(cr_pair_bad_at(a, b, x) for x in sub):
            sub_uncov.append(frozenset({a, b}))
    status = "PASS" if (len(sub_uncov) == 1 and sub_uncov[0] == sole_witness[removed]) else "FAIL"
    record("H", f"Remove {removed} → sole uncovered = {set(sole_witness[removed])}",
           [set(u) for u in sub_uncov], "—", [set(sole_witness[removed])], status)

# Remove hub → 6 uncovered pairs
sub_no_hub = CYCLE
sub_uncov = []
for a, b in combinations(sub_no_hub, 2):
    if not any(cr_pair_bad_at(a, b, x) for x in sub_no_hub):
        sub_uncov.append(frozenset({a, b}))
record("H", f"Remove hub → 6 uncovered pairs",
       len(sub_uncov), "—", 6, "PASS" if len(sub_uncov) == 6 else "FAIL")

# Exhaustive minimality (clean-room).  Coverage is not monotone under deletion,
# so the single deletions above do not certify minimality: in this same universe
# (73, 233, 1721, 4057, 18121) is covering with all five of its 4-subsets
# non-covering, yet (73, 233, 1721) is covering.  Subsets of size ≤ 2 can never
# cover (a pair needs a witness outside itself), so the scan starts at size 3.
cr_proper = [sub for r in range(3, len(CONFIG)) for sub in combinations(CONFIG, r)]
cr_covering_proper = [sub for sub in cr_proper if cr_is_covering(sub)]
record("H", f"No proper subset of size 3–5 is covering (clean-room, {len(cr_proper)} checked)",
       len(cr_covering_proper), "—", 0,
       "PASS" if not cr_covering_proper else "FAIL")

CR_NONMONO = (73, 233, 1721, 4057, 18121)
cr_nm_ok = (
    cr_is_covering(CR_NONMONO)
    and not any(cr_is_covering(tuple(p for p in CR_NONMONO if p != s)) for s in CR_NONMONO)
    and cr_is_covering((73, 233, 1721))
)
record("H", f"Non-monotonicity witness {CR_NONMONO}: one-deletion test is unsound",
       cr_nm_ok, "—", True, "PASS" if cr_nm_ok else "FAIL")

# I. Parity symmetry: 0 violations on first 80 hard primes (clean-room)
print("\n[I] Parity symmetry (clean-room, all 3160 pairs)...")
violations_cr = 0
violations_lib = 0
for p, q in combinations(cr_hard80, 2):
    cr_pq = cr_quotient_class(q, p)
    cr_qp = cr_quotient_class(p, q)
    lib_pq = lib_quotient_class(q, p)
    lib_qp = lib_quotient_class(p, q)
    if (cr_pq % 2) != (cr_qp % 2):
        violations_cr += 1
    if (lib_pq % 2) != (lib_qp % 2):
        violations_lib += 1
record("I", "Parity violations (3160 pairs)",
       violations_cr, violations_lib, 0,
       "PASS" if violations_cr == violations_lib == 0 else "FAIL")

# J. Wieferich + flimsy edges among 30 ordered pairs of CONFIG (clean-room)
print("\n[J] Wieferich/flimsy edges in CONFIG...")
n_wieferich = 0
n_flimsy = 0
for q, p in [(a, b) for a in CONFIG for b in CONFIG if a != b]:
    # Solid edge q → p iff q^(p-1) ≡ 1 (mod p²)
    if pow(q, p - 1, p * p) == 1:
        n_wieferich += 1
    # Flimsy edge r ⇝ p iff p | (r - 1)
    if (q - 1) % p == 0:
        n_flimsy += 1
record("J", "Wieferich pairs (30 ordered)", n_wieferich, "—", 0,
       "PASS" if n_wieferich == 0 else "FAIL")
record("J", "Flimsy edges (30 ordered)", n_flimsy, "—", 0,
       "PASS" if n_flimsy == 0 else "FAIL")

# K. Spot-check: bulk chi-value comparison clean-room vs library
print("\n[K] Bulk chi-value comparison (clean-room vs library) on all pairs in HARD80...")
n_compared = 0
n_diff = 0
mismatches = []
for p in cr_hard80:
    for x in cr_hard80:
        if p == x:
            continue
        cr_v = cr_quotient_class(p, x)
        lib_v = lib_quotient_class(p, x)
        n_compared += 1
        if cr_v != lib_v:
            n_diff += 1
            if len(mismatches) < 5:
                mismatches.append((p, x, cr_v, lib_v))
record("K", f"Bulk chi: {n_compared} comparisons, divergences",
       n_diff, n_diff, 0,
       "PASS" if n_diff == 0 else "FAIL")
if mismatches:
    print("    sample mismatches:", mismatches)

# -----------------------------------------------------------------------
# Summary
# -----------------------------------------------------------------------
print("\n" + "=" * 70)
print("CLEAN-ROOM AUDIT RESULTS")
print("=" * 70)
n_pass = sum(1 for r in results if r[5] == "PASS")
n_fail = sum(1 for r in results if r[5] == "FAIL")
print(f"Total checks: {len(results)}  PASS: {n_pass}  FAIL: {n_fail}")
if n_fail > 0:
    print("\nFAILURES:")
    for r in results:
        if r[5] == "FAIL":
            print(f"  [{r[0]}] {r[1]}: cr={r[2]} lib={r[3]} paper={r[4]}")
print("=" * 70)
sys.exit(0 if n_fail == 0 else 1)
