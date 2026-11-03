"""Compare two BR-001 evaluation reports and fail on a regression."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

HIGHER_IS_BETTER = ("pass_rate", "hit1", "hit5", "mrr", "answer_accuracy", "source_coverage", "no_answer_accuracy")
LOWER_IS_BETTER = ("stale_above_current",)
LATENCY_KEYS = ("p50", "p95")
LATENCY_TOLERANCE = 0.30  # shortcut: fixed tolerance, make configurable once CI latency noise is known


def load(path: Path) -> dict[str, Any]:
    report = json.loads(path.read_text(encoding="utf-8"))
    if report.get("schema_version") != "1":
        raise ValueError(f"{path}: unsupported report schema {report.get('schema_version')!r}")
    return report


def _metric(aggregate: dict[str, Any], key: str) -> Any:
    if key in LATENCY_KEYS:
        return (aggregate.get("latency_ms") or {}).get(key)
    return aggregate.get(key)


def compare(base: dict[str, Any], new: dict[str, Any]) -> dict[str, Any]:
    old_hash = (base.get("dataset") or {}).get("sha256")
    new_hash = (new.get("dataset") or {}).get("sha256")
    if not old_hash or old_hash != new_hash:
        raise ValueError(f"dataset mismatch: {old_hash} != {new_hash}")

    modes: dict[str, Any] = {}
    regressions: list[str] = []
    for mode, old_mode in (base.get("modes") or {}).items():
        new_mode = (new.get("modes") or {}).get(mode)
        if new_mode is None:
            continue
        old_agg = old_mode.get("aggregate") or {}
        new_agg = new_mode.get("aggregate") or {}
        entry: dict[str, Any] = {"base_status": old_mode.get("status"), "new_status": new_mode.get("status"), "deltas": {}}
        if old_mode.get("status") != new_mode.get("status"):
            regressions.append(f"{mode}: status {old_mode.get('status')} -> {new_mode.get('status')}")
            modes[mode] = entry
            continue
        if old_mode.get("status") != "ok":
            modes[mode] = entry
            continue
        for key in HIGHER_IS_BETTER:
            before, after = _metric(old_agg, key), _metric(new_agg, key)
            if before is None or after is None:
                continue
            entry["deltas"][key] = round(after - before, 4)
            if after < before - 1e-9:
                regressions.append(f"{mode}: {key} {before} -> {after}")
        for key in LOWER_IS_BETTER:
            before, after = _metric(old_agg, key), _metric(new_agg, key)
            if before is None or after is None:
                continue
            entry["deltas"][key] = after - before
            if after > before:
                regressions.append(f"{mode}: {key} {before} -> {after}")
        for key in LATENCY_KEYS:
            before, after = _metric(old_agg, key), _metric(new_agg, key)
            if not before or after is None:
                continue
            entry["deltas"][f"latency_ms.{key}"] = round(after - before, 2)
            if after > before * (1 + LATENCY_TOLERANCE):
                regressions.append(f"{mode}: latency_ms.{key} {before} -> {after} (>{(1 + LATENCY_TOLERANCE):.0%})")
        modes[mode] = entry
    return {
        "base_version": base.get("brain_version"),
        "new_version": new.get("brain_version"),
        "dataset_sha256": old_hash,
        "modes": modes,
        "regressions": regressions,
        "ok": not regressions,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("base", type=Path)
    parser.add_argument("new", type=Path)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args(argv)
    try:
        result = compare(load(args.base), load(args.new))
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    print(f"{result['base_version']} -> {result['new_version']} ({result['dataset_sha256'][:12]})")
    for mode, entry in result["modes"].items():
        print(f"{mode}: {entry['base_status']} -> {entry['new_status']} {entry['deltas']}")
    for regression in result["regressions"]:
        print(f"REGRESSION: {regression}")
    print("ok" if result["ok"] else f"regressions={len(result['regressions'])}")
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())