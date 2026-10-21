"""Application command dispatcher."""
from __future__ import annotations

import argparse
from collections.abc import Sequence
from datetime import datetime, date
import json
import os
from pathlib import Path
import subprocess
import sys

from . import __version__
from .bootstrap import application_roots, bootstrap
from .core.config import ConfigStore
from .core.errors import FoundationError, SelectionError
from .vault.registry import VaultRegistry


def _selector(parser):
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--vault", type=Path)
    group.add_argument("--vault-id")


def _parser():
    parser = argparse.ArgumentParser(prog="respectedbrain", description="Respected Brain")
    parser.add_argument("--version", action="version", version=__version__)
    commands = parser.add_subparsers(dest="command")
    vault = commands.add_parser("vault", help="Kasa kaydı ve açık keşif")
    actions = vault.add_subparsers(dest="action", required=True)
    register = actions.add_parser("register")
    register.add_argument("path", type=Path)
    register.add_argument("--new-identity", action="store_true")
    actions.add_parser("list")
    discover = actions.add_parser("discover")
    discover.add_argument("path", type=Path)
    configure = commands.add_parser("configure", help="Kullanıcı tercihlerini göster veya değiştir")
    configure.add_argument("--summary-provider", choices=("auto", "codex", "claude", "antigravity", "gemini", "cursor"))
    for name in ("briefing", "maps", "index-refresh"):
        _selector(commands.add_parser(name))
    compile_parser = commands.add_parser("compile")
    _selector(compile_parser)
    compile_parser.add_argument("--trigger-claim", type=Path)
    compile_parser.add_argument("--before-date", type=date.fromisoformat)
    compile_parser.add_argument("--max-calls", type=int)
    compile_parser.add_argument("--dry-run", action="store_true")
    flush = commands.add_parser("flush")
    _selector(flush)
    flush.add_argument("--hook-input", type=Path)
    flush.add_argument("--transcript", type=Path)
    flush.add_argument("--session-id")
    flush.add_argument("--reason", default="sessionend")
    flush.add_argument("--maybe-compile", action="store_true")
    _selector(commands.add_parser("open", help="Not kasası klasörünü dosya yöneticisinde aç"))
    search = commands.add_parser("search")
    _selector(search)
    search.add_argument("query", nargs="?", default="")
    search.add_argument("--reindex", action="store_true")
    search.add_argument("--category")
    search.add_argument("--limit", type=int, default=10)
    search.add_argument("--json", action="store_true")
    maintenance = commands.add_parser("maintenance")
    _selector(maintenance)
    maintenance.add_argument("name")
    maintenance.add_argument("argv", nargs=argparse.REMAINDER)
    setup_parser = commands.add_parser("setup")
    setup_parser.add_argument("--vault", type=Path)
    setup_parser.add_argument("--package", type=Path)
    setup_parser.add_argument("--gui", action="store_true")
    setup_parser.add_argument("--allow-unattested", action="store_true", help="Accept a local package without a release attestation (development builds)")
    setup_parser.add_argument("--user-name")
    setup_parser.add_argument("--user-bio")
    setup_parser.add_argument("--companion")
    setup_parser.add_argument("--os-name")
    setup_parser.add_argument("--summary-provider", choices=("auto", "codex", "claude", "antigravity", "gemini", "cursor"))
    setup_parser.add_argument("--platform", choices=("windows-native", "posix", "windows-wsl"))
    setup_parser.add_argument("--mcp-clients", dest="mcp_clients", help="Comma separated AI clients for --mcp only (default: the --clients selection)")
    setup_parser.add_argument("--clients", help="Comma separated AI clients for --global/--mcp (claude,codex,gemini,antigravity,cursor,windsurf,claude-desktop,vscode-agents); default: all")
    for flag in ("global", "mcp", "schedule", "shortcut"):
        setup_parser.add_argument("--" + flag, dest="desired_" + flag, action=argparse.BooleanOptionalAction, default=None)
    for name in ("update", "repair", "uninstall"):
        operation = commands.add_parser(name)
        _selector(operation)
        if name in ("update", "repair"):
            operation.add_argument("--package", type=Path, required=name == "update")
            operation.add_argument("--allow-unattested", action="store_true", help="Accept a local package without a release attestation (development builds)")
        if name == "uninstall":
            operation.add_argument("--keep-data", action="store_true")
            operation.add_argument("--purge-data", dest="keep_data", action="store_false", help=argparse.SUPPRESS)
            operation.set_defaults(keep_data=False)
    commands.add_parser("recover")
    rpp_parser = commands.add_parser("rpp", help=argparse.SUPPRESS)
    rpp_parser.add_argument("--data-root", type=Path)
    welcome = commands.add_parser("welcome", help="First-use personalization")
    _selector(welcome)
    welcome.add_argument("--app-root", type=Path, help=argparse.SUPPRESS)
    welcome.add_argument("--data-root", type=Path, help=argparse.SUPPRESS)
    hook = commands.add_parser("hook")
    _selector(hook)
    hook.add_argument("--provider", required=True, choices=("claude", "codex", "cursor", "antigravity", "gemini"))
    hook.add_argument("--event", required=True, choices=("start", "prompt", "precompact", "postcompact", "turn", "end", "notify"))
    hook.add_argument("--global-hook", action="store_true")
    hook.add_argument("--chain-file", type=Path)
    hook.add_argument("payload", nargs=argparse.REMAINDER)
    _selector(commands.add_parser("mcp"))
    resume = commands.add_parser("_resume-operation", help=argparse.SUPPRESS)
    resume.add_argument("--request", type=Path, required=True)
    resume.add_argument("--request-hash", required=True)
    return parser


def _dispatch(args) -> int:
    if args.command == "rpp":
        from .rpp.server import main as rpp_main
        return rpp_main(data_root=args.data_root)
    if args.command in ("compile", "flush"):
        from .memory.lifecycle import _is_reentrant
        if _is_reentrant():
            return 0
    if args.command == "_resume-operation":
        from .installation.deferred import resume_operation
        return resume_operation(args.request, expected_hash=args.request_hash)
    if args.command in ("setup", "recover", "welcome"):
        roots = application_roots()
        from .integrations.backend import NativeBackend
        backend = NativeBackend(roots.data_root)
        if args.command == "recover":
            from .installation.transaction import recover_transactions
            from dataclasses import asdict
            results = recover_transactions(roots.data_root, backend)
            print(json.dumps([asdict(result) for result in results], ensure_ascii=False, indent=2))
            return 1 if any(result.conflicts for result in results) else 0
        if args.command == "welcome":
            if getattr(args, "app_root", None) is not None or getattr(args, "data_root", None) is not None:
                from .core.paths import Roots
                roots = Roots(
                    (args.app_root or roots.app_root).resolve(),
                    (args.data_root or roots.data_root).resolve(),
                    (args.vault or roots.default_vault).resolve(),
                )
            config = ConfigStore(roots.data_root).read()
            identity = args.vault_id or config.get("active_vault_id")
            entry = config["vaults"].get(identity) if identity else None
            if args.vault is not None:
                selected = args.vault.resolve()
                entry = next((row for row in config["vaults"].values() if Path(row["path"]).resolve() == selected), None)
            elif args.vault_id is not None and entry is None:
                raise SelectionError("Kayıtlı kasa bulunamadı")
            settings = entry.get("settings", {}) if entry else {}
            if {"USER_NAME", "USER_BIO", "COMPANION", "OS_NAME"} <= settings.keys():
                return 0
            from .installation.wizard import main as wizard_main
            vault = Path(entry["path"]) if entry is not None else (args.vault.resolve() if args.vault is not None else roots.default_vault)
            return wizard_main(roots=roots, backend=backend, vault=vault, package=None, profile=settings, desired={})
        desired_overrides = {key: getattr(args, "desired_" + key) for key in ("global", "mcp", "schedule", "shortcut") if getattr(args, "desired_" + key) is not None}
        profile = {key: value for key, value in {"USER_NAME": args.user_name, "USER_BIO": args.user_bio, "COMPANION": args.companion, "OS_NAME": args.os_name, "summary_provider": args.summary_provider, "platform": args.platform}.items() if value is not None}
        vault = args.vault.resolve() if args.vault is not None else None
        package = args.package.resolve() if args.package is not None else None
        if args.gui:
            from .installation.wizard import main as wizard_main
            return wizard_main(roots=roots, backend=backend, vault=vault, package=package, profile=profile, desired=desired_overrides)
        from .installation.setup import setup
        desired = ConfigStore(roots.data_root).read()["integrations"]
        stored = {key: desired.get(key) for key in ("clients", "mcp_clients")}
        desired = {key: desired_overrides.get(key, desired.get(key, False)) for key in ("global", "mcp", "schedule", "shortcut")}
        from .integrations.rendering import CLIENTS
        for key, given in (("clients", args.clients), ("mcp_clients", args.mcp_clients)):
            chosen = [item for item in given.split(",") if item] if given is not None else stored[key]
            unknown = sorted(set(chosen or ()) - set(CLIENTS))
            if unknown:
                raise SelectionError(f"Unknown AI client(s): {', '.join(unknown)}")
            if chosen is not None:
                desired[key] = chosen
        return _operation_output(setup(roots, vault if vault is not None else roots.default_vault, profile=profile, desired=desired, backend=backend, package=package, require_provenance=False if args.allow_unattested else None))
    if args.command in ("vault", "configure"):
        roots = application_roots()
        store = ConfigStore(roots.data_root)
        if args.command == "configure":
            if args.summary_provider is not None:
                config = store.update(lambda value: value["preferences"].update(summary_provider=args.summary_provider))
            else:
                config = store.read()
            print(json.dumps(config, ensure_ascii=False, indent=2))
            return 0
        registry = VaultRegistry(store)
        if args.action == "register":
            print(registry.register(args.path, new_identity=args.new_identity))
        elif args.action == "list":
            print(json.dumps(registry.list(), ensure_ascii=False, indent=2))
        else:
            found = registry.discover(args.path)
            if found is None:
                raise SelectionError("Kayıtlı kasa bulunamadı; vault register ile kaydedin.")
            print(found)
        return 0
    ctx = bootstrap(vault=args.vault, vault_id=args.vault_id)
    if args.command == "hook":
        from .integrations.hooks.bridge import dispatch
        arguments = (["--global-hook"] if args.global_hook else []) + args.payload
        if args.chain_file is not None:
            arguments = ["--chain-file", str(args.chain_file), *arguments]
        sys.stdout.write(dispatch(ctx, provider=args.provider, event=args.event, argv=arguments, stdin=sys.stdin.read()))
        sys.stdout.flush()
        return 0
    if args.command == "mcp":
        from .integrations.mcp.server import serve
        return serve(ctx)
    if args.command in ("update", "repair", "uninstall"):
        from .integrations.backend import NativeBackend
        backend = NativeBackend(ctx.paths.data_root)
        if args.command in ("update", "uninstall"):
            from .installation.deferred import defer_operation
            queued = defer_operation(ctx, mode=args.command, package=args.package.resolve() if args.command == "update" else None, purge_data=args.command == "uninstall" and not args.keep_data,
                                     require_provenance=False if getattr(args, "allow_unattested", False) else None)
            if queued is not None:
                return _operation_output(queued)
        if args.command == "update":
            from .installation.update import update
            return _operation_output(update(ctx, package=args.package.resolve(), backend=backend, require_provenance=False if args.allow_unattested else None))
        if args.command == "repair":
            from .installation.repair import repair
            return _operation_output(repair(
                ctx,
                backend=backend,
                package=args.package.resolve() if args.package is not None else None,
                require_provenance=False if args.allow_unattested else None,
            ))
        from .installation.uninstall import uninstall
        return _operation_output(uninstall(ctx, backend=backend, purge_data=not args.keep_data))
    now = datetime.now().astimezone()
    if args.command in ("compile", "briefing", "flush"):
        from .providers.runner import ModelRunner
        model = ModelRunner(ctx)
        if args.command == "compile":
            from .memory.compile import compile_memory, compile_pending, DEFAULT_MAX_CALLS
            if args.trigger_claim or args.before_date or args.max_calls is not None or args.dry_run:
                return compile_pending(ctx, model=model, now=now, trigger_claim=args.trigger_claim,
                                       before_date=args.before_date, max_calls=args.max_calls if args.max_calls is not None else DEFAULT_MAX_CALLS,
                                       dry_run=args.dry_run)
            return compile_memory(ctx, model=model, now=now)
        if args.command == "flush":
            from .memory.flush import flush_transcript, load_hook_input, _managed_hook_input, compile_catch_up, catch_up_unflushed_sessions
            if args.maybe_compile:
                from .search.freshness import refresh_now
                refresh_now(ctx, attempts=2)  # session start: pick up notes edited outside any AI session
                catch_up_unflushed_sessions(ctx, model=model, now=now, home=Path.home())
                return compile_catch_up(ctx, model=model, now=now)
            original_input = args.hook_input.read_bytes() if args.hook_input is not None else None
            value = load_hook_input(args.hook_input) if args.hook_input is not None else {}
            session = args.session_id or value.get("session_id")
            transcript = args.transcript or (Path(value["transcript_path"]) if value.get("transcript_path") else None)
            if not session or transcript is None:
                raise SelectionError("flush requires a session and transcript")
            status = flush_transcript(ctx, session_id=session, transcript=transcript, model=model, now=now,
                                      reason=args.reason, hook_payload=value if args.hook_input is not None else None)
            if status == 0 and args.hook_input is not None and _managed_hook_input(args.hook_input, ctx.paths.state_dir):
                try:
                    unchanged = args.hook_input.read_bytes() == original_input
                except FileNotFoundError:
                    unchanged = False
                if unchanged:
                    args.hook_input.unlink(missing_ok=True)
            if status == 0:
                from .search.freshness import refresh_now
                refresh_now(ctx, attempts=2)  # notes just changed: keep the search index current
            return status
        from .briefing.service import run_if_due
        status = run_if_due(ctx, model=model, now=now)
        from .search.freshness import refresh_now
        refresh_now(ctx, attempts=2)
        return status
    if args.command == "index-refresh":
        from .search.freshness import refresh_now
        print(json.dumps(refresh_now(ctx), ensure_ascii=False))
        return 0
    if args.command == "maps":
        from .vault.maps import rebuild_maps
        rebuild_maps(ctx)
        return 0
    if args.command == "open":
        vault = ctx.paths.vault_root
        print(vault)
        if sys.platform == "win32":
            os.startfile(vault)  # noqa: S606 the user's own vault folder
        else:
            subprocess.Popen(["open" if sys.platform == "darwin" else "xdg-open", str(vault)], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return 0
    if args.command == "search":
        from .search.engine import SearchEngine
        engine = SearchEngine(ctx)
        stats = engine.index_vault(force=args.reindex)
        if args.query:
            results = engine.search(args.query, limit=args.limit, category=args.category)
            print(json.dumps(results, ensure_ascii=False, indent=2) if args.json else "\n".join(f"{r['title']} ({r['path']})\n{r['snippet']}" for r in results))
        else:
            print(json.dumps(stats, ensure_ascii=False))
        return 0
    from .maintenance import run_tool
    return run_tool(ctx, name=args.name, argv=args.argv)


def _operation_output(result) -> int:
    from dataclasses import asdict
    print(json.dumps(asdict(result), ensure_ascii=False, indent=2))
    return 0 if result.success or result.pending else 1


def main(argv: Sequence[str] | None = None) -> int:
    if sys.platform == "win32":
        for stream in (sys.stdin, sys.stdout, sys.stderr):  # RPP requests arrive as UTF-8 on stdin; the console code page must not change note names
            configure = getattr(stream, "reconfigure", None)
            if callable(configure):
                configure(encoding="utf-8", errors="replace")
    parser = _parser()
    try:
        args = parser.parse_args(argv)
        if args.command is None:
            parser.print_help()
            return 0
        return _dispatch(args)
    except SystemExit as error:
        return int(error.code)
    except (SelectionError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 2
    except (FoundationError, OSError) as error:
        print(str(error), file=sys.stderr)
        return 1
