"""
barker.arithmetic
=================
Core number-theoretic primitives for the Barker admissibility filter.

All arithmetic is exact, using Python's arbitrary-precision integers.
No external dependencies. The only import is the standard library.

Public API
----------
is_prime(n)                  -> bool
factorize(n)                 -> dict[int, int]   {prime: exponent}
valuation(n, p)              -> int               v_p(n)
euler_phi(n)                 -> int
multiplicative_order(a, m)   -> int               ord_m(a), gcd(a,m)=1
is_self_conjugate(a, m)      -> (bool, int|None)  a^j ≡ -1 (mod m)?
integer_sqrt(n)              -> int|None          exact √n or None
prime_factors(n)             -> list[int]         sorted, with repetition
"""

from __future__ import annotations
import math


# ---------------------------------------------------------------------------
# Primality — Miller-Rabin with deterministic witness sets
# ---------------------------------------------------------------------------

# These witness sets are sufficient (unconditionally) for the stated bounds.
# Source: Pomerance, Selfridge, Wagstaff (1980); subsequent refinements by
# Jaeschke (1993) and Sorenson-Webster (2015).
_MR_BOUNDS: list[tuple[int, list[int]]] = [
    (2_047,                    [2]),
    (1_373_653,                [2, 3]),
    (9_080_191,                [31, 73]),
    (25_326_001,               [2, 3, 5]),
    (3_215_031_751,            [2, 3, 5, 7]),
    (4_759_123_141,            [2, 7, 61]),
    (1_122_004_669_633,        [2, 13, 23, 1_662_803]),
    (2_152_302_898_747,        [2, 3, 5, 7, 11]),
    (3_474_749_660_383,        [2, 3, 5, 7, 11, 13]),
    (341_550_071_728_321,      [2, 3, 5, 7, 11, 13, 17]),
    (3_825_123_056_546_413_051,[2, 3, 5, 7, 11, 13, 17, 19, 23]),
]
# For n beyond the last bound we fall back to this probabilistic set,
# which is strong enough for any composite to pass with negligible probability.
_MR_FALLBACK: list[int] = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37]

_SMALL_PRIMES: list[int] = [
    2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47,
    53, 59, 61, 67, 71, 73, 79, 83, 89, 97, 101, 103, 107, 109, 113,
]


def _mr_witnesses(n: int) -> list[int]:
    for bound, witnesses in _MR_BOUNDS:
        if n < bound:
            return witnesses
    return _MR_FALLBACK


def is_prime(n: int) -> bool:
    """
    Deterministic Miller-Rabin primality test.

    Unconditionally correct for n < 3.8·10^18 (covers all Barker
    structural components reachable before factorization becomes the
    bottleneck). For larger n the witness set is probabilistic but
    astronomically reliable in practice.
    """
    if n < 2:
        return False
    if n == 2:
        return True
    if n & 1 == 0:
        return False
    for p in _SMALL_PRIMES:
        if n == p:
            return True
        if n % p == 0:
            return False

    # Write n − 1 = 2^r · d, d odd
    r, d = 0, n - 1
    while d & 1 == 0:
        r += 1
        d >>= 1

    for a in _mr_witnesses(n):
        if a >= n:
            continue
        x = pow(a, d, n)
        if x == 1 or x == n - 1:
            continue
        for _ in range(r - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                break
        else:
            return False
    return True


# ---------------------------------------------------------------------------
# Factorization — trial division + Pollard's rho
# ---------------------------------------------------------------------------

def _pollard_rho(n: int) -> int | None:
    """
    Brent's improvement of Pollard's rho algorithm.
    Returns a non-trivial factor of n, or None if the run fails.
    n must be composite and odd.
    """
    if n % 2 == 0:
        return 2
    for c in range(1, 100):          # try many c values before giving up
        x = 2
        y = 2
        d = 1
        f = lambda t: (t * t + c) % n
        while d == 1:
            x = f(x)
            y = f(f(y))
            d = math.gcd(abs(x - y), n)
        if d != n:
            return d
    return None


def _factor_into(n: int, acc: dict[int, int]) -> None:
    """Recursively factor n, accumulating prime → exponent into acc."""
    if n <= 1:
        return
    if is_prime(n):
        acc[n] = acc.get(n, 0) + 1
        return
    # Trial division for small primes
    for p in _SMALL_PRIMES:
        if p * p > n:
            # n is prime
            acc[n] = acc.get(n, 0) + 1
            return
        if n % p == 0:
            while n % p == 0:
                acc[p] = acc.get(p, 0) + 1
                n //= p
            if n > 1:
                _factor_into(n, acc)
            return
    # Pollard's rho
    d = _pollard_rho(n)
    if d is None or d == n:
        raise FactorizationError(
            f"Cannot factor {n}. Install sympy for large-number support."
        )
    _factor_into(d, acc)
    _factor_into(n // d, acc)


class FactorizationError(ValueError):
    """Raised when factorization cannot complete."""


def factorize(n: int) -> dict[int, int]:
    """
    Return the prime factorization of n as {prime: exponent}.

    >>> factorize(360)
    {2: 3, 3: 2, 5: 1}
    >>> factorize(1)
    {}
    """
    if n < 2:
        return {}
    acc: dict[int, int] = {}
    _factor_into(n, acc)
    return acc


def prime_factors(n: int) -> list[int]:
    """
    Sorted list of prime factors of n, with repetition.

    >>> prime_factors(12)
    [2, 2, 3]
    """
    factors = factorize(n)
    result = []
    for p in sorted(factors):
        result.extend([p] * factors[p])
    return result


# ---------------------------------------------------------------------------
# Valuation and Euler phi
# ---------------------------------------------------------------------------

def valuation(n: int, p: int) -> int:
    """
    Return v_p(n): the largest k such that p^k divides n.

    Raises ValueError if n == 0 (v_p(0) is infinite) or p < 2.

    >>> valuation(72, 2)
    3
    >>> valuation(72, 3)
    2
    """
    if n == 0:
        raise ValueError("valuation(0, p) is infinite")
    if p < 2:
        raise ValueError(f"valuation requires p >= 2; got {p}")
    n = abs(n)
    k = 0
    while n % p == 0:
        k += 1
        n //= p
    return k


def euler_phi(n: int) -> int:
    """
    Euler's totient φ(n).  n must be a positive integer.

    Raises ValueError if n <= 0.

    >>> euler_phi(1)
    1
    >>> euler_phi(12)
    4
    >>> euler_phi(97)
    96
    """
    if n <= 0:
        raise ValueError(f"euler_phi defined for positive integers only; got {n}")
    if n == 1:
        return 1
    factors = factorize(n)
    result = 1
    for p, a in factors.items():
        result *= (p - 1) * p ** (a - 1)
    return result


# ---------------------------------------------------------------------------
# Multiplicative order
# ---------------------------------------------------------------------------

def multiplicative_order(a: int, m: int) -> int:
    """
    Compute ord_m(a): the smallest positive integer k with a^k ≡ 1 (mod m).

    Raises ValueError if gcd(a, m) ≠ 1.  Uses the standard algorithm:
      — order divides φ(m)
      — repeatedly divide φ(m) by each prime factor p while a^(order/p) ≡ 1

    >>> multiplicative_order(2, 7)
    3
    >>> multiplicative_order(2, 5)
    4
    >>> multiplicative_order(2, 73)
    9
    """
    a = a % m
    if math.gcd(a, m) != 1:
        raise ValueError(f"gcd({a}, {m}) ≠ 1; multiplicative order undefined")
    phi = euler_phi(m)
    order = phi
    phi_factors = set(factorize(phi).keys())
    for p in phi_factors:
        while order % p == 0 and pow(a, order // p, m) == 1:
            order //= p
    return order


# ---------------------------------------------------------------------------
# Self-conjugacy
# ---------------------------------------------------------------------------

def is_self_conjugate(a: int, m: int) -> tuple[bool, int | None]:
    """
    Determine whether a is *self-conjugate* modulo m, i.e., whether
    a^j ≡ -1 (mod m) for some positive integer j.

    Returns (True, j) with the minimal such j, or (False, None).

    Mathematical background
    -----------------------
    In (Z/mZ)*, -1 is the unique element of order 2.  The element a
    is self-conjugate mod m iff -1 lies in the cyclic subgroup ⟨a⟩.
    When m = p is prime and gcd(a,p) = 1, this is equivalent to:
      ord_p(a) is even  AND  a^(ord_p(a)/2) ≡ -1 (mod p).

    For composite m the iteration is used directly.

    Reference
    ---------
    Schmidt (2002) "Cyclotomic Integers and Finite Geometry", Def. 2.1.
    Leung–Schmidt (2005), §2 "Self-conjugate elements".

    >>> is_self_conjugate(2, 5)   # 2^2 = 4 ≡ -1 (mod 5)
    (True, 2)
    >>> is_self_conjugate(2, 73)  # ord_73(2) = 9, odd → not self-conjugate
    (False, None)
    >>> is_self_conjugate(2, 7)   # 2^3 = 8 ≡ 1 (mod 7), not -1; 7 ≡ 3 (mod 4)
    (False, None)
    """
    if m <= 1:
        return False, None
    a = a % m
    if a == 0 or math.gcd(a, m) != 1:
        return False, None

    target = m - 1          # −1 mod m
    order  = multiplicative_order(a, m)

    # Iterate the cyclic group ⟨a⟩ looking for −1.
    # We only need to check up to ord/2 because a^(ord−j) = (a^j)^(−1) ≠ −1
    # if a^j ≠ 1, but we iterate the full orbit to be safe.
    power = a
    for j in range(1, order + 1):
        if power == target:
            return True, j
        power = power * a % m

    return False, None


# ---------------------------------------------------------------------------
# Integer square root
# ---------------------------------------------------------------------------

def integer_sqrt(n: int) -> int | None:
    """
    If n is a perfect square return √n (as an int), else return None.

    Uses Newton's method on integers (exact).

    >>> integer_sqrt(36)
    6
    >>> integer_sqrt(37)
    # None
    """
    if n < 0:
        return None
    if n == 0:
        return 0
    s = math.isqrt(n)
    return s if s * s == n else None


# ---------------------------------------------------------------------------
# Jacobi / Kronecker symbol (needed for Leung-Schmidt layer)
# ---------------------------------------------------------------------------

def jacobi_symbol(a: int, n: int) -> int:
    """
    Compute the Jacobi symbol (a/n).  n must be a positive odd integer.
    Returns −1, 0, or 1.

    When n is prime this equals the Legendre symbol.

    Algorithm: quadratic-reciprocity based reduction (Eisenstein/binary form).
    """
    if n <= 0 or n % 2 == 0:
        raise ValueError(f"Jacobi symbol requires positive odd n; got {n}")
    a = a % n
    result = 1
    while a != 0:
        while a % 2 == 0:
            a //= 2
            if n % 8 in (3, 5):
                result = -result
        a, n = n, a
        if a % 4 == 3 and n % 4 == 3:
            result = -result
        a = a % n
    return result if n == 1 else 0


# ---------------------------------------------------------------------------
# Convenience
# ---------------------------------------------------------------------------

def odd_part(n: int) -> int:
    """Return n with all factors of 2 removed.  n must be a positive integer."""
    if n <= 0:
        raise ValueError(f"odd_part undefined for {n}; requires a positive integer")
    while n % 2 == 0:
        n //= 2
    return n


def two_adic_valuation(n: int) -> int:
    """v_2(n). Alias for valuation(n, 2)."""
    return valuation(n, 2)
