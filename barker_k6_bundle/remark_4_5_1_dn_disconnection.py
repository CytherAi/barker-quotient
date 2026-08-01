#!/usr/bin/env python3
"""
remark_4_5_1_dn_disconnection.py — Verifies the six primes of S* are
mutually independent in the Borwein–Mossinghoff divisibility-and-Wieferich
graph D(N). This is the verification for Remark 4.5.1 of the manuscript.

Result: zero solid edges (Wieferich pairs), zero flimsy edges (p | r-1)
among the 30 ordered pairs. No D(N)-cycle can involve more than one
prime from S.
"""

S = [17881, 1801, 14537, 13417, 18121, 18521]

print("Remark 4.5.1 verification: D(N)-disconnection of S*")
print("=" * 60)

# Solid edges: q^{p-1} ≡ 1 (mod p^2)
print("\nSolid edge check (Wieferich pairs):")
solid = 0
for p in S:
    for q in S:
        if p == q:
            continue
        r = pow(q, p - 1, p * p)
        if r == 1:
            print(f"  SOLID EDGE: {q} → {p}")
            solid += 1
print(f"  Solid edges found: {solid}")

# Flimsy edges: p | (r-1)
print("\nFlimsy edge check (p | r-1):")
flimsy = 0
for r in S:
    for p in S:
        if r == p:
            continue
        if (r - 1) % p == 0:
            print(f"  FLIMSY EDGE: {r} ⇝ {p}")
            flimsy += 1
print(f"  Flimsy edges found: {flimsy}")

print(f"\nTotal D(N) edges among S: {solid + flimsy}")
if solid or flimsy:
    raise SystemExit(f"VERIFICATION FAILED: unexpected edge "
                     f"(solid={solid}, flimsy={flimsy})")
print("The six primes are completely disconnected in D(N).  ✓")
print("No D(N)-cycle can involve more than one prime from S.")
