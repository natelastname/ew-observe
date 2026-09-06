"""Exact-support queue depth utilities.

For a positive integer x with prime support S, its exact-support queue is the
increasing sequence of positive integers whose prime support is exactly S.
The zero-based queue depth of x is therefore the number of smaller integers in
that queue.
"""

from __future__ import annotations

from functools import lru_cache

from .decision import prime_support


@lru_cache(maxsize=None)
def exact_support_queue_depth(value: int) -> int:
    """Return the zero-based rank of ``value`` in its exact-support queue.

    Equivalently, count the positive integers ``y < value`` with
    ``prime_support(y) == prime_support(value)``.
    """

    if value < 1:
        raise ValueError("value must be positive")

    primes = tuple(sorted(prime_support(value)))
    if not primes:
        return 0

    count = 0

    def visit(index: int, product: int) -> None:
        nonlocal count
        if index == len(primes):
            count += 1
            return

        prime = primes[index]
        next_product = product * prime
        while next_product < value:
            visit(index + 1, next_product)
            if next_product > (value - 1) // prime:
                break
            next_product *= prime

    visit(0, 1)
    return count
