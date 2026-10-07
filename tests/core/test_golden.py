"""Golden outputs of real test runners (AC-V2-007).

Fixtures come from tools/capture_golden.py, which runs the runners for real and
records v1's verdict next to v2's. The hook knows no runner: what is verified
here is that each shipped stack template's patterns classify its runner's real
output, and that every difference from v1 is a documented deviation.
"""

import json
from pathlib import Path

import pytest

from lasagna_lib.core.classify import classify_output
from lasagna_lib.core.profile import parse_profile

REPO = Path(__file__).resolve().parents[2]
GOLDEN = REPO / "tests" / "fixtures" / "golden"
STACKS = REPO / "plugins" / "lasagna" / "templates" / "stack"
FIXTURES = sorted(GOLDEN.glob("*.json"))


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def output_of(fixture):
    resp = fixture["tool_response"]
    return "\n".join([resp.get("stdout", ""), resp.get("stderr", "")])


@pytest.mark.parametrize("path", FIXTURES, ids=[p.stem for p in FIXTURES])
def test_template_classifies_real_output(path):
    fixture = load(path)
    profile = parse_profile((STACKS / f"{fixture['stack']}.md").read_text(encoding="utf-8"))
    assert classify_output(output_of(fixture), profile).value == fixture["expected"]


@pytest.mark.parametrize("path", FIXTURES, ids=[p.stem for p in FIXTURES])
def test_differences_from_v1_are_documented(path):
    fixture = load(path)
    if fixture["v1"] != fixture["expected"]:
        assert fixture.get("deviation", "").strip()
        assert not fixture["deviation"].startswith("UNEXPLAINED")


@pytest.mark.parametrize("stack", ["python", "typescript", "jvm", "dotnet"])
def test_every_outcome_is_covered_or_reported_unverified(stack):
    seen = {load(p)["expected"] for p in FIXTURES if load(p)["stack"] == stack}
    if not seen:
        pytest.skip(f"not verified: no real {stack} runner output captured (tools/capture_golden.py)")
    assert {"green", "red-assertion", "red-compile", "red-generic"} <= seen
