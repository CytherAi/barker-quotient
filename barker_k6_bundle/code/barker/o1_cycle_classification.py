"""
barker.o1_cycle_classification
================================
Classification of all observed O1 directed 5-cycles by non-minimality mechanism.

REFUTED — RETAINED AS A HISTORICAL RECORD
------------------------------------------
This module records the O1 program's classification at 60 hard primes. Its
central conjecture — that Case 3 is impossible, i.e. that no directed 5-cycle
yields a MINIMAL k=6 covering — is FALSE. Extending the universe to the first
80 hard primes produces exactly such a configuration:

    S* = {17881} ∪ (1801, 14537, 13417, 18121, 18521)

whose cycle primes lie in V_{17881} and form a directed 5-cycle in G_{17881},
and which is minimal (all 41 proper subsets of sizes 3-5 are non-covering; see
`verify_minimal_k6.py`). S* is a Case 3 instance. Everything below describes
the state of the program BEFORE that configuration was found; the counts and
proof targets are not current claims.

Fundamental dichotomy for 5-cycles (as conjectured at 60 primes)
-----------------------------------------------------------------
The conjecture was that every directed 5-cycle in G_x produces a NON-minimal
k=6 covering set via exactly one of two mechanisms:

  CASE 1 (sub-config):  {x}∪cycle contains a k≤5 covering sub-configuration.
  CASE 2 (mutual edge): {x}∪cycle contains a mutual edge p↔q in G_x,
                         hence a covering triple {x,p,q} via T1.

CASE 3 (neither) gives a minimal k=6 O1 cover. No Case 3 instance was found at
60 primes; S* is one at 80.

Mutual-edge mechanisms
-----------------------
Within Case 2, mutual edges arise via two distinguishable mechanisms:

  T2-forced:   p is degenerate (L(p)=0) and q is a cycle neighbor with
               q ∈ H_p ∩ V_x, so p→q is forced by T2.  Combined with
               q→p from the cycle structure, this gives a mutual edge.

  Independent: Neither p nor q is degenerate; the mutual edge arises
               from the arithmetic of the specific prime pair without
               the T2 structural guarantee.

Observed 5-cycles at 60 hard primes (4 total)
----------------------------------------------
  hub=4201 [Case A]: cycle (601,11257,5689,6089,4057)
    → CASE 2: mutual edges 601↔11257 (T2-forced, degen 11257)
                               5689↔6089 (independent)
    → 2/2 mutual edges give covering triples via T1

  hub=4409 [Case B, NO degenerate vertices]: cycle (5689,12073,9769,6553,7753)
    → CASE 2: mutual edge 9769↔6553 (independent — no T2 mechanism)
    → 1/1 mutual edge gives covering triple via T1
    → First Case B 5-cycle: mutual-edge hypothesis supported non-vacuously

  hub=7993 [Case A] ×2: cycles (1609,13337,11177,2441,12841) and rotation
    → CASE 1: contained k=5 sub-config (7993,13337,11177,2441,12841)
    → No mutual edges found; non-minimality via sub-config containment

Unified mutual-edge hypothesis — corrected status
--------------------------------------------------
CLAIM: Every directed 5-cycle in G_x contains ≥1 mutual edge.

STATUS: PARTIALLY FALSE.  The two x=7993 cycles have NO mutual edges.
        They are non-minimal via a different mechanism (Case 1).

FORMULATION AS OF 60 PRIMES: every 5-cycle observed there is non-minimal (0/4),
        but the mechanism varies, so the theorem to prove is Case 3
        impossibility.  THIS TARGET IS DEAD: Case 3 is realised at 80 primes
        by S*, so no such theorem exists.  What survives is the empirical
        observation that Case 3 is rare, and Theorem B of the manuscript, which
        characterises when {x}∪C is A1 minimal.

Proof targets
-------------
T_A (Case A, degenerate cycles):
    Show that every degenerate 5-cycle either contains a mutual edge (Case 2)
    or contains a smaller known covering config (Case 1).
    The x=7993 cycles demonstrate Case 1 can arise even for Case A cycles.

T_B (Case B, no-degenerate cycles):
    Show that every non-degenerate 5-cycle (if one exists) either has a
    mutual edge or contains a smaller covering config.
    The x=4409 cycle demonstrates Case 2 for Case B (n=1).

T_general (unified):
    Case 3 is impossible: for any 5-cycle in G_x, either a k≤5 sub-config
    exists within {x}∪cycle, or a mutual edge exists in the cycle.
    This is the cleanest statement of O1 non-realizability and does not
    require the mutual-edge hypothesis to hold universally.

Blocking-pair universality (empirically strongest finding)
-----------------------------------------------------------
At 60 primes, three R1 hubs have concentrated near-miss structure:
  x=4057:  3-chains blocked by 1 permanent pair: (881→8761, Δ=2)
  x=13337: 3-chains blocked by 2 permanent pairs
  x=11113: 4-chains blocked by 2 permanent pairs

No diffuse near-miss structure observed. All near-cycles cluster on a
small set of fixed arithmetic inequalities (discrete-log facts). This
pattern, replicated across 3 hubs and 2 chain depths, is the strongest
empirical evidence that the obstruction is structural rather than statistical.
"""

from __future__ import annotations
from dataclasses import dataclass
from itertools import combinations

from .two_primary import (
    build_two_primary_table, quotient_class, TwoPrimaryCharacterTable,
)
from .minimal_cover_search import BadPairIndex
from .o1_realizability import build_cycle_graph
from .o1_cycle_obstruction import find_all_cycles


# ---------------------------------------------------------------------------
# Mutual-edge classification
# ---------------------------------------------------------------------------

@dataclass
class MutualEdgeRecord:
    """A mutual edge p↔q in G_x with its non-minimality mechanism."""
    hub:       int
    p:         int
    q:         int
    mechanism: str             # "T2-forced", "independent", or "T2-forced+independent"
    degen_p:   bool            # p is degenerate (L(p)=0)
    degen_q:   bool            # q is degenerate (L(q)=0)
    t1_gives_covering_triple: bool


# ---------------------------------------------------------------------------
# 5-cycle classification
# ---------------------------------------------------------------------------

@dataclass
class CycleClassification:
    """
    Full classification of a directed 5-cycle in G_x.

    Attributes
    ----------
    hub              : x
    cycle            : (p0,...,p4)
    is_case_a        : True iff cycle contains a degenerate vertex (L(p_j)=0)
    degen_vertices   : degenerate vertices in cycle
    covering_6set    : (x,) + cycle — the candidate k=6 covering set
    is_covering      : True iff covering_6set is a covering set
    is_minimal       : True iff covering_6set is minimal.  False for every
                       5-cycle observed at 60 primes; True for S* at 80, which
                       is why the Case 3 impossibility target was abandoned.
    mechanism        : "Case1-subconfig", "Case2-mutual-edge", or "Case3-none" (bad)
    mutual_edges     : list of MutualEdgeRecord
    contained_subconfig: smallest k≤5 covering sub-config found, or None
    """
    hub:               int
    cycle:             tuple[int, ...]
    is_case_a:         bool
    degen_vertices:    list[int]
    covering_6set:     tuple[int, ...]
    is_covering:       bool
    is_minimal:        bool
    mechanism:         str
    mutual_edges:      list[MutualEdgeRecord]
    contained_subconfig: tuple | None


def classify_5cycle(
    hub:    int,
    cycle:  tuple[int, ...],
    primes: list[int],
    table:  TwoPrimaryCharacterTable,
    index:  BadPairIndex,
) -> CycleClassification:
    """Classify a directed 5-cycle in G_x by non-minimality mechanism."""
    a_map  = {p: quotient_class(hub, p) for p in cycle}
    L_map  = {p: (-a_map[p]) % (2**table.depth[p]) for p in cycle}
    degen  = [p for p in cycle if a_map[p] == 0]
    is_a   = bool(degen)

    six   = (hub,) + cycle
    sixix = tuple(index.prime_idx[p] for p in six)
    is_cov = index.is_covering(sixix)
    is_min = index.is_minimal_covering(sixix) if is_cov else False

    me_list = []
    for i in range(5):
        for j in range(i + 1, 5):
            pi, pj = cycle[i], cycle[j]
            if (quotient_class(pj, pi) == L_map[pi] and
                    quotient_class(pi, pj) == L_map[pj]):
                dp = (a_map[pi] == 0)
                dq = (a_map[pj] == 0)
                if dp or dq:
                    mech = "T2-forced"
                else:
                    mech = "independent"
                t3ix = tuple(index.prime_idx[p] for p in [hub, pi, pj])
                t1_ok = index.is_covering(t3ix)
                me_list.append(MutualEdgeRecord(
                    hub=hub, p=pi, q=pj, mechanism=mech,
                    degen_p=dp, degen_q=dq,
                    t1_gives_covering_triple=t1_ok,
                ))

    sub_cfg = None
    for k in range(3, 6):
        for sub in combinations(six, k):
            si = tuple(index.prime_idx[p] for p in sub)
            if index.is_minimal_covering(si):
                sub_cfg = sub
                break
        if sub_cfg:
            break

    if me_list and any(me.t1_gives_covering_triple for me in me_list):
        mech_str = "Case2-mutual-edge"
    elif sub_cfg and len(sub_cfg) < 6:
        mech_str = "Case1-subconfig"
    elif not is_min:
        mech_str = "Case1-subconfig"  # non-minimal via some sub-config
    else:
        mech_str = "Case3-none"  # a minimal k=6 config — realised by S* at N=80

    return CycleClassification(
        hub=hub, cycle=cycle, is_case_a=is_a, degen_vertices=degen,
        covering_6set=six, is_covering=is_cov, is_minimal=is_min,
        mechanism=mech_str, mutual_edges=me_list,
        contained_subconfig=sub_cfg,
    )


# ---------------------------------------------------------------------------
# Full search and classification over a prime universe
# ---------------------------------------------------------------------------

@dataclass
class CycleClassificationReport:
    """
    All 5-cycles found and classified over a prime universe.

    Attributes
    ----------
    primes          : prime universe
    all_cycles      : list of CycleClassification
    n_case1         : Case 1 (sub-config mechanism)
    n_case2         : Case 2 (mutual-edge mechanism)
    n_case3         : Case 3 (neither — would be minimal!) should be 0
    n_t2_forced     : Case 2 cycles where at least one mutual edge is T2-forced
    n_independent   : Case 2 cycles where at least one mutual edge is independent
    n_case_b        : Case B cycles (no degenerate vertices)
    n_case_b_case2  : Case B cycles in Case 2 (mutual edge, no T2 mechanism)
    """
    primes:         list[int]
    all_cycles:     list[CycleClassification]
    n_case1:        int
    n_case2:        int
    n_case3:        int
    n_t2_forced:    int
    n_independent:  int
    n_case_b:       int
    n_case_b_case2: int


def classify_all_5cycles(
    primes: list[int],
    table:  TwoPrimaryCharacterTable | None = None,
) -> CycleClassificationReport:
    """Find and classify all directed 5-cycles across all hubs in the prime universe."""
    if table is None:
        table = build_two_primary_table(primes)
    index = BadPairIndex(primes, table)

    all_cls: list[CycleClassification] = []
    seen: set[tuple] = set()

    for x in primes:
        g = build_cycle_graph(x, primes, table)
        for r in find_all_cycles(g, max_length=5, table=table):
            if r.length != 5: continue
            cyc = tuple(r.cycle)
            key = (x, cyc)
            if key in seen: continue
            seen.add(key)
            cl = classify_5cycle(x, cyc, primes, table, index)
            all_cls.append(cl)

    return CycleClassificationReport(
        primes=primes,
        all_cycles=all_cls,
        n_case1=sum(1 for c in all_cls if c.mechanism == "Case1-subconfig"),
        n_case2=sum(1 for c in all_cls if c.mechanism == "Case2-mutual-edge"),
        n_case3=sum(1 for c in all_cls if c.mechanism == "Case3-none"),
        n_t2_forced=sum(1 for c in all_cls if c.mechanism == "Case2-mutual-edge"
                        and any(me.mechanism == "T2-forced" for me in c.mutual_edges)),
        n_independent=sum(1 for c in all_cls if c.mechanism == "Case2-mutual-edge"
                          and any(me.mechanism == "independent" for me in c.mutual_edges)),
        n_case_b=sum(1 for c in all_cls if not c.is_case_a),
        n_case_b_case2=sum(1 for c in all_cls
                           if not c.is_case_a and c.mechanism == "Case2-mutual-edge"),
    )


# ---------------------------------------------------------------------------
# Formatted output
# ---------------------------------------------------------------------------

def format_classification_report(report: CycleClassificationReport) -> str:
    lines, div = [], "─" * 72
    lines += [
        div,
        "  O1 5-CYCLE CLASSIFICATION: NON-MINIMALITY MECHANISM",
        f"  Prime universe: first {len(report.primes)} hard primes",
        f"  Total 5-cycles found: {len(report.all_cycles)}",
        div,
        f"  Case 1 (sub-config, no mutual edge required):  {report.n_case1}",
        f"  Case 2 (mutual edge → T1 covering triple):     {report.n_case2}",
        f"    T2-forced mutual edges:                        {report.n_t2_forced}",
        f"    Independent mutual edges:                      {report.n_independent}",
        f"  Case 3 (neither — WOULD BE MINIMAL):            {report.n_case3}",
        div,
        f"  Case B cycles (no degenerate vertices):        {report.n_case_b}",
        f"  Case B in Case 2 (mutual edge):                {report.n_case_b_case2}",
        div,
    ]
    if report.n_case3 == 0:
        lines += [
            "  RESULT: All 5-cycles are non-minimal (Case 3 = 0).",
            "  No minimal k=6 O1 covering set found.",
        ]
    else:
        lines += [f"  ALERT: {report.n_case3} Case 3 cycle(s) found — minimal k=6 O1 sets exist!"]
    lines += ["", "  CYCLE DETAILS:"]
    for c in report.all_cycles:
        lines.append(f"    hub={c.hub} [{'B' if not c.is_case_a else 'A'}]: {c.mechanism}")
        if c.mutual_edges:
            for me in c.mutual_edges:
                lines.append(f"      {me.p}↔{me.q}: {me.mechanism}, T1={me.t1_gives_covering_triple}")
        if c.contained_subconfig:
            lines.append(f"      sub-config k={len(c.contained_subconfig)}: {c.contained_subconfig}")
    lines.append(div)
    return "\n".join(lines)
