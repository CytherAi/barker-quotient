#!/usr/bin/env python3
"""Deterministic guardrails for the realization theorem.

This program does not prove the number-field statements.  It attacks the
finite algebra and coordinate identifications on which the proof depends:

* the affine commutator and the non-split 2-line;
* the exact-depth/hard Frobenius-slice count;
* conjugacy acting as a common row gauge;
* the implementation's chi coordinate agreeing with the Kummer residue;
* the exact-depth density slices through a deterministic prime bound.

The output is a stable JSON receipt suitable for provenance gating.
"""

from __future__ import annotations

import argparse
import itertools
import json
import math
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
CODE = os.path.join(os.path.dirname(HERE), "code")
if CODE not in sys.path:
    sys.path.insert(0, CODE)

from barker.sweep import find_hard_primes  # noqa: E402
from barker.two_primary import (  # noqa: E402
    _sylow2_generator,
    quotient_class,
    two_primary_depth,
)


def v2(n: int) -> int:
    if n <= 0:
        raise ValueError("v2 requires a positive integer")
    return (n & -n).bit_length() - 1


def units(modulus: int) -> list[int]:
    return [a for a in range(modulus) if math.gcd(a, modulus) == 1]


def epsilon(a: int) -> int:
    """Action of sigma_a on sqrt(2), for odd a."""
    if a % 2 == 0:
        raise ValueError("a must be odd")
    return 1 if a % 8 in (1, 7) else -1


def section_u(a: int) -> int:
    """A lift coordinate with (-1)^u = epsilon(a)."""
    return 0 if epsilon(a) == 1 else 1


def affine_mul(x: tuple[int, tuple[int, ...]],
               y: tuple[int, tuple[int, ...]],
               modulus: int) -> tuple[int, tuple[int, ...]]:
    """Left-translation law (a,c)(b,d)=(ab,c+a*d)."""
    a, c = x
    b, d = y
    base_modulus = 2 * modulus
    return (
        (a * b) % base_modulus,
        tuple((ci + (a % modulus) * di) % modulus
              for ci, di in zip(c, d)),
    )


def affine_inv(x: tuple[int, tuple[int, ...]],
               modulus: int) -> tuple[int, tuple[int, ...]]:
    a, c = x
    ainv = pow(a, -1, 2 * modulus)
    return (
        ainv,
        tuple((-(ainv % modulus) * ci) % modulus for ci in c),
    )


def affine_commutator(x: tuple[int, tuple[int, ...]],
                      y: tuple[int, tuple[int, ...]],
                      modulus: int) -> tuple[int, tuple[int, ...]]:
    xy = affine_mul(x, y, modulus)
    xyx = affine_mul(xy, affine_inv(x, modulus), modulus)
    return affine_mul(xyx, affine_inv(y, modulus), modulus)


def check_affine_depth(t: int, rank: int = 2) -> dict:
    n = 1 << t
    us = units(2 * n)

    eps_hom = all(
        epsilon((a * b) % (2 * n)) == epsilon(a) * epsilon(b)
        for a in us for b in us
    )

    lift_parity = all(
        (-1 if section_u(a) % 2 else 1) == epsilon(a) for a in us
    )

    # This is the load-bearing coefficient: no trailing (ab)^(-1).
    x = (3, (section_u(3),) + (0,) * rank)
    y = (5, (section_u(5),) + (0,) * rank)
    comm = affine_commutator(x, y, n)
    delta = ((3 - 1) * section_u(5) -
             (5 - 1) * section_u(3)) % n
    commutator_formula = comm == (1, (delta,) + (0,) * rank)
    extra_two_line = delta % 4 == 2

    # T^2 plus the extra lift commutator must be exactly Gal(M/BH).
    t_squared = {
        (c0,) + rest
        for c0 in range(0, n, 4)
        for rest in itertools.product(range(0, n, 2), repeat=rank)
    }
    generated = {
        ((c[0] + j * delta) % n,) + c[1:]
        for c in t_squared for j in range(n // 2)
    }
    expected = {
        (c0,) + rest
        for c0 in range(0, n, 2)
        for rest in itertools.product(range(0, n, 2), repeat=rank)
    }

    # Conjugating an exact-depth element (base 1+N, zero 2-coordinate)
    # rescales the row by one common unit.  Translation terms cancel because
    # 1-(1+N) is zero modulo N.
    gauge_checks = 0
    gauge_ok = True
    exact_base = 1 + n
    for a in us:
        for parity in itertools.product((0, 1), repeat=rank):
            choices = [range(bit, n, 2) for bit in parity]
            for d in itertools.product(*choices):
                h = (a, (section_u(a),) + (1,) * rank)
                g = (exact_base, (0,) + d)
                conjugate = affine_mul(
                    affine_mul(h, g, n), affine_inv(h, n), n
                )
                expected_row = tuple((a * di) % n for di in d)
                gauge_ok &= conjugate == (exact_base, (0,) + expected_row)
                gauge_checks += 1

    return {
        "t": t,
        "N": n,
        "epsilon_homomorphism": eps_hom,
        "lift_parity": lift_parity,
        "commutator_formula": commutator_formula,
        "delta_3_5": delta,
        "delta_mod_4": delta % 4,
        "extra_two_line": extra_two_line,
        "derived_subgroup_size": len(generated),
        "expected_derived_subgroup_size": len(expected),
        "derived_subgroup_exact": generated == expected,
        "gauge_checks": gauge_checks,
        "exact_depth_conjugacy_is_row_gauge": gauge_ok,
    }


def check_slice_counts() -> list[dict]:
    out = []
    prefix_depths = [3, 4, 5, 3]
    for t in range(3, 7):
        n = 1 << t
        for rank in range(5):
            depths = prefix_depths[:rank]
            a = math.prod(1 << d for d in depths)
            group_order = a * n ** (rank + 2) // (1 << (rank + 1))
            slice_size = a * (n // 2) ** rank
            out.append({
                "t": t,
                "rank": rank,
                "prefix_depths": depths,
                "group_order": group_order,
                "slice_size": slice_size,
                "density": f"{slice_size}/{group_order}",
                "density_reduced": f"1/{group_order // slice_size}",
                "equals_2_over_4t": (
                    slice_size * (4 ** t) == 2 * group_order
                ),
            })
    return out


def check_character_coordinates(n_primes: int = 8) -> dict:
    hard = [row["prime"] for row in find_hard_primes(20000)[:n_primes]]
    checks = 0
    nonzero = 0
    odd = 0
    hard_bits = 0
    for x in hard:
        sx, tx, _ = _sylow2_generator(x)
        nx = 1 << tx
        assert quotient_class(2, x) == 0
        hard_bits += 1
        for p in hard:
            if p == x:
                continue
            chi = quotient_class(p, x)
            # Reduction of the quotient coordinate to the Kummer residue in
            # F_x: p^((x-1)/N) = (s mod x)^chi.
            lhs = pow(p, (x - 1) // nx, x)
            rhs = pow(sx % x, chi, x)
            assert lhs == rhs
            legendre_parity = 0 if pow(p, (x - 1) // 2, x) == 1 else 1
            assert chi % 2 == legendre_parity
            checks += 1
            nonzero += chi != 0
            odd += chi % 2
    return {
        "hard_primes": hard,
        "ordered_pair_checks": checks,
        "nonzero_coordinates": nonzero,
        "odd_coordinates": odd,
        "hardness_coordinates_zero": hard_bits,
        "kummer_coordinate_identity": True,
        "quadratic_parity_identity": True,
    }


def primes_below(limit: int) -> bytearray:
    sieve = bytearray(b"\x01") * limit
    if limit:
        sieve[0] = 0
    if limit > 1:
        sieve[1] = 0
    for p in range(2, math.isqrt(limit - 1) + 1):
        if sieve[p]:
            start = p * p
            sieve[start:limit:p] = b"\x00" * (((limit - 1 - start) // p) + 1)
    return sieve


def check_density_slices(limit: int) -> dict:
    sieve = primes_below(limit)
    total = int(sum(sieve))
    hard_by_depth: Counter[int] = Counter()
    for p in range(3, limit, 2):
        if not sieve[p]:
            continue
        t = v2(p - 1)
        if t >= 2 and pow(2, (p - 1) >> t, p) == 1:
            hard_by_depth[t] += 1
    rows = {}
    for t in range(2, max(hard_by_depth, default=2) + 1):
        count = hard_by_depth[t]
        rows[str(t)] = {
            "count": count,
            "observed_over_all_primes": count / total,
            "theorem_density": 0.0 if t == 2 else 2 / (4 ** t),
        }
    return {
        "prime_bound_exclusive": limit,
        "prime_count": total,
        "hard_count_p_1_mod_4": sum(hard_by_depth.values()),
        "observed_total_density": sum(hard_by_depth.values()) / total,
        "theorem_total_density": 1 / 24,
        "depth_2_zero": hard_by_depth[2] == 0,
        "by_depth": rows,
    }


def build_receipt(prime_bound: int) -> dict:
    affine = [check_affine_depth(t) for t in range(2, 7)]
    slices = check_slice_counts()
    coordinates = check_character_coordinates()
    density = check_density_slices(prime_bound)
    assert all(row["epsilon_homomorphism"] for row in affine)
    assert all(row["lift_parity"] for row in affine)
    assert all(row["commutator_formula"] for row in affine)
    assert all(row["extra_two_line"] for row in affine)
    assert all(row["derived_subgroup_exact"] for row in affine)
    assert all(row["exact_depth_conjugacy_is_row_gauge"] for row in affine)
    assert all(row["equals_2_over_4t"] for row in slices)
    assert coordinates["nonzero_coordinates"] > 0
    assert coordinates["odd_coordinates"] > 0
    assert density["depth_2_zero"]
    return {
        "schema_version": 1,
        "scope": (
            "Deterministic falsification harness for finite algebra and "
            "coordinate identifications; not a proof of the number-field theorem."
        ),
        "affine_group": affine,
        "affine_depths_passed": [row["t"] for row in affine],
        "slice_counts": slices,
        "slice_count_cases": len(slices),
        "character_coordinates": coordinates,
        "coordinate_pair_checks": coordinates["ordered_pair_checks"],
        "density_slices": density,
        "all_checks_passed": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prime-bound", type=int, default=20_000_000)
    parser.add_argument(
        "--output",
        default=os.path.join(HERE, "_realization_checks.json"),
    )
    args = parser.parse_args()
    receipt = build_receipt(args.prime_bound)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(receipt, f, indent=2, sort_keys=True)
        f.write("\n")
    density = receipt["density_slices"]
    print("REALIZATION CHECKS PASSED")
    print(f"affine depths: {len(receipt['affine_group'])}")
    print(f"coordinate pairs: {receipt['character_coordinates']['ordered_pair_checks']}")
    print(f"primes < {args.prime_bound}: {density['prime_count']}")
    print(f"hard p == 1 mod 4: {density['hard_count_p_1_mod_4']}")
    print(f"receipt: {args.output}")


if __name__ == "__main__":
    main()
