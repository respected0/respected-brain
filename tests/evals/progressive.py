"""BR-012: compare progressive/budgeted context against full-note context."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import platform
import tempfile
from pathlib import Path
from typing import Any

from respected_brain import __version__
from respected_brain.memory.context import build_context
from respected_brain.rpp import memory as rpp_memory
from tests.evals.harness import (
    DEFAULT_DATASET,
    _build_fixture,
    _mean,
    _percentile,
    dataset_digest,
    load_dataset,
    score_result,
)

_MAX_NOTE = 120_000


def _full_view(results: list[dict[str, Any]], vault: Path) -> list[dict[str, Any]]:
    view = []
    for hit in results:
        path = hit.get("path")
        try:
            text = (vault / str(path)).read_bytes()[:_MAX_NOTE].decode("utf-8", "replace")
        except OSError:
            continue
        view.append({"path": path, "snippet": text})
    return view


_FILLER = "\n\n".join(
    f"Arka plan ayrintisi {index} bu senaryoyla dogrudan ilgisizdir ve yalnizca uzun notu temsil eder."
    for index in range(200)
)


def _padded(scenario: dict[str, Any], pad_chars: int) -> dict[str, Any]:
    """Keep the answer-bearing text, append irrelevant prose to emulate long real notes."""
    if pad_chars <= 0:
        return scenario
    notes = []
    for note in scenario["notes"]:
        content = note["content"]
        if len(content) < pad_chars:
            content = content + _FILLER[: pad_chars - len(content)]
        notes.append({**note, "content": content})
    return {**scenario, "notes": notes}


def _tokens(results: list[dict[str, Any]]) -> float:
    return round(sum(len(str(hit.get("snippet") or "")) for hit in results) / 4, 1)


def _aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    ok = [row for row in rows if row["status"] == "ok"]
    answerable = [row for row in ok if not row["score"]["no_answer"]]
    unknown = [row for row in ok if row["score"]["no_answer"]]
    return {
        "scenarios": len(rows),
        "evaluated": len(ok),
        "pass_rate": _mean([1.0 if row["score"]["pass"] else 0.0 for row in ok]),
        "hit1": _mean([1.0 if row["score"]["hit1"] else 0.0 for row in answerable]),
        "hit5": _mean([1.0 if row["score"]["hit5"] else 0.0 for row in answerable]),
        "mrr": _mean([row["score"]["mrr"] for row in answerable if row["score"]["mrr"] is not None]),
        "answer": _mean([1.0 if row["score"]["answer"] else 0.0 for row in answerable]),
        "coverage": _mean([row["score"]["coverage"] for row in answerable if row["score"]["coverage"] is not None]),
        "stale_above_current": sum(row["score"]["stale_above_current"] for row in ok),
        "no_answer": _mean([1.0 if row["score"]["no_answer_ok"] else 0.0 for row in unknown]),
        "tokens": _mean([row["tokens"] for row in ok]),
        "tokens_p50": _percentile([row["tokens"] for row in ok], 50),
        "tokens_p95": _percentile([row["tokens"] for row in ok], 95),
        "failures": [row["id"] for row in ok if not row["score"]["pass"]],
    }


def evaluate(dataset_path: Path = DEFAULT_DATASET, *, limit: int = 5, snippet_chars: int = 400,
             budgets: tuple[int, ...] = (600, 120, 60), pad_chars: int = 3000) -> dict[str, Any]:
    dataset = load_dataset(dataset_path)
    views = ["search", "full"] + [f"compact-{budget}" for budget in budgets]
    per_view: dict[str, list[dict[str, Any]]] = {view: [] for view in views}
    for scenario in dataset["scenarios"]:
        with tempfile.TemporaryDirectory(prefix=f"brain-progressive-{scenario['id']}-") as temporary:
            base = Path(temporary).resolve()
            data, vault_id, _, _ = _build_fixture(base, _padded(scenario, pad_chars))
            raw = rpp_memory.run_query(data, vault_id, scenario["query"], limit, snippet_chars, None, "fts")
            results = raw.get("results", [])
            built = {
                "search": results,
                "full": _full_view(results, base / "vault"),
            }
            for budget in budgets:
                context = build_context(results, budget_tokens=budget, detail="summary")
                built[f"compact-{budget}"] = context["items"]
            for view in views:
                candidates = built[view]
                score = score_result(scenario, {"results": candidates}, limit)
                per_view[view].append({
                    "id": scenario["id"],
                    "category": scenario["category"],
                    "status": "ok",
                    "score": score,
                    "tokens": _tokens(candidates),
                })
    return {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "brain_version": __version__,
        "environment": {"python": platform.python_version(), "platform": platform.platform()},
        "dataset": {"path": str(dataset_path.resolve()), "sha256": dataset_digest(dataset_path)},
        "settings": {"limit": limit, "snippet_chars": snippet_chars, "budgets": list(budgets), "pad_chars": pad_chars},
        "prompt": "retrieval-only: same FTS hits, progressive context views scored by the BR-001 harness rules",
        "views": {view: _aggregate(per_view[view]) for view in views},
        "scenarios": per_view,
    }


def render_markdown(report: dict[str, Any]) -> str:
    full_tokens = report["views"]["full"]["tokens"] or 1.0
    lines = [
        "# Respected Brain — Progressive Context Report (BR-012)",
        "",
        f"- Generated: `{report['generated_at']}`",
        f"- Brain version: `{report['brain_version']}`",
        f"- Dataset sha256: `{report['dataset']['sha256']}`",
        f"- Settings: limit `{report['settings']['limit']}`, snippet `{report['settings']['snippet_chars']}`, budgets `{report['settings']['budgets']}`, padded note chars `{report['settings'].get('pad_chars', 0)}`",
        "",
        "## Views",
        "",
        "| View | Pass | Hit@1 | Hit@5 | MRR | Answer | Stale | No-answer | Tokens | vs full | Failures |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]

    def pct(value: float | None) -> str:
        return "n/a" if value is None else f"{value * 100:.1f}%"

    for view, agg in report["views"].items():
        ratio = f"{agg['tokens'] / full_tokens:.2f}x"
        failures = ", ".join(agg["failures"]) or "-"
        lines.append(
            f"| `{view}` | {pct(agg['pass_rate'])} | {pct(agg['hit1'])} | {pct(agg['hit5'])} | "
            f"{'n/a' if agg['mrr'] is None else f'{agg["mrr"]:.3f}'} | {pct(agg['answer'])} | "
            f"{agg['stale_above_current']} | {pct(agg['no_answer'])} | {agg['tokens']} | {ratio} | {failures} |"
        )
    lines += [
        "",
        "## Notes",
        "",
        "- `search` is the current top-k snippet result; `full` reads every top-k note body (naive baseline).",
        "- `compact-*` is the same ranked hits passed through `memory.context.build_context` at that token budget.",
        "- Answer-bearing note text is unchanged; irrelevant prose pads each note to at least `pad_chars` so full-note reads represent long real notes.",
        "- Accuracy uses the BR-001 scenario rules; tokens are snippet characters / 4 (same metric as the harness).",
    ]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="BR-012 progressive context evaluation")
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--snippet-chars", type=int, default=400)
    parser.add_argument("--budgets", default="600,120,60")
    parser.add_argument("--pad-chars", type=int, default=3000)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--md-out", type=Path)
    args = parser.parse_args(argv)
    budgets = tuple(int(item) for item in args.budgets.split(",") if item.strip())
    report = evaluate(args.dataset, limit=args.limit, snippet_chars=args.snippet_chars, budgets=budgets, pad_chars=args.pad_chars)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.md_out:
        args.md_out.parent.mkdir(parents=True, exist_ok=True)
        args.md_out.write_text(render_markdown(report), encoding="utf-8")
    print(render_markdown(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
