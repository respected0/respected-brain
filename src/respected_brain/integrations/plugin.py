"""Claude and Codex receive lifecycle hooks and skills as one local plugin instead of loose hook entries."""
from __future__ import annotations
import hashlib
import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from respected_brain import __version__

PLUGIN = "respected-brain"
DISPLAY = "Respected Brain"
DESCRIPTION = "Kalıcı hafıza vault'u için oturum kancaları ve skill'ler."


def bundle_root(ctx):
    return ctx.paths.data_root / "vaults" / ctx.paths.vault_id / "plugin"


def _json(document):
    return json.dumps(document, ensure_ascii=False, indent=2) + "\n"


def bundle_writes(ctx, claude_hooks, codex_hooks, skills):
    """Marketplace + plugin files; `skills` are (path under plugin/skills, text) pairs. Version tracks content so clients refresh their copy."""
    plugin = bundle_root(ctx) / "plugin"
    files = {plugin / "hooks/claude.json": _json(claude_hooks), plugin / "hooks/codex.json": _json(codex_hooks), **dict(skills)}
    digest = hashlib.sha256(json.dumps({str(k.relative_to(plugin)): v for k, v in sorted(files.items())}, sort_keys=True).encode()).hexdigest()[:8]
    version = f"{__version__}+{digest}"
    files[plugin / ".claude-plugin/plugin.json"] = _json({"name": PLUGIN, "version": version, "description": DESCRIPTION, "author": {"name": "Respected"}, "hooks": "./hooks/claude.json"})
    files[plugin / ".codex-plugin/plugin.json"] = _json({
        "name": PLUGIN, "version": version, "description": DESCRIPTION, "skills": "./skills/", "hooks": "./hooks/codex.json",
        "interface": {"displayName": DISPLAY, "shortDescription": DESCRIPTION, "developerName": "Respected", "category": "Productivity", "capabilities": ["Instructions", "Lifecycle hooks"]},
    })
    files[bundle_root(ctx) / ".claude-plugin/marketplace.json"] = _json({
        "name": PLUGIN, "description": DESCRIPTION, "owner": {"name": "Respected"}, "plugins": [{"name": PLUGIN, "description": DESCRIPTION, "source": "./plugin", "category": "productivity"}],
    })
    files[bundle_root(ctx) / ".agents/plugins/marketplace.json"] = _json({
        "name": PLUGIN, "interface": {"displayName": DISPLAY},
        "plugins": [{"name": PLUGIN, "source": {"source": "local", "path": "./plugin"}, "policy": {"installation": "INSTALLED_BY_DEFAULT", "authentication": "ON_INSTALL"}, "category": "Productivity"}],
    })
    return sorted(files.items())


def register_claude(settings, root):
    """Point Claude Code at the local marketplace and enable the plugin."""
    for key, value in (("extraKnownMarketplaces", {PLUGIN: {"source": {"source": "directory", "path": root}}}), ("enabledPlugins", {f"{PLUGIN}@{PLUGIN}": True})):
        table = settings.setdefault(key, {})
        if not isinstance(table, dict):
            raise ValueError(f"{key} alanı bir JSON nesnesi değil")
        table.update(value)
    return settings


def _toml_table(content, header, lines):
    block = f"[{header}]\n" + "".join(line + "\n" for line in lines)
    match = re.search(r"(?ms)^\[" + re.escape(header) + r"\][ \t]*\n.*?(?=^\[|\Z)", content)
    if match:
        return content[:match.start()] + block + ("\n" if content[match.end():] else "") + content[match.end():]
    return content.rstrip() + ("\n\n" if content.strip() else "") + block


def register_codex(content, root):
    """Add the local marketplace and enable the plugin in Codex config.toml, leaving other tables as they are."""
    content = _toml_table(content, f"marketplaces.{PLUGIN}", ['source_type = "local"', f"source = '{root}'"])
    return _toml_table(content, f'plugins."{PLUGIN}@{PLUGIN}"', ["enabled = true"])


SKIP_ENV = "RESPECTED_SKIP_CLIENT_PLUGINS"  # set by the test sandbox so no suite run reaches a real client CLI


def _run_cli(client, commands, home, which, run, *, stop_on_failure):
    executable = which(client)
    env = {**os.environ, "HOME": str(home), "USERPROFILE": str(home)}
    if client == "codex":  # Codex on Windows reads the Known Folder, not USERPROFILE: name its home explicitly
        env["CODEX_HOME"] = str(Path(home) / ".codex")
    failed = []
    for args in commands if executable else ():
        try:
            ok = not run([executable, *args], env=env, capture_output=True, stdin=subprocess.DEVNULL, timeout=120).returncode
        except (OSError, subprocess.SubprocessError):
            ok = False
        if not ok:
            failed.append(f"{client} {' '.join(args[:2])}")
            if stop_on_failure:
                break
    return failed


def install_plugins(ctx, profile, desired, *, which=shutil.which, run=subprocess.run):
    """Ask the Claude and Codex CLIs to add the local marketplace and install the plugin; a missing CLI is skipped.

    Config entries alone do not install the plugin. Returns the commands that failed (never raises: the integration
    files are already committed and a later repair retries)."""
    from .rendering import selected_clients
    if os.environ.get(SKIP_ENV) or not desired.get("global") or profile.platform == "windows-wsl":
        return ()
    reference = f"{PLUGIN}@{PLUGIN}"
    steps = {"claude": (["plugin", "marketplace", "add", str(bundle_root(ctx))], ["plugin", "install", reference]), "codex": (["plugin", "add", reference],)}
    chosen = selected_clients(desired)
    return tuple(f for client, commands in steps.items() if client in chosen for f in _run_cli(client, commands, profile.user_home, which, run, stop_on_failure=True))


def remove_plugins(home, *, which=shutil.which, run=subprocess.run):
    """Uninstall the plugin and forget the marketplace in both CLIs; every step is tried, failures are returned."""
    if os.environ.get(SKIP_ENV):
        return ()
    reference = f"{PLUGIN}@{PLUGIN}"
    steps = {"claude": (["plugin", "uninstall", reference], ["plugin", "marketplace", "remove", PLUGIN]), "codex": (["plugin", "remove", reference], ["plugin", "marketplace", "remove", PLUGIN])}
    return tuple(f for client, commands in steps.items() for f in _run_cli(client, commands, home, which, run, stop_on_failure=False))
