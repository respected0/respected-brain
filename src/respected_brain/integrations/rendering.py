"""Readonly plans for explicit vault/provider contexts and stable installed launchers."""
from __future__ import annotations
import json
from pathlib import Path
import re
import subprocess
import sys
from .global_config import *
from .plugin import bundle_root, bundle_writes, register_claude, register_codex
from .mcp.tools import WRITE_TOOLS, tool_definitions
from .planning import _Planner, _assert_owned_replacement, _recorded_owner, _runtime_path, bare_command_text, bridge_argv, codex_command_text, command_text, launch_argv, validate_profile
from respected_brain.core.errors import FoundationError, OwnershipConflict
from respected_brain.core.platform import path_within_vault

def managed_rule(ctx):
    override = ctx.paths.overrides_dir / "instructions.md"
    nested = ctx.paths.overrides_dir / "instructions/default.md"
    if any(not path_within_vault(path, ctx.paths.data_root) for path in (override, nested)):
        raise OwnershipConflict('Unsafe instruction override')
    if override.is_file():
        instructions = override.read_text(encoding="utf-8").strip()
    elif nested.is_file():
        instructions = nested.read_text(encoding="utf-8").strip()
    else:
        instructions = ctx.resources.read_text("instructions/default.md").strip()
    vault = ctx.paths.vault_root
    replacements = identity_settings(ctx)
    for key, value in replacements.items():
        instructions = instructions.replace("{{" + key + "}}", str(value))
    win = windows_path(vault)
    locations = f"`{vault}`" + (f" (Windows: `{win}`)" if win else "")
    return f"{BEGIN}\n# Global ikinci beyin bağlantısı\n\nKalıcı hafıza vault'u **{vault.name}**: {locations}.\nGöreceli hafıza yollarını aktif kod reposuna göre değil bu vault köküne göre çöz. Kullanıcı istemedikçe proje kodunu vault'a taşıma.\n\n{instructions}\n{END}"

def skill_writes(ctx, roots):
    contents = {name: ctx.resources.read_text("skills/" + name) for name in ctx.resources.iter_files("skills") if name.endswith("/SKILL.md")}
    override = ctx.paths.overrides_dir / "skills"
    if not path_within_vault(override, ctx.paths.data_root):
        raise OwnershipConflict('Unsafe skill override directory')
    if override.is_dir():
        for path in override.glob("*/SKILL.md"):
            if not path_within_vault(path, ctx.paths.data_root):
                raise OwnershipConflict("Skill override has a link/reparse point")
            contents[path.relative_to(override).as_posix()] = path.read_text(encoding="utf-8")
    return [(base / name, content) for name, content in sorted(contents.items()) for base in roots]

def _global_writes(ctx, profile, planner, providers=SUPPORTED, codex_mcp=None) -> tuple[list[tuple[Path, str | None]], list[Path]]:
    writes: list[tuple[Path, str | None]] = []
    touched: list[Path] = []
    vault, home, platform = ctx.paths.vault_root, profile.user_home, profile.platform
    rule = managed_rule(ctx)
    def bridge_command(vault, provider, event, platform):
        render = {"antigravity": bare_command_text, "codex": codex_command_text}.get(provider, command_text)  # their shells (Antigravity re-escapes quotes, Codex runs PowerShell) reject a quoted program path
        return render(profile, bridge_argv(ctx, profile, provider, event, global_hook=True))
    def load_object(path):
        document = planner.object(path)
        current = planner.read(path)
        if current is None:
            return document
        owned = _recorded_owner(ctx, planner, path, current)
        expected = {bridge_command(vault, provider, event, platform) for provider in SUPPORTED for event in ("start", "prompt", "turn", "end", "precompact", "postcompact", "notify")}
        def check(value, namespace=False):
            if isinstance(value, dict):
                for key, item in value.items():
                    if key == "command" and isinstance(item, str) and (namespace or "--global-hook" in item):
                        if item not in expected and not owned:
                            raise OwnershipConflict(f"Unknown managed hook command: {path}")
                    else:
                        check(item, namespace or key == HOOK_NAME)
            elif isinstance(value, list):
                for item in value:
                    check(item, namespace)
        check(document)
        return document
    def codex_notify_argv(vault, platform):
        return bridge_argv(ctx, profile, "codex", "notify")
    def _managed_codex_notify(argv):
        if not argv:
            return False
        expected = codex_notify_argv(vault, platform)
        return argv[:len(expected)] == expected
    def _wrapped_codex_notify(argv):
        """Another tool (the Codex app's computer-use) took `notify` over and calls ours as its `--previous-notify`: capture still works, replacing it would loop."""
        expected = codex_notify_argv(vault, platform)
        for item in argv or ():
            try:
                inner = json.loads(item)
            except ValueError:
                continue
            if isinstance(inner, list) and inner[:len(expected)] == expected:
                return True
        return False
    def copy_skills(vault, roots):
        writes = skill_writes(ctx, roots)
        for target, _content in writes:
            relative = next(target.relative_to(base).as_posix() for base in roots if target.is_relative_to(base))
            try:
                baseline = ctx.resources.read_text("skills/" + relative).encode("utf-8")
            except FileNotFoundError:
                baseline = None
            _assert_owned_replacement(ctx, planner, target, baseline)
        return writes

    claude_commands = {
        "SessionStart": (bridge_command(vault, "claude", "start", platform), 15),
        "UserPromptSubmit": (bridge_command(vault, "claude", "prompt", platform), 5),
        "SessionEnd": (bridge_command(vault, "claude", "end", platform), 3),
        "PreCompact": (bridge_command(vault, "claude", "precompact", platform), 10),
        "Stop": (bridge_command(vault, "claude", "turn", platform), 10),
    }
    codex_commands = {
        "SessionStart": (bridge_command(vault, "codex", "start", platform), 15),
        "UserPromptSubmit": (bridge_command(vault, "codex", "prompt", platform), 5),
        "SessionEnd": (bridge_command(vault, "codex", "end", platform), 3),
        "Stop": (bridge_command(vault, "codex", "turn", platform), 10),
        "PreCompact": (bridge_command(vault, "codex", "precompact", platform), 10),
    }
    root = bundle_root(ctx)
    if {"claude", "codex"} & set(providers):
        writes += bundle_writes(ctx, merge_grouped_hooks({}, "claude", claude_commands, async_events=frozenset({"Stop"})), merge_grouped_hooks({}, "codex", codex_commands), skill_writes(ctx, [root / "plugin/skills"]), codex_mcp)
        if not codex_mcp and planner.read(root / "plugin/.mcp.json") is not None:  # MCP for Codex was switched off: take our file back out of the plugin
            writes += [(root / "plugin/.mcp.json", None)]
    def retire_skills(roots):
        """Loose skill copies from before the plugin: remove only the ones still byte-identical to the package."""
        retired = []
        for target, content in skill_writes(ctx, roots):
            current = planner.read(target)
            if current is not None and (current == content.encode("utf-8") or _recorded_owner(ctx, planner, target, current)):
                retired.append((target, None))
        return retired

    if "antigravity" in providers:
        config = home / ".gemini/config"
        hooks_path = config / "hooks.json"
        hooks = load_object(hooks_path)
        hooks[HOOK_NAME] = {
            "PreInvocation": [{"type": "command", "command": bridge_command(vault, "antigravity", "start", platform), "timeout": 15}],
            "Stop": [{"type": "command", "command": bridge_command(vault, "antigravity", "turn", platform), "timeout": 10}],
        }
        rule_path = home / ".gemini/GEMINI.md"
        writes += [(hooks_path, json.dumps(hooks, ensure_ascii=False, indent=2) + "\n"), (rule_path, merge_managed(planner.text(rule_path), rule))]
        writes += copy_skills(vault, [config / "skills"])
        touched += [hooks_path, rule_path]

    if "gemini" in providers:
        config = home / ".gemini"
        settings_path = config / "settings.json"
        settings = load_object(settings_path)
        commands = {
            "SessionStart": (bridge_command(vault, "gemini", "start", platform), 15000),
            "BeforeAgent": (bridge_command(vault, "gemini", "prompt", platform), 5000),
            "AfterAgent": (bridge_command(vault, "gemini", "turn", platform), 10000),
            "SessionEnd": (bridge_command(vault, "gemini", "end", platform), 10000),
            "PreCompress": (bridge_command(vault, "gemini", "precompact", platform), 10000),
        }
        merge_gemini_hooks(settings, commands)
        rule_path = config / "GEMINI.md"
        writes += [
            (settings_path, json.dumps(settings, ensure_ascii=False, indent=2) + "\n"),
            (
                rule_path,
                merge_managed(
                    planner.text(rule_path),
                    rule,
                ),
            ),
        ]
        writes += copy_skills(vault, [config / "skills"])
        touched += [settings_path, rule_path]

    if "codex" in providers:
        config = home / ".codex"
        hooks_path = config / "hooks.json"
        rule_path = config / "AGENTS.md"
        writes += [(rule_path, merge_managed(planner.text(rule_path), rule))]
        if planner.read(hooks_path) is not None:
            writes += [(hooks_path, json.dumps(strip_grouped_hooks(load_object(hooks_path), "codex"), ensure_ascii=False, indent=2) + "\n")]
            touched += [hooks_path]
        writes += retire_skills([home / ".agents/skills"])
        touched += [rule_path]

        config_toml_path = config / "config.toml"
        notify_cmd = codex_notify_argv(vault, platform)
        existing_toml = planner.text(config_toml_path)
        existing_notify = parse_codex_notify_argv(existing_toml)
        if re.search(r"(?m)^notify\s*=", existing_toml) and existing_notify is None:
            raise ValueError(
                "Codex notify ayarı güvenle ayrıştırılamadı; config.toml içindeki notify "
                "dizisini tek satıra getirip yeniden deneyin"
            )
        chain_path = ctx.paths.state_dir / "codex-notify-chain.json"
        wrapped = bool(existing_notify) and not _managed_codex_notify(existing_notify) and _wrapped_codex_notify(existing_notify)
        if wrapped:
            pass
        elif existing_notify and not _managed_codex_notify(existing_notify):
            notify_cmd += ["--chain-file", _runtime_path(chain_path, platform)]
            writes += [(chain_path, json.dumps({"argv": existing_notify}, ensure_ascii=False, indent=2) + "\n")]
            touched += [chain_path]
        elif planner.read(chain_path) is not None:
            chain = load_object(chain_path)
            chain_argv = chain.get("argv")
            if not isinstance(chain_argv, list) or not chain_argv or not all(isinstance(item, str) for item in chain_argv):
                raise ValueError(f"geçersiz Codex notify zinciri: {chain_path}")
            notify_cmd += ["--chain-file", _runtime_path(chain_path, platform)]
        updated_toml = register_codex(existing_toml if wrapped else update_codex_config_toml(existing_toml, notify_cmd), str(root))
        writes += [(config_toml_path, updated_toml)]
        touched += [config_toml_path]

    if "cursor" in providers:
        config = home / ".cursor"
        hooks_path = config / "hooks.json"
        hooks = load_object(hooks_path)
        hooks.setdefault("version", 1)
        additions = {
            "sessionStart": [{"command": bridge_command(vault, "cursor", "start", platform), "timeout": 15}],
            "beforeSubmitPrompt": [{"command": bridge_command(vault, "cursor", "prompt", platform), "timeout": 5}],
            "sessionEnd": [{"command": bridge_command(vault, "cursor", "end", platform), "timeout": 10}],
            "preCompact": [{"command": bridge_command(vault, "cursor", "precompact", platform), "timeout": 10}],
            "afterAgentResponse": [{"command": bridge_command(vault, "cursor", "turn", platform), "timeout": 10}],
        }
        merge_simple_hooks(hooks, "cursor", additions)
        rule_path = config / "rules" / CURSOR_RULE
        cursor_rule = merge_managed(planner.text(rule_path), rule) if planner.read(rule_path) is not None else "---\ndescription: Respected Brain global memory\nalwaysApply: true\n---\n\n" + rule + "\n"
        writes += [(hooks_path, json.dumps(hooks, ensure_ascii=False, indent=2) + "\n"), (rule_path, cursor_rule)]
        writes += copy_skills(vault, [config / "skills"])
        touched += [hooks_path, rule_path]

    if "claude" in providers:
        config = home / ".claude"
        settings_path = config / "settings.json"
        settings = load_object(settings_path)
        register_claude(strip_grouped_hooks(settings, "claude"), str(root))
        rule_path = config / "CLAUDE.md"
        writes += [(settings_path, json.dumps(settings, ensure_ascii=False, indent=2) + "\n"), (rule_path, merge_managed(planner.text(rule_path), rule))]
        writes += retire_skills([config / "skills"])
        touched += [settings_path, rule_path]

    return writes, touched



def mcp_destinations(profile):
    home = profile.user_home
    if profile.platform.startswith("windows"):
        appdata = home / "AppData/Roaming"
    elif sys.platform == "darwin":
        appdata = home / "Library/Application Support"
    else:
        appdata = home / ".config"
    paths = [home / ".claude.json", home / ".cursor/mcp.json", home / ".codeium/windsurf/mcp_config.json", appdata / "Claude/claude_desktop_config.json"]
    if (home / ".gemini").is_dir():
        paths.append(home / ".gemini/config/mcp_config.json")
    storage = appdata / "Code/User/globalStorage"
    for extension, filename in [("saoudrizwan.claude-dev", "cline_mcp_settings.json"), ("rooveterinaryinc.roo-cline", "roo_mcp_settings.json")]:
        if (storage / extension).is_dir():
            paths.append(storage / extension / "settings" / filename)
    return tuple(paths)

# AI client id -> hook/rule provider (None: MCP registration only). `desired["clients"]` (a list of ids) limits `global`
# and `mcp` to those clients; without it every client is included (the pre-selection behaviour).
CLIENTS = {"claude": "claude", "codex": "codex", "gemini": "gemini", "antigravity": "antigravity", "cursor": "cursor",
           "windsurf": None, "claude-desktop": None, "vscode-agents": None}


def selected_clients(desired, key="clients"):
    """Clients chosen for hooks/rules ("clients") or MCP ("mcp_clients", defaulting to the hook selection)."""
    chosen = desired.get(key, desired.get("clients")) if key == "mcp_clients" else desired.get(key)
    return set(CLIENTS) if chosen is None else {client for client in chosen if client in CLIENTS}


def mcp_client_of(path):
    text = Path(path).as_posix().casefold()
    if text.endswith("/.claude.json"):
        return "claude"
    if "/.cursor/" in text:
        return "cursor"
    if "windsurf" in text:
        return "windsurf"
    if text.endswith("claude_desktop_config.json"):
        return "claude-desktop"
    if "/.gemini/" in text:
        return "antigravity"
    return "vscode-agents"


def detect_clients(profile):
    """Which AI clients have a configuration folder/file on this computer (read-only)."""
    home = profile.user_home
    storage_hit = any(mcp_client_of(path) == "vscode-agents" for path in mcp_destinations(profile))  # listed only when the extension's folder exists
    appdata = home / ("AppData/Roaming" if profile.platform.startswith("windows") else ".config")
    return {"claude": (home / ".claude").is_dir() or (home / ".claude.json").is_file(), "codex": (home / ".codex").is_dir(),
            "gemini": (home / ".gemini").is_dir(), "antigravity": (home / ".gemini").is_dir(), "cursor": (home / ".cursor").is_dir(),
            "windsurf": (home / ".codeium").is_dir(), "claude-desktop": (appdata / "Claude").is_dir(), "vscode-agents": storage_hit}


def obsidian_shortcut(vault_name, obsidian_exe):
    """The text of an Internet Shortcut (.url) that opens the vault in Obsidian; with Obsidian's own icon when it is installed."""
    from urllib.parse import quote
    lines = ["[InternetShortcut]", "URL=obsidian://open?vault=" + quote(vault_name, safe="")]
    if Path(obsidian_exe).is_file():
        lines += [f"IconFile={obsidian_exe}", "IconIndex=0"]
    return "\r\n".join(lines) + "\r\n"


def obsidian_state(vault_root, home):
    """Whether the Obsidian link can open this vault: `not-installed`, `unknown-vault` (Obsidian has never opened it) or `ready`. Read-only."""
    import os
    exe = Path(home) / "AppData/Local/Programs/Obsidian/Obsidian.exe"
    config = Path(home) / "AppData/Roaming/obsidian/obsidian.json"
    if not exe.is_file() and not config.is_file():
        return "not-installed"
    try:
        vaults = json.loads(config.read_text(encoding="utf-8")).get("vaults", {})
        known = {os.path.normcase(os.path.realpath(row["path"])) for row in vaults.values() if isinstance(row, dict) and "path" in row}
    except (OSError, ValueError, AttributeError):
        return "unknown-vault"
    return "ready" if os.path.normcase(os.path.realpath(vault_root)) in known else "unknown-vault"


# The MCP server is registered under the product's name.
MCP_SERVER = "respected-brain"


def plan_integrations(ctx, profile, desired, backend, planned_keys=None):
    """Planned external changes; `planned_keys`, when given, also receives every (kind, key) the plan owns, changed or not."""
    if not any(desired.get(key, False) for key in ("global", "mcp", "schedule", "shortcut")):
        return ()
    validate_profile(ctx, profile)
    planner = _Planner(backend)
    # a tool that is not on this computer is left alone: creating its folders would make it look installed afterwards
    found = {client for client, there in detect_clients(profile).items() if there}

    def chosen(key="clients"):
        return selected_clients(desired, key) & found
    if desired.get("global"):
        clients = chosen()
        # Codex gets its memory MCP server through the plugin (it needs Sources on for Codex too): config.toml is already written as the hooks' file
        codex_mcp = None
        if desired.get("mcp") and "codex" in chosen("mcp_clients"):
            argv = launch_argv(ctx, profile, "mcp")
            codex_mcp = {"command": argv[0], "args": argv[1:]}
        writes, _ = _global_writes(ctx, profile, planner, tuple(p for p in SUPPORTED if p in {CLIENTS[c] for c in clients}), codex_mcp)
        for key, content in writes:
            planner.put("file", key, content)
    if desired.get("mcp"):
        argv = launch_argv(ctx, profile, "mcp")
        entry = {"command": argv[0], "args": argv[1:]}
        for path in mcp_destinations(profile):
            if mcp_client_of(path) not in chosen("mcp_clients"):
                continue
            document = planner.object(path, "mcp")
            servers = document.setdefault("mcpServers", {})
            if not isinstance(servers, dict):
                raise ValueError(f"Invalid mcpServers: {path}")
            previous = servers.get(MCP_SERVER)
            if previous is not None:
                same_target = isinstance(previous, dict) and previous.get("command") == entry["command"] and previous.get("args") == entry["args"]
                if not same_target:
                    raise OwnershipConflict(f"Unknown {MCP_SERVER} MCP registration: {path}")
                entry_for_path = dict(previous, **entry) if isinstance(previous, dict) else entry
            else:
                entry_for_path = entry
            servers[MCP_SERVER] = entry_for_path
            planner.put("mcp", path, json.dumps(document, ensure_ascii=False, indent=2) + "\n")
    if desired.get("mcp") and "antigravity" in chosen("mcp_clients"):
        settings = identity_settings(ctx)
        directory = profile.user_home / ".gemini/antigravity-ide/mcp" / MCP_SERVER
        instructions = f"# Respected Brain MCP Server\n\nBu sunucu, kalıcı ikinci beyin vault'una ({ctx.paths.vault_root.name}) doğrudan erişim sağlar.\nBaşka projelerde çalışırken mimari kararları, kuralları veya geçmiş bilgileri sorgulamak için bu araçları kullan.\n"
        _assert_owned_replacement(ctx, planner, directory / "instructions.md", instructions.encode("utf-8"), kind="mcp")
        planner.put("mcp", directory / "instructions.md", instructions)
        for tool in tool_definitions(str(settings["OS_NAME"]), str(settings["COMPANION"])):
            if tool["name"] in WRITE_TOOLS:
                continue
            path = directory / (tool["name"] + ".json")
            content = json.dumps({"name": tool["name"], "description": tool["description"], "parameters": tool["inputSchema"]}, ensure_ascii=False, indent=2)
            _assert_owned_replacement(ctx, planner, path, content.encode("utf-8"), kind="mcp")
            planner.put("mcp", path, content)
    if desired.get("schedule"):
        from .scheduling.service import plan_schedule
        for row in plan_schedule(ctx, profile, backend, time_str=ctx.config.get("preferences", {}).get("briefing_time", "08:00")):
            planner.put(row.kind, row.key, row.after)
    if desired.get("shortcut"):
        if profile.platform != "windows-native":
            raise FoundationError("Native shortcut registration is unavailable for this profile")
        # a plain Obsidian shortcut (what Explorer's New > Shortcut with obsidian://open?vault=NAME makes); Obsidian names a vault after its folder
        name = ctx.paths.vault_root.name
        key = profile.user_home / "Desktop" / f"Obsidian - {name}.url"
        text = obsidian_shortcut(name, profile.user_home / "AppData/Local/Programs/Obsidian/Obsidian.exe")
        _assert_owned_replacement(ctx, planner, key, text.encode("utf-8"), kind="shortcut")
        planner.put("shortcut", key, text)
    if planned_keys is not None:
        planned_keys.update(planner.after)
    return planner.changes()

