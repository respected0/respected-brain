"""BR-004 read-only AI-client integration matrix.

A client is declared ``full`` only when a real session result is recorded in the
evidence file (default: ``tests/evals/results/br004-evidence.json``). Everything
else stays explicitly ``limited``; configuration presence is never promoted to a
real-session pass.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from respected_brain.integrations.backend import IntegrationProfile  # noqa: E402
from respected_brain.integrations.rendering import detect_clients  # noqa: E402

CLIENTS = ("claude", "codex", "antigravity", "cursor", "gemini")
EXECUTABLES = {
    "claude": ("claude",),
    "codex": ("codex",),
    "antigravity": ("agy", "antigravity"),
    "cursor": ("cursor-agent", "cursor"),
    "gemini": ("gemini",),
}
DEFAULT_EVIDENCE = ROOT / "tests/evals/results/br004-evidence.json"


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return ""


def _executable(home: Path, client: str) -> str:
    for name in EXECUTABLES[client]:
        found = shutil.which(name)
        if found:
            return found
    known = {
        "claude": (home / ".local/bin/claude.exe", home / ".local/bin/claude"),
        "codex": (home / "AppData/Local/Programs/OpenAI/Codex/bin/codex.exe",),
        "gemini": (home / ".local/bin/gemini.exe", home / ".local/bin/gemini"),
        "antigravity": (home / ".local/bin/agy.exe",),
        "cursor": (home / ".local/bin/cursor-agent.exe",),
    }
    return next((str(path) for path in known.get(client, ()) if path.is_file()), "")


def _hook_marker(text: str, client: str) -> bool:
    folded = text.casefold()
    return "respected" in folded and f"--provider {client}" in folded


def _plugin_enabled(text: str) -> bool:
    folded = text.casefold()
    return "respected-brain@respected-brain" in folded and "enabled = true" in folded


def _connection(home: Path, client: str) -> tuple[bool, bool | None]:
    """(connected, approved): approved is False only for an explicit disable; None when unknown."""
    text = ""
    if client == "claude":
        text = _read(home / ".claude/settings.json")
        enabled = '"enabledplugins"' in text.casefold() and "respected-brain@respected-brain" in text.casefold()
        connected = enabled or _hook_marker(text, client)
        disabled = '"disableallhooks": true' in text.replace(" ", "").casefold()
        return connected, False if disabled else (True if enabled else None)
    if client == "codex":
        text = _read(home / ".codex/config.toml")
        hooks = _read(home / ".codex/hooks.json")
        connected = _plugin_enabled(text) or ("notify" in text.casefold() and "respected" in text.casefold()) or _hook_marker(hooks, client)
        return connected, True if connected else None
    if client == "antigravity":
        text = _read(home / ".gemini/config/hooks.json")
        return _hook_marker(text, client), None
    if client == "gemini":
        text = _read(home / ".gemini/settings.json")
        return _hook_marker(text, client), None
    if client == "cursor":
        text = _read(home / ".cursor/hooks.json")
        return _hook_marker(text, client), None
    return False, None


def _evidence(path: Path) -> dict:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return {"clients": {}, "cross_agent": {}}
    return document if isinstance(document, dict) else {"clients": {}, "cross_agent": {}}


def probe(home: Path, evidence_path: Path | None = None) -> dict:
    home = Path(home).resolve()
    evidence = _evidence(evidence_path or DEFAULT_EVIDENCE)
    detected = detect_clients(IntegrationProfile("windows-native" if os.name == "nt" else "posix", (), home))
    rows = []
    for client in CLIENTS:
        connected, approved = _connection(home, client)
        executable = _executable(home, client)
        passed = bool((evidence.get("clients") or {}).get(client, {}).get("real_test_passed"))
        support = "full" if passed and bool(executable) and connected and approved is not False else "limited"
        rows.append({
            "id": client,
            "detected": bool(detected.get(client)),
            "installed": bool(executable),
            "executable": executable,
            "connected": connected,
            "approved": approved,
            "real_test_passed": passed,
            "support": support,
        })
    return {"home": str(home), "writes_nothing": True, "clients": rows,
            "cross_agent": evidence.get("cross_agent") or {}}


def markdown(matrix: dict) -> str:
    mark = {True: "evet", False: "hayır", None: "bilinmiyor"}
    lines = ["| İstemci | Kurulu | Bağlı | Onaylı | Gerçek test | Destek |", "|---|---|---|---|---|---|"]
    for row in matrix["clients"]:
        lines.append(
            f"| {row['id']} | {mark[row['installed']]} | {mark[row['connected']]} | "
            f"{mark[row['approved']]} | {mark[row['real_test_passed']]} | {row['support']} |"
        )
    if matrix.get("cross_agent"):
        lines += ["", "| Çapraz senaryo | Sonuç |", "|---|---|"]
        lines += [f"| {name} | {'geçti' if value.get('passed') else 'geçmedi / doğrulanmadı'} |"
                  for name, value in matrix["cross_agent"].items()]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--home", type=Path, default=Path.home())
    parser.add_argument("--evidence", type=Path, default=DEFAULT_EVIDENCE)
    parser.add_argument("--output", type=Path, help="write JSON here (default: stdout)")
    parser.add_argument("--markdown", type=Path, help="write the human report here")
    args = parser.parse_args(argv)
    matrix = probe(args.home, args.evidence)
    text = json.dumps(matrix, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    if args.markdown:
        args.markdown.parent.mkdir(parents=True, exist_ok=True)
        args.markdown.write_text(markdown(matrix), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())