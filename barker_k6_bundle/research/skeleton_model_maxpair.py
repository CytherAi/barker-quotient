#!/usr/bin/env python3
"""
skeleton_model_maxpair.py — the maximal-pairwise model (the last experiment).

Same {covering, minimal, zero-δ} conditioning and (3,3,3,3,4) profile as
skeleton_model_e1_mixed.py, but the higher digits of the six depth-3 pairs are
drawn JOINTLY from the measured universe (3,3) joints (even sector and odd
sector, full support incl 0) instead of independent-uniform. The four (3,4) pairs
(vertex 4 = depth-4) are drawn independently — the measured (3,4) joint is flat.

Reading, and its limits. If R moves from the skeleton value toward the observed
0.250, that is consistent with the gap being pairwise (the (3,3) universe law the
skeleton lacked). If it stalls above 0.250, the residual is what THIS pairwise
construction fails to absorb.

That residual is NOT a certificate of irreducible higher-order dependence, and
must not be reported as one. Three reasons, each sufficient on its own:

  * This model is one pairwise construction, not the best one. It injects the
    measured (3,3) joints only, and draws the four (3,4) pairs independently on
    the grounds that the measured (3,4) joint is flat. A pairwise model that
    also carried the (3,4) and higher-depth joints is not explored here, so
    "no pairwise model can absorb the gap" is not a conclusion this experiment
    can reach.
  * The joints are measured on, and the residual evaluated against, overlapping
    data. Nothing is held out, so the fit is not calibrated.
  * The conditioning {covering, minimal, zero-δ} is applied downstream of a
    universe-pair draw, while the measured joints come from a differently
    conditioned population (see the population-trap note in the
    preregistration). Injecting a pair-joint measured on one population into a
    sampler that conditions on another double-counts the conditioning.

Report the residual as the miss of this specific construction, with its size and
the counts behind it, and nothing stronger.

Vertices 0..3 are depth-3, vertex 4 is depth-4. Pairs:
  (3,3): the 6 pairs within {0,1,2,3} — drawn from the measured joints.
  (3,4): the 4 pairs {i,4} — drawn independently (skeleton way).
"""
from __future__ import annotations
import sys, glob
import numpy as np
from itertools import combinations

import os
# Resolve the library relative to THIS file: the script is documented to be
# run from the repository root, where a bare "code" does not exist.
sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "code"))
PAIRS33 = [(i, j) for i in range(4) for j in range(i + 1, 4)]
PAIRS34 = [(i, 4) for i in range(4)]
SUBSETS = [tuple(s) for s in combinations(range(5), 3)] + [tuple(s) for s in combinations(range(5), 4)]
EVEN = [0, 2, 4, 6]; ODD = [1, 3, 5, 7]


def measure_joints(N=320):
    from barker.two_primary import build_two_primary_table
    from barker.arithmetic import is_prime, multiplicative_order, jacobi_symbol
    def hardN(n):
        out=[]; p=5
        while len(out)<n:
            if is_prime(p) and p%4==1 and multiplicative_order(2,p)%2==1: out.append(p)
            p+=2
        return out
    primes=hardN(N); table=build_two_primary_table(primes)
    dep=lambda p: table.depth[p]; chi=lambda hub,arg: table.chi[(arg,hub)]
    Jeven=np.zeros((4,4)); Jodd=np.zeros((4,4)); ie={v:k for k,v in enumerate(EVEN)}; io={v:k for k,v in enumerate(ODD)}
    n_even=n_odd=0
    for a,b in combinations(primes,2):
        if dep(a)!=3 or dep(b)!=3: continue
        if a>b: a,b=b,a
        sec=jacobi_symbol(a%b,b)
        va=chi(a,b)%8; vb=chi(b,a)%8
        if sec==1: Jeven[ie[va],ie[vb]]+=1; n_even+=1
        else:      Jodd[io[va],io[vb]]+=1; n_odd+=1
    Jeven/=Jeven.sum(); Jodd/=Jodd.sum()
    p_even=n_even/(n_even+n_odd)
    return Jeven, Jodd, p_even


def generate(B, rng, Jeven, Jodd, p_even):
    M=np.zeros((B,5,5),dtype=np.int64)
    ev_flat=Jeven.ravel(); od_flat=Jodd.ravel()
    ev_pairs=[(EVEN[k//4],EVEN[k%4]) for k in range(16)]
    od_pairs=[(ODD[k//4],ODD[k%4]) for k in range(16)]
    EVarr=np.array(ev_pairs); ODarr=np.array(od_pairs)
    for (i,j) in PAIRS33:
        is_even=rng.random(B)<p_even
        idx_e=rng.choice(16,size=B,p=ev_flat); idx_o=rng.choice(16,size=B,p=od_flat)
        vi=np.where(is_even,EVarr[idx_e,0],ODarr[idx_o,0])
        vj=np.where(is_even,EVarr[idx_e,1],ODarr[idx_o,1])
        M[:,i,j]=vi; M[:,j,i]=vj
    for (i,j) in PAIRS34:   # i depth-3 (mod8), j=4 depth-4 (mod16), shared parity
        b=rng.integers(0,2,B)
        M[:,i,j]=2*rng.integers(0,4,B)+b          # chi_i(j) mod 8
        M[:,j,i]=2*rng.integers(0,8,B)+b          # chi_j(i) mod 16
    mod=np.array([8,8,8,8,16],dtype=np.int64)
    return M, np.broadcast_to(mod,(B,5)).copy()


def pair_wit(M,mod,members,i,j):
    out=np.zeros(M.shape[0],dtype=bool)
    for k in members:
        if k in (i,j): continue
        out|=((M[:,k,i]+M[:,k,j])%mod[:,k]==0)
    return out
def is_cov(M,mod,members):
    members=list(members); ok=np.ones(M.shape[0],dtype=bool)
    for a in range(len(members)):
        for b in range(a+1,len(members)):
            ok&=pair_wit(M,mod,members,members[a],members[b])
            if not ok.any(): return ok
    return ok
def keep(M,mod):
    mask=np.ones(M.shape[0],dtype=bool)
    for i in range(5):
        for j in range(5):
            if i!=j: mask&=(M[:,i,j]!=0)
    if not mask.any(): return mask
    mask&=is_cov(M,mod,range(5))
    if not mask.any(): return mask
    for T in SUBSETS:
        mask&=~is_cov(M,mod,T)
        if not mask.any(): return mask
    return mask


def sample(total,batch,seed,outfile):
    rng=np.random.default_rng(seed)
    Jeven,Jodd,p_even=measure_joints()
    keptM=[]; n_tr=n_kept=0
    while n_tr<total:
        B=min(batch,total-n_tr)
        M,mod=generate(B,rng,Jeven,Jodd,p_even)
        m=keep(M,mod)
        if m.any(): keptM.append(M[m]); n_kept+=int(m.sum())
        n_tr+=B
    M=np.concatenate(keptM) if keptM else np.zeros((0,5,5),np.int64)
    np.savez(outfile,M=M)
    print(f"  seed={seed} trials={n_tr:,} kept={n_kept:,} acc={n_kept/n_tr:.2e} -> {outfile}.npz")


def cell_matrix(M):
    """(targets, successes) as (n_survivors, 4) boolean arrays.

    Entry [r, x] is depth-3 hub x of survivor r: a target when its cofactor is
    all-QNR with w = 2, a success when σ = 0 as well. Rows are the resampling
    cluster; the four columns are the hubs the estimand pools. Vertex labels
    are the primes in increasing order, so column x is hub size-rank x — and
    the columns are NOT exchangeable, because the injected joint is indexed by
    prime order and is not symmetric.
    """
    tgt=np.zeros((M.shape[0],4),bool); suc=np.zeros((M.shape[0],4),bool)
    for r in range(M.shape[0]):
        for x in range(4):
            cof=[p for p in range(5) if p!=x]   # 3 depth-3 + p4 = (3,3,3,4)
            vals=[int(M[r,x,p]%8) for p in cof]
            if not all(v%2==1 for v in vals): continue
            if sum(1 for a,b in combinations(range(4),2) if (vals[a]+vals[b])%8==0)!=2: continue
            tgt[r,x]=True; suc[r,x]=sum(vals)%8==0
    return tgt,suc


def measure(files):
    M=np.concatenate([np.load(f)["M"] for f in files])
    print(f"  loaded {M.shape[0]:,} survivors")
    # (3,3,3,4) all-QNR w=2 cell, R and p4-witness strata.  vertex 4 = depth-4.
    tgt,suc=cell_matrix(M); s0=int(suc.sum()); n=int(tgt.sum()); strat={}
    for r in range(M.shape[0]):
        if not tgt[r].any(): continue
        wc4=sum(1 for a,b in combinations(range(4),2) if (int(M[r,4,a])+int(M[r,4,b]))%16==0)
        d=strat.setdefault(wc4,[0,0]); d[0]+=int(suc[r].sum()); d[1]+=int(tgt[r].sum())
    R=s0/n if n else 0
    print(f"  maximal-pairwise R(3,3,3,4) = {R:.4f}  (n={n})   [skeleton 0.266, empirical 0.250]")
    for k in sorted(strat):
        kk,nn=strat[k]; print(f"    p4-witness={k}: {kk}/{nn} = {kk/nn:.3f}")
    return {"survivors": int(M.shape[0]), "successes": s0, "targets": n,
            "R": R, "by_p4_witness": {int(k): [int(v[0]), int(v[1])] for k, v in strat.items()}}


# Published aggregate over the ten registered seed pools. The manuscript quotes
# these counts, so `check` regenerates and asserts them rather than trusting a
# hash of the pools.
PUBLISHED = {"survivors": 9205, "contributors": 5732, "successes": 3003,
             "targets": 11550, "R": 0.2600,
             # per hub, so a pool that redistributes cells between hubs cannot
             # pass on an unchanged aggregate. The exact engine pools these
             # same four hubs and they are not exchangeable.
             "by_hub": [[785, 2921], [745, 2885], [727, 2835], [746, 2909]]}
# The exact pooled value this pool now validates (skeleton_exact/maxpair_exact.py,
# §6.2). The pool no longer sources a claim: it is the sampling check on that
# number, so the gate below asks whether its cluster interval covers it.
EXACT_POOLED = 0.2663959
SEEDS = list(range(501, 511))
GENERATION = {"N_universe": 320, "trials_per_seed": 1_500_000_000,
              "batch": 2_000_000, "seeds": SEEDS}


def per_cluster(files):
    """(successes, targets) per survivor matrix — the resampling unit. One
    matrix contributes up to four depth-3 hubs to the cell, and they share its
    values, so uncertainty must be taken at matrix level, not target level.
    Also returns the same counts summed the other way, by hub."""
    M=np.concatenate([np.load(f)["M"] for f in files])
    tgt,suc=cell_matrix(M)
    return (suc.sum(1).astype(np.int64), tgt.sum(1).astype(np.int64),
            suc.sum(0).astype(np.int64), tgt.sum(0).astype(np.int64))


def check(files):
    """Regenerate the published aggregate and its cluster uncertainty, and
    assert the exact counts the manuscript quotes. Exits non-zero on mismatch."""
    import json
    succ, tot, hub_succ, hub_tot = per_cluster(files)
    contrib = tot > 0
    got = {"survivors": int(succ.size), "contributors": int(contrib.sum()),
           "successes": int(succ.sum()), "targets": int(tot.sum()),
           "by_hub": [[int(s), int(t)] for s, t in zip(hub_succ, hub_tot)]}
    got["R"] = round(got["successes"] / got["targets"], 4)
    rng = np.random.default_rng(20260727)
    idx = np.nonzero(contrib)[0]; s_, t_ = succ[idx], tot[idx]
    draws = rng.integers(0, idx.size, size=(20000, idx.size))
    boot = s_[draws].sum(axis=1) / t_[draws].sum(axis=1)
    lo, hi = (float(v) for v in np.percentile(boot, [2.5, 97.5]))
    const = 1123/4215
    se = float(boot.std(ddof=1))
    summary = {**got, "generation": GENERATION,
               "cluster_se": round(se, 5),
               "cluster_ci95": [round(lo, 4), round(hi, 4)],
               "independent_digit_constant": round(const, 6),
               "constant_inside_ci": bool(lo <= const <= hi),
               "exact_pooled": EXACT_POOLED,
               "exact_inside_ci": bool(lo <= EXACT_POOLED <= hi),
               "point_below_exact_se": round((EXACT_POOLED - got["R"]) / se, 2),
               "observed_census": round(844/3379, 4)}
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "_maxpair_summary.json")
    with open(out, "w") as fh:
        json.dump(summary, fh, indent=2)
    print(json.dumps(summary, indent=2))
    print(f"  wrote {out}")
    bad = [k for k, v in PUBLISHED.items() if got.get(k) != v]
    if bad:
        raise SystemExit(f"CHECK FAILED: {', '.join(bad)} differ from published "
                         f"{ {k: PUBLISHED[k] for k in bad} } vs regenerated "
                         f"{ {k: got.get(k) for k in bad} }")
    if not summary["exact_inside_ci"]:
        raise SystemExit(f"CHECK FAILED: cluster interval {summary['cluster_ci95']} "
                         f"no longer covers the exact pooled value {EXACT_POOLED}; "
                         f"the pool would then contradict the exact engine rather "
                         f"than validate it, and §6.2 would need revisiting")
    print(f"  CHECK OK — counts match the manuscript; the cluster interval covers "
          f"the exact pooled value {EXACT_POOLED}, with the point estimate "
          f"{summary['point_below_exact_se']} SE below it.")


if __name__=="__main__":
    mode=sys.argv[1]
    if mode=="sample": sample(int(sys.argv[2]),int(sys.argv[3]),int(sys.argv[4]),sys.argv[5])
    elif mode=="measure": measure(sys.argv[2:])
    elif mode=="check":
        import glob as _g
        fs = sys.argv[2:] or sorted(_g.glob(os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "_maxpair_s5*.npz")))
        check(fs)
    elif mode=="joints":
        Je,Jo,pe=measure_joints(); print("p_even=",pe); print("Jeven=",np.round(Je,4)); print("Jodd=",np.round(Jo,4))
