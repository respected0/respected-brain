#!/usr/bin/env python3
"""Real OpenCode smoke: install into a temp HOME, open a session, prove plugin load, MCP handshake and transcript."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_MODEL = "opencode/beam-free"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(command, *, env, cwd, stdin=None, timeout=300):
    started = time.perf_counter()
    result = subprocess.run(command, cwd=cwd, env=env, input=stdin, capture_output=True, text=True,
                            encoding="utf-8", errors="replace", timeout=timeout,
                            creationflags=0x08000000 if os.name == "nt" else 0)
    return result, time.perf_counter() - started


def clean_env(home: Path, app: Path, data: Path):
    names = ("PATH", "SystemRoot", "WINDIR", "COMSPEC", "PATHEXT", "TEMP", "TMP", "TMPDIR", "LOCALAPPDATA",
             "APPDATA", "USER", "LOGNAME", "SHELL", "LANG", "LC_ALL")
    env = {name: os.environ[name] for name in names if name in os.environ}
    env.update({"HOME": str(home), "USERPROFILE": str(home), "XDG_CONFIG_HOME": str(home / ".config"),
                "XDG_DATA_HOME": str(home / ".local/share"), "RESPECTED_APP_DIR": str(app),
                "RESPECTED_DATA_DIR": str(data), "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"})
    return env


def plan_and_apply(app: Path, data: Path, vault: Path, home: Path):
    sys.path.insert(0, str(ROOT / "src"))
    from respected_brain.core.config import ConfigStore
    from respected_brain.core.paths import Roots
    from respected_brain.integrations.backend import IntegrationProfile, NativeBackend
    from respected_brain.integrations.rendering import plan_integrations
    from respected_brain.installation.transaction import Transaction
    from respected_brain.vault.registry import build_context

    roots = Roots(app, data, vault)
    ctx = build_context(roots, ConfigStore(roots.data_root), vault=None, vault_id=None, env={})
    backend = NativeBackend(roots.data_root, user_home=home)
    profile = IntegrationProfile("windows-native", (str(roots.app_root / "respected-brain.exe"),), home)
    changes = plan_integrations(ctx, profile, {"global": True, "mcp": True, "clients": ["opencode"]}, backend)
    with Transaction(roots.data_root, backend) as tx:
        for row in changes:
            tx.apply_external(row)
        tx.commit()
    return ctx.paths.vault_id, [(row.kind, str(row.key)) for row in changes]


def transcript_rows(data: Path, vault_id: str):
    directory = data / "vaults" / vault_id / "integrations/opencode/transcripts"
    roles, files = [], []
    for path in sorted(directory.glob("*.jsonl")) if directory.is_dir() else []:
        files.append(str(path))
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                roles.append(json.loads(line)["message"]["role"])
            except (ValueError, KeyError, TypeError):
                roles.append("invalid")
    return roles, files


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, default=ROOT / "dist/RespectedBrain")
    parser.add_argument("--output", type=Path, default=ROOT / "tests/evals/results/br016-opencode-smoke.json")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--prompt", default="Reply with exactly OK")
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--keep", action="store_true")
    args = parser.parse_args(argv)

    report = {"task": "BR-016", "opencode": None, "model": args.model, "checks": [], "artifacts": {}, "overall": "SKIPPED"}
    exe = shutil.which("opencode")
    node = shutil.which("node")
    if not exe or not node:
        report["reason"] = "opencode or node is not installed"
    elif not (args.package / "respected-brain.exe").is_file():
        report["reason"] = f"package not built: {args.package}"
    else:
        workspace = Path(tempfile.mkdtemp(prefix="br016-opencode-"))
        try:
            app, data, vault, home = [workspace / name for name in ("app", "data", "vault", "home")]
            shutil.copytree(args.package, app)
            for path in (data, vault, home, workspace / "cwd"):
                path.mkdir()
            env = clean_env(home, app, data)
            report["opencode"] = run([exe, "--version"], env=env, cwd=workspace / "cwd", timeout=60)[0].stdout.strip()

            setup, setup_seconds = run([sys.executable, str(ROOT / "tests/native/smoke/lifecycle_driver.py"), "setup",
                                        "--app-root", str(app), "--data-root", str(data), "--vault", str(vault),
                                        "--home", str(home)], env={**env, "PYTHONPATH": str(ROOT / "src")},
                                       cwd=workspace / "cwd")
            report["checks"].append({"name": "install", "passed": setup.returncode == 0 and '"success": true' in setup.stdout,
                                     "seconds": round(setup_seconds, 2), "detail": setup.stdout[-500:] if setup.returncode else "setup ok"})

            vault_id, planned = plan_and_apply(app.resolve(), data.resolve(), vault.resolve(), home.resolve())
            report["planned"] = [kind for kind, _ in planned]
            config = home / ".config/opencode/opencode.json"
            document = json.loads(config.read_text(encoding="utf-8"))
            plugin = home / ".config/opencode/plugins/respected-brain.js"
            report["checks"].append({"name": "configuration", "passed":
                                     document.get("mcp", {}).get("respected-brain", {}).get("type") == "local"
                                     and plugin.is_file() and "__COMMAND__" not in plugin.read_text(encoding="utf-8")})

            bridge, _ = run([str(app / "respected-brain.exe"), "hook", "--vault-id", vault_id, "--provider",
                             "opencode", "--global-hook", "--event", "start"],
                            env=env, cwd=workspace / "cwd",
                            stdin=json.dumps({"session_id": "ses-smoke", "cwd": str(workspace / "cwd")}), timeout=120)
            try:
                bridge_payload = json.loads(bridge.stdout)
            except ValueError:
                bridge_payload = None
            report["checks"].append({"name": "bridge", "passed": bridge.returncode == 0 and isinstance(bridge_payload, dict),
                                     "detail": {"keys": sorted(bridge_payload), "has_context": bool(bridge_payload.get("additionalContext"))}
                                     if isinstance(bridge_payload, dict) else bridge.stdout[-300:]})

            session, session_seconds = run([exe, "--standalone", "--print-logs", "--log-level", "debug", "run", "--auto",
                                            "--model", args.model, args.prompt],
                                           env=env, cwd=workspace / "cwd", timeout=args.timeout)
            log = session.stdout + session.stderr
            log_path = workspace / "opencode-debug.log"
            log_path.write_text(log, encoding="utf-8")
            report["artifacts"]["log_sha256"] = sha256(log_path)
            plugin_line = next((line for line in log.splitlines() if "loading plugin" in line and "respected-brain.js" in line), "")
            mcp_line = next((line for line in log.splitlines() if "mcp connected" in line and "server=respected-brain" in line), "")
            bad = [line for line in log.splitlines() if ("schema" in line.lower() or "failed to load plugin" in line.lower())
                   and "respected-brain" in line]
            report["checks"].extend([
                {"name": "session", "passed": session.returncode == 0, "seconds": round(session_seconds, 2),
                 "detail": log[-800:] if session.returncode else "exit 0"},
                {"name": "plugin_loaded", "passed": bool(plugin_line), "detail": plugin_line[:300]},
                {"name": "mcp_handshake", "passed": bool(mcp_line), "detail": mcp_line[:300]},
                {"name": "plugin_schema", "passed": not bad, "detail": bad[:3]},
            ])
            roles, files = transcript_rows(data, vault_id)
            report["artifacts"]["transcripts"] = [Path(name).name for name in files]
            report["artifacts"]["transcript_roles"] = roles
            report["checks"].append({"name": "transcript", "passed": "user" in roles and "assistant" in roles,
                                     "detail": sorted(set(roles))})
            report["artifacts"]["opencode_config_sha256"] = sha256(config)
            report["artifacts"]["plugin_sha256"] = sha256(plugin)
        finally:
            if args.keep:
                report["workspace"] = str(workspace)
            else:
                shutil.rmtree(workspace, ignore_errors=True)

    if report["overall"] == "SKIPPED" and "reason" not in report:
        report["overall"] = "VERIFIED" if all(check["passed"] for check in report["checks"]) else "FAILED"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"overall": report["overall"], "checks": [{c["name"]: c["passed"]} for c in report["checks"]],
                      "output": str(args.output)}, ensure_ascii=False))
    return 0 if report["overall"] in ("VERIFIED", "SKIPPED") else 1


if __name__ == "__main__":
    raise SystemExit(main())
