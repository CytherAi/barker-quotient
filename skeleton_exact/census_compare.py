#!/usr/bin/env python3
"""
census_compare.py — parity-graph-conditioned support comparison (Question 6.2.G).

Census side: every k = 5 zero-δ minimal covering enumerated per universe
(`research/_per_depth_w2_cache_N*.json`), restricted to the two depth profiles
with exact skeleton support — uniform (3,3,3,3,3) and mixed (3,3,3,3,4), deep
vertex in slot 4. Other profiles are excluded and counted aloud.

Skeleton side: the exact conditioned support of exact_dp.py (`_support.npz`),
with per-parity-graph weights recomputed from the row tables.

Design (exposure-conditioned): the expected census count of a witness-structure
orbit o in a stratum is
    E(o) = Σ_β n_β · P(o | survive, β),
where n_β is the stratum's exposure to labeled parity graph β. This does not
mistake an unusual census parity-graph distribution for a higher reciprocity
obstruction, and Rédei-type identities — pending the bridge lemma — activate
under specific β.

Terminology: realizable orbits with E(o) > 0 that never occur in the census are
reported as UNOBSERVED SKELETON-ADMISSIBLE MOTIFS — never "forbidden" — until
an arithmetic identity proves an absence. Discovery stratum: N ≤ 160.
Held-out increments: 160→200, 200→240, 240→280.

Two reporting rules the numbers themselves forced:
  - the activating parity graph is ranked on exposure aggregated across ALL
    strata, matching the total the frontier is ranked on; ranking on a single
    stratum's contribution names the wrong β for part of the table;
  - orbits sharing a RESPONSE SIGNATURE — identical weight vectors w(o | β)
    over all 1,024 β — have equal expectations by identity, not by a hidden
    symmetry. They are grouped and their common support sectors printed, so a
    tie is read as indistinguishability to the skeleton rather than as
    evidence of a group action beyond S5.

Run:  python3 skeleton_exact/census_compare.py
"""
from __future__ import annotations

import json
import os
import sys
from collections import Counter
from itertools import combinations, permutations

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
RESEARCH = os.path.join(REPO, "barker_k6_bundle", "research")
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(REPO, "barker_k6_bundle", "code"))

from exact_dp import (BITPOS, PAIRS, S_LUT, K, canonicalize, check,
                      predicate_reference, row_tables)
# Only depths and directed quotient classes are needed. build_two_primary_table
# would additionally construct the cubic pair-level table, which dominates the
# runtime and is never read here.
from barker.two_primary import two_primary_depth, quotient_class

UNIVERSES = [100, 120, 140, 160, 200, 240, 280]
DISCOVERY_N = 160
PERMS5 = list(permutations(range(K)))
PERMS4 = [pi for pi in PERMS5 if pi[4] == 4]


# ------------------------------------------------------------- census side
def load_configs():
    """Every expected cache, with the nesting the strata split assumes."""
    out = {}
    for n in UNIVERSES:
        path = os.path.join(RESEARCH, f"_per_depth_w2_cache_N{n}.json")
        check(os.path.exists(path), f"missing census cache for N={n}: {path}")
        with open(path) as f:
            raw = json.load(f)
        cfgs = [tuple(sorted(c)) for c in raw]
        check(len(set(cfgs)) == len(cfgs), f"duplicate configurations in N={n}")
        out[n] = cfgs
    for a, b in zip(UNIVERSES, UNIVERSES[1:]):
        missing = set(out[a]) - set(out[b])
        check(not missing, f"universes not nested: {len(missing)} configuration(s) "
                           f"in N={a} absent from N={b}")
    return out


def config_state(primes):
    """(profile, beta, code) for one 5-set, or (excl_reason, None, None).

    Vertex order: uniform profile — ascending primes; mixed — the four depth-3
    primes ascending, the depth-4 prime in slot 4 (the S4-marked convention of
    exact_dp's profile B).
    """
    depths = {p: two_primary_depth(p) for p in primes}
    d3 = sorted(p for p in primes if depths[p] == 3)
    d4 = sorted(p for p in primes if depths[p] == 4)
    if len(d3) == 5:
        order, profile = list(primes), "A"
    elif len(d3) == 4 and len(d4) == 1:
        order, profile = d3 + d4, "B"
    else:
        prof = tuple(sorted(depths[p] for p in primes))
        return f"excluded profile {prof}", None, None

    t = [depths[p] for p in order]
    M = [[0] * K for _ in range(K)]
    for i in range(K):
        for j in range(K):
            if i != j:
                M[i][j] = quotient_class(order[j], order[i])
                check(M[i][j] != 0, f"{primes}: zero δ violated at χ")
    for i, j in combinations(range(K), 2):
        check((M[i][j] - M[j][i]) % 2 == 0,
              f"{primes}: reciprocity parity violated on ({i},{j})")

    beta = 0
    for e, (i, j) in enumerate(PAIRS):
        beta |= (M[i][j] & 1) << e
    code = 0
    for v in range(K):
        mod = 1 << t[v]
        for a, b in combinations([u for u in range(K) if u != v], 2):
            if (M[v][a] + M[v][b]) % mod == 0:
                code |= 1 << (6 * v + BITPOS[v][(a, b)])
    check(predicate_reference(code),
          f"{primes}: census structure fails the covering/minimality predicate")
    return profile, beta, code, M


# ------------------------------------------------------------ skeleton side
class Support:
    """Per-profile conditioned support with per-β orbit weights on demand."""

    def __init__(self, npz, profile, tab3, tab4):
        self.profile = profile
        suffix = "A" if profile == "A" else "B"
        self.reps = npz[f"reps_{suffix}"]
        self.orbit_size = npz[f"orbit_size_{suffix}"]
        self.weight_total = npz[f"weight_{suffix}"]
        codes = npz["codes"]
        canon = npz[f"canon_{suffix}"]
        self.inv = np.searchsorted(self.reps, canon)
        self.ms = [((codes >> (6 * v)) & 63).astype(np.int64) for v in range(K)]
        depths = (3, 3, 3, 3, 3) if profile == "A" else (3, 3, 3, 3, 4)
        tab = {3: tab3, 4: tab4}
        self.q = [tab[depths[v]]["all"] for v in range(K)]
        self._cache = {}

    def orbit_weights(self, beta):
        """Integer orbit weights w(o | β); Σ_o w = D(β)."""
        if beta in self._cache:
            return self._cache[beta]
        w = np.ones(self.ms[0].shape[0], dtype=np.float64)
        for v in range(K):
            w *= self.q[v][S_LUT[beta, v]][self.ms[v]]
        ow = np.bincount(self.inv, weights=w, minlength=self.reps.shape[0])
        check(ow.max() < 2 ** 53, "orbit weight exceeds float64-exact range")
        ow = np.round(ow).astype(np.int64)
        self._cache[beta] = ow
        return ow

    def canon_code(self, code):
        arr = np.array([code], dtype=np.int64)
        group = PERMS5 if self.profile == "A" else PERMS4
        return int(canonicalize(arr, group)[0])


def main():
    print("[1/4] load census caches and classify configurations", flush=True)
    configs = load_configs()
    npz = np.load(os.path.join(HERE, "_support.npz"))
    pg = np.load(os.path.join(HERE, "_per_graph.npz"))
    tab3, tab4 = row_tables(3), row_tables(4)
    support = {"A": Support(npz, "A", tab3, tab4),
               "B": Support(npz, "B", tab3, tab4)}
    D = {"A": pg["D_A"], "B": pg["D_B"]}

    # strata: discovery = cumulative at N=160; held-out = nested increments
    ns = sorted(configs)
    strata = {f"N<={DISCOVERY_N}": set(configs[DISCOVERY_N])}
    prev = DISCOVERY_N
    for n in [x for x in ns if x > DISCOVERY_N]:
        strata[f"N{prev}->{n}"] = set(configs[n]) - set(configs[prev])
        prev = n

    excluded = {}
    states = {}          # config -> (profile, beta, code, residue)
    for n, cs in configs.items():
        for cfg in cs:
            if cfg in states or cfg in excluded:
                continue
            st = config_state(cfg)
            if st[1] is None:
                excluded[cfg] = st[0]
            else:
                states[cfg] = st
                # the configuration's own parity graph must give its structure
                # positive skeleton weight — containment, checked not assumed
                profile, beta, code, _ = st
                w = 1
                for v in range(K):
                    q = (tab3 if (profile == "A" or v < 4) else tab4)["all"]
                    w *= int(q[S_LUT[beta, v]][(code >> (6 * v)) & 63])
                check(w > 0, f"{cfg}: zero skeleton weight at its own parity "
                             f"graph {beta:#012b} (profile {profile})")
    print(f"  {len(states)} eligible configurations; "
          f"{len(excluded)} excluded by depth profile", flush=True)
    excl_hist = Counter(excluded.values())
    for reason, cnt in excl_hist.most_common():
        print(f"    {cnt:4d}  {reason}")

    print("[2/4] observed orbits and exposures per stratum", flush=True)
    report = {"excluded_profiles": {r: c for r, c in excl_hist.items()},
              "strata": {}}
    # batch-canonicalize all census codes once per profile
    canon_of = {}
    for profile in ("A", "B"):
        group = PERMS5 if profile == "A" else PERMS4
        items = [(cfg, st[2]) for cfg, st in states.items() if st[0] == profile]
        if items:
            arr = np.array([c for _, c in items], dtype=np.int64)
            can = canonicalize(arr, group)
            canon_of.update({cfg: int(c) for (cfg, _), c in zip(items, can)})

    seen_orbits = {"A": {}, "B": {}}   # canon -> {stratum: count}
    exposures = {}                     # (stratum, profile) -> Counter(beta)
    residues = {"A": {}, "B": {}}      # canonical residue matrix -> [configs]
    for sname, cs in strata.items():
        for profile in ("A", "B"):
            exposures[(sname, profile)] = Counter()
        for cfg in sorted(cs):
            if cfg not in states:
                continue
            profile, beta, code, M = states[cfg]
            exposures[(sname, profile)][beta] += 1
            seen_orbits[profile].setdefault(canon_of[cfg], Counter())[sname] += 1
            # residue-level inventory: canonical matrix under simultaneous
            # row-and-column relabeling by the profile's group
            group = PERMS5 if profile == "A" else PERMS4
            best = min(tuple(tuple(M[pi[a]][pi[b]] for b in range(K))
                             for a in range(K)) for pi in group)
            residues[profile].setdefault(best, []).append(cfg)

    print("[3/4] exposure-conditioned expected counts E(o)", flush=True)
    frontier = {}
    for profile in ("A", "B"):
        sup = support[profile]
        realizable = np.nonzero(sup.weight_total > 0)[0]
        E = {sname: np.zeros(sup.reps.shape[0]) for sname in strata}
        for sname in strata:
            for beta, n_beta in exposures[(sname, profile)].items():
                ow = sup.orbit_weights(beta)
                d = int(D[profile][beta])
                check(int(ow.sum()) == d, f"orbit mass != D({beta})")
                E[sname] += n_beta * (ow / d)
        E_disc = E[f"N<={DISCOVERY_N}"]
        E_total = sum(E.values())
        obs_canon = set(seen_orbits[profile])
        for c in obs_canon:
            i = int(np.searchsorted(sup.reps, c))
            check(i < sup.reps.shape[0] and int(sup.reps[i]) == c,
                  f"census orbit {c:#x} outside skeleton support "
                  f"(profile {profile})")
        obs_idx = {int(np.searchsorted(sup.reps, c)) for c in obs_canon}
        # orbits absent through discovery but realized in a held-out increment:
        # the persistence check for discovery-ranked absences
        disc_canon = {c for c, per in seen_orbits[profile].items()
                      if per.get(f"N<={DISCOVERY_N}", 0) > 0}
        late = [c for c in obs_canon if c not in disc_canon]
        absent = [i for i in realizable if i not in obs_idx]
        absent.sort(key=lambda i: -E_total[i])
        # total exposure per β across ALL strata: the activating graph must be
        # ranked on the same total the frontier is ranked on, not on whichever
        # single stratum happens to contribute most.
        total_expo = Counter()
        for (sname, prof), expo in exposures.items():
            if prof == profile:
                total_expo.update(expo)

        rows = []
        for i in absent[:25]:
            code = int(sup.reps[i])
            contrib = sorted(
                ((n_beta * int(sup.orbit_weights(beta)[i]) / int(D[profile][beta]),
                  beta) for beta, n_beta in total_expo.items()),
                reverse=True)
            support_betas = [b for b in range(1024)
                             if int(sup.orbit_weights(b)[i]) > 0]
            wit = {f"{PAIRS[p]}": sorted(
                       v for v in range(K) if v not in PAIRS[p]
                       and (code >> (6 * v)) & (1 << BITPOS[v][PAIRS[p]]))
                   for p in range(len(PAIRS))}
            rows.append({
                "rep_code": code,
                "orbit_size": int(sup.orbit_size[i]),
                "E_discovery": float(E_disc[i]),
                "E_heldout": float(E_total[i] - E_disc[i]),
                "E_total": float(E_total[i]),
                # ranked on the same all-strata total as the frontier itself
                "top_activating_beta": (f"0b{contrib[0][1]:010b}"
                                        if contrib else None),
                "top_activating_share": (float(contrib[0][0] / E_total[i])
                                         if contrib and E_total[i] else None),
                # every parity graph giving this motif positive skeleton
                # weight — the sectors in which it could have appeared at all,
                # listed in full (the leading mixed-profile motif has 50)
                "support_betas": [f"0b{b:010b}" for b in support_betas],
                "n_support_betas": len(support_betas),
                "witness_sets": wit,
                "redei_status": "pending bridge lemma (χ high bit ↔ Rédei "
                                "symbol not yet proved)",
            })
        # Response signature: orbits with identical weight vectors w(o | β)
        # over ALL 1,024 β are indistinguishable to the skeleton, so equal
        # expectations are an identity, not a coincidence to be explained by
        # a conjectural group action beyond S5.
        # Grouped over EVERY absent orbit, not just the reported head: a class
        # is only meaningful if its membership is complete.
        W = np.stack([sup.orbit_weights(b) for b in range(1024)])   # (1024, n)
        sig_groups = {}
        for i in absent:
            sig_groups.setdefault(tuple(W[:, i].tolist()), []).append(i)
        signature_classes = sorted(
            ({"members": [int(sup.reps[i]) for i in idxs],
              "size": len(idxs),
              "E_total_each": float(E_total[idxs[0]]),
              "support_betas": [f"0b{b:010b}"
                                for b in range(1024) if sig[b] > 0],
              "weight_at_support": sorted({int(sig[b]) for b in range(1024)
                                           if sig[b] > 0})}
             for sig, idxs in sig_groups.items() if len(idxs) > 1),
            key=lambda c: -c["E_total_each"])

        n_res = len(residues[profile])
        n_cfg = sum(len(v) for v in residues[profile].values())
        collisions = {str(k)[:60]: [list(c) for c in v]
                      for k, v in residues[profile].items() if len(v) > 1}
        frontier[profile] = {
            "realizable_orbits": int(realizable.shape[0]),
            "observed_orbits": len(obs_idx),
            "unobserved_admissible": len(absent),
            "E_mass_on_unobserved_discovery":
                float(sum(E_disc[i] for i in absent)),
            "discovery_absent_later_observed": len(late),
            "response_signature_classes": signature_classes,
            "top_unobserved": rows,
            "residue_states": {"distinct": n_res, "configs": n_cfg,
                               "collisions": len(collisions)},
        }
        print(f"  profile {profile}: {len(obs_idx)} observed orbits / "
              f"{realizable.shape[0]} realizable; "
              f"{len(absent)} unobserved skeleton-admissible; "
              f"E-mass on unobserved (discovery) = "
              f"{sum(E_disc[i] for i in absent):.2f}", flush=True)

    print("[4/4] emit report", flush=True)
    for sname in strata:
        report["strata"][sname] = {
            prof: {"configs": sum(exposures[(sname, prof)].values()),
                   "distinct_beta": len(exposures[(sname, prof)])}
            for prof in ("A", "B")}

    # Sector exposure across the whole census. The all-QR sector (β = 0) is
    # where classical Rédei side conditions hold, so its exposure is what
    # decides whether a Rédei test there is powered at all.
    all_beta = Counter()
    for (_, _), expo in exposures.items():
        all_beta.update(expo)
    report["sector_exposure"] = {
        "eligible_configs": sum(all_beta.values()),
        "distinct_beta_occupied": len(all_beta),
        "beta_all_QR_0b0000000000": all_beta.get(0, 0),
        "beta_all_QNR_0b1111111111": all_beta.get(1023, 0),
        "top_beta": [[f"0b{b:010b}", n] for b, n in all_beta.most_common(5)],
    }
    print(f"  sector exposure: all-QR β=0 -> {all_beta.get(0, 0)} configs; "
          f"all-QNR β=1023 -> {all_beta.get(1023, 0)}; "
          f"{len(all_beta)} of 1024 parity graphs occupied")
    report["frontier"] = frontier
    out = os.path.join(HERE, "_census_compare.json")
    with open(out, "w") as f:
        json.dump(report, f, indent=2)
    print(f"wrote {out}\n")

    for profile in ("A", "B"):
        fr = frontier[profile]
        label = "(3,3,3,3,3)" if profile == "A" else "(3,3,3,3,4)"
        print(f"=== FRONTIER, profile {label} ===")
        print(f"  observed {fr['observed_orbits']} / "
              f"{fr['realizable_orbits']} realizable orbits; "
              f"{fr['unobserved_admissible']} unobserved skeleton-admissible "
              f"motifs; expected census mass on them (discovery) "
              f"{fr['E_mass_on_unobserved_discovery']:.2f}")
        print(f"  discovery-absent orbits later realized: "
              f"{fr['discovery_absent_later_observed']} — absence through "
              f"discovery alone is weak evidence")
        for r in fr["top_unobserved"][:5]:
            print(f"  E_disc={r['E_discovery']:.3f}  E_total={r['E_total']:.3f}"
                  f"  orbit_size={r['orbit_size']}  code={r['rep_code']:#010x}"
                  f"  β*={r['top_activating_beta']} "
                  f"({100 * (r['top_activating_share'] or 0):.0f}% of E_total)"
                  f"  support on {r['n_support_betas']} β")
        classes = fr["response_signature_classes"]
        print(f"  response-signature classes among ALL {fr['unobserved_admissible']} "
              f"absent orbits: {len(classes)} (grouping {sum(c['size'] for c in classes)} orbits)")
        for cls in classes[:3]:
            sect = cls["support_betas"]
            shown = ", ".join(sect[:4]) + (f", … ({len(sect)} sectors)"
                                           if len(sect) > 4 else "")
            print(f"    {cls['size']} orbits, E_total {cls['E_total_each']:.3f} each; "
                  f"support at {shown}")


if __name__ == "__main__":
    main()
