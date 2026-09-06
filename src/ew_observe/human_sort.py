"""Shared human-only sort keys for EW microscope presentations."""

from __future__ import annotations


def prime_exponents(value: int) -> tuple[tuple[int, int], ...]:
    """Return ``(prime, exponent)`` pairs in increasing-prime order."""

    if value < 1:
        raise ValueError("value must be positive")
    if value == 1:
        return ()

    remaining = value
    factors: list[tuple[int, int]] = []
    divisor = 2
    while divisor * divisor <= remaining:
        exponent = 0
        while remaining % divisor == 0:
            remaining //= divisor
            exponent += 1
        if exponent:
            factors.append((divisor, exponent))
        divisor = 3 if divisor == 2 else divisor + 2
    if remaining > 1:
        factors.append((remaining, 1))
    return tuple(factors)


def prime_lex_key(value: int) -> tuple[tuple[int, int], ...]:
    """Key for prime-digit lex order with small primes least significant.

    Regard ``value`` as the exponent vector

        (v_2(value), v_3(value), v_5(value), ...)

    with the exponent of 2 as the least-significant digit. Two values are
    compared at the largest prime where their exponent vectors differ.

    The finite key consists of nonzero ``(prime, exponent)`` digits ordered
    from largest prime to smallest. Ordinary Python tuple comparison then
    implements exactly that reverse lexicographic comparison, including zero
    exponents at omitted intermediate primes.
    """

    return tuple(reversed(prime_exponents(value)))
