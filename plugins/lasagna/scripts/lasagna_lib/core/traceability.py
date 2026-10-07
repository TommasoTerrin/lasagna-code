"""Traceability by id, in both directions.

No acceptance criterion without a test referencing it; no reference in the
tests to a criterion the spec does not contain.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, List, Sequence, Tuple

ID_PATTERN = r"AC-[A-Za-z0-9][A-Za-z0-9-]*-[0-9]{3}"
_ID = re.compile(ID_PATTERN)


@dataclass(frozen=True)
class TraceReport:
    spec_ids: Tuple[str, ...]
    missing: Tuple[str, ...]
    orphans: Tuple[str, ...]


@dataclass(frozen=True)
class CommandOutput:
    stdout: str
    stderr: str
    exit_code: int


def trace(spec_text: str, test_texts: Iterable[str]) -> TraceReport:
    spec = set(_ID.findall(spec_text))
    tests = set()
    for text in test_texts:
        tests.update(_ID.findall(text))
    return TraceReport(
        spec_ids=tuple(sorted(spec)),
        missing=tuple(sorted(spec - tests)),
        orphans=tuple(sorted(tests - spec)),
    )


def render_trace(
    report: TraceReport, spec_name: str, test_paths: Sequence[str], any_test_dir_found: bool
) -> CommandOutput:
    n_spec, n_miss = len(report.spec_ids), len(report.missing)
    out: List[str] = [
        f"lasagna: traceability of {spec_name}",
        f"  criteria in the spec:     {n_spec}",
        f"  criteria covered by test: {n_spec - n_miss}",
    ]
    err: List[str] = []
    if not any_test_dir_found:
        err.append(
            f"  WARNING: none of the profile test_path entries exist ({' '.join(test_paths)})."
        )
    if report.missing:
        err += ["", f"Criteria with NO test ({n_miss}):"]
        err += [f"  - {i}" for i in report.missing]
        err += [
            "",
            "Each line above is behaviour the spec promises and nobody verifies.",
            "Send them back to the test-writer, one at a time.",
        ]
    if report.orphans:
        err += ["", f"ORPHAN references in tests ({len(report.orphans)}):"]
        err += [f"  - {i}" for i in report.orphans]
        err += [
            "",
            "These IDs appear in tests but not in the spec: either the criterion",
            "was renamed (align the test) or the test verifies something nobody",
            "asked for (delete it, or add the criterion to the spec).",
        ]
    if n_spec == 0:
        err += [
            "",
            "The spec contains no IDs in the AC-<feature>-NNN format.",
            "Without IDs there is no traceability: re-read the spec template.",
        ]
    ok = n_spec > 0 and not report.missing and not report.orphans
    if ok:
        out.append("  OK: no uncovered criteria, no orphan tests.")
    return CommandOutput(
        stdout="\n".join(out) + "\n",
        stderr="\n".join(err) + "\n" if err else "",
        exit_code=0 if ok else 1,
    )
