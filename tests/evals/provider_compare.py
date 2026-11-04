"""Compare two summarisation eval reports produced from the same dataset."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


HIGHER_IS_BETTER = ("pass_rate", "schema_valid_rate", "fact_coverage", "prompt_coverage", "section_accuracy")
LOWER_IS_BETTER = (
    "truncated_facts", "hallucination_scenarios", "secret_leak_scenarios",
    "injection_leak_scenarios", "raw_transcript_stored", "flush_failures",
)


def load(path: Path) -> dict[str, Any]:
    report = json.loads(path.read_text(encoding="utf-8"))
    if report.get("schema_version") != "1" or not isinstance(report.get("aggregate"), dict):
        raise ValueError(f"{path}: unsupported summarisation report")
    return report


def compare(base: dict[str, Any], new: dict[str, Any]) -> dict[str, Any]:
    old_hash = (base.get("dataset") or {}).get("sha256")
    new_hash = (new.get("dataset") or {}).get("sha256")
    if not old_hash or old_hash != new_hash:
        raise ValueError(f"dataset mismatch: {old_hash} != {new_hash}")
    old, fresh = base["aggregate"], new["aggregate"]
    deltas: dict[str, float] = {}
    regressions: list[str] = []
    for key in HIGHER_IS_BETTER:
        if isinstance(old.get(key), (int, float)) and isinstance(fresh.get(key), (int, float)):
            deltas[key] = round(fresh[key] - old[key], 4)
            if fresh[key] < old[key]:
                regressions.append(f"{key} {old[key]} -> {fresh[key]}")
    for key in LOWER_IS_BETTER:
        if isinstance(old.get(key), (int, float)) and isinstance(fresh.get(key), (int, float)):
            deltas[key] = round(fresh[key] - old[key], 4)
            if fresh[key] > old[key]:
                regressions.append(f"{key} {old[key]} -> {fresh[key]}")
    categories: dict[str, Any] = {}
    for name, before in (old.get("categories") or {}).items():
        after = (fresh.get("categories") or {}).get(name) or {}
        categories[name] = {
            "pass_rate": round(after.get("pass_rate", 0) - before.get("pass_rate", 0), 4),
            "fact_coverage": round(after.get("fact_coverage", 0) - before.get("fact_coverage", 0), 4),
        }
    return {
        "dataset_sha256": old_hash,
        "base": {"provider": (base.get("model") or {}).get("provider"), "label": (base.get("model") or {}).get("label")},
        "new": {"provider": (new.get("model") or {}).get("provider"), "label": (new.get("model") or {}).get("label")},
        "deltas": deltas,
        "categories": categories,
        "regressions": regressions,
        "ok": not regressions,
    }


def markdown(report: dict[str, Any]) -> str:
    base, new = report["base"], report["new"]
    lines = [
        "# Provider quality comparison",
        "",
        f"- Dataset: `{report['dataset_sha256']}`",
        f"- Base: `{base['label']}` ({base['provider']})",
        f"- New: `{new['label']}` ({new['provider']})",
        f"- Regressions: {len(report['regressions'])}",
        "",
        "| Metric | Delta (new - base) |",
        "|---|---:|",
    ]
    lines.extend(f"| `{key}` | {value:+.4f} |" for key, value in report["deltas"].items())
    lines.extend(["", "| Category | Pass-rate delta | Fact-coverage delta |", "|---|---:|---:|"])
    lines.extend(
        f"| `{name}` | {value['pass_rate']:+.4f} | {value['fact_coverage']:+.4f} |"
        for name, value in report["categories"].items()
    )
    lines.extend(["", "## Regressions", ""])
    lines.extend(f"- {value}" for value in report["regressions"]) if report["regressions"] else lines.append("- None.")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("base", type=Path)
    parser.add_argument("new", type=Path)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--md-out", type=Path)
    args = parser.parse_args(argv)
    report = compare(load(args.base), load(args.new))
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if args.md_out:
        args.md_out.parent.mkdir(parents=True, exist_ok=True)
        args.md_out.write_text(markdown(report), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
