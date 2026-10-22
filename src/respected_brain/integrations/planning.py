"""Planning primitives shared by the integration renderers: launcher/bridge commands, profile validation, ownership checks and the change planner."""
from __future__ import annotations
import json
from pathlib import Path
import re
import shlex
import subprocess
from respected_brain.core.errors import FoundationError, OwnershipConflict
from .backend import ExternalChange


def wsl_path(path):
    value = str(path).replace("\\", "/")
    if len(value) >= 3 and value[1:3] == ":/":
        return f"/mnt/{value[0].lower()}/{value[3:]}"
    return value


def _runtime_path(path, platform):
    return wsl_path(path) if platform == "windows-wsl" else str(path)


def validate_profile(ctx, profile):
    if not profile.user_home.is_absolute() or not profile.user_home.is_dir():
        raise ValueError("Explicit provider home must be an existing absolute directory")
    if not profile.launcher or any(not isinstance(p, str) or not p for p in profile.launcher):
        raise ValueError("Explicit installed launcher is required")
    executable = Path(profile.launcher[0]).name.casefold()
    if re.fullmatch(r"(?:py|python(?:[0-9]+(?:\.[0-9]+)*)?)(?:\.exe)?", executable) or any(item.endswith(".py") for item in profile.launcher):
        raise ValueError("Persistent registrations require the installed application launcher")
    if profile.platform == "windows-native":
        if profile.launcher != (str(ctx.paths.app_root / "respected-brain.exe"),):
            raise ValueError("Native registrations require the stable AppRoot executable")
    elif profile.platform == "windows-wsl":
        script = 'if [ "${1#/}" != "$1" ]; then test -x "$1"; else command -v "$1" >/dev/null; fi'
        result = subprocess.run(["wsl.exe", "--", "sh", "-c", script, "respected-brain", profile.launcher[0]], capture_output=True, timeout=15)
        if result.returncode:
            raise FoundationError("WSL launcher was not executable inside WSL")
        command = ["wsl.exe", "--", *profile.launcher, "vault", "list"]
        registered = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", timeout=15)
        diagnosis = "WSL configuration conflict: Linux DataRoot must register the same vault UUID. Run inside WSL: " + shlex.join([*profile.launcher, "vault", "register", wsl_path(ctx.paths.vault_root)])
        try:
            document = json.loads(registered.stdout) if registered.returncode == 0 else {}
            entry = document.get(ctx.paths.vault_id) if isinstance(document, dict) else None
            recorded = entry.get("path") if isinstance(entry, dict) else None
            expected = wsl_path(ctx.paths.vault_root)
            if not isinstance(recorded, str) or recorded.rstrip("/") != expected.rstrip("/"):
                raise OwnershipConflict(diagnosis)
        except (ValueError, TypeError) as error:
            raise OwnershipConflict(diagnosis) from error
    elif profile.platform != "posix":
        raise ValueError("Unsupported integration platform")


def launch_argv(ctx, profile, command, *args):
    argv = [*profile.launcher, command, "--vault-id", ctx.paths.vault_id, *args]
    if profile.platform == "windows-wsl":
        return ["wsl.exe", "--cd", wsl_path(ctx.paths.vault_root), *argv]
    return argv


def bridge_argv(ctx, profile, provider, event, *, global_hook=False):
    return launch_argv(ctx, profile, "hook", "--provider", provider, "--event", event, *(["--global-hook"] if global_hook else []))


def command_text(profile, argv):
    if not profile.platform.startswith("windows"):
        return shlex.join(argv)
    # The program is always quoted: Claude Code runs hook commands through Git Bash when it exists, and an unquoted
    # C:\pathpp.exe loses its backslashes there (the hook silently never runs). cmd.exe accepts the quoted form too.
    head = subprocess.list2cmdline(argv[:1])
    head = head if head.startswith('"') or "\\" not in head else '"' + head + '"'  # bare names such as wsl.exe stay as they are
    return " ".join([head, *([subprocess.list2cmdline(argv[1:])] if len(argv) > 1 else [])])


def _short_path(path):
    """The 8.3 form of an existing Windows path (no spaces), or the path itself when there is none."""
    if not path.startswith(("\\\\", "/")) and __import__("os").name == "nt":
        import ctypes
        buffer = ctypes.create_unicode_buffer(32768)
        if ctypes.windll.kernel32.GetShortPathNameW(path, buffer, len(buffer)):
            return buffer.value
    return path


def bare_command_text(profile, argv):
    """A hook command with no quote characters. Antigravity on Windows re-escapes quotes (`\\"`) before cmd.exe sees them,
    and Codex runs hooks through PowerShell, where a command starting with a quoted path is a parse error (exit 1);
    a path with spaces goes in its 8.3 form. Falls back to the quoted
    form when quotes cannot be avoided (the hook then fails visibly in Antigravity's log, as before)."""
    if profile.platform != "windows-native":
        return command_text(profile, argv)
    head, rest = _short_path(argv[0]) if " " in argv[0] else argv[0], subprocess.list2cmdline(argv[1:])
    if " " in head or '"' in rest:
        return command_text(profile, argv)
    return " ".join([head, rest])


class _Planner:
    def __init__(self, backend):
        self.backend = backend
        self.before = {}
        self.after = {}
    def read(self, path, kind="file"):
        identity = (kind, str(path))
        if identity not in self.before:
            self.before[identity] = self.backend.read(*identity)
        return self.before[identity]
    def text(self, path):
        return (self.read(path) or b"").decode("utf-8-sig")
    def object(self, path, kind="file"):
        data = self.read(path, kind)
        value = json.loads(data) if data is not None else {}
        if not isinstance(value, dict):
            raise ValueError(f"{path} is not a JSON object")
        return value
    def put(self, kind, key, after):
        identity = (kind, str(key))
        self.read(key, kind)
        if isinstance(after, str):
            after = after.encode("utf-8")
        if identity in self.after and self.after[identity] != after:
            raise OwnershipConflict(f"Conflicting planned registration: {key}")
        self.after[identity] = after
    def changes(self):
        return tuple(ExternalChange(kind, key, self.before[(kind, key)], after) for (kind, key), after in self.after.items() if self.before[(kind, key)] != after)


def _recorded_owner(ctx, planner, path, current, kind="file"):
    payload = planner.read(ctx.paths.data_root / "install-manifest.json")
    if payload is None:
        return False
    import base64
    try:
        document = json.loads(payload)
        if document.get("schema_version") != 3:
            raise ValueError("manifest schema")
        import hashlib
        fingerprint = hashlib.sha256(current).hexdigest() if current is not None else None
        return any(row.get("kind") == kind and row.get("key") == str(path)
                   and ((row.get("after") is not None and base64.b64decode(row["after"], validate=True) == current)
                        or (row.get("after_sha256") is not None and row.get("after_sha256") == fingerprint))
                   for row in document.get("external", []))
    except (ValueError, TypeError, AttributeError) as error:
        raise OwnershipConflict("Invalid integration ownership manifest") from error


def _assert_owned_replacement(ctx, planner, path, baseline, *, kind="file"):
    current = planner.read(path, kind)
    if current is not None and current != baseline and not _recorded_owner(ctx, planner, path, current, kind):
        raise OwnershipConflict(f"Unowned or user-changed integration file: {path}")
