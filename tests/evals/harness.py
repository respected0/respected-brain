"""BR-001 memory evaluation harness.

Runs synthetic, retrieval-level memory scenarios against an isolated temporary vault and
compares the product's search modes (none, fts, hybrid, semantic). It never touches the
user's real vault, settings or data root.

Example:
    python -m tests.evals.harness --modes none,fts,hybrid --repeats 3
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import sqlite3
import statistics
import tempfile
import time
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any
from unittest.mock import patch
from uuid import uuid4

from respected_brain.core.config import ConfigStore
from respected_brain.memory.inbox import MemoryOpError
from respected_brain.rpp import memory as rpp_memory
from respected_brain.rpp.integrations import _context
from respected_brain.search import semantic
from respected_brain.search.engine import SearchEngine

HERE = Path(__file__).resolve().parent
BRAIN_ROOT = HERE.parents[1]
DEFAULT_DATASET = HERE / "scenarios.json"
DEFAULT_OUT_DIR = HERE / "results"
MODES = ("none", "fts", "hybrid", "semantic")
CATEGORIES = ("recall", "multi_session", "temporal", "update", "unknown")
PROMPT = "retrieval-only: synthetic query -> top-k path/title/snippet; no generation model is invoked"
SCHEMA_VERSION = "1"


def _version() -> str:
    try:
        return version("respected-brain")
    except PackageNotFoundError:
        return "unknown"


def load_dataset(path: Path = DEFAULT_DATASET) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    scenarios = data.get("scenarios")
    if not isinstance(scenarios, list) or not 40 <= len(scenarios) <= 50:
        raise ValueError("dataset must contain 40-50 scenarios")
    ids: set[str] = set()
    found = {scenario.get("category") for scenario in scenarios}
    if not set(CATEGORIES) <= found:
        raise ValueError(f"dataset is missing categories: {sorted(set(CATEGORIES) - found)}")
    for scenario in scenarios:
        sid = scenario.get("id")
        if not isinstance(sid, str) or not sid or sid in ids:
            raise ValueError(f"invalid or duplicate scenario id: {sid!r}")
        ids.add(sid)
        if scenario.get("category") not in CATEGORIES:
            raise ValueError(f"{sid}: unknown category {scenario.get('category')!r}")
        if not isinstance(scenario.get("query"), str) or not scenario["query"].strip():
            raise ValueError(f"{sid}: empty query")
        notes = scenario.get("notes")
        if not isinstance(notes, list) or not notes:
            raise ValueError(f"{sid}: notes must be a non-empty list")
        for note in notes:
            if not isinstance(note.get("path"), str) or not note["path"].endswith(".md"):
                raise ValueError(f"{sid}: invalid note path")
            if not isinstance(note.get("content"), str) or not note["content"].strip():
                raise ValueError(f"{sid}: empty note content")
        expected = scenario.get("expected_paths")
        if not isinstance(expected, list):
            raise ValueError(f"{sid}: expected_paths must be a list")
        if scenario.get("no_answer"):
            if expected:
                raise ValueError(f"{sid}: no-answer scenario must not expect paths")
        elif not expected:
            raise ValueError(f"{sid}: answerable scenario needs expected_paths")
    return data


def dataset_digest(path: Path = DEFAULT_DATASET) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _build_fixture(base: Path, scenario: dict[str, Any]) -> tuple[Path, str, dict[str, Any], dict[str, Any]]:
    data, vault = base / "data", base / "vault"
    data.mkdir()
    vault.mkdir()
    for note in scenario["notes"]:
        target = vault / note["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(note["content"], encoding="utf-8")

    patcher = patch.dict(os.environ, {"RESPECTED_APP_DIR": str(base / "app"), "RESPECTED_DATA_DIR": str(data)})
    patcher.start()
    try:
        vault_id = str(uuid4())

        def mutate(document: dict[str, Any]) -> None:
            document["vaults"][vault_id] = {"path": str(vault)}
            document["active_vault_id"] = vault_id

        ConfigStore(data).update(mutate)
        _, ctx = _context(data, {})
        started = time.perf_counter()
        stats = SearchEngine(ctx).index_vault(force=True)
        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        if stats is None:
            raise RuntimeError("index busy")
        cfg = semantic.load_config(data)
        return data, vault_id, cfg, {"index": stats, "index_ms": elapsed_ms}
    finally:
        patcher.stop()


def _snippets(result: dict[str, Any]) -> str:
    return " ".join(str(hit.get("snippet") or "") for hit in result.get("results", [])).casefold()


def score_result(scenario: dict[str, Any], result: dict[str, Any], limit: int) -> dict[str, Any]:
    """Score one retrieval result against one scenario; pure function (tested directly)."""
    hits = result.get("results", [])
    paths = [hit.get("path") for hit in hits]
    expected = scenario.get("expected_paths") or []

    if scenario.get("no_answer"):
        return {
            "pass": len(hits) == 0,
            "no_answer": True,
            "no_answer_ok": len(hits) == 0,
            "hit1": None, "hit5": None, "mrr": None, "answer": None, "coverage": None,
            "stale_above_current": 0, "paths": paths,
        }

    terms = [str(term).casefold() for term in scenario.get("answer_terms", [])]
    text = _snippets(result)
    answer_ok = all(term in text for term in terms)
    hit1 = bool(paths) and paths[0] in expected
    hitk = any(path in expected for path in paths[:limit])
    rr = next((1.0 / (position + 1) for position, path in enumerate(paths) if path in expected), 0.0)
    coverage = len(set(expected) & set(paths)) / len(expected) if expected else 0.0
    top1_ok = hit1 if scenario.get("expect_top1") else True

    current_positions = [position for position, path in enumerate(paths) if path in expected]
    best_current = min(current_positions) if current_positions else None
    stale_leaks = 0
    for stale in scenario.get("stale_paths", []):
        if stale in paths and (best_current is None or paths.index(stale) < best_current):
            stale_leaks += 1

    return {
        "pass": bool(hitk and answer_ok and top1_ok and stale_leaks == 0),
        "no_answer": False,
        "no_answer_ok": None,
        "hit1": hit1,
        "hit5": hitk,
        "mrr": rr,
        "answer": answer_ok,
        "coverage": coverage,
        "stale_above_current": stale_leaks,
        "top1_ok": top1_ok,
        "paths": paths,
    }


def _run_query(scenario: dict[str, Any], mode: str, data: Path, vault_id: str,
               limit: int, snippet_chars: int) -> tuple[dict[str, Any], dict[str, Any], float]:
    if mode == "none":
        return {"results": [], "count": 0}, {"mode": "none"}, 0.0
    started = time.perf_counter()
    try:
        result = rpp_memory.run_query(data, vault_id, scenario["query"], limit, snippet_chars, None, mode)
    except MemoryOpError:
        raise
    elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
    return result, result.get("search", {}), elapsed_ms


def _percentile(values: list[float], percentile: int) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, math.ceil(percentile / 100 * len(ordered)) - 1))
    return round(ordered[index], 3)


def _mean(values: list[float]) -> float | None:
    return round(statistics.fmean(values), 4) if values else None


def _aggregate(scenarios: list[dict[str, Any]], per_scenario: dict[str, Any], repeats: int) -> dict[str, Any]:
    available = [row for row in per_scenario.values() if row.get("status") == "ok"]
    retrieval = [row for row in available if not row["score"]["no_answer"]]
    unknown = [row for row in available if row["score"]["no_answer"]]
    runs = [run for row in available for run in row.get("runs", [])]
    latencies = [run["latency_ms"] for run in runs if run["latency_ms"] is not None and run["latency_ms"] > 0]
    distributions = []
    for repetition in range(repeats):
        rep_runs = [row["runs"][repetition] for row in available if len(row.get("runs", [])) > repetition]
        distributions.append(_mean([1.0 if run["pass"] else 0.0 for run in rep_runs]))

    category_breakdown: dict[str, dict[str, Any]] = {}
    for category in CATEGORIES:
        rows = [row for row in available if row["category"] == category]
        category_breakdown[category] = {
            "scenarios": len(rows),
            "pass_rate": _mean([1.0 if row["score"]["pass"] else 0.0 for row in rows]),
        }

    return {
        "scenarios": len(scenarios),
        "evaluated": len(available),
        "pass_rate": _mean([1.0 if row["score"]["pass"] else 0.0 for row in available]),
        "hit1": _mean([1.0 if row["score"]["hit1"] else 0.0 for row in retrieval]),
        "hit5": _mean([1.0 if row["score"]["hit5"] else 0.0 for row in retrieval]),
        "mrr": _mean([row["score"]["mrr"] for row in retrieval if row["score"]["mrr"] is not None]),
        "answer_accuracy": _mean([1.0 if row["score"]["answer"] else 0.0 for row in retrieval]),
        "source_coverage": _mean([row["score"]["coverage"] for row in retrieval if row["score"]["coverage"] is not None]),
        "stale_above_current": sum(row["score"]["stale_above_current"] for row in retrieval),
        "no_answer_accuracy": _mean([1.0 if row["score"]["no_answer_ok"] else 0.0 for row in unknown]),
        "latency_ms": {"p50": _percentile(latencies, 50), "p95": _percentile(latencies, 95), "samples": len(latencies)},
        "context_tokens_estimate": _mean([run["context_tokens"] for run in runs if run["context_tokens"] is not None]),
        "repeat_pass_rate": distributions,
        "repeat_stdev": round(statistics.pstdev([value for value in distributions if value is not None]), 4) if len([value for value in distributions if value is not None]) > 1 else 0.0,
        "categories": category_breakdown,
    }


def evaluate(dataset_path: Path = DEFAULT_DATASET, modes: tuple[str, ...] = ("none", "fts", "hybrid"),
             repeats: int = 3, limit: int = 5, snippet_chars: int = 400) -> dict[str, Any]:
    if not modes or any(mode not in MODES for mode in modes):
        raise ValueError(f"modes must be a subset of {MODES}")
    if repeats < 1:
        raise ValueError("repeats must be >= 1")
    dataset = load_dataset(dataset_path)
    scenarios = dataset["scenarios"]
    report: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "harness": "BR-001",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "brain_version": _version(),
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "sqlite": sqlite3.sqlite_version,
        },
        "dataset": {
            "path": str(Path(dataset_path).resolve()),
            "sha256": dataset_digest(dataset_path),
            "version": dataset.get("version"),
            "scenario_count": len(scenarios),
            "categories": {category: sum(1 for s in scenarios if s["category"] == category) for category in CATEGORIES},
        },
        "settings": {"modes": list(modes), "repeats": repeats, "limit": limit, "snippet_chars": snippet_chars},
        "prompt": PROMPT,
        "model": {"generation": None, "note": "no generation model is invoked by this harness", "semantic": None},
        "modes": {},
    }

    for mode in modes:
        per_scenario: dict[str, Any] = {}
        semantic_cfg: dict[str, Any] | None = None
        for scenario in scenarios:
            with tempfile.TemporaryDirectory(prefix=f"brain-eval-{scenario['id']}-") as temporary:
                base = Path(temporary).resolve()
                try:
                    data, vault_id, cfg, fixture = _build_fixture(base, scenario)
                    semantic_cfg = semantic_cfg or cfg
                    runs = []
                    blocked: dict[str, Any] | None = None
                    for repetition in range(repeats):
                        try:
                            raw, info, latency = _run_query(
                                scenario, mode, data, vault_id, limit, snippet_chars)
                        except MemoryOpError as error:
                            if error.code == "SEMANTIC_OFF":
                                blocked = {"status": "unavailable", "reason": error.code, "message": error.message}
                                break
                            raise
                        score = score_result(scenario, raw, limit)
                        runs.append({
                            "repetition": repetition,
                            "pass": score["pass"],
                            "latency_ms": latency,
                            "context_tokens": round(sum(len(str(h.get("snippet") or "")) for h in raw.get("results", [])) / 4, 1),
                            "search": info,
                        })
                    if blocked:
                        per_scenario[scenario["id"]] = {
                            "category": scenario["category"], "status": "unavailable", **blocked,
                            "index": fixture["index"], "index_ms": fixture["index_ms"],
                        }
                    else:
                        per_scenario[scenario["id"]] = {
                            "category": scenario["category"],
                            "status": "ok",
                            "query": scenario["query"],
                            "score": score_result(scenario, raw, limit),
                            "runs": runs,
                            "index": fixture["index"],
                            "index_ms": fixture["index_ms"],
                        }
                except Exception as error:  # a broken fixture must be visible, not silently skipped
                    per_scenario[scenario["id"]] = {
                        "category": scenario["category"],
                        "status": "error",
                        "error": f"{type(error).__name__}: {error}",
                    }

        available = [row for row in per_scenario.values() if row["status"] == "ok"]
        report["modes"][mode] = {
            "status": "unavailable" if not available and per_scenario else "ok",
            "aggregate": _aggregate(scenarios, per_scenario, repeats),
            "scenarios": per_scenario,
        }
        if semantic_cfg is not None and report["model"]["semantic"] is None:
            report["model"]["semantic"] = {
                "enabled": semantic_cfg.get("enabled"),
                "provider": semantic_cfg.get("provider"),
                "model": semantic_cfg.get("model"),
            }
    return report


def render_markdown(report: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Respected Brain — Memory Evaluation Report (BR-001)")
    lines.append("")
    lines.append(f"- Generated: `{report['generated_at']}`")
    lines.append(f"- Brain version: `{report['brain_version']}`")
    lines.append(f"- Dataset: `{report['dataset']['scenario_count']}` scenarios, sha256 `{report['dataset']['sha256']}`")
    lines.append(f"- Settings: modes `{', '.join(report['settings']['modes'])}`, repeats `{report['settings']['repeats']}`, limit `{report['settings']['limit']}`, snippet `{report['settings']['snippet_chars']}`")
    lines.append(f"- Prompt: {report['prompt']}")
    lines.append(f"- Semantic model: `{report['model']['semantic']}`")
    lines.append("")
    lines.append("## Aggregate")
    lines.append("")
    lines.append("| Mode | Pass | Hit@1 | Hit@5 | MRR | Answer | Coverage | Stale leak | No-answer | P50 ms | P95 ms | Ctx tokens |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for mode, payload in report["modes"].items():
        agg = payload["aggregate"]
        def pct(value: float | None) -> str:
            return "n/a" if value is None else f"{value * 100:.1f}%"
        lines.append(
            f"| `{mode}` | {pct(agg['pass_rate'])} | {pct(agg['hit1'])} | {pct(agg['hit5'])} | "
            f"{'n/a' if agg['mrr'] is None else f'{agg["mrr"]:.3f}'} | {pct(agg['answer_accuracy'])} | "
            f"{pct(agg['source_coverage'])} | {agg['stale_above_current']} | {pct(agg['no_answer_accuracy'])} | "
            f"{'n/a' if agg['latency_ms']['p50'] is None else agg['latency_ms']['p50']} | "
            f"{'n/a' if agg['latency_ms']['p95'] is None else agg['latency_ms']['p95']} | "
            f"{'n/a' if agg['context_tokens_estimate'] is None else agg['context_tokens_estimate']} |"
        )
    lines.append("")
    lines.append("## Category pass rate")
    lines.append("")
    header = "| Mode | " + " | ".join(CATEGORIES) + " |"
    lines.append(header)
    lines.append("|---|" + "---|" * len(CATEGORIES))
    for mode, payload in report["modes"].items():
        cells = []
        for category in CATEGORIES:
            value = payload["aggregate"]["categories"][category]["pass_rate"]
            cells.append("n/a" if value is None else f"{value * 100:.0f}%")
        lines.append(f"| `{mode}` | " + " | ".join(cells) + " |")
    lines.append("")
    lines.append("## Failures")
    lines.append("")
    failures = 0
    for mode, payload in report["modes"].items():
        for sid, row in payload["scenarios"].items():
            if row["status"] == "error":
                lines.append(f"- `{mode}` / `{sid}` — fixture error: {row['error']}")
                failures += 1
                continue
            if row["status"] != "ok" or row["score"]["pass"]:
                continue
            score = row["score"]
            reason = []
            if score.get("no_answer"):
                reason.append("returned hits for an unknown query")
            else:
                if not score["hit5"]:
                    reason.append("expected source outside top-k")
                if not score["answer"]:
                    reason.append("answer term missing")
                if score.get("top1_ok") is False:
                    reason.append("expected source not first")
                if score["stale_above_current"]:
                    reason.append("superseded note ranked above current")
            lines.append(
                f"- `{mode}` / `{sid}` ({row['category']}) — {', '.join(reason)}; got `{[p for p in score.get('paths', [])][:3]}`")
            failures += 1
    if not failures:
        lines.append("- None.")
    lines.append("")
    lines.append("## Repeat distribution")
    lines.append("")
    for mode, payload in report["modes"].items():
        values = payload["aggregate"]["repeat_pass_rate"]
        lines.append(f"- `{mode}`: {values} (stdev {payload['aggregate']['repeat_stdev']})")
    lines.append("")
    lines.append("## Limits")
    lines.append("")
    lines.append("- Retrieval-level evaluation only: no answer synthesis/judge model, no summary quality claim.")
    lines.append("- Semantic mode reports `unavailable` when the local provider is disabled; it is not silently scored as zero.")
    lines.append("- Synthetic notes are isolated in temporary directories; the real user vault is never read.")
    lines.append("")
    return "\n".join(lines)


def _paths(args: argparse.Namespace) -> tuple[Path, Path]:
    suffix = f"baseline-{_version()}"
    json_path = Path(args.json_out) if args.json_out else DEFAULT_OUT_DIR / f"{suffix}.json"
    md_path = Path(args.md_out) if args.md_out else DEFAULT_OUT_DIR / f"{suffix}.md"
    return json_path, md_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="BR-001 synthetic memory evaluation harness")
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--modes", default="none,fts,hybrid", help=f"comma-separated subset of {MODES}")
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--snippet-chars", type=int, default=400)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--md-out", type=Path)
    args = parser.parse_args(argv)

    modes = tuple(mode.strip() for mode in args.modes.split(",") if mode.strip())
    report = evaluate(args.dataset, modes, args.repeats, args.limit, args.snippet_chars)
    json_path, md_path = _paths(args)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(report) + "\n", encoding="utf-8")

    print(f"dataset={report['dataset']['scenario_count']} scenarios sha256={report['dataset']['sha256'][:12]}")
    for mode, payload in report["modes"].items():
        agg = payload["aggregate"]
        pct = lambda value: "n/a" if value is None else f"{value * 100:.1f}%"
        print(f"{mode}: evaluated={agg['evaluated']} pass={pct(agg['pass_rate'])} "
              f"hit@5={pct(agg['hit5'])} answer={pct(agg['answer_accuracy'])} "
              f"p50={agg['latency_ms']['p50']}ms p95={agg['latency_ms']['p95']}ms")
    print(f"json={json_path.resolve()}")
    print(f"markdown={md_path.resolve()}")
    errors = sum(1 for payload in report["modes"].values()
                 for row in payload["scenarios"].values() if row["status"] == "error")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
