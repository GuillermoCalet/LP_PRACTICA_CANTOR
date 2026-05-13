#!/usr/bin/env python3
"""Command-line entry point for the Cantor interpreter."""

# argparse sirve para leer argumentos de linea de comandos.
import argparse

# sys nos da acceso a stdin, stderr y argv.
import sys


# Excepciones propias: asi mostramos errores limpios al usuario.
from errors import CantorError, CantorInputError, CantorRuntimeError

# del codigo loader (que hemos programado), importamos la funcion load_program, que se encarga de cargar un progrma 
from loader import load_program

# encode_input transforma la lista de stdin en un unico natural de Cantor.
from runtime import encode_input


def parse_stdin(text: str) -> list[int]:
    """Transforma el texto de stdin en una lista de números naturales.

    Input:
        Texto de stdin, for example "1 3 2\n".
    Return:
        Una lista de números naturales, for example [1, 3, 2].
    Por que:
        Para que a los archvios .canto, les llegue una lista de naturales, 
        que es lo que se pide. 
    Ejemplo:
        parse_stdin("1 3 2") == [1, 3, 2].
    """

    values = []

    # text.split() separa por cualquier espacio: espacios, tabs o saltos.
    # Ejemplo: "1  2\n3" -> ["1", "2", "3"].
    for raw_value in text.split():
        try:
            # Convertimos cada trozo textual a entero.
            value = int(raw_value)
        except ValueError as exc:
            # Si no es entero, salta el error.
            raise CantorInputError(
                f"el valor del input '{raw_value}' no es un entero"
            ) from exc

        # El lenguaje solo trabaja con naturales: 0, 1, 2, ...
        if value < 0:
            raise CantorInputError(
                f"el valor del input '{raw_value}' no es mayor o igual a 0"
            )
        values.append(value)

    return values


def build_argument_parser() -> argparse.ArgumentParser: # esta funcion devuelve un parser de argumentos 
    # El parser es lo que nos ayuda a leer argumentos de terminal. 
    parser = argparse.ArgumentParser(
        # esto es a modo de ayuda, es como el usage que se muestra con --help.
        prog="cantor.py",
        description="Interpret a Cantor language program.",
    )

    # Definimos un argumento obligatorio, al que accederemos desde script, que 
    #representa la ruta al programa .cantor que queremos ejecutar.
    parser.add_argument("script", help="path to the .cantor program")
    return parser


def run(script: str, stdin_text: str) -> int: #devuelvo un entero (0 bien : 1 mal)
    # aqui definimos que la funcion, tiene dos variables como parametro 
    # por un lado, tenemos script que es un string, y stdin_text, que es el texto que llega por stdin, tambien un string.

    """Carga, codifica, ejecuta y muestra el resultado de un programa Cantor."""

    # 1. Cargamos el programa Cantor.
    program = load_program(script)

    # 2. Convertimos stdin_text ("1 2 3") en una lista Python ([1, 2, 3]).
    values = parse_stdin(stdin_text)

    # 3. Codificamos la lista como un unico natural usando pi de derecha a
    # izquierda, porque todas las funciones Cantor reciben un solo natural.
    encoded_input = encode_input(values)

    try:
        # 4. Ejecutamos la funcion main del programa Cantor.
        result = program.main_function(encoded_input)
    except RecursionError as exc:
        # Por si un programa produce recursion demasiado profunda en Python.
        raise CantorRuntimeError("maximum Python recursion depth reached") from exc

    # 5. La salida correcta va por stdout.
    print(result)

    # 0 significa "todo ha ido bien" en programas de terminal.
    return 0


def main(argv: list[str] | None = None) -> int:
    # Leemos lo que nos llega por terminal 
    parser = build_argument_parser()

    #ahora en parser, tenemos los argumentos, parseados (sin contar el argv[0])
    #en agrs guardamos esos valores del vector argv, que lo leemos
    #llamando a la funcion parse_args, que esta dentro de la clase ArgumentParser, 
    #que es la que nos devuelve la funcion build_argument_parser.

    # Ejemplo real:
    #   python3 cantor.py tests/add3.cantor

    #luego, obviamente, podemos acceder a esos argumentos con el nombre que les 
    # hayamos dado al definir el parser, en este caso, el primer argumento 
    #es el script (EL ORDEN IMPORTANTE)
    # produce:
    #   args.script == "tests/add3.cantor"
    args = parser.parse_args(argv)

    try:
        # sys.stdin.read() lee todo lo que llegue por stdin y lo guarda como un string entero 
        # Ejemplo: echo "1 2 3" | python3 cantor.py script.cantor
        return run(args.script, sys.stdin.read())
    except CantorError as exc:
        # Errores esperados: sintaxis, imports, entrada invalida, etc.
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        # Ultima red de seguridad: evita tracebacks feos al usuario.
        print(f"Unexpected error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    # Solo se ejecuta cuando llamamos directamente:
    #   python3 cantor.py archivo.cantor
    # raise SystemExit convierte el entero devuelto por main en codigo de salida.
    raise SystemExit(main())
