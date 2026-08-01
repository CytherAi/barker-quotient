#!/usr/bin/env python3
"""
make_figures.py — generate the three figures specified in
docs/figure_drafts.md.

Outputs (written to <repo-root>/figures/):
  figure4_1_census_matrix.{png,pdf}     — seven-cell taxonomy census
  figure5_1_discrimination_depth.{png,pdf} — marginal-contribution histogram
  figure5_2_v_substructure.{png,pdf}           — V-substructure network around 17881

This script is editorial, not part of verify_all.sh. It depends on
matplotlib, outside the verification path's pure-stdlib discipline.
Run from repo root:

    python3 barker_k6_bundle/research/make_figures.py

The ASCII mockups in docs/figure_drafts.md are the authoritative
specification of what each figure must communicate; this script
renders them and should not silently drift from those specifications.
"""

import matplotlib
import numpy as np

matplotlib.use("Agg")
from pathlib import Path

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch


REPO_ROOT = Path(__file__).resolve().parents[2]
FIG_DIR = REPO_ROOT / "figures"
FIG_DIR.mkdir(exist_ok=True)


# ---------------------------------------------------------------------------
# Figure 4.1 — Census matrix
# ---------------------------------------------------------------------------

CENSUS = {
    3: {"A1": 68, "A2": 0, "A3": 157, "B0": 0,  "B1": 0,  "B_int": 0},
    4: {"A1": 9,  "A2": 0, "A3": 13,  "B0": 50, "B1": 5,  "B_int": 0},
    5: {"A1": 7,  "A2": 8, "A3": 28,  "B0": 6,  "B1": 6,  "B_int": 3},
    6: {"A1": 1,  "A2": 8, "A3": 23,  "B0": 6,  "B1": 10, "B_int": 13},
}

KS = [3, 4, 5, 6]
COLUMNS = ["A1", "A2", "A3", "B0", "B1", "B_int"]
# Code and descriptor drawn separately: the long descriptors overlapped at a
# shared fontsize, so codes go at fs 11 and short descriptors at fs 8.5.
COL_CODES = ["A1", "A2", "A3", "B0", "B1", "B_int"]
COL_DESCS = ["full hub", "partial hub", "pure canc.",
             "diffuse", "codim-1", "interior"]

# A_blocked sub-counts per (k, A-stratum) — Type A configurations that
# also have some target with delta_x = k - 2.
A_BLOCKED = {
    (4, "A1"): 4,
    (4, "A3"): 8,
    (5, "A2"): 1,
    (5, "A3"): 3,
    (6, "A3"): 3,
}


def fig_census_matrix():
    fig, ax = plt.subplots(figsize=(12, 5.8))

    n_rows = len(KS)
    n_cols = len(COLUMNS)
    counts = np.zeros((n_rows, n_cols), dtype=int)
    for i, k in enumerate(KS):
        for j, col in enumerate(COLUMNS):
            counts[i, j] = CENSUS[k][col]

    max_c = counts.max()
    cmap = plt.cm.Blues
    norm = plt.Normalize(vmin=0, vmax=max_c)

    for i, k in enumerate(KS):
        for j, col in enumerate(COLUMNS):
            c = counts[i, j]
            face = cmap(norm(c)) if c > 0 else (0.97, 0.97, 0.97, 1.0)
            ax.add_patch(plt.Rectangle(
                (j, n_rows - 1 - i), 1, 1,
                facecolor=face, edgecolor="black", linewidth=0.8,
            ))
            if c == 0:
                ax.text(j + 0.5, n_rows - 1 - i + 0.5, "—",
                        ha="center", va="center", fontsize=12, color="gray")
            else:
                tot = sum(CENSUS[k].values())
                pct = 100 * c / tot
                txt_color = "white" if norm(c) > 0.55 else "black"
                ax.text(j + 0.5, n_rows - 1 - i + 0.62, str(c),
                        ha="center", va="center",
                        fontsize=15, fontweight="bold", color=txt_color)
                ax.text(j + 0.5, n_rows - 1 - i + 0.30, f"{pct:.1f}%",
                        ha="center", va="center",
                        fontsize=9, color=txt_color)

            ab = A_BLOCKED.get((k, col))
            if ab:
                # top-right corner: clear of the centred count and pct texts
                ax.text(j + 0.95, n_rows - 1 - i + 0.92, f"╳{ab}",
                        ha="right", va="top",
                        fontsize=9, color="firebrick", fontweight="bold")

    for i, k in enumerate(KS):
        tot = sum(CENSUS[k].values())
        ax.text(-0.15, n_rows - 1 - i + 0.5, f"k={k}\nn={tot}",
                ha="right", va="center", fontsize=11, fontweight="bold")

    for j, code in enumerate(COL_CODES):
        ax.text(j + 0.5, n_rows + 0.15, code,
                ha="center", va="bottom", fontsize=11, fontweight="bold")

    # One legend line instead of per-column descriptors, which collide at
    # this column width no matter the font size.
    ax.text(n_cols / 2, -1.55,
            "Strata:  " + "  ·  ".join(f"{c} {d}" for c, d in
                                       zip(COL_CODES, COL_DESCS)),
            ha="center", va="top", fontsize=9, color="dimgray")

    # Group brackets — well above the column labels
    bracket_y = n_rows + 0.95
    label_y_main = n_rows + 1.10
    label_y_sub = n_rows + 1.42
    ax.plot([0.05, 2.95], [bracket_y, bracket_y], color="black", linewidth=1.0)
    ax.text(1.5, label_y_main, "Type A",
            ha="center", va="bottom", fontsize=12, fontweight="bold")
    ax.text(1.5, label_y_sub, "(some chi-sum vanishes)",
            ha="center", va="bottom", fontsize=9.5, color="dimgray")
    ax.plot([3.05, 5.95], [bracket_y, bracket_y], color="black", linewidth=1.0)
    ax.text(4.5, label_y_main, "Type B",
            ha="center", va="bottom", fontsize=12, fontweight="bold")
    ax.text(4.5, label_y_sub, "(no chi-sum vanishes)",
            ha="center", va="bottom", fontsize=9.5, color="dimgray")

    ax.text(0.5, -0.85, "A1 collapse:\n68 → 9 → 7 → 1",
            ha="center", va="top", fontsize=9, color="firebrick")
    ax.text(3.5, -0.85, "B0 dominant\nat k=4 (50/77)",
            ha="center", va="top", fontsize=9, color="firebrick")
    ax.text(5.5, -0.85, "B_int emerges\nat k ≥ 5",
            ha="center", va="top", fontsize=9, color="firebrick")

    ax.text(n_cols + 0.15, n_rows - 0.5,
            "╳ N (Type A only):\nnumber of A_blocked\nconfigurations within\nthe cell — some target\nhas δ = k − 2.",
            ha="left", va="center", fontsize=8.5, color="firebrick",
            bbox=dict(boxstyle="round,pad=0.35", facecolor="white",
                      edgecolor="firebrick", linewidth=0.6))

    ax.set_xlim(-0.7, n_cols + 2.8)
    ax.set_ylim(-2.3, n_rows + 2.2)
    ax.set_aspect("equal")
    ax.axis("off")

    plt.title(
        "Figure 4.1.  Census of 421 minimal hard-prime covering configurations\n"
        "by k and mechanism stratum; A_blocked sub-counts annotated (first 80 hard primes)",
        fontsize=12, pad=28,
    )
    plt.tight_layout()
    out_png = FIG_DIR / "figure4_1_census_matrix.png"
    out_pdf = FIG_DIR / "figure4_1_census_matrix.pdf"
    fig.savefig(out_png, dpi=200, bbox_inches="tight")
    fig.savefig(out_pdf, bbox_inches="tight")
    plt.close(fig)
    return out_png


# ---------------------------------------------------------------------------
# Figure 5.1 — Discrimination-depth histogram
# ---------------------------------------------------------------------------

def fig_discrimination_depth():
    fig, ax = plt.subplots(figsize=(11, 5.0))

    levels = [
        "λ=1\nδ-profile",
        "λ=2\nV-graph",
        "λ=3\nI₆",
        "λ=4\n1-WL",
        "λ=5\n2-FWL",
    ]
    counts = [14719, 26, 111, 0, 1]
    y_pos = np.arange(len(levels))
    colors = ["#3b76b5", "#3b76b5", "#3b76b5", "#d8d8d8", "#b22222"]

    ax.barh(y_pos, counts, color=colors, edgecolor="black", linewidth=0.7)

    for i, count in enumerate(counts):
        if count == 0:
            ax.text(150, i, "0   ← empty level",
                    va="center", ha="left", fontsize=11, color="firebrick",
                    fontweight="bold")
        elif count == 1:
            ax.text(150, i, "1   ← singleton  (k = 5)",
                    va="center", ha="left", fontsize=11, color="firebrick",
                    fontweight="bold")
        else:
            ax.text(count + 150, i, f"{count:,}",
                    va="center", ha="left", fontsize=11, fontweight="bold")

    ax.set_yticks(y_pos)
    ax.set_yticklabels(levels, fontsize=10)
    ax.invert_yaxis()
    ax.set_xlabel("Cross-class pairs (exact count; n = 14,857 total)", fontsize=11)
    ax.set_xlim(0, 17500)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    note = (
        "λ(S, T) = min{ r : level-r invariant of S ≠ level-r of T }.\n"
        "\n"
        "λ = 4 is empty: every cross-class pair separated by 1-WL on this\n"
        "census is already separated by δ-profile, V-graph, or I₆\n"
        "(Observation 5.5). 1-WL nonetheless strictly refines I₆ on this\n"
        "graph class (Observation 5.4).\n"
        "\n"
        "λ = 5 singleton (k = 5):\n"
        "   S_A = (937, 1721, 11257, 16729, 18121)   B_int (δ_max=1)\n"
        "   S_B = (1433, 4201, 6361, 9769, 16249)    stratum A3"
    )
    # anchored in the empty area right of the λ ≥ 2 bars, clear of the x-axis
    ax.text(7200, 1.15, note, fontsize=8.5,
            va="top", ha="left", family="monospace",
            bbox=dict(boxstyle="round,pad=0.5", facecolor="#fff7d6",
                      edgecolor="gray", linewidth=0.5))

    plt.title(
        "Figure 5.1.  Discrimination-depth distribution on 14,857 cross-stratum pairs\n"
        "of the exhaustive enumeration at k ∈ {3,4,5,6}, first 80 hard primes",
        fontsize=12, pad=12,
    )
    plt.tight_layout()
    out_png = FIG_DIR / "figure5_1_discrimination_depth.png"
    out_pdf = FIG_DIR / "figure5_1_discrimination_depth.pdf"
    fig.savefig(out_png, dpi=200, bbox_inches="tight")
    fig.savefig(out_pdf, bbox_inches="tight")
    plt.close(fig)
    return out_png


# ---------------------------------------------------------------------------
# Figure 5.2 — V-substructure network around 17881
# ---------------------------------------------------------------------------

V_PIVOT_LEAVES = [
    (937,   ["B₀"],          (-2.8,  1.6)),
    (1721,  ["B₀"],          (-0.0,  2.0)),
    (4297,  ["B₁"],          ( 2.8,  1.6)),
    (6361,  ["sg-A"],        (-2.8, -1.6)),
    (13417, ["S*"],          ( 0.0, -2.0)),
    (18121, ["S*", "sg-B"],  ( 2.8, -1.6)),
]

SET_STYLE = {
    "B₀":   ("#d62728", "B₀ quadruple boundary"),
    "B₁":   ("#9467bd", "B₁ five-set boundary"),
    "S*":   ("#1f77b4", "S* (k=6 full-hub witness)"),
    "sg-A": ("#2ca02c", "singleton, A3 side"),
    "sg-B": ("#ff7f0e", "singleton, B(δ=1) side"),
}


def fig_v_pivot():
    fig, ax = plt.subplots(figsize=(12, 7.5))

    center = (0.0, 0.0)
    cbox = FancyBboxPatch(
        (center[0] - 1.0, center[1] - 0.35),
        2.0, 0.7,
        boxstyle="round,pad=0.08",
        facecolor="#fff7d6", edgecolor="black", linewidth=2.2,
        zorder=3,
    )
    ax.add_patch(cbox)
    ax.text(0, 0.10, "17881", ha="center", va="center",
            fontsize=20, fontweight="bold", zorder=4)
    ax.text(0, -0.20, "central V-substructure node\nS* k=6 hub",
            ha="center", va="center", fontsize=8, color="gray", zorder=4)

    for _, _, pos in V_PIVOT_LEAVES:
        ax.plot([pos[0], center[0]], [pos[1], center[1]],
                color="gray", linewidth=1.3, zorder=1)

    for prime, sets, pos in V_PIVOT_LEAVES:
        box = FancyBboxPatch(
            (pos[0] - 0.65, pos[1] - 0.28),
            1.30, 0.56,
            boxstyle="round,pad=0.05",
            facecolor="white", edgecolor="black", linewidth=1.0,
            zorder=3,
        )
        ax.add_patch(box)
        ax.text(pos[0], pos[1] + 0.07, str(prime),
                ha="center", va="center",
                fontsize=12, fontweight="bold", zorder=4)
        badge_y = pos[1] - 0.16
        badge_w = 0.18
        n = len(sets)
        start_x = pos[0] - badge_w * (n - 1) / 2 - badge_w / 2
        for k_idx, s in enumerate(sets):
            color, _ = SET_STYLE[s]
            badge = plt.Rectangle(
                (start_x + k_idx * badge_w * 1.1, badge_y - 0.04),
                badge_w, 0.08,
                facecolor=color, edgecolor="black", linewidth=0.5,
                zorder=4,
            )
            ax.add_patch(badge)

    legend_patches = [
        mpatches.Patch(color=color, label=label)
        for _, (color, label) in SET_STYLE.items()
    ]
    ax.legend(
        handles=legend_patches, loc="center left",
        bbox_to_anchor=(1.02, 0.78), fontsize=9,
        frameon=True, title="Membership badge", title_fontsize=10,
    )

    set_notes = (
        "S*   = (17881, 1801, 14537, 13417, 18121, 18521)\n"
        "         k=6 full-hub witness, §4.4\n"
        "sg-A = (1433, 4201, 6361, 9769, 16249)\n"
        "         singleton, A3 side, §5.7\n"
        "sg-B = (937, 1721, 11257, 16729, 18121)\n"
        "         singleton, B(δ=1) side, §5.7\n"
        "B₀   = (337, 937, 1433, 1721)\n"
        "         B₀ quadruple boundary\n"
        "B₁   = (4297, 4409, 5689, 6553, 7753)\n"
        "         B₁ five-set boundary\n"
        "\n"
        "Edges:  χ_p(17881) = 0,  i.e., 17881 ∈ V_p  for each leaf p."
    )
    ax.text(-4.6, -3.0, set_notes, ha="left", va="top",
            fontsize=8.5, family="monospace",
            bbox=dict(boxstyle="round,pad=0.5", facecolor="white",
                      edgecolor="gray", linewidth=0.5))

    ax.set_xlim(-5.0, 5.5)
    ax.set_ylim(-4.8, 2.9)
    ax.set_aspect("equal")
    ax.axis("off")

    plt.title("Figure 5.2.  Featured V-substructure: central node 17881  (Remark 5.6)",
              fontsize=12, pad=14)
    plt.tight_layout()
    out_png = FIG_DIR / "figure5_2_v_substructure.png"
    out_pdf = FIG_DIR / "figure5_2_v_substructure.pdf"
    fig.savefig(out_png, dpi=200, bbox_inches="tight")
    fig.savefig(out_pdf, bbox_inches="tight")
    plt.close(fig)
    return out_png


def main():
    print(f"Generating figures into {FIG_DIR}")
    print(f"  {fig_census_matrix()}")
    print(f"  {fig_discrimination_depth()}")
    print(f"  {fig_v_pivot()}")


if __name__ == "__main__":
    main()
