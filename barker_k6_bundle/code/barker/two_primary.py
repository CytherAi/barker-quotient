"""
barker.two_primary
==================
2-primary character analysis for the hard-prime frontier.

Mathematical setting
--------------------
For an odd prime x, the unit group G_x := (Z/x²Z)* is cyclic of order

    φ(x²) = x(x-1) = 2^t · m,    m odd,    t = v₂(x-1).

G_x has a unique odd-order subgroup H_x ≤ G_x of index 2^t, and a quotient

    Q_x := G_x / H_x  ≅  C_{2^t}.

The 2-torsion subgroup of Q_x is {0, 2^(t-1)} in additive notation
(the identity and the unique involution).

Key criterion
-------------
For p ∈ G_x:

    ord_{x²}(p) odd   iff   χ_x(p) = 0   (p ∈ H_x, trivial class)
    ord_{x²}(p) even  iff   χ_x(p) ≠ 0   (p ∉ H_x)

Pair cancellation
-----------------
Writing χ_x(p) ∈ Z/2^t (additive C_{2^t}):

    p·q ∈ H_x   iff   χ_x(p) + χ_x(q) ≡ 0 (mod 2^t).

Triple failure (all three pairs fail at target x) requires

    χ_x(a) + χ_x(b) ≡ 0,   χ_x(a) + χ_x(c) ≡ 0   →   χ_x(b) = χ_x(c).
    Then  χ_x(b) + χ_x(c) = 2·χ_x(b) ≡ 0 (mod 2^t)   iff   χ_x(b) ∈ {0, 2^(t-1)}.

So all three pairs fail at x  ⟺  χ_x(a) = χ_x(b) = χ_x(c) ∈ {0, 2^(t-1)}.

Empirical theorem (verified for all 7 hard primes < 1000)
---------------------------------------------------------
For every hard prime x and every torsion class c ∈ {0, 2^(t-1)}, at most
ONE other hard prime has χ_x = c.

This is strictly stronger than "max_failing ≤ 2 for triples" — it rules
out even TWO-prime torsion concentration, making triple failure impossible.

References
----------
- J.-P. Serre, "A Course in Arithmetic", Ch. 6.
- K. H. Leung and B. Schmidt (2005): self-conjugacy = χ_x ≠ 0 condition.
- R. J. Turyn (1968): the generalised test uses χ_x(a·b) ≠ 0.
"""

from __future__ import annotations
from dataclasses import dataclass

from .arithmetic import (
    multiplicative_order, jacobi_symbol, is_prime,
)


# ---------------------------------------------------------------------------
# Basic 2-primary machinery
# ---------------------------------------------------------------------------

def _v2(n: int) -> int:
    """v₂(n) — 2-adic valuation.  n must be nonzero."""
    if n == 0:
        raise ValueError("v₂(0) is infinite")
    k = 0
    while n % 2 == 0:
        k += 1
        n >>= 1
    return k


def _odd_part(n: int) -> int:
    if n <= 0:
        raise ValueError(f"_odd_part undefined for {n}; requires a positive integer")
    while n % 2 == 0:
        n >>= 1
    return n


def two_primary_depth(x: int) -> int:
    """t_x = v₂(x-1) — depth of the 2-Sylow quotient of (Z/x²Z)*."""
    if not is_prime(x) or x == 2:
        raise ValueError(f"x must be an odd prime; got {x}")
    return _v2(x - 1)


def two_primary_level(p: int, x: int) -> int:
    """λ_x(p) = v₂(ord_{x²}(p)) — 2-primary level of p in G_x."""
    d = multiplicative_order(p % (x * x), x * x)
    return _v2(d)


def in_odd_subgroup(p: int, x: int) -> bool:
    """True iff p ∈ H_x (odd order mod x²), i.e., λ_x(p) = 0."""
    return two_primary_level(p, x) == 0


def legendre_layer(p: int, x: int) -> int:
    """Legendre symbol (p/x) — the first bit of the 2-primary filtration."""
    return jacobi_symbol(p % x, x)


# ---------------------------------------------------------------------------
# Sylow 2-generator and quotient class
# ---------------------------------------------------------------------------

def _sylow2_generator(x: int) -> tuple[int, int, int]:
    """
    Find a generator of the unique Sylow 2-subgroup of (Z/x²Z)*.

    Returns (s, t, m) where:
      s  = g^m mod x²  (generator of Sylow 2-subgroup, order 2^t)
      t  = v₂(φ(x²)) = v₂(x(x-1)) = v₂(x-1)
      m  = φ(x²) / 2^t  (odd part)

    g is the smallest primitive root mod x².
    """
    M  = x * (x - 1)      # φ(x²)
    t  = _v2(M)
    m  = M >> t
    x2 = x * x

    for g in range(2, x2):
        if multiplicative_order(g, x2) == M:
            s = pow(g, m, x2)
            return s, t, m
    raise RuntimeError(f"No primitive root found for x={x}")


_SYLOW_CACHE: dict = {}


def quotient_class(p: int, x: int) -> int:
    """
    χ_x(p) ∈ {0, 1, ..., 2^t - 1} — image of p in Q_x ≅ C_{2^t}.

    Defined as the discrete log of p^m in ⟨s⟩ = Sylow 2-subgroup,
    where s = g^m mod x² is the canonical Sylow generator.

    χ_x(p) = 0   iff   p ∈ H_x   iff   ord_{x²}(p) is odd.

    Raises ValueError if p is not invertible mod x² (e.g. p ≡ 0 mod x,
    or p = x).  x must be an odd prime.

    The per-x Sylow generator computation is memoised in module-level
    `_SYLOW_CACHE` since it is the expensive step.
    """
    if x not in _SYLOW_CACHE:
        _SYLOW_CACHE[x] = _sylow2_generator(x)
    s, t, m = _SYLOW_CACHE[x]

    x2 = x * x
    pm = pow(p % x2, m, x2)   # image in Sylow 2-subgroup

    power = 1
    for k in range(2 ** t):
        if power == pm:
            return k
        power = power * s % x2
    raise ValueError(
        f"Discrete log failed for p={p} mod x²={x*x}: "
        f"p^m={pm} not found in ⟨s={s}⟩ (t={t}).  "
        f"Likely cause: p ≡ 0 (mod x) or p = x (not invertible mod x²)."
    )


def is_2torsion(p: int, x: int) -> bool:
    """
    True iff χ_x(p) ∈ {0, 2^(t-1)} — p lies in the 2-torsion of Q_x.

    The 2-torsion subgroup of C_{2^t} is {0, 2^(t-1)}: the identity
    and the unique involution.

    p ∈ 2-torsion  ⟺  p has order ≤ 2 in Q_x
                   ⟺  p^2 ∈ H_x
                   ⟺  ord_{x²}(p) divides 2·|H_x|
    """
    t   = two_primary_depth(x)
    chi = quotient_class(p, x)
    return chi in {0, 2 ** (t - 1)}


# ---------------------------------------------------------------------------
# 2-primary character table
# ---------------------------------------------------------------------------

@dataclass
class TwoPrimaryCharacterTable:
    """
    Full 2-primary character data for a set of hard primes.

    Attributes
    ----------
    primes         : the hard primes
    depth          : {x: t_x}
    level          : {(p,x): λ_x(p)}
    chi            : {(p,x): χ_x(p) ∈ Z/2^t}
    legendre       : {(p,x): (p/x)}
    pair_level     : {((a,b),x): λ_x(a·b)}  (a<b, x ∉ {a,b})
    pair_chi_sum   : {((a,b),x): (χ_x(a)+χ_x(b)) mod 2^t}  — 0 = cancellation
    cancellations  : {(a,b): [x where pair cancels]}
    universal_pairs: pairs with zero cancellations
    torsion_primes : {x: [(p, chi) where chi ∈ 2-torsion of Q_x]}
    max_torsion_concentration: max number of primes in any single torsion class
    """
    primes:                       list[int]
    depth:                        dict[int, int]
    level:                        dict[tuple, int]
    chi:                          dict[tuple, int]
    legendre:                     dict[tuple, int]
    pair_level:                   dict[tuple, int]
    pair_chi_sum:                 dict[tuple, int]
    cancellations:                dict[tuple, list[int]]
    universal_pairs:              list[tuple]
    torsion_primes:               dict[int, list[tuple]]
    max_torsion_concentration:    int

    def is_sc(self, p: int, q: int) -> bool:
        return self.level.get((p, q), -1) > 0

    def cancels(self, a: int, b: int, x: int) -> bool:
        """True iff χ_x(a) + χ_x(b) ≡ 0.  Symmetric in a and b.

        `pair_chi_sum` is keyed with the smaller prime first, so the key must
        be normalised here: looking up (a, b) verbatim silently returned False
        for every call with a > b, reporting a cancelling pair as non-cancelling.
        """
        key = (a, b) if a < b else (b, a)
        return self.pair_chi_sum.get((key, x), -1) == 0


def build_two_primary_table(primes: list[int]) -> TwoPrimaryCharacterTable:
    """Build the complete 2-primary character table."""
    from itertools import combinations as _comb

    depth:         dict[tuple, int] = {x: two_primary_depth(x) for x in primes}
    level:         dict[tuple, int] = {}
    chi_dict:      dict[tuple, int] = {}
    legendre:      dict[tuple, int] = {}

    for p in primes:
        for x in primes:
            if p == x:
                continue
            level[(p, x)]    = two_primary_level(p, x)
            chi_dict[(p, x)] = quotient_class(p, x)
            legendre[(p, x)] = legendre_layer(p, x)

    pair_level:    dict[tuple, int] = {}
    pair_chi_sum:  dict[tuple, int] = {}

    for a, b in _comb(sorted(primes), 2):
        for x in primes:
            if x in (a, b):
                continue
            t   = depth[x]
            two_t = 2 ** t
            pair_level[((a, b), x)]    = two_primary_level(a * b, x)
            pair_chi_sum[((a, b), x)]  = (chi_dict[(a, x)] + chi_dict[(b, x)]) % two_t

    # Cancellations and universal pairs
    cancellations: dict[tuple, list] = {}
    universal_pairs = []
    for a, b in _comb(sorted(primes), 2):
        others  = [x for x in primes if x not in (a, b)]
        cancels = [x for x in others if pair_chi_sum[((a, b), x)] == 0]
        cancellations[(a, b)] = cancels
        if not cancels:
            universal_pairs.append((a, b))

    # 2-torsion concentration
    torsion_primes: dict[int, list] = {}
    max_conc = 0
    for x in primes:
        t    = depth[x]
        inv  = 2 ** (t - 1)
        tors = [(p, chi_dict[(p, x)]) for p in primes
                if p != x and chi_dict[(p, x)] in {0, inv}]
        torsion_primes[x] = tors
        # Count within each torsion class
        for cls in {0, inv}:
            count = sum(1 for _, c in tors if c == cls)
            max_conc = max(max_conc, count)

    return TwoPrimaryCharacterTable(
        primes=primes,
        depth=depth,
        level=level,
        chi=chi_dict,
        legendre=legendre,
        pair_level=pair_level,
        pair_chi_sum=pair_chi_sum,
        cancellations=cancellations,
        universal_pairs=universal_pairs,
        torsion_primes=torsion_primes,
        max_torsion_concentration=max_conc,
    )


# ---------------------------------------------------------------------------
# Pair-sufficiency proof structure
# ---------------------------------------------------------------------------

@dataclass
class TripleCancellationResult:
    triple:    tuple[int, int, int]
    levels:    dict[tuple, int]
    n_failing: int
    all_fail:  bool


def triple_cancellation_analysis(
    primes: list[int],
) -> list[TripleCancellationResult]:
    """
    For every triple, check whether all three pairs simultaneously fail.
    Equivalent to: all three χ_x values in same 2-torsion class.
    """
    from itertools import combinations as _comb
    results = []
    for a, b, c in _comb(primes, 3):
        lv_ab_c = two_primary_level(a * b, c)
        lv_ac_b = two_primary_level(a * c, b)
        lv_bc_a = two_primary_level(b * c, a)
        n = (lv_ab_c == 0) + (lv_ac_b == 0) + (lv_bc_a == 0)
        results.append(TripleCancellationResult(
            triple=(a, b, c),
            levels={
                ((a, b), c): lv_ab_c,
                ((a, c), b): lv_ac_b,
                ((b, c), a): lv_bc_a,
            },
            n_failing=n,
            all_fail=(n == 3),
        ))
    return results


# ---------------------------------------------------------------------------
# Formatted output
# ---------------------------------------------------------------------------

def format_character_table(tbl: TwoPrimaryCharacterTable) -> str:
    """Render the 2-primary quotient class and level table."""
    primes = tbl.primes
    lines  = []
    div    = "─" * 72
    lines.append(div)
    lines.append("  2-Primary Character Table:  χ_x(p) ∈ Q_x ≅ C_{2^t}")
    lines.append("  λ_x(p) = v₂(ord_{x²}(p))   ★ = p in 2-torsion of Q_x")
    lines.append(f"  Primes: {primes}")
    lines.append(f"  Depths t_x: {tbl.depth}")
    lines.append(div)

    hdr = f"  {'p':>6}"
    for x in primes:
        hdr += f"  {'x='+str(x):>12}(C_{2**tbl.depth[x]})"
    lines.append(hdr)
    lines.append("  " + "─" * (len(hdr) - 2))

    for p in primes:
        row = f"  {p:>6}"
        for x in primes:
            if p == x:
                row += f"  {'—':>18}"
                continue
            t     = tbl.depth[x]
            inv   = 2 ** (t - 1)
            chi   = tbl.chi[(p, x)]
            lv    = tbl.level[(p, x)]
            in_t  = chi in {0, inv}
            mark  = "★" if in_t else " "
            row  += f"  χ={chi:>2}/{2**t-1} λ={lv}{mark}   "
        lines.append(row)

    lines.append(div)
    lines.append("  ★ marks primes in the 2-torsion {0, 2^(t-1)} of Q_x")
    lines.append(f"  Max 2-torsion concentration: {tbl.max_torsion_concentration} per class")
    lines.append(div)

    lines.append("")
    lines.append(f"  2-torsion membership by prime:")
    for p in primes:
        tors_xs = [(x, tbl.chi[(p,x)], 2**tbl.depth[x])
                   for x in primes if x != p and tbl.chi[(p,x)] in {0, 2**(tbl.depth[x]-1)}]
        if tors_xs:
            lines.append(f"    p={p}: 2-torsion at x ∈ {tors_xs}")
        else:
            lines.append(f"    p={p}: never in 2-torsion for any tested x")

    lines.append(div)
    lines.append("")
    lines.append(f"  Universal witness pairs ({len(tbl.universal_pairs)}):")
    for a, b in tbl.universal_pairs:
        lines.append(f"    {a}·{b} = {a*b:,}")
    lines.append(div)
    return "\n".join(lines)


def format_triple_analysis(results: list[TripleCancellationResult]) -> str:
    """Summarise triple cancellation analysis."""
    lines = []
    div   = "─" * 60
    lines.append(div)
    lines.append("  Triple Cancellation Analysis")
    lines.append("  (Triple fails iff χ_x(a)=χ_x(b)=χ_x(c) ∈ 2-torsion of Q_x)")
    lines.append(div)
    max_failing = max(r.n_failing for r in results)
    worst       = [r for r in results if r.n_failing == max_failing]
    lines.append(f"  Total triples: {len(results)}")
    lines.append(f"  All-fail (pair-suff violated): {sum(r.all_fail for r in results)}")
    lines.append(f"  Max failing pairs per triple:  {max_failing}")
    lines.append("")
    lines.append("  Worst cases:")
    for r in worst:
        a, b, c = r.triple
        lv1 = r.levels[((a, b), c)]
        lv2 = r.levels[((a, c), b)]
        lv3 = r.levels[((b, c), a)]
        lines.append(
            f"    ({a},{b},{c}): "
            f"λ_{c}({a}·{b})={lv1}  "
            f"λ_{b}({a}·{c})={lv2}  "
            f"λ_{a}({b}·{c})={lv3}  "
            f"→ {r.n_failing}/3 failing"
        )
    lines.append(div)
    return "\n".join(lines)
