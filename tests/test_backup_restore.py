"""Backup verification by content and the restore path, against a functional restic stand-in.

The stand-in implements restic's documented behaviour that this code relies on (init / cat config / backup --json / restore
<id>:/subfolder --target, as observed with real restic 0.19.1 on Windows). It is NOT real restic; scratchpad/real_restic.py was run against the real binary.
"""
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from respectedbrain.maintenance.backup import backup_restic as B


class FakeRestic:
    def __init__(self, corrupt_restore: bool = False, drop_file: bool = False):
        self.calls = []
        self.corrupt_restore, self.drop_file = corrupt_restore, drop_file

    def __call__(self, command, **kwargs):
        env, repo = kwargs.get("env", {}), Path(kwargs["env"]["RESTIC_REPOSITORY"])
        self.calls.append(command[1])
        done = lambda out="", code=0, err="": subprocess.CompletedProcess(command, code, out, err)
        if not (env.get("RESTIC_PASSWORD") or env.get("RESTIC_PASSWORD_FILE")):
            return done(code=1, err="no password")
        action = command[1]
        if action == "cat":
            return done(code=0 if (repo / "config").is_file() else 1)
        if action == "init":
            repo.mkdir(parents=True)
            (repo / "config").write_text("repo", encoding="utf-8")
            return done()
        if action == "backup":
            source = Path(command[2])
            snapshot = f"snap{len(list(repo.glob('snap*'))) + 1:04d}"
            shutil.copytree(source, repo / snapshot / Path(*[p.strip(":\\/") for p in source.parts]))
            (repo / snapshot / "source.txt").write_text(str(source), encoding="utf-8")
            return done(json.dumps({"message_type": "summary", "snapshot_id": snapshot}))
        if action == "snapshots":   # restic snapshots <id|latest> --json
            snapshot = sorted(repo.glob("snap*"))[-1].name if command[2] == "latest" else command[2]
            return done(json.dumps([{"id": snapshot, "paths": [(repo / snapshot / "source.txt").read_text(encoding="utf-8")]}]))
        if action == "restore":     # restic restore <id>:/subfolder: only the subfolder lands in --target (a bare id recreates C:\Users\...)
            snapshot, _, sub = command[2].partition(":")
            snapshot = sorted(repo.glob("snap*"))[-1].name if snapshot == "latest" else snapshot
            target = Path(command[command.index("--target") + 1])
            shutil.copytree(repo / snapshot / Path(*sub.strip("/").split("/")) if sub else repo / snapshot, target, dirs_exist_ok=True)
            for file in sorted(target.rglob("*.md")):
                if self.drop_file:
                    file.unlink()
                elif self.corrupt_restore:
                    file.write_text("bit rot", encoding="utf-8")
                break
            return done()
        return done(code=2, err="unknown")


class BackupRestoreTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="brain-bk-")).resolve()
        self.addCleanup(lambda: shutil.rmtree(self.root, ignore_errors=True))
        self.vault, self.repo = self.root / "Vault", self.root / "repo"
        (self.vault / "daily").mkdir(parents=True)
        (self.vault / "daily" / "a.md").write_text("alpha", encoding="utf-8")
        (self.vault / "b.md").write_text("beta", encoding="utf-8")
        mock.patch.object(B, "check_prerequisites", return_value=(True, "fake")).start()
        self.addCleanup(mock.patch.stopall)

    def run_with(self, fake, function, *args, **kwargs):
        with mock.patch.object(B.subprocess, "run", side_effect=fake):
            return function(*args, **kwargs)

    def backup(self, fake, **kwargs):
        return self.run_with(fake, B.run_backup, self.vault, str(self.repo), apply=True, password="pw", **kwargs)

    def test_first_backup_initialises_the_repository_and_is_verified_by_content(self):
        fake = FakeRestic()
        result = self.backup(fake)
        self.assertEqual(result["status"], "ok", result)
        self.assertEqual(fake.calls[:3], ["cat", "init", "backup"])

    def test_a_snapshot_that_restores_wrong_or_incomplete_is_not_ok(self):
        for fake in (FakeRestic(corrupt_restore=True), FakeRestic(drop_file=True)):
            result = self.backup(fake)
            self.assertEqual(result["status"], "verify-failed", result)
            self.assertRegex(result["error"], "different|missing")

    def test_backup_without_a_password_source_refuses_instead_of_prompting(self):
        with mock.patch.dict(B.os.environ, {}, clear=False):
            for name in ("RESTIC_PASSWORD", "RESTIC_PASSWORD_FILE"):
                B.os.environ.pop(name, None)
            result = B.run_backup(self.vault, str(self.repo), apply=True)
        self.assertEqual(result["status"], "error")
        self.assertIn("parola", result["error"])

    def test_restore_goes_to_a_new_folder_and_never_touches_the_vault(self):
        self.assertEqual(self.backup(FakeRestic())["status"], "ok")
        before = {p.relative_to(self.vault).as_posix(): p.read_bytes() for p in self.vault.rglob("*") if p.is_file()}
        (self.vault / "b.md").write_text("beta edited after the backup", encoding="utf-8")
        target = self.root / "recovered"
        result = self.run_with(FakeRestic(), B.run_restore, str(self.repo), target, self.vault, password="pw")
        self.assertEqual(result["status"], "ok", result)
        self.assertEqual(result["files"], 2)
        copy = target                                                                          # the vault's content lands directly in the target
        self.assertEqual((copy / "b.md").read_text(encoding="utf-8"), "beta")                 # the snapshot state, not the edited one
        self.assertEqual((self.vault / "b.md").read_text(encoding="utf-8"), "beta edited after the backup")   # the vault is untouched
        self.assertEqual(before["daily/a.md"], (self.vault / "daily" / "a.md").read_bytes())

    def test_restore_refuses_every_unsafe_target_and_bad_snapshot_ids(self):
        self.assertEqual(self.backup(FakeRestic())["status"], "ok")
        occupied = self.root / "occupied"
        occupied.mkdir()
        (occupied / "keep.txt").write_text("user data", encoding="utf-8")
        cases = {"non-empty folder": occupied, "inside the vault": self.vault / "restore-here", "the vault itself": self.vault,
                 "a parent of the vault": self.root, "relative path": Path("relative-target")}
        for name, target in cases.items():
            with self.subTest(name):
                fake = FakeRestic()
                result = self.run_with(fake, B.run_restore, str(self.repo), target, self.vault, password="pw")
                self.assertEqual(result["status"], "error", result)
                self.assertNotIn("restore", fake.calls)
        self.assertEqual((occupied / "keep.txt").read_text(encoding="utf-8"), "user data")
        for bad in ("latest; rm -rf /", "--target", "../x", ""):
            with self.subTest(bad):
                self.assertEqual(self.run_with(FakeRestic(), B.run_restore, str(self.repo), self.root / "new", self.vault, snapshot=bad, password="pw")["status"], "error")

    def test_restore_into_an_existing_empty_folder_works_and_needs_a_password(self):
        self.assertEqual(self.backup(FakeRestic())["status"], "ok")
        empty = self.root / "empty"
        empty.mkdir()
        self.assertEqual(B.run_restore(str(self.repo), empty, self.vault)["status"], "error")      # no password source
        result = self.run_with(FakeRestic(), B.run_restore, str(self.repo), empty, self.vault, password="pw")
        self.assertEqual(result["status"], "ok", result)


if __name__ == "__main__":
    unittest.main()
