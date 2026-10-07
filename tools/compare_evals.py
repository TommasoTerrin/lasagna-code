"""Compare two `claude plugin eval` runs case by case.

    python tools/compare_evals.py <old aggregate-result.json> <new aggregate-result.json>

`claude plugin eval` compares a plugin with no plugin; it does not compare two
versions of the plugin. Run the same suite on both checkouts (see
plugins/lasagna/evals/README.md), then feed the two aggregate-result.json files
here. A case whose score drops is a regression to explain before a release.
"""

from __future__ import annotations

import json
import sys
from typing import Dict, Tuple


def load(path: str) -> Tuple[Dict[str, dict], dict]:
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    cases = {c["name"]: c for c in data.get("cases", [])}
    return cases, data


def runs(case: dict) -> int:
    return len(case.get("arms", {}).get("with", []))


def errors(case: dict) -> int:
    return sum(1 for r in case.get("arms", {}).get("with", []) if r.get("error"))


def score(case: dict) -> float:
    return float(case.get("aggregates", {}).get("score", 0.0))


def main(argv) -> int:
    if len(argv) != 2:
        print(__doc__)
        return 2
    old, old_data = load(argv[0])
    new, new_data = load(argv[1])
    width = max([len(n) for n in set(old) | set(new)] + [4])
    print(f"{'case':<{width}}  {'old':>6}  {'new':>6}  {'delta':>7}  runs(old/new)  note")
    worse = 0
    for name in sorted(set(old) | set(new)):
        o, n = old.get(name), new.get(name)
        if o is None or n is None:
            print(f"{name:<{width}}  {'-' if o is None else f'{score(o):.2f}':>6}  "
                  f"{'-' if n is None else f'{score(n):.2f}':>6}  {'':>7}  {'':13}  only in {'new' if o is None else 'old'}")
            continue
        delta = score(n) - score(o)
        note = []
        if min(runs(o), runs(n)) < 5:
            note.append("fewer than 5 runs: noisy")
        if errors(o) or errors(n):
            note.append(f"errors {errors(o)}/{errors(n)}")
        if delta < 0:
            worse += 1
            note.insert(0, "REGRESSION")
        print(f"{name:<{width}}  {score(o):6.2f}  {score(n):6.2f}  {delta:+7.2f}  {runs(o):>5}/{runs(n):<7}  {', '.join(note)}")
    print()
    for label, data in (("old", old_data), ("new", new_data)):
        agg = data.get("aggregates", {})
        print(f"{label}: overall {agg.get('overallScore', 0):.2f}, cost ${data.get('costUsd', 0):.2f}, "
              f"claude {data.get('claudeVersion', '?')}")
    return 1 if worse else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
