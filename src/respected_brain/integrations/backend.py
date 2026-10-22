"""Shared transaction protocol; implementations perform explicit external I/O."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Literal


def revert_external(current: bytes | None, before: bytes | None, after: bytes | None) -> bytes | None:
    """What `current` becomes when only our registration is undone; ValueError when the user changed the same entry too."""
    if current == after:
        return before
    from . import delta
    try:
        return delta.revert(current, delta.make_delta(before, after))
    except delta.DeltaConflict as error:
        raise ValueError("conflict") from error


@dataclass(frozen=True)
class ExternalChange:
    kind: str
    key: str
    before: bytes | None
    after: bytes | None
    has_uninstall_baseline: bool = False
    uninstall_before: bytes | None = None
    # Persisted form for client config files: only the entries we changed (integrations/delta.py) + fingerprints of the full
    # files, so no complete copy of a client's config (and the secrets other tools keep in it) is retained.
    delta: bytes | None = None
    before_sha256: str | None = None
    after_sha256: str | None = None

    def restored(self, current: bytes | None) -> bool:
        """Is `current` already the state before our change (nothing of ours left to undo)?"""
        if self.delta is None:
            return current == self.before
        from .delta import sha256
        return sha256(current) == self.before_sha256

    def undo(self, current: bytes | None) -> bytes | None:
        """`current` with only our entries undone; ValueError when someone changed the same entry."""
        from . import delta
        if self.kind not in ("file", "mcp"):      # scheduled tasks, shortcuts, registry values: exact bytes or a conflict
            if current == self.after:
                return self.before
            raise ValueError("conflict")
        if self.delta is None:
            return revert_external(current, self.before, self.after)
        try:
            return delta.revert(current, self.delta)
        except delta.DeltaConflict as error:
            raise ValueError("conflict") from error

    def compact(self) -> "ExternalChange":
        """The persisted form (config files only): drops the full before/after copies, keeps the delta and fingerprints."""
        if self.delta is not None or self.kind not in ("file", "mcp"):
            return self
        from . import delta
        return ExternalChange(self.kind, self.key, None, None, self.has_uninstall_baseline, None, delta.make_delta(
            self.uninstall_before if self.has_uninstall_baseline else self.before, self.after),
            delta.sha256(self.uninstall_before if self.has_uninstall_baseline else self.before), delta.sha256(self.after))


@dataclass(frozen=True)
class IntegrationProfile:
    platform: Literal["windows-native", "posix", "windows-wsl"]
    launcher: tuple[str, ...]
    user_home: Path


import base64
import hashlib
import json
import os
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET

from respected_brain.core.config import atomic_write_bytes
from respected_brain.core.coordination import quiesce_writers
from respected_brain.core.errors import FoundationError, OwnershipConflict
from respected_brain.core.locking import exclusive_lock
from respected_brain.core.platform import path_within_vault

_KINDS = frozenset({"file", "mcp", "task", "shortcut", "registry"})


def canonical_json(value) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")


def canonical_task_xml(content: str, *, current_sid: str | None = None) -> bytes:
    """Ignore only Windows-generated defaults; meaningful deviations stay owned."""
    root = ET.fromstring(content)
    defaults = {
        "DisallowStartIfOnBatteries": {"true"}, "StopIfGoingOnBatteries": {"true"},
        "AllowHardTerminate": {"true"}, "RunOnlyIfNetworkAvailable": {"false"},
        "AllowStartOnDemand": {"true"}, "Enabled": {"true"}, "Hidden": {"false"},
        "RunOnlyIfIdle": {"false"}, "WakeToRun": {"false"}, "Priority": {"7"},
        "StopOnIdleEnd": {"true"}, "RestartOnIdle": {"false"},
        "RandomDelay": {"PT0S", "PT0M"}, "Delay": {"PT0S", "PT0M"},
        "UseUnifiedSchedulingEngine": {"true"},
    }
    def local(node):
        return node.tag.rsplit("}", 1)[-1]
    for parent in list(root.iter()):
        for child in list(parent):
            tag, text = local(child), (child.text or "").strip()
            if tag in defaults and text in defaults[tag] and not list(child):
                parent.remove(child)
            elif local(parent) == "RegistrationInfo" and tag in {"Date", "URI"}:
                parent.remove(child)
    if current_sid:
        for parent in list(root):
            if local(parent) == "Principals" and len(parent) == 1:
                principal = parent[0]
                values = {local(item): (item.text or "").strip() for item in principal}
                if values.get("UserId") == current_sid and values.get("LogonType") == "InteractiveToken" and values.get("RunLevel", "LeastPrivilege") == "LeastPrivilege" and set(values) <= {"UserId", "LogonType", "RunLevel"}:
                    root.remove(parent)
    for parent in reversed(list(root.iter())):
        for child in list(parent):
            if not list(child) and not (child.text or "").strip() and local(child) in {"IdleSettings", "RegistrationInfo", "Repetition"}:
                parent.remove(child)
    def describe(node):
        return {"tag": local(node), "attrs": dict(sorted(node.attrib.items())), "text": (node.text or "").strip(), "children": [describe(child) for child in (sorted(node, key=lambda item: local(item)) if local(node) in {"Task", "Settings", "RegistrationInfo", "Principal", "CalendarTrigger", "Exec"} else node)]}
    return canonical_json(describe(root))


def task_xml_from_bytes(content: bytes) -> str:
    document = json.loads(content)
    namespace = "http://schemas.microsoft.com/windows/2004/02/mit/task"
    def restore(node):
        element = ET.Element("{" + namespace + "}" + node["tag"], node["attrs"])
        element.text = node["text"] or None
        for child in node["children"]:
            element.append(restore(child))
        return element
    return ET.tostring(restore(document), encoding="unicode")


class NativeBackend:
    """Native registration I/O with explicit keys and compare-and-swap rollback."""
    def __init__(self, data_root: Path, *, user_home: Path | None = None):
        if not data_root.is_absolute():
            raise ValueError("DataRoot must be absolute")
        self.data_root = data_root.resolve()
        self.user_home = user_home.resolve() if user_home is not None else None

    def _path(self, key: str) -> Path:
        path = Path(key)
        if not path.is_absolute():
            raise ValueError("External file key must be absolute")
        for candidate in (path, *path.parents):
            if candidate.is_symlink() or (candidate.exists() and getattr(candidate.lstat(), "st_file_attributes", 0) & 0x400):
                raise OwnershipConflict(f"External target has a link/reparse point: {candidate}")
        return path

    def _windows(self):
        if os.name != "nt":
            raise FoundationError("Windows native registration is unavailable on this platform")

    def _powershell(self, script: str, **environment):
        self._windows()
        executable = shutil.which("powershell.exe") or shutil.which("pwsh.exe")
        if not executable:
            raise FoundationError("PowerShell is unavailable for native registration")
        encoded = base64.b64encode(("$ErrorActionPreference='Stop'; " + script).encode("utf-16-le")).decode("ascii")
        env = dict(os.environ, **{key: str(value) for key, value in environment.items()})
        try:
            result = subprocess.run([executable, "-NoProfile", "-NonInteractive", "-EncodedCommand", encoded], capture_output=True, env=env, timeout=30)
        except (OSError, subprocess.TimeoutExpired) as error:
            raise FoundationError('Native registration command unavailable or timed out') from error
        if result.returncode:
            raise FoundationError(result.stderr.decode("utf-8", errors="replace") or "Native registration failed")
        raw = result.stdout.decode("utf-8-sig", errors="strict").strip()
        return json.loads(raw) if raw else None

    def _native_command(self, argv, *, allowed=(0,)):
        try:
            result = subprocess.run(argv, capture_output=True, timeout=30)
        except (OSError, subprocess.TimeoutExpired) as error:
            raise FoundationError(f"Native scheduler is unavailable: {argv[0]}") from error
        if result.returncode not in allowed:
            raise FoundationError(result.stderr.decode("utf-8", errors="replace") or f"Native scheduler failed: {argv[0]}")
        return result

    def _posix_task_read(self, key):
        if key.startswith("systemd:"):
            unit = key[8:]
            if not re.fullmatch(r"[A-Za-z0-9_.@-]+\.timer", unit):
                raise ValueError("Invalid explicit systemd timer")
            enabled = self._native_command(["systemctl", "--user", "is-enabled", unit], allowed=(0, 1, 3, 4))
            enabled_text = enabled.stdout.decode().strip()
            if enabled_text not in {"enabled", "disabled", "not-found", ""}:
                raise FoundationError("Unsupported systemd timer enable state: " + enabled_text)
            active = self._native_command(["systemctl", "--user", "is-active", unit], allowed=(0, 3, 4))
            state = {"enabled": enabled_text == "enabled", "active": active.stdout.decode().strip() == "active"}
            return canonical_json(state) if any(state.values()) else None
        path = self._path(key[len("launchd:"):])
        target = f"gui/{os.getuid()}/{path.stem}"
        result = self._native_command(["launchctl", "print", target], allowed=(0, 113))
        return canonical_json({"loaded": True}) if result.returncode == 0 else None

    def _posix_task_write(self, key, content):
        document = json.loads(content) if content else {}
        if key.startswith("systemd:"):
            unit = key[8:]
            if not re.fullmatch(r"[A-Za-z0-9_.@-]+\.timer", unit):
                raise ValueError("Invalid explicit systemd timer")
            self._native_command(["systemctl", "--user", "daemon-reload"])
            if document.get("enabled"):
                self._native_command(["systemctl", "--user", "enable", unit])
            else:
                self._native_command(["systemctl", "--user", "disable", unit])
            self._native_command(["systemctl", "--user", "start" if document.get("active") else "stop", unit])
            return
        path = self._path(key[len("launchd:"):])
        domain = f"gui/{os.getuid()}"
        if document.get("loaded"):
            self._native_command(["launchctl", "bootstrap", domain, str(path)])
        else:
            self._native_command(["launchctl", "bootout", domain + "/" + path.stem], allowed=(0, 113))

    def _task_read(self, key: str) -> bytes | None:
        if key.startswith(("systemd:", "launchd:")):
            return self._posix_task_read(key)
        if not key or "\0" in key:
            raise ValueError("Invalid scheduled task key")
        document = self._powershell(r"""
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$service = New-Object -ComObject Schedule.Service; $service.Connect(); $folder = $service.GetFolder('\')
try { $task = $folder.GetTask($env:RESPECTED_EXTERNAL_KEY); @{ xml=$task.Xml; sid=[System.Security.Principal.WindowsIdentity]::GetCurrent().User.Value } | ConvertTo-Json -Compress }
catch { if ($_.Exception.HResult -eq -2147024894) { 'null' } else { throw } }
""", RESPECTED_EXTERNAL_KEY=key)
        if document is None:
            return None
        return canonical_task_xml(document["xml"], current_sid=document["sid"])

    def _shortcut_read(self, key: str) -> bytes | None:
        path = self._path(key)
        if not path.exists():
            return None
        document = self._powershell(r"""
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$shell=New-Object -ComObject WScript.Shell; $item=$shell.CreateShortcut($env:RESPECTED_EXTERNAL_KEY)
@{target=$item.TargetPath; arguments=$item.Arguments; working_directory=$item.WorkingDirectory; description=$item.Description; icon_location=$item.IconLocation; window_style=$item.WindowStyle; hotkey=$item.Hotkey} | ConvertTo-Json -Compress
""", RESPECTED_EXTERNAL_KEY=str(path))
        if document.get("icon_location") == ",0":
            document["icon_location"] = ""
        return canonical_json(document)

    def _registry_path(self, key: str):
        self._windows()
        if not key.startswith("HKCU\\") or "\0" in key:
            raise ValueError("Only explicit HKCU registry keys are supported")
        import winreg
        return winreg, key[5:]

    def _registry_read(self, key: str) -> bytes | None:
        registry, subkey = self._registry_path(key)
        def read_node(path):
            with registry.OpenKey(registry.HKEY_CURRENT_USER, path, 0, registry.KEY_READ) as handle:
                child_count, value_count, _ = registry.QueryInfoKey(handle)
                values = {}
                for index in range(value_count):
                    name, value, kind = registry.EnumValue(handle, index)
                    if isinstance(value, bytes):
                        value = {"base64": base64.b64encode(value).decode("ascii")}
                    values[name] = {"type": kind, "data": value}
                children = {registry.EnumKey(handle, index): None for index in range(child_count)}
            return {"values": values, "subkeys": {name: read_node(path + "\\" + name) for name in children}}
        try:
            return canonical_json(read_node(subkey))
        except FileNotFoundError:
            return None

    def read(self, kind: str, key: str) -> bytes | None:
        if kind not in _KINDS:
            raise ValueError(f"Unsupported external kind: {kind}")
        if kind in {"file", "mcp"}:
            path = self._path(key)
            return path.read_bytes() if path.exists() else None
        if kind == "task":
            return self._task_read(key)
        if kind == "shortcut":
            return self._shortcut_read(key)
        return self._registry_read(key)

    def _write(self, kind: str, key: str, content: bytes | None):
        if kind in {"file", "mcp"}:
            path = self._path(key)
            if content is None:
                path.unlink(missing_ok=True)
            else:
                atomic_write_bytes(path, content)
            return
        if kind == "task":
            if key.startswith(("systemd:", "launchd:")):
                self._posix_task_write(key, content)
                return
            xml = task_xml_from_bytes(content) if content is not None else ""
            self._powershell(r"""
$service = New-Object -ComObject Schedule.Service; $service.Connect(); $folder=$service.GetFolder('\')
if ($env:RESPECTED_DELETE -eq '1') { $folder.DeleteTask($env:RESPECTED_EXTERNAL_KEY, 0) }
else { $null=$folder.RegisterTask($env:RESPECTED_EXTERNAL_KEY, $env:RESPECTED_EXTERNAL_XML, 6, $null, $null, 3, $null) }
""", RESPECTED_EXTERNAL_KEY=key, RESPECTED_EXTERNAL_XML=xml, RESPECTED_DELETE="1" if content is None else "0")
            return
        if kind == "shortcut":
            path = self._path(key)
            if content is None:
                path.unlink(missing_ok=True)
                return
            path.parent.mkdir(parents=True, exist_ok=True)
            self._powershell(r"""
$value=$env:RESPECTED_EXTERNAL_JSON | ConvertFrom-Json; $shell=New-Object -ComObject WScript.Shell; $item=$shell.CreateShortcut($env:RESPECTED_EXTERNAL_KEY)
$item.TargetPath=$value.target; $item.Arguments=$value.arguments; $item.WorkingDirectory=$value.working_directory; $item.Description=$value.description; if ($value.icon_location) { $item.IconLocation=$value.icon_location }; $item.WindowStyle=$value.window_style; $item.Hotkey=$value.hotkey; $item.Save()
""", RESPECTED_EXTERNAL_KEY=str(path), RESPECTED_EXTERNAL_JSON=content.decode("utf-8"))
            return
        registry, subkey = self._registry_path(key)
        def remove(path):
            with registry.OpenKey(registry.HKEY_CURRENT_USER, path, 0, registry.KEY_READ) as handle:
                children = [registry.EnumKey(handle, index) for index in range(registry.QueryInfoKey(handle)[0])]
            for child in children:
                remove(path + "\\" + child)
            registry.DeleteKey(registry.HKEY_CURRENT_USER, path)
        if content is None:
            remove(subkey)
            return
        document = json.loads(content)
        def write_node(path, node):
            with registry.CreateKeyEx(registry.HKEY_CURRENT_USER, path, 0, registry.KEY_READ | registry.KEY_WRITE) as handle:
                old_names = [registry.EnumValue(handle, index)[0] for index in range(registry.QueryInfoKey(handle)[1])]
                old_children = [registry.EnumKey(handle, index) for index in range(registry.QueryInfoKey(handle)[0])]
                for name in old_names:
                    if name not in node["values"]:
                        registry.DeleteValue(handle, name)
                for name, row in node["values"].items():
                    value = row["data"]
                    if isinstance(value, dict) and set(value) == {"base64"}:
                        value = base64.b64decode(value["base64"])
                    registry.SetValueEx(handle, name, 0, row["type"], value)
            for name in old_children:
                if name not in node["subkeys"]:
                    remove(path + "\\" + name)
            for name, child in node["subkeys"].items():
                write_node(path + "\\" + name, child)
        write_node(subkey, document)

    def _change(self, change: ExternalChange, *, restore: bool):
        identity = hashlib.sha256((change.kind + "\0" + change.key).encode("utf-8")).hexdigest()
        lock = self.data_root / "external-locks" / (identity + ".lock")
        if not path_within_vault(lock, self.data_root):
            raise OwnershipConflict('Unsafe external registration lock')
        with exclusive_lock(lock):
            expected, replacement = (change.after, change.before) if restore else (change.before, change.after)
            if self.read(change.kind, change.key) != expected:
                raise OwnershipConflict(f"External registration changed: {change.kind}:{change.key}")
            if expected != replacement:
                self._write(change.kind, change.key, replacement)
            if self.read(change.kind, change.key) != replacement:
                raise OwnershipConflict(f"Native registration did not match the planned result: {change.kind}:{change.key}")

    def apply(self, change: ExternalChange) -> None:
        self._change(change, restore=False)

    def restore(self, change: ExternalChange) -> None:
        self._change(change, restore=True)

    def quiesce(self, vault_id: str | None):
        return quiesce_writers(self.data_root, vault_id)
