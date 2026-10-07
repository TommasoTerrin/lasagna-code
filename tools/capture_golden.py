"""Capture golden test-runner outputs for capture-test-result.

    python tools/capture_golden.py [--v1-ref <git-ref>]

Runs REAL test runners on tiny throwaway projects (never transcribed output),
records what v1's capture-test-result.sh made of each output (taken from git at
--v1-ref) and what v2 makes of it with the shipped stack template. Writes one
JSON per case to tests/fixtures/golden/. Where v2 differs from v1 the fixture
must carry a `deviation` explaining why; tests/core/test_golden.py enforces it.

Only runners installed on this machine are captured. Stacks without fixtures
show up as "not verified" (skipped) in the test report.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "tests" / "fixtures" / "golden"
sys.path.insert(0, str(REPO / "plugins" / "lasagna" / "scripts"))

from lasagna_lib.core.classify import classify_output  # noqa: E402
from lasagna_lib.core.profile import parse_profile  # noqa: E402

# Known, accepted deviations from v1 (docs/v2-spec.md §6.1).
DEVIATIONS = {
    ("python", "red-generic", "red-assertion"): (
        "v1 applied the patterns to the raw JSON payload, where the whole output is one "
        "line, so '^E +assert' could never match; v2 reads the real output line by line."
    ),
}

PYTEST_CASES = {
    "pass": {"test_a.py": "def test_ok():\n    assert 1 + 1 == 2\n"},
    "assert": {"test_a.py": "def test_sum():\n    total = 1 + 1\n    assert total == 3\n"},
    "assert-message": {
        "test_a.py": "def test_sum():\n    assert sorted([2, 1]) == [1, 3], 'order'\n"
    },
    "compile": {"test_a.py": "from shop.cart import Cart\n\n\ndef test_cart():\n    assert Cart()\n"},
    "syntax": {"test_a.py": "def test_x(:\n    pass\n"},
    "generic": {"test_a.py": "def test_div():\n    return 1 / 0\n"},
    "raises": {
        "test_a.py": "import pytest\n\n\ndef test_raises():\n    with pytest.raises(ValueError):\n        int('1')\n"
    },
}


def git_show(ref: str, path: str) -> str:
    return subprocess.run(
        ["git", "show", f"{ref}:{path}"], cwd=REPO, capture_output=True, text=True, check=True
    ).stdout


def v1_classify(ref: str, stack: str, command: str, response: dict) -> str:
    """Run v1's capture-test-result.sh on the payload and read the state back."""
    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp)
        scripts = t / "scripts"
        scripts.mkdir()
        for name in ("lib.sh", "capture-test-result.sh"):
            (scripts / name).write_bytes(git_show(ref, f"plugins/lasagna/scripts/{name}").encode("utf-8"))
        proj = t / "proj"
        (proj / ".lasagna" / "state").mkdir(parents=True)
        (proj / ".lasagna" / "stack.md").write_text(
            git_show(ref, f"plugins/lasagna/templates/stack/{stack}.md"), encoding="utf-8"
        )
        state = proj / ".lasagna" / "state" / "G.state.md"
        state.write_text("feature_id: G\nlast_test_result: none\n", encoding="utf-8")
        payload = {"tool_name": "Bash", "tool_input": {"command": command}, "tool_response": response}
        env = dict(os.environ, CLAUDE_PROJECT_DIR=str(proj))
        subprocess.run(
            [shutil.which("sh"), str(scripts / "capture-test-result.sh")],
            input=json.dumps(payload).encode(),
            env=env,
            capture_output=True,
            check=False,
        )
        for line in state.read_text(encoding="utf-8").splitlines():
            if line.startswith("last_test_result:"):
                return line.split(":", 1)[1].strip()
    return "none"


def capture_pytest(ref: str) -> None:
    profile = parse_profile(
        (REPO / "plugins" / "lasagna" / "templates" / "stack" / "python.md").read_text(encoding="utf-8")
    )
    version = subprocess.run(
        [sys.executable, "-m", "pytest", "--version"], capture_output=True, text=True
    ).stdout.strip() or "pytest"
    command = "python -m pytest -q -p no:cacheprovider"
    for case, files in PYTEST_CASES.items():
        with tempfile.TemporaryDirectory() as tmp:
            for name, body in files.items():
                (Path(tmp) / name).write_text(body, encoding="utf-8")
            p = subprocess.run(
                [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"],
                cwd=tmp,
                capture_output=True,
                text=True,
            )
        # Temp paths change every run: keep the output stable for review diffs.
        response = {
            "stdout": p.stdout.replace(tmp, "<tmp>"),
            "stderr": p.stderr.replace(tmp, "<tmp>"),
            "interrupted": False,
        }
        v2 = classify_output("\n".join([response["stdout"], response["stderr"]]), profile).value
        v1 = v1_classify(ref, "python", command, response)
        fixture = {
            "stack": "python",
            "runner": version,
            "case": case,
            "command": command,
            "tool_response": response,
            "expected": v2,
            "v1": v1,
        }
        if v1 != v2:
            fixture["deviation"] = DEVIATIONS.get(("python", v1, v2), "UNEXPLAINED: review before committing")
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / f"python-pytest-{case}.json").write_bytes((json.dumps(fixture, indent=2) + "\n").encode("utf-8"))
        print(f"python/pytest {case:15} v1={v1:14} v2={v2}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--v1-ref", default="main", help="git ref holding the v1 shell scripts")
    args = parser.parse_args()
    capture_pytest(args.v1_ref)
    return 0


if __name__ == "__main__":
    sys.exit(main())
