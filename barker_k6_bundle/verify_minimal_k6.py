#!/usr/bin/env python3
"""
verify_minimal_k6.py  —  Standalone verification of the minimal k=6 configuration.
{17881, 1801, 14537, 13417, 18121, 18521}  is a minimal covering set of hard primes.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "code"))
from barker.two_primary import build_two_primary_table, quotient_class
from barker.sweep import find_hard_primes
from itertools import combinations

print("Building 2-primary character table (first 80 hard primes)…")
hard80 = [h["prime"] for h in find_hard_primes(80000)][:80]
tbl    = build_two_primary_table(hard80)

CONFIG = (17881, 1801, 14537, 13417, 18121, 18521)
HUB, CYCLE = 17881, (1801, 14537, 13417, 18121, 18521)
x = HUB


def check(cond, msg):
    """assert that survives python -O: verification must fail closed."""
    if not cond:
        raise SystemExit(f"VERIFICATION FAILED: {msg}")

def covered_by(a, b, S):
    for c in S:
        if c in (a, b): continue
        t = tbl.depth[c]
        if (quotient_class(a, c) + quotient_class(b, c)) % (2**t) == 0:
            return c
    return None

def is_covering(S):
    return all(covered_by(a, b, S) is not None for a, b in combinations(S, 2))

# 1. Hard primes
print("\n[1] Hard-prime status")
prime_set = set(hard80)
for p in CONFIG:
    check(p in prime_set, f"{p} not a hard prime"); t = tbl.depth[p]; check(t >= 3, f"{p} depth {t} < 3")
    print(f"    {p}: depth={t}  ✓")

# 2. V_x membership
print("\n[2] V_{17881} membership  (chi_{17881}(p) = 0)")
for p in CYCLE:
    chi = quotient_class(p, x); check(chi == 0, f"chi_{x}({p}) = {chi} != 0")
    print(f"    chi_{x}({p}) = {chi}  ✓")

# 3. Directed 5-cycle
print("\n[3] Directed 5-cycle in G_{17881}")
vx    = [p for p in hard80 if p != x and quotient_class(p, x) == 0]
L_map = {p: (-quotient_class(x, p)) % (2**tbl.depth[p]) for p in vx}
for i in range(5):
    pi, pj = CYCLE[i], CYCLE[(i+1) % 5]
    chi, L = quotient_class(pj, pi), L_map[pi]
    check(chi == L, f"cycle edge {pi} -> {pj}: chi={chi} != L={L}")
    dg = " (degenerate)" if quotient_class(x, pi) == 0 else ""
    print(f"    {pi} → {pj}: chi={chi} = L={L}  ✓{dg}")

# 4. Covering
print("\n[4] All 15 pairs covered")
for a, b in combinations(CONFIG, 2):
    w = covered_by(a, b, CONFIG); check(w is not None, f"pair ({a},{b}) uncovered")
print("    All 15 pairs covered  ✓")

# 5. Minimality
#
# Coverage is NOT monotone under deletion, so the single-element deletions do
# not certify minimality.  Counterexample in this same universe:
#
#     S = (73, 233, 1721, 4057, 18121)   is covering
#     all five 4-element subsets of S    are non-covering
#     (73, 233, 1721) ⊂ S                is covering
#
# Minimality therefore requires every proper subset to be tested.  Subsets of
# size ≤ 2 are never covering (a pair needs a witness outside itself), so the
# scan starts at size 3.
print("\n[5] No proper subset is covering")
n_checked = 0
for r in range(3, len(CONFIG)):
    for sub in combinations(CONFIG, r):
        n_checked += 1
        check(not is_covering(sub), f"Proper subset {sub} is covering!")
    print(f"    all C(6,{r}) = {len(list(combinations(CONFIG, r)))} subsets of size {r}: none covering  ✓")
print(f"    {n_checked} proper subsets checked exhaustively  ✓")

print("\n" + "="*56)
print("VERIFICATION COMPLETE")
print(f"Config:  {CONFIG}")
print("Result:  MINIMAL k=6 COVERING SET  ✓")
print("="*56)
