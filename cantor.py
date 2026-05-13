#!/usr/bin/env python3
"""Command-line entry point for the Cantor interpreter."""

import argparse
from pathlib import Path
import sys


def add_local_antlr_runtime() -> None:
    """Prefer the local teaching virtualenv if it exists."""

    root = Path(__file__).resolve().parent
    lib_dir = root / "lp" / "lib"
    if not lib_dir.exists():
        return
    for site_packages in sorted(lib_dir.glob("python*/site-packages")):
        sys.path.insert(0, str(site_packages))


add_local_antlr_runtime()

from errors import CantorError, CantorInputError, CantorRuntimeError
from loader import load_program
from runtime import encode_input


def parse_stdin(text: str) -> list[int]:
    """Parse stdin as a whitespace-separated list of natural numbers.

    Problem solved:
        Converts the external textual input into Python integers before the
        runtime encodes them with pi.
    Input:
        Text from stdin, for example "1 3 2\n".
    Return:
        A list of naturals, for example [1, 3, 2].
    Why this way:
        Keeping parsing separate from encode_input makes error reporting clear:
        textual mistakes are input errors; pairing is runtime logic.
    Small test:
        parse_stdin("1 3 2") == [1, 3, 2].
    """

    values = []
    for raw_value in text.split():
        try:
            value = int(raw_value)
        except ValueError as exc:
            raise CantorInputError(
                f"input value '{raw_value}' is not an integer"
            ) from exc
        if value < 0:
            raise CantorInputError(
                f"input value '{raw_value}' is not a natural number"
            )
        values.append(value)
    return values


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cantor.py",
        description="Interpret a Cantor language program.",
    )
    parser.add_argument("script", help="path to the .cantor program")
    return parser


def run(script: str, stdin_text: str) -> int:
    """Load, encode, execute and print the result of one Cantor program."""

    program = load_program(script)
    values = parse_stdin(stdin_text)
    encoded_input = encode_input(values)
    try:
        result = program.main_function(encoded_input)
    except RecursionError as exc:
        raise CantorRuntimeError("maximum Python recursion depth reached") from exc
    print(result)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_argument_parser()
    args = parser.parse_args(argv)
    try:
        return run(args.script, sys.stdin.read())
    except CantorError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Unexpected error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
