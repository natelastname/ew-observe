from ew_observe import EWObserver
from ew_observe.human_sort import prime_lex_key
from ew_observe.queue_frontier_presentation import ordered_queue_frontiers


EW_PREFIX_100 = [
    1, 2, 6, 15, 35, 14, 12, 33, 55, 10, 18, 21, 77, 22, 20,
    45, 39, 26, 28, 63, 51, 34, 38, 57, 69, 46, 40, 65, 91, 42,
    30, 85, 119, 56, 24, 75, 95, 76, 36, 87, 145, 50, 44, 99, 93,
    62, 52, 117, 105, 70, 58, 261, 111, 74, 68, 153, 123, 82, 80,
    115, 161, 84, 60, 155, 217, 98, 48, 129, 215, 100, 54, 141, 235,
    110, 66, 147, 133, 152, 72, 135, 175, 112, 78, 143, 187, 102, 86,
    301, 189, 90, 88, 209, 171, 96, 92, 253, 165, 108, 94, 329,
]


def _values(sort_order: str) -> list[int]:
    trace = EWObserver(EW_PREFIX_100[:87]).trace_queue_heads(87)
    return [
        queue.frontier_value
        for queue in ordered_queue_frontiers(trace, sort_order=sort_order)
    ]


def test_prime_lex_treats_small_primes_as_least_significant_digits():
    assert prime_lex_key(12) == ((3, 1), (2, 2))
    assert prime_lex_key(18) == ((3, 2), (2, 1))
    assert prime_lex_key(20) == ((5, 1), (2, 2))
    assert prime_lex_key(30) == ((5, 1), (3, 1), (2, 1))

    assert prime_lex_key(12) < prime_lex_key(18) < prime_lex_key(20)
    assert prime_lex_key(20) < prime_lex_key(30)


def test_value_sort_is_numerical():
    assert _values("value") == [
        46, 52, 57, 58, 60, 62, 69, 70, 74, 78, 82, 84, 100, 112,
        117, 135, 147, 152,
    ]


def test_depth_sort_is_maturity_first():
    assert _values("depth") == [
        100, 112, 135, 147, 152, 52, 60, 84, 117, 46, 57, 58, 62,
        69, 70, 74, 78, 82,
    ]


def test_prime_lex_uses_highest_differing_prime_exponent_first():
    assert _values("prime-lex") == [
        60, 135, 100, 112, 84, 70, 147, 52, 78, 117, 152, 57, 46,
        69, 58, 62, 74, 82,
    ]


def test_retained_sort_groups_lowest_continuity_prime():
    assert _values("retained") == [
        46, 52, 58, 60, 62, 70, 74, 78, 82, 84, 100, 112, 152, 57,
        69, 117, 135, 147,
    ]
