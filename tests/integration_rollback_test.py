"""Integration transaction rollback and unknown-user-data protections."""
from unittest import TestCase, mock
from tests.foundation_integrations_test import IntegrationFixture
from tests.foundation_support import snapshot
from respectedbrain.integrations.rendering import plan_integrations
from respectedbrain.integrations.backend import ExternalChange
from respectedbrain.installation.transaction import Transaction


class IntegrationRollbackTest(IntegrationFixture, TestCase):
    def test_failed_apply_removes_new_files_and_directories_after_rollback(self):
        backend = self.backend()
        writes = [ExternalChange("file", str(self.home / ".codex/hooks.json"), None, b"{}\n"), ExternalChange("file", str(self.home / ".codex/AGENTS.md"), None, b"managed\n")]
        original = backend.apply
        def fail_second(change):
            if change.key.endswith("AGENTS.md"):
                raise OSError("injected-write-failure")
            return original(change)
        with mock.patch.object(backend, "apply", side_effect=fail_second):
            with self.assertRaisesRegex(OSError, "injected-write-failure"):
                with Transaction(self.data, backend, vault_id=self.ctx.paths.vault_id) as tx:
                    for row in writes:
                        tx.apply_external(row)
                    tx.commit()
        self.assertFalse((self.home / ".codex").exists())

    def test_backup_roots_are_preserved_as_unknown_user_data(self):
        for relative in (".respected-backups",):
            path = self.home / relative
            path.mkdir()
            (path / "keep.txt").write_text(relative, encoding="utf-8")
        before = snapshot(self.home)
        rows = plan_integrations(self.ctx, self.profile, {"global": True}, self.backend())
        self.assertEqual(snapshot(self.home), before)
        self.assertFalse(any("backups" in row.key for row in rows))
