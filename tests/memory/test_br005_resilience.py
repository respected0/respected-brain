"""BR-005: bounded capture failures and hook isolation."""
import datetime as dt
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from respected_brain.core.context import ModelResult
from respected_brain.memory import flush as F
from respected_brain.memory import lifecycle as L
from tests.support.files import make_context

SID = '12345678-1234-4123-8123-123456789abc'
NOW = dt.datetime(2026, 10, 8, 12, 0, tzinfo=dt.timezone.utc)
SUMMARY = '\n'.join('## ' + section + '\nORIGINAL' for section in F.EXPECTED_SECTIONS)


class Model:
    def __init__(self):
        self.calls = 0

    def run(self, prompt, **kwargs):
        self.calls += 1
        return ModelResult(SUMMARY, 'codex', None)


class FailingModel:
    def __init__(self, code):
        self.code = code
        self.calls = 0

    def run(self, prompt, **kwargs):
        self.calls += 1
        return ModelResult(None, 'codex', self.code)


class Br005ResilienceTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='br005-')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.ctx = make_context(self.root, self.root / 'vault-a')
        self.vault = self.ctx.paths.vault_root
        self.state = self.ctx.paths.state_dir
        self.state.mkdir(parents=True)
        self.home = self.root / 'home'
        self.sessions = self.home / '.codex/sessions'
        self.sessions.mkdir(parents=True)
        self.daily = self.vault / 'daily/2026-10-08.md'
        self.transcript_path = self.sessions / f'rollout-{SID}.jsonl'
        env = mock.patch.dict(os.environ, {'RESPECTED_PROVIDER': 'codex'})
        env.start()
        self.addCleanup(env.stop)

    def write(self, text=None):
        records = [{'type': 'session_meta', 'payload': {'id': SID, 'cwd': str(self.vault)}}]
        if text is not None:
            records.append({'role': 'user', 'content': text})
        self.transcript_path.write_text(
            '\n'.join(json.dumps(record) for record in records) + '\n', encoding='utf-8'
        )
        os.utime(self.transcript_path, (NOW.timestamp() - 60, NOW.timestamp() - 60))
        return self.transcript_path

    def write_malformed(self):
        self.transcript_path.write_text(
            json.dumps({'type': 'session_meta', 'payload': {'id': SID, 'cwd': str(self.vault)}})
            + '\n{not-json\n',
            encoding='utf-8',
        )
        os.utime(self.transcript_path, (NOW.timestamp() - 60, NOW.timestamp() - 60))
        return self.transcript_path

    def flush(self, path, model=None, when=NOW):
        return F.flush_transcript(
            self.ctx, session_id=SID, transcript=path, model=model or Model(), now=when
        )

    def catch(self, model=None, when=NOW):
        return F.catch_up_unflushed_sessions(
            self.ctx, model=model or Model(), now=when, home=self.home
        )

    def state_payload(self):
        path = F._session_state_path(self.state, SID)
        return json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}

    def health(self):
        path = self.state / 'health.json'
        return json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}

    def test_malformed_transcript_is_recorded_as_bounded_failure(self):
        path = self.write_malformed()
        model = Model()
        self.assertEqual(self.flush(path, model), 1)
        self.assertEqual(model.calls, 0)
        self.assertFalse(self.daily.exists())
        state = self.state_payload()
        self.assertEqual(state['status'], 'fail')
        self.assertEqual(state['detail'], 'transcript-jsonl-invalid')
        self.assertEqual(state['attempts'], 1)
        self.assertEqual(self.health()['error'], 'transcript-jsonl-invalid')

    def test_malformed_catch_up_is_bounded_without_model_or_daily_write(self):
        self.write_malformed()
        model = Model()
        self.assertEqual(self.catch(model), 0)
        self.assertEqual(self.state_payload()['attempts'], 1)
        self.assertEqual(self.catch(model), 0)
        self.assertEqual(self.state_payload()['attempts'], 2)
        self.assertEqual(self.catch(model), 0)
        self.assertEqual(model.calls, 0)
        self.assertFalse(self.daily.exists())
        report = json.loads((self.state / 'catch-up-report.json').read_text(encoding='utf-8'))
        self.assertIn('failure-bound', [entry['reason'] for entry in report['skipped']])

    def test_persistent_model_failure_is_bounded_after_two_attempts(self):
        for code in ('provider-timeout', 'provider-quota-exceeded'):
            with self.subTest(code=code):
                sid = SID
                F._session_state_path(self.state, sid).unlink(missing_ok=True)
                daily = self.vault / 'daily/2026-10-08.md'
                daily.unlink(missing_ok=True)
                path = self.write('SECRET-BODY-' + code)
                model = FailingModel(code)
                self.assertEqual(self.flush(path, model), 1)
                self.assertEqual(self.catch(model), 0)
                self.assertEqual(self.state_payload()['attempts'], 2)
                self.assertEqual(self.catch(model), 0)
                self.assertEqual(model.calls, 2)
                self.assertFalse(daily.exists())
                report = json.loads((self.state / 'catch-up-report.json').read_text(encoding='utf-8'))
                self.assertIn('failure-bound', [entry['reason'] for entry in report['skipped']])

    def test_closed_terminal_records_launch_failure_without_raising(self):
        with mock.patch.object(L.subprocess, 'Popen', side_effect=OSError('closed terminal')):
            self.assertFalse(L._launch_flush(self.ctx, 'codex'))
            result = L.handle_event(
                self.ctx, event='end', session_id=SID, transcript=None,
                payload={'provider': 'codex'}, now=NOW,
            )
        self.assertEqual(result, '')
        self.assertEqual(self.health()['error'], 'flush-launch-failed')

    def test_bridge_exception_keeps_native_json_and_records_health(self):
        from respected_brain.integrations.hooks import bridge
        with mock.patch.object(L, 'handle_event', side_effect=RuntimeError('fixture failure')):
            response = bridge.dispatch(
                self.ctx, provider='cursor', event='end', argv=[],
                stdin=json.dumps({'session_id': SID, 'cwd': str(self.vault)}),
            )
        self.assertEqual(json.loads(response), {})
        self.assertTrue(self.health()['error'].startswith('bridge-error:'))


if __name__ == '__main__':
    unittest.main()