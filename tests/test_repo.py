"""What the plugin repository must (not) contain — docs/v2-spec.md §7."""

import json
import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
PLUGIN = REPO / "plugins" / "lasagna"
MARKDOWN = sorted(PLUGIN.rglob("*.md"))

# v1 profiles keep working (AC-V2-019): only the compatibility layer may name
# the removed keys.
COMPAT = {
    PLUGIN / "scripts" / "lasagna_lib" / "core" / "profile.py",
    PLUGIN / "scripts" / "lasagna_lib" / "core" / "budget.py",
    PLUGIN / "templates" / "stack" / "base.md",
}


def plugin_text_files():
    for p in PLUGIN.rglob("*"):
        if p.is_file() and p.suffix in (".md", ".py", ".json", ".sh") and p not in COMPAT:
            yield p


def test_run_sh_is_the_only_shell_script():  # AC-V2-001
    assert [p.name for p in (PLUGIN / "scripts").rglob("*.sh")] == ["run.sh"]


@pytest.mark.parametrize(
    "word", ["check-onion", "onion-baseline", "core_path", "core_allowed_import", "core_forbidden_pattern"]
)
def test_no_v1_layering_left(word):  # AC-V2-012
    hits = [str(p.relative_to(REPO)) for p in plugin_text_files() if word in p.read_text(encoding="utf-8")]
    assert hits == []


def test_no_v1_script_names_left():
    pattern = re.compile(r"scripts/[a-z-]+\.sh")
    hits = []
    for p in plugin_text_files():
        for m in pattern.findall(p.read_text(encoding="utf-8")):
            if m != "scripts/run.sh":
                hits.append(f"{p.relative_to(REPO)}: {m}")
    assert hits == []


def test_ports_adapters_gone_and_pr_gate_exists():  # AC-V2-013
    assert not (PLUGIN / "skills" / "ports-adapters").exists()
    assert (PLUGIN / "skills" / "pr-gate" / "SKILL.md").is_file()
    for p in MARKDOWN:
        assert "ports-adapters" not in p.read_text(encoding="utf-8"), p


def test_contract_template_has_external_dependencies():  # AC-V2-016
    text = (PLUGIN / "templates" / "contract.md").read_text(encoding="utf-8")
    assert "## External dependencies" in text
    assert "## Required ports" not in text
    assert "## Determinism" not in text


def test_phase_values_have_characterize_not_ports_adapters():  # AC-V2-017
    text = (PLUGIN / "templates" / "phase-state.md").read_text(encoding="utf-8")
    assert "`characterize`" in text
    tdd = (PLUGIN / "skills" / "tdd-loop" / "SKILL.md").read_text(encoding="utf-8")
    assert "tracer bullet" in tdd


def test_no_hand_written_context_md():  # AC-V2-018
    hits = [str(p.relative_to(REPO)) for p in MARKDOWN if "CONTEXT.md" in p.read_text(encoding="utf-8")]
    assert hits == []
    for stack in ("python", "typescript", "jvm", "dotnet"):
        assert "context_dir: docs/context" in (PLUGIN / "templates" / "stack" / f"{stack}.md").read_text(
            encoding="utf-8"
        )


def test_hooks_json_wires_every_hook_through_run_sh():
    hooks = json.loads((PLUGIN / "hooks" / "hooks.json").read_text(encoding="utf-8"))["hooks"]
    commands = [h["command"] for groups in hooks.values() for g in groups for h in g["hooks"]]
    names = sorted(c.rsplit(" ", 1)[1] for c in commands)
    assert names == sorted(
        ["session-status", "block-test-edits", "block-reads", "capture-test-result", "count-cycle", "dump-phase-state"]
    )
    assert all(c.startswith('sh "${CLAUDE_PLUGIN_ROOT}/scripts/run.sh" hook ') for c in commands)


def test_core_tests_use_no_mocks():  # AC-V2-011
    for p in (REPO / "tests" / "core").glob("*.py"):
        text = p.read_text(encoding="utf-8")
        for word in ("unittest.mock", "monkeypatch", "MagicMock"):
            assert word not in text, f"{p.name} uses {word}"


def test_core_is_pure():
    """The core imports nothing that reaches the world (INV-4)."""
    forbidden = re.compile(r"^\s*(import|from)\s+(os|sys|subprocess|shutil|glob|tempfile|pathlib|datetime|time|random)\b", re.M)
    for p in (PLUGIN / "scripts" / "lasagna_lib" / "core").glob("*.py"):
        assert not forbidden.search(p.read_text(encoding="utf-8")), p.name
