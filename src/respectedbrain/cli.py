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
from .settings import SettingsError
from .vault.registry import VaultRegistry


def _selector(parser):
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--vault", type=Path)
    group.add_argument("--vault-id")


def _parser():
    parser = argparse.ArgumentParser(prog="respectedbrain", description="Respected Brain")
    parser.add_argument("--version", action="version", version=f"respected-secondbrain {__version__}")
    commands = parser.add_subparsers(dest="command")
    vault = commands.add_parser("vault", help="Kasa kaydı ve açık keşif")
    actions = vault.add_subparsers(dest="action", required=True)
    register = actions.add_parser("register")
    register.add_argument("path", type=Path)
    register.add_argument("--new-identity", action="store_true")
    actions.add_parser("list")
    discover = actions.add_parser("discover")
    discover.add_argument("path", type=Path)
    config = commands.add_parser("config", help="Ayarları göster veya değiştir (config, config get <anahtar>, config set <anahtar>=<değer>...)")
    config.add_argument("action", nargs="?", choices=("get", "set"))
    config.add_argument("items", nargs="*")
    commands.add_parser("health", help="Sağlık kontrolü")
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
    setup_parser = commands.add_parser("setup", help="Kurucunun yazdığı programı kaydet, kasayı ve ayarları hazırla")
    setup_parser.add_argument("--vault", type=Path)
    setup_parser.add_argument("--platform", choices=("windows-native", "posix", "windows-wsl"))
    setup_parser.add_argument("--set", dest="assignments", action="append", default=[], metavar="ANAHTAR=DEĞER", help="Ayar (config set ile aynı anahtarlar); tekrarlanabilir")
    _selector(commands.add_parser("repair", help="Program dosyalarını doğrula, kayıtları ve bağlantıları onar"))
    uninstall = commands.add_parser("uninstall", help="Bağlantıları ve kayıtları kaldır; --purge ayarları ve verileri de siler (kasa asla)")
    _selector(uninstall)
    uninstall.add_argument("--purge", action="store_true")
    commands.add_parser("recover")
    commands.add_parser("rpp", help="Respected Product Protocol sunucusu (stdin/stdout)")
    hook = commands.add_parser("hook")
    _selector(hook)
    hook.add_argument("--provider", required=True, choices=("claude", "codex", "cursor", "antigravity", "gemini"))
    hook.add_argument("--event", required=True, choices=("start", "prompt", "precompact", "postcompact", "turn", "end", "notify"))
    hook.add_argument("--global-hook", action="store_true")
    hook.add_argument("--chain-file", type=Path)
    hook.add_argument("payload", nargs=argparse.REMAINDER)
    _selector(commands.add_parser("mcp"))
    return parser


def _dispatch(args) -> int:
    if args.command == "rpp":
        from .rpp.server import main as rpp_main
        return rpp_main()
    if args.command in ("config", "health"):
        return _config(args) if args.command == "config" else _health()
    if args.command in ("compile", "flush"):
        from .memory.lifecycle import _is_reentrant
        if _is_reentrant():
            return 0
    if args.command in ("setup", "recover"):
        roots = application_roots()
        from .integrations.backend import NativeBackend
        backend = NativeBackend(roots.data_root)
        if args.command == "recover":
            from .installation.transaction import recover_transactions
            from dataclasses import asdict
            results = recover_transactions(roots.data_root, backend)
            print(json.dumps([asdict(result) for result in results], ensure_ascii=False, indent=2))
            return 1 if any(result.conflicts for result in results) else 0
        from . import settings as product_settings
        from .installation.setup import setup
        values = dict(product_settings.parse(item) for item in args.assignments)
        vault = args.vault.resolve() if args.vault is not None else roots.default_vault
        return _operation_output(setup(roots, vault, values=values, backend=backend, platform=args.platform))
    if args.command == "vault":
        roots = application_roots()
        store = ConfigStore(roots.data_root)
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
    ctx = bootstrap(vault=args.vault, vault_id=args.vault_id, allow_missing_vault=args.command == "uninstall")
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
    if args.command in ("repair", "uninstall"):
        from .integrations.backend import NativeBackend
        backend = NativeBackend(ctx.paths.data_root)
        if args.command == "repair":
            from .installation.repair import repair
            return _operation_output(repair(ctx, backend=backend))
        from .installation.uninstall import uninstall
        return _operation_output(uninstall(ctx, backend=backend, purge_data=args.purge))
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


def _print(document) -> None:
    print(json.dumps(document, ensure_ascii=False, indent=2))


def _config(args) -> int:
    from . import settings as product_settings
    data_root = application_roots().data_root
    if args.action is None and not args.items:
        _print(product_settings.readback(data_root))
        return 0
    if args.action == "get" and len(args.items) == 1:
        values = product_settings.readback(data_root)
        if args.items[0] not in values:
            raise product_settings.SettingsError([{"key": args.items[0], "message": f"Bilinmeyen ayar: {args.items[0]}"}])
        _print({args.items[0]: values[args.items[0]]})
        return 0
    if args.action == "set" and args.items:
        values = dict(product_settings.parse(item) for item in args.items)
        product_settings.apply(data_root, values)
        current = product_settings.readback(data_root)
        _print({key: current[key] for key in values})
        return 0
    raise ValueError("Kullanım: config | config get <anahtar> | config set <anahtar>=<değer>...")


def _health() -> int:
    from .rpp.server import serve
    result = serve(json.dumps({"rpp": "1", "op": "health"}))["result"]
    _print(result)
    return 0 if result["status"] == "healthy" else 1


def _operation_output(result) -> int:
    from dataclasses import asdict
    print(json.dumps(asdict(result), ensure_ascii=False, indent=2))
    return 0 if result.success else 1


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
    except SettingsError as error:
        _print({"error": {"code": "INVALID_SETTINGS", "message": str(error), "hint": "Geçerli anahtarlar ve değerler için: respectedbrain config"}})
        return 2
    except (SelectionError, ValueError) as error:
        _print({"error": {"code": "USAGE", "message": str(error), "hint": "respectedbrain --help"}})
        return 2
    except (FoundationError, OSError) as error:
        _print({"error": {"code": "FAILED", "message": str(error), "hint": "İşlem geri alındı; ayrıntı için mesaja bakın."}})
        return 1
