"""Maintenance failure and ownership boundaries: selected-vault writes, idempotency state, snapshots, backup/restore and merge."""
from pathlib import Path
from datetime import datetime
import contextlib
import errno
import importlib
import io
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from unittest import mock
from unittest.mock import patch

from respected_brain.core.context import AppContext
from respected_brain.core.paths import AppPaths
from respected_brain.core.resources import ResourceCatalog

from tests.support.files import make_context, snapshot
from respected_brain.maintenance import run_tool
from respected_brain.maintenance import smart_merge, repair_daily, vault_linter, _atomic
from respected_brain.maintenance.ingestion.mine_agent_history import AgentHistoryMiner
from respected_brain.maintenance.backup import backup_restic, publish_git_snapshot


class MaintenanceReviewTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        self.ctx = make_context(self.root)
        self.vault = self.ctx.paths.vault_root
        self.vault.mkdir(parents=True, exist_ok=True)

    def notes(self):
        source, target, ref = [self.vault / name for name in ('Source.md', 'Target.md', 'Ref.md')]
        source.write_text('# Source\noriginal source\n', encoding='utf-8')
        target.write_text('# Target\noriginal target\n', encoding='utf-8')
        ref.write_text('[[Source]]\n', encoding='utf-8')
        return source, target, ref

    def test_merge_preserves_opaque_target_frontmatter_timeline(self):
        source, target, _ = self.notes()
        timeline = 'timeline:\n  - from: 2026-01-01\n    source: "human decision"\n'
        target.write_text('---\ntitle: Target\n' + timeline + '---\noriginal target\n', encoding='utf-8')
        smart_merge.smart_merge(source, target, self.vault)
        self.assertIn(timeline, target.read_text(encoding='utf-8'))

    def test_repeated_daily_backups_do_not_overwrite_same_second(self):
        daily = self.vault / 'daily'
        daily.mkdir()
        path = daily / '2026-10-06.md'
        path.write_bytes(b'first original')
        _, first = repair_daily.repair_daily_file(path, self.vault)
        path.write_bytes(b'second original')
        _, second = repair_daily.repair_daily_file(path, self.vault)
        self.assertNotEqual(first, second)
        self.assertEqual(first.read_bytes(), b'first original')

    def test_merge_late_user_edit_preserves_both_original_contents(self):
        source, target, ref = self.notes()
        write = smart_merge._atomic_write_text
        def edit(path, text, **options):
            write(path, text, **options)
            if path == ref:
                source.write_bytes(b'late user edit')
        with patch.object(smart_merge, '_atomic_write_text', side_effect=edit), self.assertRaises(ValueError):
            smart_merge.smart_merge(source, target, self.vault)
        self.assertEqual(source.read_bytes(), b'late user edit')
        self.assertIn('original source', target.read_text(encoding='utf-8'))
        self.assertIn('original target', target.read_text(encoding='utf-8'))

    def test_merge_refuses_source_outside_selected_vault(self):
        source, target, _ = self.notes()
        outside = self.root / 'outside.md'
        outside.write_bytes(source.read_bytes())
        before = snapshot(self.vault), outside.read_bytes()
        with self.assertRaises(ValueError):
            smart_merge.smart_merge(outside, target, self.vault)
        self.assertEqual((snapshot(self.vault), outside.read_bytes()), before)

    def test_merge_write_failure_restores_all_prior_note_changes(self):
        source, target, _ = self.notes()
        before = snapshot(self.vault)
        write = smart_merge._atomic_write_text
        def fail(path, text, **options):
            if path == source and 'redirect:' in text:
                raise OSError('fixture disk failure')
            return write(path, text, **options)
        with patch.object(smart_merge, '_atomic_write_text', side_effect=fail), self.assertRaises(OSError):
            smart_merge.smart_merge(source, target, self.vault)
        self.assertEqual(snapshot(self.vault), before)

    def test_cross_volume_failed_commit_preserves_staging(self):
        staging, destination = self.root / 'stage', self.vault / 'note.md'
        staging.write_bytes(b'new')
        destination.write_bytes(b'old')
        with patch.object(_atomic.os, 'replace', side_effect=[OSError(errno.EXDEV, 'fixture volume'), OSError('fixture commit')]):
            with self.assertRaises(OSError):
                _atomic.replace_staged(staging, destination)
        self.assertEqual(staging.read_bytes(), b'new')
        self.assertEqual(destination.read_bytes(), b'old')

    def test_daily_date_cannot_escape_daily_directory(self):
        self.vault.joinpath('daily').mkdir()
        target = self.vault / 'outside.md'
        target.write_text('### Oturum (10:00)\nbody\n', encoding='utf-8')
        before = snapshot(self.vault)
        with self.assertRaises(ValueError):
            repair_daily.main(['--date', '../outside'], ctx=self.ctx)
        self.assertEqual(snapshot(self.vault), before)

    def test_dash_fix_obeys_writer_admission(self):
        from respected_brain.core.locking import exclusive_lock
        from respected_brain.core.errors import BusyError
        note = self.vault / 'a—b.md'
        note.write_text('human', encoding='utf-8')
        with exclusive_lock(self.ctx.paths.data_root / '.operation.lock', timeout=0):
            with self.assertRaises(BusyError), contextlib.redirect_stdout(io.StringIO()):
                run_tool(self.ctx, name='vault_linter', argv=['--fix-dashes'])
        self.assertTrue(note.exists())

    def parsed(self, identity):
        return dict(id=identity, agent='codex', title='Same title', mtime=datetime(2026, 10, 6), user_inputs=[identity], summaries=[])

    def miner(self):
        return AgentHistoryMiner(self.vault, state_file=self.ctx.paths.state_dir / 'imported_sessions.json', temp_dir=self.ctx.paths.cache_dir)

    def test_history_title_collision_never_overwrites_previous_session(self):
        miner = self.miner()
        first = miner.import_session(self.parsed('one'))
        original = first.read_bytes()
        second = miner.import_session(self.parsed('two'))
        self.assertNotEqual(first, second)
        self.assertEqual(first.read_bytes(), original)

    def test_history_import_refuses_overwriting_user_edit_on_retry(self):
        miner = self.miner()
        path = miner.import_session(self.parsed('one'))
        path.write_bytes(b'user-edit')
        with self.assertRaises(ValueError):
            miner.import_session(self.parsed('one'))
        self.assertEqual(path.read_bytes(), b'user-edit')

    def test_history_state_write_failure_is_visible(self):
        miner = self.miner()
        with patch.object(miner, '_save_state', side_effect=OSError('fixture state')):
            with self.assertRaises(OSError):
                miner.import_session(self.parsed('one'))
        self.assertNotIn('one', miner.imported_ids)

    def test_modern_codex_event_is_parsed_without_malformed_record_aborting(self):
        path = self.root / 'transcript.jsonl'
        path.write_text('\n'.join(json.dumps(record) for record in (
            [], {'type': 'event_msg', 'payload': {'type': 'user_message', 'message': 'inspect this project'}},
        )), encoding='utf-8')
        result = self.miner().parse_session(dict(path=path, agent='codex', id='modern', mtime=datetime(2026, 10, 6)))
        self.assertIsNotNone(result)
        self.assertIn('inspect this project', result['user_inputs'])

    def test_restic_does_not_verify_an_unidentified_latest_snapshot(self):
        completed = subprocess.CompletedProcess([], 0, stdout='[]\n', stderr='')
        with patch.object(backup_restic, 'check_prerequisites', return_value=(True, 'fixture-restic')), patch.object(backup_restic.subprocess, 'run', return_value=completed) as run:
            result = backup_restic.run_backup(self.vault, str(self.root / 'backup'), apply=True, password='test')
        self.assertNotEqual(result['status'], 'ok')
        self.assertEqual(run.call_count, 2)  # repository probe + backup; no restore for an unidentified snapshot

    def test_snapshot_failed_commit_never_pushes_or_writes_receipt(self):
        receipt = self.ctx.paths.state_dir / 'receipt.json'
        calls = []
        def run(command, **options):
            calls.append(command)
            return subprocess.CompletedProcess(command, 1 if command[1] == 'commit' else 0, stdout='', stderr='fixture failure')
        with patch.object(publish_git_snapshot, '_branch_divergence_status', return_value='clean'), patch.object(publish_git_snapshot.subprocess, 'run', side_effect=run):
            result = publish_git_snapshot.publish_if_due(self.vault, receipt_file=receipt, apply=True)
        self.assertNotEqual(result['status'], 'ok')
        self.assertFalse(any(command[1] == 'push' for command in calls))
        self.assertFalse(receipt.exists())

    @unittest.skipUnless(os.name == 'nt', 'Windows junction fixture')
    def test_dash_fix_does_not_follow_junction_outside_vault(self):
        outside = self.root / 'outside'
        outside.mkdir()
        note = outside / 'a—b.md'
        note.write_bytes(b'human')
        link = self.vault / 'linked'
        subprocess.run(['cmd', '/c', 'mklink', '/J', str(link), str(outside)], check=True, capture_output=True)
        try:
            vault_linter.fix_dashes(self.vault)
            self.assertTrue(note.exists())
            self.assertEqual(note.read_bytes(), b'human')
        finally:
            os.rmdir(link)


class FoundationMaintenanceToolsTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.app, self.data = self.root / 'app', self.root / 'data'
        self.vault, self.vault2 = self.root / 'Türkçe 🧠 Vault', self.root / 'İkinci Vault'
        self.project = self.root / 'code project'
        for root in (self.app, self.vault, self.vault2, self.project):
            root.mkdir()
        (self.vault / 'knowledge').mkdir()
        (self.vault / 'daily').mkdir()
        (self.vault2 / 'sentinel.md').write_text('other vault', encoding='utf-8')
        self.ctx = AppContext(AppPaths(self.app, self.data, self.vault,
                             '8c76006b-33bb-4cc0-80ce-52a0c8f38f2a'), {}, ResourceCatalog())

    def test_tools_use_selected_vault_without_app_or_other_vault_writes(self):
        maintenance = importlib.import_module('respected_brain.maintenance')
        before_app, before_other = snapshot(self.app), snapshot(self.vault2)
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = maintenance.run_tool(self.ctx, name='vault_linter', argv=['--json'])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(output.getvalue())['vault_root'], str(self.vault))
        self.assertEqual(snapshot(self.app), before_app)
        self.assertEqual(snapshot(self.vault2), before_other)

    def test_explicit_tool_vault_mismatch_fails_before_mutation(self):
        maintenance = importlib.import_module('respected_brain.maintenance')
        before = snapshot(self.root)
        with self.assertRaises(ValueError):
            maintenance.run_tool(self.ctx, name='vault_linter', argv=['--vault', str(self.vault2), '--fix-dashes'])
        self.assertEqual(snapshot(self.root), before)

    def test_agent_history_idempotency_is_in_state_not_vault(self):
        miner_module = importlib.import_module('respected_brain.maintenance.ingestion.mine_agent_history')
        miner = miner_module.AgentHistoryMiner(self.vault, state_file=self.ctx.paths.state_dir / 'imported_sessions.json')
        miner.imported_ids.add('session-one')
        miner._save_state()
        another = miner_module.AgentHistoryMiner(self.vault, state_file=self.ctx.paths.state_dir / 'imported_sessions.json')
        self.assertEqual(another.imported_ids, {'session-one'})

    def test_snapshot_receipt_uses_data_and_preserves_interval_guard(self):
        module = importlib.import_module('respected_brain.maintenance.backup.publish_git_snapshot')
        receipt = self.ctx.paths.state_dir / 'git-snapshot-receipt.json'
        remote = self.root / 'snapshot-remote.git'
        subprocess.run(['git', 'init', '--bare', '--initial-branch=main', str(remote)], check=True, capture_output=True)
        for command in (
            ['git', 'init', '--initial-branch=main'],
            ['git', 'config', 'user.name', 'Test'],
            ['git', 'config', 'user.email', 'test@test.com'],
            ['git', 'remote', 'add', 'origin', str(remote)],
        ):
            subprocess.run(command, cwd=self.vault, check=True, capture_output=True)
        with mock.patch.object(module, '_branch_divergence_status', return_value='clean'):
            result = module.publish_if_due(self.vault, apply=True, receipt_file=receipt)
            second = module.publish_if_due(self.vault, apply=True, receipt_file=receipt)
        self.assertEqual(result['status'], 'ok')
        self.assertEqual(second['status'], 'skipped:not_due')
        self.assertTrue(receipt.is_file())

    def test_restic_restore_verification_temp_is_data_cache(self):
        module = importlib.import_module('respected_brain.maintenance.backup.backup_restic')
        restore_targets = []
        def fake_restic(command, **kwargs):
            if command[1] in ('cat', 'init'):  # repository probe / first-run init
                return subprocess.CompletedProcess(command, 0, '', '')
            if command[1] == 'backup':
                return subprocess.CompletedProcess(command, 0, '{"message_type":"summary","snapshot_id":"snapshot-one"}', '')
            target = Path(command[-1])
            self.assertTrue(target.is_relative_to(self.ctx.paths.cache_dir))
            self.assertTrue(target.is_dir())
            restore_targets.append(target)
            copy = target.joinpath(*[part.strip(':\\/') for part in self.vault.parts])    # restic restores the saved absolute path
            shutil.copytree(self.vault, copy)
            return subprocess.CompletedProcess(command, 0, '', '')
        with mock.patch.object(module, 'check_prerequisites', return_value=(True, 'restic')), mock.patch.object(module.subprocess, 'run', side_effect=fake_restic):
            result = module.run_backup(self.vault, str(self.root / 'backup-target'), apply=True, password='test', temp_dir=self.ctx.paths.cache_dir)
        self.assertEqual(result, {'status': 'ok', 'snapshot_id': 'snapshot-one'})
        self.assertEqual(len(restore_targets), 1)
        self.assertFalse(restore_targets[0].exists())

    def test_smart_merge_commits_safely_when_vault_is_on_another_volume(self):
        module = importlib.import_module('respected_brain.maintenance.smart_merge')
        maintenance = importlib.import_module('respected_brain.maintenance')
        source, target = self.vault / 'Source.md', self.vault / 'Target.md'
        source.write_text('---\ntags: source\n---\n# Source\nNew fact\n', encoding='utf-8')
        target.write_text('---\ntags: target\n---\n# Target\nExisting fact\n', encoding='utf-8')
        real_replace = os.replace
        cross_volume_attempts, commit_temps = [], []
        def replace(staging, destination):
            staging, destination = Path(staging), Path(destination)
            if staging.is_relative_to(self.ctx.paths.cache_dir):
                cross_volume_attempts.append(staging)
                raise OSError(errno.EXDEV, 'different volume')
            self.assertEqual(staging.parent, destination.parent)
            commit_temps.append(staging)
            return real_replace(staging, destination)
        with mock.patch.object(os, 'replace', side_effect=replace), contextlib.redirect_stdout(io.StringIO()):
            code = maintenance.run_tool(self.ctx, name='smart_merge', argv=['--source', str(source), '--target', str(target)])
        self.assertEqual(code, 0)
        merged = target.read_text(encoding='utf-8')
        self.assertIn('New fact', merged)
        self.assertIn('Existing fact', merged)
        self.assertIn('[[Target]]', source.read_text(encoding='utf-8'))
        self.assertEqual(len(cross_volume_attempts), 2)
        self.assertEqual(len(commit_temps), 2)
        self.assertEqual(set(path.name for path in self.vault.glob('*.md')), {'Source.md', 'Target.md'})
        self.assertFalse(any(path.is_file() for path in self.ctx.paths.cache_dir.rglob('*')))

    def test_backup_cannot_write_an_explicit_repository_under_app_root(self):
        maintenance = importlib.import_module('respected_brain.maintenance')
        module = importlib.import_module('respected_brain.maintenance.backup.backup_restic')
        before = snapshot(self.app)
        with mock.patch.object(module, 'check_prerequisites', return_value=(True, 'restic')), mock.patch.object(module.subprocess, 'run', side_effect=AssertionError('backup must reject before subprocess')):
            with self.assertRaises(ValueError):
                maintenance.run_tool(self.ctx, name='backup_restic', argv=['--repo', str(self.app / 'backup-repository'), '--apply'])
        self.assertEqual(snapshot(self.app), before)

    def test_local_html_ingestion_keeps_existing_conversion(self):
        maintenance = importlib.import_module('respected_brain.maintenance')
        source = self.root / 'page.html'
        target = self.root / 'clean.md'
        source.write_text('<html><body><h1>Useful</h1><script>noise()</script><p>A fact</p></body></html>', encoding='utf-8')
        with contextlib.redirect_stdout(io.StringIO()):
            code = maintenance.run_tool(self.ctx, name='defuddle', argv=['--file', str(source), '--output', str(target)])
        self.assertEqual(code, 0)
        self.assertIn('# Useful', target.read_text(encoding='utf-8'))
        self.assertNotIn('noise()', target.read_text(encoding='utf-8'))
