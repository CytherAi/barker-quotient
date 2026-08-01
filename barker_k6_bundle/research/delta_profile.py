#!/usr/bin/env python3
"""
delta_profile.py — compute the follow-on paper's defect invariant

    δ_x(S) := |V_x ∩ (S \\ {x})|   for x ∈ S

for each known minimal covering, and apply the five-class partition
{A1, A2, A3, B0, B1} from §1.3 of `submission/followon_section1.md`:

  A1: some x ∈ S has δ_x = k - 1                (full hub)
  A2: some x ∈ S has chi-sum = 0 with 2 ≤ δ_x < k - 1    (partial hub)
  A3: some x ∈ S has chi-sum = 0 with δ_x ≤ 1            (pure cancellation)
  B0: no chi-sum vanishes; δ_x = 0 for all x       (maximally diffuse)
  B1: no chi-sum vanishes; some x has δ_x = k - 2  (blocked near-hub)

This is a verification probe: it re-derives the follow-on paper's
classification from the chi table to confirm the δ invariant fully
separates the 13 known configurations as claimed (A1=4, A2=1, A3=6,
B0=1, B1=1).
"""

import os
import sys

sys.path.insert(
    0,
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "code"),
)

from barker.cofactor_analysis import classify_all_known  # noqa: E402
from barker.sweep import find_hard_primes  # noqa: E402
from barker.two_primary import build_two_primary_table  # noqa: E402

from _common import classify  # noqa: E402


def main():
    hp = find_hard_primes(80000)
    target_primes = [d["prime"] for d in hp[:80]]
    table = build_two_primary_table(target_primes)
    cs = classify_all_known()

    rows = []
    for r in cs.type_a + cs.type_b:
        C = tuple(sorted(r.config))
        c = classify(C, table)
        type_paper = "B" if r.is_genuine else "A"
        rows.append((type_paper, len(C), C, c.cls, c.deltas, c.chi_sums, c.elim))

    rows.sort(key=lambda r: (r[3], r[1], r[2]))

    print("=" * 78)
    print("  δ-profile classification (follow-on paper §1.3)")
    print("=" * 78)
    print(
        f"{'paper':>5} {'k':>2}  {'class':>5}  "
        f"{'δ-profile':>20}  {'config':32}  elim"
    )
    for type_paper, k, C, cls, deltas, chi_sums, elim in rows:
        d_sorted = sorted(deltas.values(), reverse=True)
        cfg_str = str(C)
        if len(cfg_str) > 30:
            cfg_str = cfg_str[:27] + "..."
        elim_str = str(elim) if elim else "[]"
        print(
            f"{type_paper:>5} {k:>2}  {cls:>5}  "
            f"{str(d_sorted):>20}  {cfg_str:32}  {elim_str}"
        )

    counts = {}
    for r in rows:
        counts[r[3]] = counts.get(r[3], 0) + 1
    print()
    print(f"Counts: {dict(sorted(counts.items()))}")
    print("Follow-on paper expects: {'A1': 4, 'A2': 1, 'A3': 6, 'B0': 1, 'B1': 1}")


if __name__ == "__main__":
    main()
