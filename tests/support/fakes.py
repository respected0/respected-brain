"""Shared fakes and fixtures for the test packages (no product behaviour here)."""
from __future__ import annotations

from contextlib import contextmanager
import importlib
import json
import os
from pathlib import Path
import subprocess
import tempfile

from respected_brain.core.context import AppContext
from respected_brain.core.paths import AppPaths
from respected_brain.core.resources import ResourceCatalog
from respected_brain.core.errors import BusyError
from respected_brain.integrations.backend import IntegrationProfile


SUMMARY = "\n".join("## " + name + "\n- Kalıcı karar." for name in
    ("Bağlam", "Önemli Konuşmalar", "Alınan Kararlar", "Öğrenilenler", "Yapılacaklar"))


class Backend:
    def __init__(self):
        self.records = {}
        self.busy = False

    def read(self, kind, key):
        return self.records.get((kind, key))

    def apply(self, change):
        if self.read(change.kind, change.key) != change.before:
            raise ValueError("external-conflict")
        self.records[(change.kind, change.key)] = change.after

    def restore(self, change):
        if self.read(change.kind, change.key) != change.after:
            raise ValueError("external-conflict")
        self.records[(change.kind, change.key)] = change.before

    def quiesce(self, vault_id):
        from contextlib import contextmanager
        @contextmanager
        def quiet():
            if self.busy:
                raise BusyError("writer-active")
            yield
        return quiet()


def with_ai_tools(home: Path) -> Path:
    """The configuration folders of every AI tool the product can connect to: planning skips a tool that is not on the computer."""
    for name in (".claude", ".codex", ".gemini", ".cursor", ".codeium", "AppData/Roaming/Claude"):
        (home / name).mkdir(parents=True, exist_ok=True)
    return home


class IntegrationFixture:

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.app, self.data, self.vault, self.home = [self.root / name for name in ('app', 'data', 'Türkçe 🧠 Vault', 'home')]
        for path in (self.app, self.vault, self.home):
            path.mkdir()
        with_ai_tools(self.home)
        self.ctx = AppContext(AppPaths(self.app, self.data, self.vault, '93e9e921-3334-4a6a-a381-1d4c42a9d405'), {'integrations': {}, 'preferences': {'summary_provider': 'codex'}}, ResourceCatalog())
        self.profile = IntegrationProfile('windows-native', (str(self.app / 'respected-brain.exe'),), self.home)

    def wsl_registry_output(self):
        from respected_brain.integrations.planning import wsl_path
        return json.dumps({self.ctx.paths.vault_id: {"path": wsl_path(self.vault)}})

    def backend(self):
        module = importlib.import_module('respected_brain.integrations.backend')
        return module.NativeBackend(self.data, user_home=self.home)


class FakeModel:
    def __init__(self, response=SUMMARY):
        self.calls = 0
        self.response = response
    def run(self, prompt, *, cwd, mode, timeout):
        from respected_brain.core.context import ModelResult
        self.calls += 1
        if mode == "workspace":
            index = cwd / "knowledge/index.md"
            index.write_text(index.read_text(encoding="utf-8") + "\nDerlenmiş bilgi.\n", encoding="utf-8")
        return ModelResult(self.response, "codex", None)


@contextmanager
def owned_temp_alias(testcase, root):
    """Exercise an allocated OS temp alias with a real local directory link."""
    allocated, alias = root / 'allocated-temp', root / 'temp-alias'
    allocated.mkdir()
    if os.name == 'nt':
        created = subprocess.run(['cmd', '/c', 'mklink', '/J', str(alias), str(allocated)], capture_output=True, text=True)
        if created.returncode:
            testcase.skipTest('Native directory junction creation unavailable')
    else:
        try:
            alias.symlink_to(allocated, target_is_directory=True)
        except OSError:
            testcase.skipTest('Native directory symlink creation unavailable')
    try:
        yield alias, allocated
    finally:
        assert alias.resolve() == allocated and allocated.is_relative_to(root)
        os.rmdir(alias) if os.name == 'nt' else alias.unlink()


def memory_context(vault: Path, fixture_root: Path | None = None) -> AppContext:
    root = fixture_root or vault.parent
    return AppContext(AppPaths(root / "app", root / "data", vault,
        "11111111-1111-4111-8111-111111111111"), {"preferences": {}}, ResourceCatalog())
