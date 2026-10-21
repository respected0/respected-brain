"""The Codex notifier forwards to the original handler and only flushes sessions it can resolve."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from respectedbrain.core.errors import BusyError
from respectedbrain.integrations.hooks import codex_notify
from tests.support.files import make_context


class PayloadParsingTest(unittest.TestCase):
    def test_json_argument_is_found_among_other_arguments(self):
        self.assertEqual(codex_notify._parse_payload(["", "plain", '{"thread-id": "t1"}']), {"thread-id": "t1"})

    def test_payload_split_across_arguments_is_joined(self):
        self.assertEqual(codex_notify._parse_payload(['{"a":', '1}']), {"a": 1})

    def test_non_object_or_broken_json_yields_empty_payload(self):
        for argv in ([], [""], ["[1]"], ["{broken}"], ["{", "}"]):
            with self.subTest(argv=argv):
                self.assertEqual(codex_notify._parse_payload(argv), {})

    def test_chain_file_option_is_split_from_payload_arguments(self):
        self.assertEqual(codex_notify._chain_file_and_payload(["--chain-file", "c.json", "{}"]), (Path("c.json"), ["{}"]))
        self.assertEqual(codex_notify._chain_file_and_payload(["{}"]), (None, ["{}"]))
        self.assertEqual(codex_notify._chain_file_and_payload(["{}", "--chain-file"]), (None, ["{}", "--chain-file"]))

    def test_windows_drive_paths_become_wsl_mounts_only_off_windows(self):
        with mock.patch.object(codex_notify.os, "name", "posix"):
            self.assertEqual(codex_notify._wsl_executable("C:\\Tools\\codex.exe"), "/mnt/c/Tools/codex.exe")
            self.assertEqual(codex_notify._wsl_executable("/usr/bin/codex"), "/usr/bin/codex")
        with mock.patch.object(codex_notify.os, "name", "nt"):
            self.assertEqual(codex_notify._wsl_executable("C:\\Tools\\codex.exe"), "C:\\Tools\\codex.exe")


class ForwardChainedTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.chain = self.root / "chain.json"
        environment = mock.patch.dict(codex_notify.os.environ, {"CODEX_NOTIFY_CHAIN": ""})
        environment.start()
        self.addCleanup(environment.stop)
        popen = mock.patch.object(codex_notify.subprocess, "Popen")
        self.popen = popen.start()
        self.addCleanup(popen.stop)

    def write_chain(self, document):
        self.chain.write_text(json.dumps(document), encoding="utf-8")

    def test_persisted_chain_receives_the_payload_arguments(self):
        self.write_chain({"argv": ["original-notify", "--flag"]})
        codex_notify._forward_chained(["--chain-file", str(self.chain), '{"x": 1}'])
        self.assertEqual(self.popen.call_args.args[0], ["original-notify", "--flag", '{"x": 1}'])

    def test_unreadable_or_malformed_chain_forwards_nothing(self):
        for document in ({"argv": []}, {"argv": [1]}, {"argv": "x"}, ["x"]):
            with self.subTest(document=document):
                self.write_chain(document)
                self.assertIsNone(codex_notify._read_persisted_chain(self.chain))
        self.chain.write_text("not json", encoding="utf-8")
        self.assertIsNone(codex_notify._read_persisted_chain(self.chain))
        self.assertIsNone(codex_notify._read_persisted_chain(self.root / "missing.json"))
        self.assertIsNone(codex_notify._read_persisted_chain(None))
        codex_notify._forward_chained(["--chain-file", str(self.chain), "{}"])
        self.popen.assert_not_called()

    def test_environment_handler_is_used_when_the_persisted_chain_fails(self):
        self.write_chain({"argv": ["original-notify"]})
        self.popen.side_effect = [OSError("gone"), None]
        with mock.patch.dict(codex_notify.os.environ, {"CODEX_NOTIFY_CHAIN": str(self.chain)}):
            codex_notify._forward_chained(["--chain-file", str(self.chain), "{}"])
        self.assertEqual(self.popen.call_args.args[0], [str(self.chain), "turn-ended", "{}"])

    def test_failing_environment_handler_is_swallowed(self):
        self.popen.side_effect = OSError("gone")
        with mock.patch.dict(codex_notify.os.environ, {"CODEX_NOTIFY_CHAIN": str(self.chain)}):
            self.chain.write_text("{}", encoding="utf-8")
            codex_notify._forward_chained(["{}"])
        self.assertEqual(self.popen.call_count, 1)

    def test_no_handler_means_nothing_is_launched(self):
        codex_notify._forward_chained(["{}"])
        self.popen.assert_not_called()


class DispatchTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.ctx = make_context(Path(temporary.name).resolve())
        self.forward = self.patch("_forward_chained")
        self.transcript = self.patch("resolve_codex_transcript", return_value="/sessions/t1.jsonl")
        self.flush = mock.patch.object(codex_notify.lifecycle, "_launch_flush").start()
        reentrant = mock.patch.object(codex_notify.lifecycle, "_is_reentrant", return_value=False)
        reentrant.start()
        self.addCleanup(mock.patch.stopall)

    def patch(self, name, **kwargs):
        return mock.patch.object(codex_notify, name, **kwargs).start()

    def dispatch(self, payload, *, argv=()):
        return codex_notify.dispatch(self.ctx, argv=[*argv, json.dumps(payload)], stdin="")

    def test_reentrant_call_does_nothing(self):
        with mock.patch.object(codex_notify.lifecycle, "_is_reentrant", return_value=True):
            self.assertEqual(self.dispatch({"thread-id": "t1"}), "")
        self.forward.assert_not_called()
        self.flush.assert_not_called()

    def test_chain_file_outside_the_selected_vault_is_refused(self):
        with self.assertRaises(ValueError):
            self.dispatch({}, argv=["--chain-file", str(self.ctx.paths.data_root / "other.json")])
        self.forward.assert_not_called()

    def test_resolved_thread_is_flushed_with_normalized_payload(self):
        self.assertEqual(self.dispatch({"thread_id": "t1", "cwd": "/work"}), "")
        _, provider = self.flush.call_args.args
        payload = self.flush.call_args.kwargs["payload"]
        self.assertEqual(provider, "codex")
        self.assertEqual((payload["session_id"], payload["transcript_path"], payload["provider"], payload["cwd"]),
                         ("t1", "/sessions/t1.jsonl", "codex", "/work"))
        self.assertEqual(self.flush.call_args.kwargs["reason"], "turn")

    def test_cwd_defaults_to_the_vault_root(self):
        self.dispatch({"session_id": "t1"})
        self.assertEqual(self.flush.call_args.kwargs["payload"]["cwd"], str(self.ctx.paths.vault_root))

    def test_stdin_payload_is_used_when_no_argument_carries_one(self):
        codex_notify.dispatch(self.ctx, argv=[], stdin=json.dumps({"thread-id": "t1"}))
        self.flush.assert_called_once()

    def test_nothing_is_flushed_for_exec_clients_missing_ids_or_transcripts(self):
        self.dispatch({"client": "codex_exec", "thread-id": "t1"})
        self.dispatch({})
        self.transcript.return_value = None
        self.dispatch({"thread-id": "t1"})
        self.flush.assert_not_called()
        self.assertEqual(self.forward.call_count, 3)

    def test_busy_writer_is_not_an_error(self):
        self.flush.side_effect = BusyError("busy")
        self.assertEqual(self.dispatch({"thread-id": "t1"}), "")


if __name__ == "__main__":
    unittest.main()
