"""Runtime support for the Cantor language."""

import math
import os
from typing import Callable

from errors import CantorRuntimeError


NaturalFunction = Callable[[int], int]
DEFAULT_MU_LIMIT = 100000


def require_natural(value: int, name: str = "value") -> None:
    """Validate that a runtime value belongs to N."""

    if not isinstance(value, int) or value < 0:
        raise CantorRuntimeError(f"{name} must be a natural number")


def pi(x: int, y: int) -> int:
    """Cantor pairing function.

    Problem solved:
        Encodes two natural numbers as one natural number.
    Input:
        Two naturals, x and y.
    Return:
        One natural that represents the pair <x.y>.
    Why this way:
        This is the standard Cantor pairing formula used in the statement:
        ((x + y) * (x + y + 1)) // 2 + y.
    Small test:
        pi(47, 32) == 3192.
    """

    require_natural(x, "x")
    require_natural(y, "y")
    total = x + y
    return (total * (total + 1)) // 2 + y


def unpi(z: int) -> tuple[int, int]:
    """Inverse of the Cantor pairing function.

    Problem solved:
        Recovers the two components encoded by pi.
    Input:
        One natural z.
    Return:
        A pair (x, y) such that pi(x, y) == z.
    Why this way:
        Cantor numbers grow by diagonals. isqrt gives the diagonal exactly
        without floating-point rounding problems.
    Small test:
        unpi(3192) == (47, 32).
    """

    require_natural(z, "z")
    diagonal = (math.isqrt(8 * z + 1) - 1) // 2
    triangle = diagonal * (diagonal + 1) // 2
    y = z - triangle
    x = diagonal - y
    return x, y


def encode_input(values: list[int]) -> int:
    """Encode stdin values from right to left with pi.

    Problem solved:
        Turns the external list input into the single natural expected by every
        Cantor function.
    Input:
        A list of naturals, for example [1, 3, 2].
    Return:
        A natural. The empty list is represented as 0.
    Why this way:
        The statement fixes right-to-left pairing, so [1, 3, 2] becomes
        pi(1, pi(3, 2)).
    Small test:
        encode_input([1, 3, 2]) == 188.
    """

    for index, value in enumerate(values):
        require_natural(value, f"input[{index}]")
    if not values:
        return 0

    result = values[-1]
    for value in reversed(values[:-1]):
        result = pi(value, result)
    return result


def base_functions() -> dict[str, NaturalFunction]:
    """Return the predefined functions available in basic mode."""

    def add(encoded_pair: int) -> int:
        x, y = unpi(encoded_pair)
        return x + y

    def mul(encoded_pair: int) -> int:
        x, y = unpi(encoded_pair)
        return x * y

    def diff(encoded_pair: int) -> int:
        x, y = unpi(encoded_pair)
        return max(0, x - y)

    return {
        "k_1": lambda _x: 1,
        "id": lambda x: x,
        "add": add,
        "mul": mul,
        "diff": diff,
    }


def extended_functions() -> dict[str, NaturalFunction]:
    """Return the predefined functions added by extended mode."""

    return {
        "fst": lambda encoded_pair: unpi(encoded_pair)[0],
        "snd": lambda encoded_pair: unpi(encoded_pair)[1],
    }


def make_pair(f_func: NaturalFunction, g_func: NaturalFunction) -> NaturalFunction:
    """Build pair f g: x -> pi(f(x), g(x))."""

    return lambda x: pi(f_func(x), g_func(x))


def make_comp(f_func: NaturalFunction, g_func: NaturalFunction) -> NaturalFunction:
    """Build comp f g: x -> f(g(x))."""

    return lambda x: f_func(g_func(x))


def make_compair(
    f_func: NaturalFunction,
    g_func: NaturalFunction,
    h_func: NaturalFunction,
) -> NaturalFunction:
    """Build compair f g h: x -> f(pi(g(x), h(x)))."""

    return lambda x: f_func(pi(g_func(x), h_func(x)))


def mu_limit() -> int:
    """Read the search limit used by mu from the environment."""

    raw_value = os.environ.get("CANTOR_MU_LIMIT")
    if raw_value is None:
        return DEFAULT_MU_LIMIT
    try:
        value = int(raw_value)
    except ValueError as exc:
        raise CantorRuntimeError("CANTOR_MU_LIMIT must be a natural number") from exc
    require_natural(value, "CANTOR_MU_LIMIT")
    return value


def make_mu(predicate: NaturalFunction) -> NaturalFunction:
    """Build mu f.

    Problem solved:
        Expresses unbounded search: find the first k such that f(<x.k>) != 0.
    Input:
        A predicate-like Cantor function f. The returned function receives x.
    Return:
        A function h where h(x) is the first valid k.
    Why this way:
        The language works over one natural argument, so each candidate is
        tested by encoding the pair <x.k>. A configurable limit avoids an
        accidental infinite loop during tests.
    Small test:
        If f(<x.k>) checks k > x, then mu f applied to 3 returns 4.
    """

    def search(x: int) -> int:
        limit = mu_limit()
        for candidate in range(limit + 1):
            if predicate(pi(x, candidate)) != 0:
                return candidate
        raise CantorRuntimeError(
            f"mu search exceeded limit {limit}; "
            "set CANTOR_MU_LIMIT to allow a larger search"
        )

    return search


def make_primrec(
    is_base: NaturalFunction,
    base_case: NaturalFunction,
    recursive_step: NaturalFunction,
) -> NaturalFunction:
    """Build primrec f g h.

    Problem solved:
        Computes a finite primitive-recursive sequence from 0 to x.
    Input:
        f decides if index i is a base case, g computes base values, and h
        computes recursive values from <i.previous_results>.
    Return:
        A function returning <s(x).<s(x-1)....<s(0).0>>>.
    Why this way:
        The recursive step often needs s(i-1), s(i-2), etc. Keeping previous
        results as a head-first Cantor list makes fst(previous) equal s(i-1),
        fst(snd(previous)) equal s(i-2), and so on. The trailing 0 is an
        internal sentinel for the empty previous-result list.
    Small test:
        With base s(0)=0, s(1)=1, and step s(i)=s(i-1)+s(i-2), fst(result)
        is Fibonacci(x).
    """

    def evaluate(bound: int) -> int:
        require_natural(bound, "primrec input")
        previous_results = 0
        for index in range(bound + 1):
            if is_base(index) != 0:
                value = base_case(index)
            else:
                value = recursive_step(pi(index, previous_results))
            require_natural(value, "primrec result")
            previous_results = pi(value, previous_results)
        return previous_results

    return evaluate
