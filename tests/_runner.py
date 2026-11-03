"""Subprocess entry point for the golden harness.

Runs PNG2ObjV3.py in a fresh interpreter with a fixed RNG seed and a given
argv, so that each case is isolated (module-level globals in the script reset
on every run) and the optical-illusion output is reproducible.

Usage (invoked by tests/golden.py, not by hand):
    python tests/_runner.py <seed> <script_path> -- <args passed to script>
"""
import random
import runpy
import sys
from pathlib import Path


def main() -> int:
    sep = sys.argv.index("--")
    seed = int(sys.argv[1])
    script = sys.argv[2]
    script_args = sys.argv[sep + 1:]

    # Deterministic illusions: the script calls random.randint without seeding.
    random.seed(seed)

    # argparse in the script reads sys.argv; present it as if invoked directly.
    sys.argv = [script] + script_args

    # Mirror `python PNG2ObjV3.py`: direct execution puts the script's directory
    # on sys.path[0], which is what lets the script import its own png2obj package.
    script_dir = str(Path(script).resolve().parent)
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)

    try:
        runpy.run_path(script, run_name="__main__")
    except SystemExit as exc:
        # The script uses exit()/sys.exit() liberally; treat 0/None as success.
        code = exc.code
        return 0 if code in (0, None) else int(code)
    return 0


if __name__ == "__main__":
    sys.exit(main())
