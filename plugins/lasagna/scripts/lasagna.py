"""lasagna entry point, started by run.sh.

    lasagna.py hook <name>      a Claude Code hook; payload on stdin
    lasagna.py <command> [...]  set-state, check-traceability, init, status
"""

from __future__ import annotations

import os
import sys

if sys.version_info < (3, 9):  # run.sh checks this too; belt and braces
    sys.stderr.write("lasagna requires Python >= 3.9\n")
    sys.exit(2 if sys.argv[1:3] in (["hook", "block-test-edits"], ["hook", "block-reads"]) else 0)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lasagna_lib.shell.cli import run_cli  # noqa: E402
from lasagna_lib.shell.hooks import Streams, run_hook  # noqa: E402


def main(argv: list) -> int:
    # Hook output must survive any console code page (Windows: cp1252), and
    # keep plain \n line ends.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace", newline="\n")
    io = Streams(sys.stdout, sys.stderr)
    env = dict(os.environ)
    if not argv:
        sys.stderr.write("usage: run.sh hook <name> | run.sh <command> [args]\n")
        return 1
    if argv[0] == "hook":
        name = argv[1] if len(argv) > 1 else ""
        try:
            stdin = sys.stdin.buffer.read().decode("utf-8", errors="replace")
        except Exception:  # noqa: BLE001 — an unreadable stdin is handled like bad JSON
            stdin = ""
        return run_hook(name, stdin, env, io)
    return run_cli(argv[0], argv[1:], env, io)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
