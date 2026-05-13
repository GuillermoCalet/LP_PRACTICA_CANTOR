"""Runtime support for the Cantor language."""

# math.isqrt calcula raices cuadradas enteras exactas, sin floats.
import math

# os se usa para leer variables de entorno, como CANTOR_MU_LIMIT.
import os

# Callable permite escribir el tipo "funcion que recibe int y devuelve int".
from typing import Callable

from errors import CantorRuntimeError


# En el lenguaje Cantor toda funcion tiene tipo:
#   natural -> natural
# En Python lo escribimos como Callable[[int], int].
NaturalFunction = Callable[[int], int]

# Limite por defecto para la busqueda de mu.
DEFAULT_MU_LIMIT = 100000


def require_natural(value: int, name: str = "value") -> None:
    """Mira si un numero es natual o no """

    # bool tambien es int en Python, pero en esta practica solo generamos ints.
    # La comprobacion importante es que el valor no sea negativo y que sea un entero.
    if not isinstance(value, int) or value < 0: 
        raise CantorRuntimeError(f"{name} el numero debe ser natural ")


def pi(x: int, y: int) -> int:

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

    # diagonal es el numero de diagonal donde cae z.
    # Usamos isqrt para evitar errores de redondeo.
    w = (math.isqrt(8 * z + 1) - 1) // 2

    # triangle es el primer valor de esa diagonal.
    t = w * (w + 1) // 2

    # Dentro de la diagonal, y es el desplazamiento desde triangle.
    y = z - t

    # En una diagonal se cumple x + y == diagonal.
    x = w - y
    return x, y


def encode_input(values: list[int]) -> int:

    # Primero validamos que todos los valores sean naturales.
    for index, value in enumerate(values):
        require_natural(value, f"input[{index}]") # si no lo son, saldremos 
        #del programa por la excepcion que tiene dentro requiere_natural 

    if not values:
        return 0

    # Empezamos por el ultimo elemento.
    # Para [1, 3, 2], result empieza siendo 2.
    result = values[-1]

    # Despues emparejamos de derecha a izquierda:
    # result = pi(3, 2), luego result = pi(1, result).

    #recorremos el values sin el ultimo elemento, y del reves 
    for value in reversed(values[:-1]):
        result = pi(value, result)
    return result


def base_functions() -> dict[str, NaturalFunction]:
    """Return the predefined functions available in basic mode."""

    # add, mul y diff reciben una pareja ya codificada.
    # Por eso lo primero es hacer unpi.
    def add(encoded_pair: int) -> int:
        x, y = unpi(encoded_pair)
        return x + y

    def mul(encoded_pair: int) -> int:
        x, y = unpi(encoded_pair)
        return x * y

    def diff(encoded_pair: int) -> int:
        x, y = unpi(encoded_pair)
        return max(0, x - y)

    # El diccionario asocia nombres Cantor con funciones Python.
    # Ejemplo: cuando el script dice "main add", se usara esta funcion add.
    return {
        "k_1": lambda _x: 1,
        "id": lambda x: x,
        "add": add,
        "mul": mul,
        "diff": diff,
    }


def extended_functions() -> dict[str, NaturalFunction]:
    """Return the predefined functions added by extended mode."""

    # fst y snd son las proyecciones de una pareja codificada.
    return {
        "fst": lambda encoded_pair: unpi(encoded_pair)[0],
        "snd": lambda encoded_pair: unpi(encoded_pair)[1],
    }


def make_pair(f_func: NaturalFunction, g_func: NaturalFunction) -> NaturalFunction:
    """Build pair f g: x -> pi(f(x), g(x))."""

    # Devuelve una nueva funcion. No se ejecuta f_func ni g_func ahora;
    # se ejecutaran cuando la funcion resultante reciba una x.
    return lambda x: pi(f_func(x), g_func(x))


def make_comp(f_func: NaturalFunction, g_func: NaturalFunction) -> NaturalFunction:
    """Build comp f g: x -> f(g(x))."""

    # Primero se aplica g a x. Despues se aplica f al resultado.
    return lambda x: f_func(g_func(x))


def make_compair(
    f_func: NaturalFunction,
    g_func: NaturalFunction,
    h_func: NaturalFunction,
) -> NaturalFunction:
    """Build compair f g h: x -> f(pi(g(x), h(x)))."""

    # Es una abreviatura de:
    #   pair_result = pi(g(x), h(x))
    #   return f(pair_result)
    return lambda x: f_func(pi(g_func(x), h_func(x)))


def mu_limit() -> int:
    """Read the search limit used by mu from the environment."""

    # Si el usuario no define nada, usamos el limite por defecto.
    raw_value = os.environ.get("CANTOR_MU_LIMIT")
    if raw_value is None:
        return DEFAULT_MU_LIMIT

    try:
        # Las variables de entorno son texto; hay que convertir a int.
        value = int(raw_value)
    except ValueError as exc:
        raise CantorRuntimeError("CANTOR_MU_LIMIT must be a natural number") from exc

    require_natural(value, "CANTOR_MU_LIMIT")
    return value


def make_mu(predicate: NaturalFunction) -> NaturalFunction:
    
    def search(x: int) -> int:
        limit = mu_limit()

        # Probamos k = 0, 1, 2, ...
        for candidate in range(limit + 1):
            # El predicado recibe la pareja <x.k>, codificada con pi.
            # En esta practica "verdadero" significa cualquier valor != 0.
            if predicate(pi(x, candidate)) != 0:
                return candidate

        # Si llegamos aqui, no se ha encontrado ningun k dentro del limite.
        raise CantorRuntimeError(
            f"mu search exceeded limit {limit}; "
            "set CANTOR_MU_LIMIT to allow a larger search"
        )

    # make_mu devuelve la funcion search, no el resultado de search.
    return search


def make_primrec(
    is_base: NaturalFunction,
    base_case: NaturalFunction,
    recursive_step: NaturalFunction,
) -> NaturalFunction:
    

    def evaluate(bound: int) -> int:
        require_natural(bound, "primrec input")

        # previous_results contiene la lista codificada de resultados ya
        # calculados. Al principio no hay resultados, por eso usamos 0.
        previous_results = 0

        # Calculamos s(0), s(1), ..., s(bound).
        for index in range(bound + 1):
            # f decide si index es caso base.
            if is_base(index) != 0:
                value = base_case(index)
            else:
                # h recibe <index.previous_results>.
                value = recursive_step(pi(index, previous_results))

            require_natural(value, "primrec result")

            # Guardamos el nuevo valor delante de la lista:
            # si antes teniamos <s(i-1).<...>>, ahora tendremos
            # <s(i).<s(i-1).<...>>>.
            previous_results = pi(value, previous_results)

        return previous_results

    # Devolvemos la funcion que sabe calcular la secuencia hasta bound.
    return evaluate
