#!/usr/bin/env python3
"""Tests for boundary regressions (unsafe staging) and tracked bytecode cleanup (Faz 1)."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from respected_brain.core.config import ConfigStore
from respected_brain.core.errors import SelectionError
from respected_brain.core.paths import Roots
from respected_brain.integrations.backend import IntegrationProfile
from respected_brain.installation.transaction import Transaction
from tests.support.packages import seed_package
from tests.support.fakes import Backend, with_ai_tools
from tests.support.files import snapshot


class BoundaryRegressionTest(unittest.TestCase):
    def setUp(self):
        from respected_brain.memory import compile
        self.compile = compile
        temporary = tempfile.TemporaryDirectory(prefix="boundary-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.vault = self.root / "vault"
        self.vault.mkdir()
        self.roots = Roots(self.root / "app", self.root / "data", self.vault)
        self.backend = Backend()
        self.profile = IntegrationProfile("windows-native", (str(self.roots.app_root / "respected-brain.exe"),), self.root / "home")

    def test_staging_inside_vault_is_rejected_before_model_call(self):
        """If temporary staging directory falls inside vault root, compile must abort immediately."""
        with tempfile.TemporaryDirectory() as temp_dir:
            vault_root = Path(temp_dir).resolve()
            state_dir = vault_root / "engine" / ".state"
            state_dir.mkdir(parents=True, exist_ok=True)
            daily_dir = vault_root / "daily"
            daily_dir.mkdir(parents=True, exist_ok=True)
            daily_file = daily_dir / "2026-09-01.md"
            daily_file.write_text("# Test Daily\n\nSome content", encoding="utf-8")
            knowledge_dir = vault_root / "knowledge"
            knowledge_dir.mkdir(parents=True, exist_ok=True)
            (knowledge_dir / "index.md").write_text("# Index", encoding="utf-8")

            # Simulate staging created inside vault
            inside_stage = vault_root / "accidental_internal_staging"
            inside_stage.mkdir(parents=True, exist_ok=True)

            with mock.patch("tempfile.mkdtemp", return_value=str(inside_stage)), \
                 mock.patch.object(self.compile, "_run_model") as mock_model:

                with self.assertRaises(self.compile.PolicyError) as cm:
                    self.compile._prepare_stage(vault_root, state_dir, daily_file, Path(tempfile.gettempdir()).resolve())

                self.assertIn("staging-inside-vault", str(cm.exception))
                self.assertEqual(mock_model.call_count, 0)

    def test_corrupt_configuration_fails_closed(self):
        self.roots.data_root.mkdir()
        (self.roots.data_root / "config.json").write_text('{invalid_json: true,}\n', encoding="utf-8")
        with self.assertRaises(SelectionError):
            ConfigStore(self.roots.data_root).read()

    def test_transaction_backups_are_outside_vault_and_overlap_fails_before_write(self):
        before = snapshot(self.root)
        with self.assertRaises(SelectionError):
            Roots(self.roots.app_root, self.vault / "unsafe-backups", self.vault)
        self.assertEqual(snapshot(self.root), before)
        note = self.vault / "note.md"
        note.write_bytes(b"user note")
        with Transaction(self.roots.data_root, self.backend) as tx:
            tx.backup(note)
            self.assertTrue(tx.directory.is_relative_to(self.roots.data_root / "backups"))
            self.assertFalse(tx.directory.is_relative_to(self.vault))
            tx.commit()
        self.assertEqual(note.read_bytes(), b"user note")

    def test_install_antigravity_global_accepts_non_windows_vault_path(self):
        """install_antigravity_global must not reject Linux/POSIX vault paths where windows_path is None."""
        from respected_brain.integrations.backend import IntegrationProfile, NativeBackend
        from respected_brain.integrations import rendering
        from respected_brain.installation.transaction import Transaction
        from tests.support.fakes import memory_context as make_context
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary).resolve()
            ctx = make_context(base / "Ada Brain")
            home = base / "home"
            home.mkdir()
            with_ai_tools(home)
            backend = NativeBackend(ctx.paths.data_root, user_home=home)
            profile = IntegrationProfile("posix", ("/opt/respected-brain/bin/respected-brain",), home)
            with mock.patch.object(rendering, "windows_path", return_value=None):
                changes = rendering.plan_integrations(ctx, profile, {"global": True}, backend)
            with Transaction(ctx.paths.data_root, backend) as tx:
                for change in changes:
                    tx.apply_external(change)
                tx.commit()
            hooks = home / ".gemini/config/hooks.json"
            self.assertTrue(hooks.is_file())
            self.assertIn(ctx.paths.vault_id, hooks.read_text(encoding="utf-8"))
            self.assertIn("/opt/respected-brain/bin/respected-brain", hooks.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
