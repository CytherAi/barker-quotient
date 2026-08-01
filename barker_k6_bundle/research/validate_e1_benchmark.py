#!/usr/bin/env python3
"""
validate_e1_benchmark.py — gate (b): validate the mixed-depth E1 model in the
(3,3,3,4) regime BEFORE the larger-N enumeration (a) measures against it.

Three checks:
  (1) Within-cell faithfulness: does the model reproduce the empirical QNR
      fraction and w-distribution of depth-3-hub (3,3,3,4) targets?
  (2) Cell occupancy / depletion: does the model reproduce the conditioning-
      induced depletion of the (3,3,3,4) profile relative to (3,3,3,3)?
      depletion factor = P(survive | profile) / P(survive | (3,3,3,3,3));
      model gives this as the ratio of fixed-profile acceptances.
  (3) Bookkeeping reconciliation: the pooled all-QNR-w2 σ=0 rate (262/1032 at
      N=160) must equal the cell-weighted sum of the stratified per-profile
      rates. If it doesn't, that's a set/incidence-style census conflation.
"""
from __future__ import annotations
import sys, os, json, glob
import numpy as np
from itertools import combinations
from math import comb

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "code"))
from barker.two_primary import build_two_primary_table
from barker.arithmetic import is_prime, multiplicative_order

def hardN(n):
    out=[]; p=5
    while len(out)<n:
        if is_prime(p) and p%4==1 and multiplicative_order(2,p)%2==1: out.append(p)
        p+=2
    return out

primes = hardN(160)
table = build_two_primary_table(primes)
zd5 = [tuple(s) for s in json.load(open(os.path.join(os.path.dirname(__file__), "_per_depth_w2_cache_N160.json")))]

def wval(C, x):
    return sum(1 for a,b in combinations(C,2) if (table.chi[(a,x)]+table.chi[(b,x)])%8==0)

# ---------------------------------------------------------------------------
print("="*70)
print("(1) WITHIN-CELL FAITHFULNESS at (3,3,3,4): model vs empirical")
print("="*70)

# empirical: depth-3 hub, cofactor depth profile (3,3,3,4)
emp_qnr_n=emp_qnr_tot=0; emp_w={}
for S in zd5:
    for x in S:
        if table.depth[x]!=3: continue
        C=[p for p in S if p!=x]
        if tuple(sorted(table.depth[p] for p in C))!=(3,3,3,4): continue
        vals=[table.chi[(p,x)] for p in C]
        for v in vals:
            emp_qnr_tot+=1; emp_qnr_n+=(v%2==1)
        w=wval(C,x); emp_w[w]=emp_w.get(w,0)+1
emp_wt=sum(emp_w.values())

# model: profile-B survivors (global depths {3,3,3,3,4}); depth-3 hubs -> (3,3,3,4) cofactor
Bfiles=sorted(glob.glob(os.path.join(os.path.dirname(__file__),"_e1mix_B_s*.npz")))
Ms=[np.load(f) for f in Bfiles]
M=np.concatenate([d["M"] for d in Ms]); t=np.concatenate([d["t"] for d in Ms])
mod_qnr_n=mod_qnr_tot=0; mod_w={}
for r in range(M.shape[0]):
    for x in range(5):
        if t[r,x]!=3: continue
        cof=[p for p in range(5) if p!=x]
        if tuple(sorted(int(t[r,p]) for p in cof))!=(3,3,3,4): continue
        vals=M[r,x,cof]%8
        for v in vals:
            mod_qnr_tot+=1; mod_qnr_n+=int(v%2==1)
        w=int(sum(1 for a in range(4) for b in range(a+1,4) if (vals[a]+vals[b])%8==0))
        mod_w[w]=mod_w.get(w,0)+1
mod_wt=sum(mod_w.values())

print(f"  QNR fraction:  model {mod_qnr_n/mod_qnr_tot:.3f} (n={mod_qnr_tot})   "
      f"empirical {emp_qnr_n/emp_qnr_tot:.3f} (n={emp_qnr_tot})")
print(f"  w-distribution (model vs empirical):")
for w in sorted(set(mod_w)|set(emp_w)):
    print(f"    w={w}:  model {mod_w.get(w,0)/mod_wt:.3f}   empirical {emp_w.get(w,0)/emp_wt:.3f}")

# ---------------------------------------------------------------------------
print("\n"+"="*70)
print("(2) CELL OCCUPANCY / DEPLETION: model vs empirical")
print("="*70)
# model acceptances (from run logs): pool all-depth-3 + profile-B
acc_333 = (131+2912)/(1e8+2.1e9)          # {3,3,3,3,3}
acc_3334 = 737/1.25e9                       # {3,3,3,3,4}
model_depletion = acc_3334/acc_333
print(f"  model acceptance  (3,3,3,3,3) = {acc_333:.3e}")
print(f"  model acceptance  (3,3,3,3,4) = {acc_3334:.3e}")
print(f"  model depletion factor P(MC|3334)/P(MC|33333) = {model_depletion:.3f}")

# empirical depletion factor: [#emp{3,3,3,3,4}/#cand{3,3,3,3,4}] / [#emp{33333}/#cand{33333}]
n3 = sum(1 for p in primes if table.depth[p]==3)
n4 = sum(1 for p in primes if table.depth[p]==4)
emp_33333 = sum(1 for S in zd5 if sorted(table.depth[p] for p in S)==[3,3,3,3,3])
emp_33334 = sum(1 for S in zd5 if sorted(table.depth[p] for p in S)==[3,3,3,3,4])
cand_33333 = comb(n3,5)
cand_33334 = comb(n3,4)*n4
emp_depletion = (emp_33334/cand_33334)/(emp_33333/cand_33333)
print(f"  universe N=160: n3={n3}, n4={n4}")
print(f"  empirical zero-δ MC counts: (3,3,3,3,3)={emp_33333}  (3,3,3,3,4)={emp_33334}")
print(f"  empirical depletion factor = {emp_depletion:.3f}")
print(f"  -> {'MATCH' if abs(model_depletion-emp_depletion)<0.15 else 'MISMATCH'} "
      f"(model {model_depletion:.3f} vs empirical {emp_depletion:.3f})")

# ---------------------------------------------------------------------------
print("\n"+"="*70)
print("(3) BOOKKEEPING RECONCILIATION: pooled vs stratified all-QNR-w2 σ=0")
print("="*70)
strat={}
pooled_s0=pooled_n=0
for S in zd5:
    for x in S:
        if table.depth[x]!=3: continue
        C=[p for p in S if p!=x]
        vals=[table.chi[(p,x)] for p in C]
        if not all(v%2==1 for v in vals): continue
        if wval(C,x)!=2: continue
        prof=tuple(sorted(table.depth[p] for p in C))
        d=strat.setdefault(prof,[0,0]); d[1]+=1
        pooled_n+=1
        if sum(vals)%8==0: d[0]+=1; pooled_s0+=1
print(f"  pooled all-QNR-w2 σ=0 (N=160) = {pooled_s0}/{pooled_n} = {pooled_s0/pooled_n:.4f}")
print(f"  (reaudit reference: 262/1032 = 0.2539)")
print(f"  stratified by cofactor depth profile:")
ssum_s0=ssum_n=0
for prof in sorted(strat, key=lambda p:(sum(p),p)):
    s0,n=strat[prof]; ssum_s0+=s0; ssum_n+=n
    print(f"    {str(prof):>14}: {s0:>4}/{n:<4} = {s0/n:.3f}  (weight {n/pooled_n:.3f})")
print(f"  Σ stratified = {ssum_s0}/{ssum_n}  (must equal pooled {pooled_s0}/{pooled_n})")
print(f"  -> {'RECONCILES' if (ssum_s0,ssum_n)==(pooled_s0,pooled_n) else 'CONFLATION #4'}")
