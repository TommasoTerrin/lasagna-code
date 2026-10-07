"""Where things live, and reading/writing them safely."""

from __future__ import annotations

import glob
import os
import tempfile
from datetime import datetime, timezone
from typing import Mapping, Optional

from ..core.profile import Profile, parse_profile

Env = Mapping[str, str]

# plugins/lasagna/scripts/lasagna_lib/shell/files.py -> plugins/lasagna
PLUGIN_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def project_dir(env: Env) -> str:
    return env.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def lasagna_dir(env: Env) -> str:
    """Fixed at .lasagna/ (a dotdir cannot collide); LASAGNA_DIR for monorepos."""
    return env.get("LASAGNA_DIR") or os.path.join(project_dir(env), ".lasagna")


def profile_path(env: Env) -> str:
    return os.path.join(lasagna_dir(env), "stack.md")


def read_text(path: str) -> Optional[str]:
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError:
        return None


def load_profile(env: Env) -> Optional[Profile]:
    text = read_text(profile_path(env))
    return None if text is None else parse_profile(text)


def active_state_path(env: Env) -> Optional[str]:
    """LASAGNA_STATE_FILE if it exists, else the most recently modified state."""
    forced = env.get("LASAGNA_STATE_FILE")
    if forced and os.path.isfile(forced):
        return forced
    candidates = glob.glob(os.path.join(lasagna_dir(env), "state", "*.state.md"))
    if not candidates:
        return None
    return max(candidates, key=os.path.getmtime)


def write_atomic(path: str, text: str, must_exist: bool = True) -> bool:
    """Write via temp file + rename, so a reader never sees half a file.

    With must_exist, a file that vanished since it was read is not recreated.
    """
    if must_exist and not os.path.isfile(path):
        return False
    directory = os.path.dirname(path) or "."
    fd, tmp = tempfile.mkstemp(prefix=".lasagna-", suffix=".tmp", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
    return True
