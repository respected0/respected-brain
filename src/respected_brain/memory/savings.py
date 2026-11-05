"""Token savings: actual session usage plus the measured BR-012 baseline."""

from __future__ import annotations

from typing import Any

BENCHMARK = {
    "source": "docs/evidence/br012-progressive.json",
    "baseline_view": "full",
    "compact_view": "compact-600",
    "full_tokens": 1103.458,
    "compact_tokens": 47.452,
    "full_pass_rate": 0.98,
    "compact_pass_rate": 0.98,
    "low_budget_tokens": 29.186,
    "low_budget_pass_rate": 0.80,
}


def benchmark_report() -> dict[str, Any]:
    """BR-012 measured on its own fixture, not on the user's sessions."""
    full = BENCHMARK["full_tokens"]
    compact = BENCHMARK["compact_tokens"]
    return {
        **BENCHMARK,
        "reduction_percent": round((1 - compact / full) * 100, 1),
        "same_accuracy": BENCHMARK["full_pass_rate"] == BENCHMARK["compact_pass_rate"],
        "note": "BR-012 fixture olcumu; kullanici oturumlarinin tasarrufu degildir.",
    }


def savings_report(usage: dict[str, Any]) -> dict[str, Any]:
    return {"usage": usage, "benchmark": benchmark_report()}
