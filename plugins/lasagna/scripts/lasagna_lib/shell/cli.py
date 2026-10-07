"""Commands run by the lasagna skills or by hand:

    run.sh set-state <key> <value> | set-state --append <line>
    run.sh check-traceability [FEAT-NNN]
    run.sh init [<stack-template>]
    run.sh status
"""

from __future__ import annotations

import glob
import os
import shutil
import sys
from typing import List, Sequence

from ..core.state import state_append, state_set
from ..core.traceability import render_trace, trace
from .files import (
    PLUGIN_ROOT,
    Env,
    active_state_path,
    lasagna_dir,
    load_profile,
    now,
    profile_path,
    project_dir,
    read_text,
    write_atomic,
)
from .hooks import Streams, session_status

CLAUDE_MD_LINE = (
    "Project context (domain glossary per bounded context, code map) lives in "
    "{context_dir}/ — start from INDEX.md."
)


def set_state(args: Sequence[str], env: Env, io: Streams) -> int:
    """Hooks read active_role from the state: set it with this, not by hand."""
    path = active_state_path(env)
    text = read_text(path) if path else None
    if path is None or text is None:
        io.err.write(f"lasagna: no phase state in {lasagna_dir(env)}/state/.\n")
        io.err.write("Run /lasagna-init, or create one from templates/phase-state.md.\n")
        return 1
    if len(args) < 2:
        io.err.write("usage: run.sh set-state <key> <value> | set-state --append <line>\n")
        return 1
    if args[0] == "--append":
        text = state_append(text, "## Checkpoint", args[1])
        write_atomic(path, state_set(text, "updated", now()))
        io.out.write(f"lasagna: checkpoint added to {path}\n")
        return 0
    text = state_set(text, args[0], args[1])
    write_atomic(path, state_set(text, "updated", now()))
    io.out.write(f"lasagna: {args[0]} = {args[1]}  ({path})\n")
    return 0


def check_traceability(args: Sequence[str], env: Env, io: Streams) -> int:
    specs = os.path.join(lasagna_dir(env), "specs")
    if args and args[0]:
        spec = os.path.join(specs, args[0] + ".md")
    else:
        found = glob.glob(os.path.join(specs, "*.md"))
        spec = max(found, key=os.path.getmtime) if found else ""
    spec_text = read_text(spec) if spec else None
    if spec_text is None:
        io.err.write(f"lasagna: spec not found (looked in {specs}).\n")
        return 2

    profile = load_profile(env)
    paths: List[str] = list(profile.get_all("test_path")) if profile else []
    paths = paths or ["tests"]
    texts: List[str] = []
    any_dir = False
    for p in paths:
        root = os.path.join(project_dir(env), p.rstrip("/\\"))
        if not os.path.isdir(root):
            continue
        any_dir = True
        for dirpath, _, files in os.walk(root):
            for name in files:
                texts.append(read_text(os.path.join(dirpath, name)) or "")

    result = render_trace(trace(spec_text, texts), os.path.basename(spec), paths, any_dir)
    io.out.write(result.stdout)
    io.err.write(result.stderr)
    return result.exit_code


def init(args: Sequence[str], env: Env, io: Streams) -> int:
    """Idempotent bootstrap: creates only what is missing, never overwrites."""
    proj = project_dir(env)
    ldir = lasagna_dir(env)

    def rel(path: str) -> str:
        r = os.path.relpath(path, proj)
        return path if r.startswith("..") else r.replace("\\", "/")

    def report(tag: str, what: str) -> None:
        io.out.write(f"  {tag:<8} {what}\n")

    def copy_template(src: str, dst: str, note: str = "") -> None:
        if os.path.exists(dst):
            report("EXISTS", rel(dst))
        elif os.path.isfile(src):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copyfile(src, dst)
            report("CREATED", rel(dst) + note)
        else:
            report("MISSING", f"{rel(dst)}  (template not found: {src})")

    io.out.write(f"lasagna: initialising in {proj}\n")
    for d in (ldir, *(os.path.join(ldir, s) for s in ("specs", "specs/archive", "contracts", "state"))):
        if os.path.isdir(d):
            report("EXISTS", rel(d) + "/")
        else:
            os.makedirs(d, exist_ok=True)
            report("CREATED", rel(d) + "/")

    profile_file = profile_path(env)
    tpl = args[0] if args else ""
    if os.path.isfile(profile_file):
        report("EXISTS", rel(profile_file))
    elif tpl and os.path.isfile(tpl):
        shutil.copyfile(tpl, profile_file)
        report("CREATED", f"{rel(profile_file)}  (from {os.path.basename(tpl)})")
        io.out.write("           review every value before trusting the guardrails\n")
    else:
        report("MISSING", f"{rel(profile_file)}  <-- guardrails stay INACTIVE until this exists")

    templates = os.path.join(PLUGIN_ROOT, "templates")
    copy_template(
        os.path.join(templates, "architecture.md"),
        os.path.join(ldir, "architecture.md"),
        "  (fill it in: grilling or reverse-spec does)",
    )

    # .gitignore: the phase state is local and changes every cycle.
    gi = os.path.join(proj, ".gitignore")
    entry = os.path.basename(ldir.rstrip("/\\")) + "/state/"
    current = read_text(gi) or ""
    if entry in current.splitlines():
        report("EXISTS", f".gitignore entry {entry}")
    else:
        sep = "" if not current or current.endswith("\n") else "\n"
        with open(gi, "a", encoding="utf-8", newline="\n") as fh:
            fh.write(f"{sep}\n# lasagna phase state: local, per-feature, changes every cycle\n{entry}\n")
        report("CREATED", f".gitignore entry {entry}")

    profile = load_profile(env)
    legacy_file = profile.get("context_file") if profile else None
    context_dir = (profile.get("context_dir") if profile else None) or None
    if legacy_file and not context_dir:
        f = os.path.join(proj, legacy_file)
        report("EXISTS" if os.path.isfile(f) else "SKIPPED", f"{legacy_file}  (v1 context_file)")
    else:
        context_dir = context_dir or "docs/context"
        copy_template(
            os.path.join(templates, "context", "INDEX.md"),
            os.path.join(proj, context_dir, "INDEX.md"),
        )
        claude_md = read_text(os.path.join(proj, "CLAUDE.md")) or ""
        if context_dir in claude_md:
            report("EXISTS", f"CLAUDE.md mentions {context_dir}/")
        else:
            report("SUGGEST", "add to CLAUDE.md (only with the user's consent):")
            io.out.write(f"           {CLAUDE_MD_LINE.format(context_dir=context_dir)}\n")

    adr = os.path.join(proj, (profile.get("adr_dir") if profile else None) or "docs/adr")
    if os.path.isdir(adr):
        report("EXISTS", rel(adr) + "/")
    else:
        report("SKIPPED", f"{rel(adr)}/  (created with the first ADR)")

    v = sys.version_info
    report("PYTHON", f"{sys.executable} ({v.major}.{v.minor}.{v.micro})")

    io.out.write("\n")
    if os.path.isfile(profile_file):
        io.out.write("lasagna: ready. Guardrails active. Start with /lasagna <what you want>.\n")
        return 0
    io.out.write("lasagna: NOT ready. Write the stack profile before relying on anything.\n")
    return 1


def status(args: Sequence[str], env: Env, io: Streams) -> int:
    if not os.path.isdir(lasagna_dir(env)):
        io.out.write(f"lasagna: not initialised here (no {lasagna_dir(env)}). Run /lasagna-init.\n")
        return 0
    return session_status("", env, io)


COMMANDS = {
    "set-state": set_state,
    "check-traceability": check_traceability,
    "init": init,
    "status": status,
}


def run_cli(name: str, args: Sequence[str], env: Env, io: Streams) -> int:
    command = COMMANDS.get(name)
    if command is None:
        io.err.write(
            f"lasagna: unknown command {name!r}. "
            f"Commands: hook <name>, {', '.join(COMMANDS)}, python.\n"
        )
        return 1
    return command(args, env, io)
