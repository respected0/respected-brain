import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from respected_brain.integrations.hooks import bridge


class HookTraceTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.dir = Path(temporary.name)
        self.ctx = SimpleNamespace(paths=SimpleNamespace(data_root=self.dir))
        patch = mock.patch.dict(os.environ)
        patch.start()
        self.addCleanup(patch.stop)
        os.environ.pop(bridge.TRACE_ENV, None)

    def rows(self, path):
        return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines()]

    def test_trace_is_off_unless_asked_for(self):
        bridge._trace(self.ctx, "codex", "start", "{}", "")
        self.assertEqual([p.name for p in self.dir.iterdir()], [])

    def test_the_variable_names_the_trace_file(self):
        target = self.dir / "trace.jsonl"
        os.environ[bridge.TRACE_ENV] = str(target)
        bridge._trace(self.ctx, "codex", "start", '{"session_id": "s"}', "{}")
        bridge._trace(self.ctx, "codex", "turn", "", "")
        self.assertEqual([(r["provider"], r["event"], r["stdin"], r["stdout"]) for r in self.rows(target)], [("codex", "start", '{"session_id": "s"}', "{}"), ("codex", "turn", "", "")])

    def test_a_file_in_the_data_folder_works_when_the_tool_trims_the_environment(self):
        target = self.dir / "trace.jsonl"
        (self.dir / bridge.TRACE_FILE).write_text(str(target) + "\n", encoding="utf-8")
        bridge._trace(self.ctx, "codex", "start", "{}", "x")
        self.assertEqual(self.rows(target)[0]["stdout"], "x")

    def test_an_unwritable_or_empty_trace_never_breaks_the_hook(self):
        os.environ[bridge.TRACE_ENV] = str(self.dir)  # a directory, not a file
        bridge._trace(self.ctx, "codex", "start", "{}", "")
        del os.environ[bridge.TRACE_ENV]
        (self.dir / bridge.TRACE_FILE).write_text("", encoding="utf-8")
        bridge._trace(self.ctx, "codex", "start", "{}", "")


if __name__ == "__main__":
    unittest.main()
