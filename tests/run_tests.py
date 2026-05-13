#!/usr/bin/env python3
"""Run .cantor examples and compare them with their .out files."""

from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
TEST_DIR = ROOT / "tests"


def run_case(input_file: Path) -> tuple[bool, str]:
    script = input_file.with_suffix(".cantor")
    expected_file = input_file.with_suffix(".out")
    if not script.exists():
        return False, f"missing script for {input_file.name}"
    if not expected_file.exists():
        return False, f"missing expected output for {input_file.name}"

    completed = subprocess.run(
        [sys.executable, "cantor.py", str(script)],
        cwd=ROOT,
        input=input_file.read_text(encoding="utf-8"),
        text=True,
        capture_output=True,
        check=False,
    )
    expected = expected_file.read_text(encoding="utf-8").strip()
    actual = completed.stdout.strip()

    if completed.returncode != 0:
        return (
            False,
            f"{script.name} exited with {completed.returncode}: "
            f"{completed.stderr.strip()}",
        )
    if actual != expected:
        return False, f"{script.name}: expected {expected!r}, got {actual!r}"
    return True, script.name


def main() -> int:
    input_files = sorted(TEST_DIR.glob("*.inp"))
    failures = []
    for input_file in input_files:
        ok, message = run_case(input_file)
        status = "ok" if ok else "FAIL"
        print(f"{status:4} {message}")
        if not ok:
            failures.append(message)

    if failures:
        print(f"\n{len(failures)} test(s) failed", file=sys.stderr)
        return 1

    print(f"\n{len(input_files)} test(s) passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
