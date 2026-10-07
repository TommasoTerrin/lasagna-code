"""Shared fixtures for the process-level tests of plugins/lasagna/scripts/run.sh."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

import pytest

REPO = Path(__file__).resolve().parent.parent
PLUGIN = REPO / "plugins" / "lasagna"
RUN_SH = PLUGIN / "scripts" / "run.sh"
SH = shutil.which("sh")
REAL_PYTHON = sys.executable.replace("\\", "/")

PROFILE = """language: python
test_command: python -m pytest
test_command_pattern: (pytest|python -m pytest)
fail_compile_pattern: (ModuleNotFoundError|ImportError)
fail_assert_pattern: (AssertionError|^E +assert)
fail_generic_pattern: ([0-9]+ failed|ERROR)
pass_pattern: ([0-9]+ passed)
test_path: tests/
test_file_pattern: (^|/)tests?/|(^|/)test_[^/]*\\.py$
source_path: src/
"""

STATE = """# Phase state — FEAT-001

feature_id: FEAT-001
flow: official
phase: tdd-loop
layer: core
current_slice: S1
budget_max: 3
cycles_used: 0
active_role: none
last_test_result: none
escalation: none
updated: never

## Criteria

AC-FEAT-001-001: open

## Checkpoint

- [2026-10-07T09:00] about to start

## Cycle log

| when | role | outcome |
|---|---|---|
"""


@dataclass
class Result:
    code: int
    out: str
    err: str


class Project:
    """A temp project plus a plugin data dir, and a way to run run.sh in it."""

    def __init__(self, root: Path) -> None:
        self.root = root / "proj"
        self.data = root / "plugin-data"
        self.bin = root / "bin"  # holds fake interpreters when a test needs them
        self.root.mkdir()
        self.data.mkdir()
        self.bin.mkdir()
        self.lasagna = self.root / ".lasagna"

    def init(self, profile: str = PROFILE, state: Optional[str] = STATE) -> "Project":
        (self.lasagna / "state").mkdir(parents=True, exist_ok=True)
        (self.lasagna / "stack.md").write_text(profile, encoding="utf-8")
        if state is not None:
            self.state_file.write_text(state, encoding="utf-8")
        return self

    @property
    def state_file(self) -> Path:
        return self.lasagna / "state" / "FEAT-001.state.md"

    def state(self) -> str:
        return self.state_file.read_text(encoding="utf-8")

    def save_python(self, path: str = REAL_PYTHON) -> None:
        (self.data / "python-path").write_text(path + "\n", encoding="utf-8")

    def saved_python(self) -> Optional[str]:
        f = self.data / "python-path"
        return f.read_text(encoding="utf-8").strip() if f.exists() else None

    def fake(self, name: str, body: str) -> None:
        f = self.bin / name
        f.write_text("#!/bin/sh\n" + body + "\n", encoding="utf-8", newline="\n")
        f.chmod(0o755)

    def run(
        self,
        *args: str,
        stdin: object = "",
        isolated_path: bool = False,
        env: Optional[Dict[str, str]] = None,
    ) -> Result:
        full = dict(os.environ)
        full.update(
            {
                "CLAUDE_PROJECT_DIR": str(self.root),
                "CLAUDE_PLUGIN_DATA": str(self.data),
                "CLAUDE_PLUGIN_ROOT": str(PLUGIN),
            }
        )
        for key in ("LASAGNA_DIR", "LASAGNA_STATE_FILE"):
            full.pop(key, None)
        if isolated_path:
            full["PATH"] = str(self.bin)
        full.update(env or {})
        data = stdin if isinstance(stdin, str) else json.dumps(stdin)
        p = subprocess.run(
            [SH, str(RUN_SH), *args],
            input=data.encode("utf-8"),
            capture_output=True,
            env=full,
            cwd=str(self.root),
            timeout=60,
        )
        return Result(
            p.returncode, p.stdout.decode("utf-8", "replace"), p.stderr.decode("utf-8", "replace")
        )


@pytest.fixture
def project(tmp_path: Path) -> Project:
    if SH is None:
        pytest.skip("sh not available")
    return Project(tmp_path)
