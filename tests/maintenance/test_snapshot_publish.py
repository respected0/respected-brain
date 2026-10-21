'''Immutable Git snapshot publication regressions.'''
from pathlib import Path
import os, shutil, subprocess, sys, tempfile, unittest
from unittest import mock
from respectedbrain.maintenance.backup.publish_git_snapshot import publish_if_due
import json
import respectedbrain.maintenance.backup.publish_git_snapshot as snapshot_module

class ImmutableSnapshotPublicationTest(unittest.TestCase):
    def setUp(self):
        if shutil.which('git') is None: self.skipTest('git is not available')
    def _git(self, repo, *args, check=True):
        result = subprocess.run(['git',*args],cwd=repo,check=check,capture_output=True)
        return result.stdout.decode().strip()
    def _fixture(self, root):
        remote = root/'remote.git'; repo = root/'vault'
        subprocess.run(['git','init','--bare',str(remote)],check=True,capture_output=True)
        subprocess.run(['git','init','-b','main',str(repo)],check=True,capture_output=True)
        self._git(repo,'config','user.name','Fixture'); self._git(repo,'config','user.email','fixture@example.invalid')
        self._git(repo,'remote','add','origin',str(remote)); (repo/'safe.md').write_text('safe')
        self._git(repo,'add','safe.md'); self._git(repo,'commit','-m','baseline'); self._git(repo,'push','-u','origin','main')
        return remote, repo

    def test_post_scan_isolated_index_race_cannot_change_published_tree(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); remote, repo = self._fixture(root); secret = 'sk-proj-SYNTHETICONLY1234567890'*3
            import os, respectedbrain.maintenance.backup.publish_git_snapshot as module
            def race(*args,**kwargs):
                if not Path(kwargs['index_file']).name.startswith('index.tree_'):
                    return True,[]
                isolated = next((repo/'.git').glob('index.snapshot_*'))
                (repo/'race.md').write_text(secret)
                subprocess.run(['git','add','race.md'],cwd=repo,env={**os.environ,'GIT_INDEX_FILE':str(isolated)},check=True,capture_output=True)
                (repo/'race.md').unlink(); return True,[]
            with mock.patch.object(module,'scan_git_index_for_secrets',side_effect=race):
                result = publish_if_due(repo,remote='origin',branch='main',apply=True,receipt_file=root/'receipt.json')
            self.assertEqual(result['status'],'ok',result); self.assertEqual(self._git(remote,'grep','-I','-n',secret,'main',check=False),'')

    def test_staged_secret_surviving_only_in_user_index_cannot_publish(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); remote, repo = self._fixture(root); secret = 'sk-proj-SYNTHETICONLY1234567890'*3
            mixed = repo / 'mixed.md'
            mixed.write_text(secret)
            self._git(repo, 'add', 'mixed.md')
            mixed.write_text('safe working tree content')
            before_index = (repo/'.git'/'index').read_bytes()
            result = publish_if_due(repo, remote='origin', branch='main', apply=True, receipt_file=root/'receipt.json')
            self.assertEqual(result['status'], 'aborted:secret_found', result)
            self.assertEqual(self._git(remote, 'grep', '-I', '-n', secret, 'main', check=False), '')
            self.assertEqual((repo/'.git'/'index').read_bytes(), before_index)

    def test_clean_filter_cannot_inject_secret_into_scanned_tree(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); remote, repo = self._fixture(root); secret = 'sk-proj-SYNTHETICONLY1234567890'*3
            script = root / 'inject_secret.py'
            script.write_text(f"import sys\nsys.stdout.write({secret!r})\n", encoding='utf-8')
            command = '"{}" "{}"'.format(sys.executable.replace('\\','/'), str(script).replace('\\','/'))
            self._git(repo, 'config', 'filter.leak.clean', command)
            (repo/'.gitattributes').write_text('*.filtered filter=leak\n')
            (repo/'content.filtered').write_text('safe source')
            self._git(repo, 'add', '.gitattributes')
            self.assertIn('filter: leak', self._git(repo, 'check-attr', 'filter', 'content.filtered'))
            self._git(repo, 'add', 'content.filtered')
            self.assertEqual(self._git(repo, 'show', ':content.filtered'), secret)
            result = publish_if_due(repo, remote='origin', branch='main', apply=True, receipt_file=root/'receipt.json')
            self.assertEqual(result['status'], 'aborted:secret_found', result)
            self.assertEqual(self._git(remote, 'grep', '-I', '-n', secret, 'main', check=False), '')

    def test_tracked_ignored_file_and_user_index_head_are_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); remote, repo = self._fixture(root); (repo/'kept.md').write_text('tracked safe note')
            self._git(repo,'add','kept.md'); (repo/'.gitignore').write_text('kept.md\n')
            before_index = (repo/'.git'/'index').read_bytes(); before_head = self._git(repo,'rev-parse','HEAD')
            result = publish_if_due(repo,remote='origin',branch='main',apply=True,receipt_file=root/'receipt.json')
            self.assertEqual(result['status'],'ok',result)
            self.assertEqual(self._git(remote,'cat-file','-p','main:kept.md',check=False),'tracked safe note')
            self.assertEqual((repo/'.git'/'index').read_bytes(),before_index); self.assertEqual(self._git(repo,'rev-parse','HEAD'),before_head)


class ImmutableSnapshotChainTest(unittest.TestCase):
    def setUp(self) -> None:
        if subprocess.run(['git', '--version'], capture_output=True).returncode != 0:
            self.skipTest('git is not available')

    def _git(self, repository: Path, *arguments: str) -> str:
        result = subprocess.run(
            ['git', *arguments],
            cwd=repository,
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()

    def _fixture(self, root: Path) -> tuple[Path, Path]:
        remote = root / 'remote.git'
        repository = root / 'vault'
        subprocess.run(['git', 'init', '--bare', str(remote)], check=True, capture_output=True)
        subprocess.run(['git', 'init', '-b', 'main', str(repository)], check=True, capture_output=True)
        self._git(repository, 'config', 'user.name', 'Fixture')
        self._git(repository, 'config', 'user.email', 'fixture@example.invalid')
        self._git(repository, 'remote', 'add', 'origin', str(remote))
        (repository / 'note.md').write_text('first\n', encoding='utf-8')
        self._git(repository, 'add', 'note.md')
        self._git(repository, 'commit', '-m', 'baseline')
        self._git(repository, 'push', '-u', 'origin', 'main')
        return remote, repository

    def test_three_snapshots_form_fast_forward_chain_without_user_state_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            remote, repository = self._fixture(root)
            receipt = root / 'receipt.json'
            commits: list[str] = []
            note = repository / 'note.md'

            for expected in ('first\n', 'second\n', 'third\n'):
                note.write_text(expected, encoding='utf-8')
                result = publish_if_due(
                    repository,
                    remote='origin',
                    branch='main',
                    apply=True,
                    min_interval_seconds=0,
                    receipt_file=receipt,
                )
                self.assertEqual('ok', result['status'], result)
                commits.append(result['commit'])
                self.assertEqual(expected.strip(), self._git(remote, 'show', f'main:{note.name}'))

            self.assertEqual(3, len(set(commits)))
            self.assertEqual(commits[0], self._git(remote, 'rev-parse', f'{commits[1]}^'))
            self.assertEqual(commits[1], self._git(remote, 'rev-parse', f'{commits[2]}^'))

    def test_user_head_progression_still_extends_snapshot_chain(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            remote, repository = self._fixture(root)
            receipt = root / 'receipt.json'
            first = publish_if_due(repository, remote='origin', branch='main', apply=True, min_interval_seconds=0, receipt_file=receipt)
            self.assertEqual('ok', first['status'], first)

            (repository / 'user-commit.md').write_text('safe\n', encoding='utf-8')
            self._git(repository, 'add', 'user-commit.md')
            self._git(repository, 'commit', '-m', 'user work')
            second = publish_if_due(repository, remote='origin', branch='main', apply=True, min_interval_seconds=0, receipt_file=receipt)
            self.assertEqual('ok', second['status'], second)
            self.assertEqual(first['commit'], self._git(remote, 'rev-parse', f'{second["commit"]}^'))
            self.assertEqual('safe', self._git(remote, 'show', f'main:user-commit.md'))

    def test_external_remote_change_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            remote, repository = self._fixture(root)
            receipt = root / 'receipt.json'
            first = publish_if_due(repository, remote='origin', branch='main', apply=True, min_interval_seconds=0, receipt_file=receipt)
            self.assertEqual('ok', first['status'], first)

            external = root / 'external'
            subprocess.run(['git', 'clone', str(remote), str(external)], check=True, capture_output=True)
            self._git(external, 'config', 'user.name', 'External')
            self._git(external, 'config', 'user.email', 'external@example.invalid')
            (external / 'external.md').write_text('external\n', encoding='utf-8')
            self._git(external, 'add', 'external.md')
            self._git(external, 'commit', '-m', 'external')
            external_commit = self._git(external, 'rev-parse', 'HEAD')
            self._git(external, 'push', 'origin', 'main')

            changed = publish_if_due(repository, remote='origin', branch='main', apply=True, min_interval_seconds=0, receipt_file=receipt)
            self.assertEqual('halted:remote_changed', changed['status'], changed)
            self.assertEqual(external_commit, self._git(remote, 'rev-parse', 'main'))

    def test_process_restart_preserves_snapshot_chain(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            remote, repository = self._fixture(root)
            receipt = root / 'receipt.json'
            script = (
                'import json, sys\n'
                'from pathlib import Path\n'
                'from respectedbrain.maintenance.backup.publish_git_snapshot import publish_if_due\n'
                'result = publish_if_due(Path(sys.argv[1]), remote="origin", branch="main", apply=True, min_interval_seconds=0, receipt_file=Path(sys.argv[2]))\n'
                'print(json.dumps(result))\n'
            )
            commits = []
            note = repository / 'note.md'
            for content in ('first\n', 'second\n', 'third\n'):
                note.write_text(content, encoding='utf-8')
                process = subprocess.run(
                    [sys.executable, '-c', script, str(repository), str(receipt)],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                result = json.loads(process.stdout)
                self.assertEqual('ok', result['status'], result)
                commits.append(result['commit'])
            self.assertEqual(commits[0], self._git(remote, 'rev-parse', f'{commits[1]}^'))
            self.assertEqual(commits[1], self._git(remote, 'rev-parse', f'{commits[2]}^'))

    def test_unchanged_note_still_creates_fast_forward_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            remote, repository = self._fixture(root)
            receipt = root / 'receipt.json'
            first = publish_if_due(repository, remote='origin', branch='main', apply=True, min_interval_seconds=0, receipt_file=receipt)
            self.assertEqual('ok', first['status'], first)
            second = publish_if_due(repository, remote='origin', branch='main', apply=True, min_interval_seconds=0, receipt_file=receipt)
            self.assertEqual('ok', second['status'], second)
            self.assertNotEqual(first['commit'], second['commit'])
            self.assertEqual(first['commit'], self._git(remote, 'rev-parse', f'{second["commit"]}^'))
            self.assertEqual('first', self._git(remote, 'show', 'main:note.md'))

    def test_push_failure_retry_extends_same_verified_parent(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            remote, repository = self._fixture(root)
            receipt = root / 'receipt.json'
            first = publish_if_due(repository, remote='origin', branch='main', apply=True, min_interval_seconds=0, receipt_file=receipt)
            self.assertEqual('ok', first['status'], first)
            original_run = snapshot_module.subprocess.run
            failed_once = False

            def fail_push_once(command, **options):
                nonlocal failed_once
                if not failed_once and command[:2] == ['git', 'push']:
                    failed_once = True
                    return subprocess.CompletedProcess(command, 1, stdout='', stderr='simulated push failure')
                return original_run(command, **options)

            with mock.patch.object(snapshot_module.subprocess, 'run', side_effect=fail_push_once):
                failed = publish_if_due(repository, remote='origin', branch='main', apply=True, min_interval_seconds=0, receipt_file=receipt)
            self.assertEqual('push-failed', failed['status'], failed)
            self.assertEqual(first['commit'], json.loads(receipt.read_text(encoding='utf-8'))['commit'])
            self.assertEqual(first['commit'], self._git(remote, 'rev-parse', 'main'))

            retried = publish_if_due(repository, remote='origin', branch='main', apply=True, min_interval_seconds=0, receipt_file=receipt)
            self.assertEqual('ok', retried['status'], retried)
            self.assertEqual(first['commit'], self._git(remote, 'rev-parse', f'{retried["commit"]}^'))


if __name__ == '__main__': unittest.main()
