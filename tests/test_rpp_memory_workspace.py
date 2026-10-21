"""Hub-facing memory workspace ops (search, read, quick capture, briefing) through rpp.serve; temporary directories only."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from respectedbrain.rpp import server as rpp
from respectedbrain.core.config import ConfigStore
from respectedbrain.rpp.integrations import _context
from respectedbrain.search import freshness


class WorkspaceTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="rpp-ws-")
        self.addCleanup(temporary.cleanup)
        base = Path(temporary.name).resolve()
        self.data, self.vault = base / "data", base / "vault"
        self.data.mkdir()
        (self.vault / "notes").mkdir(parents=True)
        (self.vault / "notes" / "zebra.md").write_text("# Zebra\nThe zebra crosses the road.\n", encoding="utf-8")
        (self.vault / "notes" / "secret.txt").write_text("not a note", encoding="utf-8")
        patcher = patch.dict(os.environ, {"RESPECTED_APP_DIR": str(base / "app"), "RESPECTED_DATA_DIR": str(self.data)})
        patcher.start()
        self.addCleanup(patcher.stop)

        def mutate(document):
            vault_id = str(uuid4())
            document["vaults"][vault_id] = {"path": str(self.vault)}
            document["active_vault_id"] = vault_id
        ConfigStore(self.data).update(mutate)
        _, ctx = _context(self.data, {})
        freshness.refresh_now(ctx)

    def call(self, op, payload=None, operation_id=None):
        request = {"rpp": "1.1", "op": op, "payload": payload or {}}
        if operation_id:
            request["operation_id"] = operation_id
        return rpp.serve(json.dumps(request), data_root=str(self.data))

    def test_search_needs_no_token_and_returns_snippets(self):
        found = self.call("memory.search", {"query": "zebra"})
        self.assertTrue(found["ok"], found)
        self.assertEqual([r["path"] for r in found["result"]["results"]], ["notes/zebra.md"])
        self.assertEqual(self.call("memory.search", {"query": "zebra", "path": "x"})["error"]["code"], "BAD_REQUEST")
        self.assertEqual(self.call("memory.search", {"query": "   "})["error"]["code"], "BAD_REQUEST")
        self.assertEqual(self.call("memory.search", {"query": "zebra"})["result"]["search"]["mode"], "fts")

    def test_read_is_limited_to_markdown_notes_inside_the_vault(self):
        ok = self.call("memory.note.read", {"path": "notes/zebra.md"})
        self.assertIn("zebra crosses", ok["result"]["content"])
        for bad in ("../outside.md", "notes/secret.txt", "C:/Windows/win.ini", "/etc/passwd", "notes\\..\\..\\x.md"):
            self.assertFalse(self.call("memory.note.read", {"path": bad})["ok"], bad)
        self.assertEqual(self.call("memory.note.read", {"path": "notes/none.md"})["error"]["code"], "NOT_FOUND")

    @unittest.skipUnless(os.name == "nt", "Windows junction fixture")
    def test_read_refuses_a_junction_that_leaves_the_vault(self):
        import subprocess
        outside = self.vault.parent / "outside"
        outside.mkdir()
        (outside / "private.md").write_text("PRIVATE", encoding="utf-8")
        subprocess.run(["cmd", "/c", "mklink", "/J", str(self.vault / "notes" / "link"), str(outside)], capture_output=True, check=True)
        try:
            reply = self.call("memory.note.read", {"path": "notes/link/private.md"})
            self.assertFalse(reply["ok"], reply)
            self.assertNotIn("PRIVATE", json.dumps(reply))
        finally:
            os.rmdir(self.vault / "notes" / "link")

    @unittest.skipUnless(os.name == "nt", "Windows console code page")
    def test_non_ascii_note_names_survive_the_rpp_stdin_of_the_real_command(self):
        import subprocess
        import sys
        (self.vault / "notes" / "hızlı not.md").write_text("# Hızlı\nçalışıyor\n", encoding="utf-8")
        env = {k: v for k, v in os.environ.items() if k not in ("PYTHONUTF8", "PYTHONIOENCODING")}
        env["PYTHONPATH"] = str(Path(__file__).resolve().parents[1] / "src")
        request = json.dumps({"rpp": "1.1", "op": "memory.note.read", "payload": {"path": "notes/hızlı not.md"}}, ensure_ascii=False)
        done = subprocess.run([sys.executable, "-m", "respectedbrain", "rpp", "--data-root", str(self.data)], input=request.encode("utf-8"), capture_output=True, env=env, timeout=60)
        reply = json.loads(done.stdout.decode("utf-8").strip().splitlines()[-1])
        self.assertTrue(reply["ok"], reply)
        self.assertIn("çalışıyor", reply["result"]["content"])

    def test_quick_capture_creates_one_new_searchable_note_and_is_idempotent(self):
        before = {p: p.read_bytes() for p in self.vault.rglob("*") if p.is_file()}
        first = self.call("memory.capture.note", {"title": "Idea", "content": "Buy a marmalade jar", "tags": ["idea"]}, "op-note-0001")
        self.assertTrue(first["ok"], first)
        note = self.vault / first["result"]["path"]
        self.assertTrue(note.is_file() and "Inbox" in first["result"]["path"] and "Dump" in first["result"]["path"])
        self.assertIn("source: hub_quick_capture", note.read_text(encoding="utf-8"))
        self.assertTrue(first["result"]["indexed"])
        self.assertEqual({p: p.read_bytes() for p in before}, before)  # nothing existing changed
        again = self.call("memory.capture.note", {"title": "Idea", "content": "Buy a marmalade jar", "tags": ["idea"]}, "op-note-0001")
        self.assertTrue(again["result"]["replayed"])
        self.assertEqual(len(list((self.vault / "📥 000-Inbox" / "Dump").glob("*.md"))), 1)
        self.assertEqual(self.call("memory.capture.note", {"content": "other"}, "op-note-0001")["error"]["code"], "OPERATION_ID_CONFLICT")
        self.assertEqual(self.call("memory.search", {"query": "marmalade"})["result"]["count"], 1)

    def test_capture_rejects_paths_empty_and_oversize_content(self):
        for payload in ({"content": "x", "path": "../x.md"}, {"content": "  "}, {"content": "x" * 20_001}, {"content": "x", "tags": ["a b"]}):
            self.assertEqual(self.call("memory.capture.note", payload, "op-note-0002")["error"]["code"], "BAD_REQUEST", payload)

    def test_briefing_needs_confirmation(self):
        self.assertEqual(self.call("memory.briefing.run", {})["error"]["code"], "BAD_REQUEST")
        with patch("respectedbrain.briefing.service.run_if_due", return_value=0), patch("respectedbrain.providers.runner.ModelRunner"):
            self.assertEqual(self.call("memory.briefing.run", {"confirm": True})["result"], {"status": 0})

    def test_v10_manifest_hides_the_workspace_capability(self):
        old = rpp.serve(json.dumps({"rpp": "1.0", "op": "manifest"}), data_root=str(self.data))["result"]
        self.assertNotIn("memory_workspace", old["capabilities"])


if __name__ == "__main__":
    unittest.main()
