"""Entry-level undo of client config changes (JSON, TOML, Markdown) and minimal retention of config content."""
import json
import tempfile
import unittest
from pathlib import Path

from respectedbrain.installation.ownership import OwnershipManifest, manifest_document, read_manifest
from respectedbrain.installation.transaction import Transaction, scrub_committed_journals
from respectedbrain.integrations import delta
from respectedbrain.integrations.backend import ExternalChange
from tests.foundation_transactions_test import Backend

SECRET = "sk-live-" + "9f8e7d6c5b4a39281706"


def j(value) -> bytes:
    return json.dumps(value, indent=2).encode("utf-8")


OURS_MCP = {"command": "C:/app/respectedbrain.exe", "args": ["mcp"]}
OURS_HOOK = {"hooks": [{"type": "command", "command": "C:/app/respectedbrain.exe hook"}]}
CLAUDE_BEFORE = {"numStartups": 3, "mcpServers": {"github": {"command": "npx", "env": {"GITHUB_TOKEN": SECRET}}}, "hooks": {"Stop": [{"hooks": [{"type": "command", "command": "other"}]}]}}
CLAUDE_AFTER = {**CLAUDE_BEFORE, "mcpServers": {**CLAUDE_BEFORE["mcpServers"], "respected-vault": OURS_MCP},
                "hooks": {"Stop": [*CLAUDE_BEFORE["hooks"]["Stop"], OURS_HOOK]}}


class JsonDeltaTest(unittest.TestCase):
    def setUp(self):
        self.change = ExternalChange("mcp", "C:/home/.claude.json", j(CLAUDE_BEFORE), j(CLAUDE_AFTER))
        self.compact = self.change.compact()

    def test_the_delta_keeps_only_our_entries_and_no_unrelated_secret(self):
        self.assertIsNone(self.compact.before)
        self.assertIsNone(self.compact.after)
        self.assertNotIn(SECRET.encode(), self.compact.delta)
        self.assertNotIn(b"github", self.compact.delta)
        self.assertIn(b"respected-vault", self.compact.delta)
        self.assertEqual(self.compact.after_sha256, delta.sha256(j(CLAUDE_AFTER)))

    def test_undo_removes_only_our_entries_after_the_client_rewrote_the_file(self):
        rewritten = {**CLAUDE_AFTER, "numStartups": 99, "projects": {"C:/p": {"trusted": True}},
                     "mcpServers": {**CLAUDE_AFTER["mcpServers"], "figma": {"url": "https://x", "env": {"KEY": "k"}}}}
        rewritten["hooks"]["Stop"] = [*rewritten["hooks"]["Stop"], {"hooks": [{"type": "command", "command": "user-added"}]}]
        restored = json.loads(self.compact.undo(j(rewritten)))
        self.assertNotIn("respected-vault", restored["mcpServers"])
        self.assertEqual(restored["mcpServers"]["github"]["env"]["GITHUB_TOKEN"], SECRET)       # others' secrets stay where they were
        self.assertEqual(restored["mcpServers"]["figma"], rewritten["mcpServers"]["figma"])
        self.assertEqual(restored["numStartups"], 99)
        self.assertEqual(restored["projects"], rewritten["projects"])
        commands = [h["command"] for entry in restored["hooks"]["Stop"] for h in entry["hooks"]]
        self.assertEqual(commands, ["other", "user-added"])

    def test_a_user_edit_of_our_own_entry_is_a_conflict_and_a_removed_entry_is_not(self):
        edited = json.loads(j(CLAUDE_AFTER))
        edited["mcpServers"]["respected-vault"]["command"] = "C:/evil/other.exe"
        with self.assertRaises(ValueError):
            self.compact.undo(j(edited))
        gone = json.loads(j(CLAUDE_AFTER))
        del gone["mcpServers"]["respected-vault"]
        self.assertEqual(json.loads(self.compact.undo(j(gone)))["mcpServers"], CLAUDE_BEFORE["mcpServers"])

    def test_restored_detection_uses_fingerprints_and_an_unrelated_file_is_never_rewritten(self):
        self.assertTrue(self.compact.restored(j(CLAUDE_BEFORE)))
        self.assertTrue(self.compact.untouched_since(j(CLAUDE_AFTER)))
        clean = j({**CLAUDE_BEFORE, "numStartups": 4})
        self.assertEqual(self.compact.undo(clean), clean)           # nothing of ours: same bytes back, no reformatting

    def test_a_file_we_created_is_removed_unless_someone_added_content(self):
        created = ExternalChange("mcp", "C:/home/.cursor/mcp.json", None, j({"mcpServers": {"respected-vault": OURS_MCP}})).compact()
        self.assertIsNone(created.undo(j({"mcpServers": {"respected-vault": OURS_MCP}})))
        kept = json.loads(created.undo(j({"mcpServers": {"respected-vault": OURS_MCP, "other": {"command": "x"}}})))
        self.assertEqual(kept, {"mcpServers": {"other": {"command": "x"}}})


CODEX_BEFORE = (b'# my config\nmodel = "gpt"\n\n[projects."C:/a"]\ntrust_level = "trusted"\n\n[mcp_servers.other]\ncommand = "y"\nenv = { TOKEN = "' + SECRET.encode() + b'" }\n')
CODEX_BLOCK = b'\n[mcp_servers.respected-vault]\ncommand = "C:/app/respectedbrain.exe"\nargs = ["mcp"]\n'
CODEX_AFTER = CODEX_BEFORE + CODEX_BLOCK


class TextDeltaTest(unittest.TestCase):
    def setUp(self):
        self.compact = ExternalChange("mcp", "C:/home/.codex/config.toml", CODEX_BEFORE, CODEX_AFTER).compact()

    def test_toml_delta_holds_only_our_block(self):
        self.assertNotIn(SECRET.encode(), self.compact.delta)
        self.assertNotIn(b"trusted", self.compact.delta)
        self.assertIn(b"respected-vault", self.compact.delta)

    def test_toml_undo_survives_codex_adding_projects_and_keeps_every_other_byte(self):
        rewritten = CODEX_AFTER + b'\n[projects."C:/new"]\ntrust_level = "trusted"\n'
        restored = self.compact.undo(rewritten)
        self.assertNotIn(b"respected-vault", restored)
        self.assertEqual(restored, CODEX_BEFORE + b'\n[projects."C:/new"]\ntrust_level = "trusted"\n')
        edited = CODEX_AFTER.replace(b"C:/app/respectedbrain.exe", b"C:/evil/x.exe")
        with self.assertRaises(ValueError):
            self.compact.undo(edited)
        removed_by_user = CODEX_BEFORE + b"# user cleaned up\n"
        self.assertEqual(self.compact.undo(removed_by_user), removed_by_user)

    def test_markdown_block_is_undone_inside_a_file_the_user_kept_editing(self):
        before = b"# Notes\n\nmy own rules\n"
        block = b"<!-- RESPECTED:BEGIN -->\nuse the vault\n<!-- RESPECTED:END -->\n"
        compact = ExternalChange("file", "C:/home/CLAUDE.md", before, before + b"\n" + block).compact()
        current = b"# Notes (edited)\n\nmy own rules\nmore rules\n\n" + block
        self.assertEqual(compact.undo(current), b"# Notes (edited)\n\nmy own rules\nmore rules\n")
        with self.assertRaises(ValueError):
            compact.undo(current.replace(b"use the vault", b"use my edited text"))


class PersistedFormTest(unittest.TestCase):
    def test_manifest_and_committed_journal_never_hold_a_complete_config_copy(self):
        change = ExternalChange("mcp", "C:/home/.claude.json", j(CLAUDE_BEFORE), j(CLAUDE_AFTER))
        document = manifest_document(OwnershipManifest(3, (), (change,)))
        self.assertNotIn(SECRET, json.dumps(document))
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "m.json"
            path.write_text(json.dumps(document), encoding="utf-8")
            loaded = read_manifest(path).external[0]
            self.assertEqual(json.loads(loaded.undo(j(CLAUDE_AFTER)))["mcpServers"], CLAUDE_BEFORE["mcpServers"])
            data = Path(tmp) / "data"
            backend = Backend()
            backend.records[("mcp", change.key)] = change.before
            with Transaction(data, backend) as tx:
                tx.apply_external(change)
                journal = tx.journal
                self.assertIn(SECRET, journal.read_text(encoding="utf-8").replace("\\", "") + __import__("base64").b64decode(
                    tx.document["external"][0]["before"]).decode())        # while the transaction can still roll back it needs the images
                tx.commit()
            stored = journal.read_text(encoding="utf-8")
            self.assertNotIn("before", json.loads(stored)["external"][0])
            import base64
            for token in (SECRET, base64.b64encode(SECRET.encode()).decode()):
                self.assertNotIn(token, stored)
            # journals written by older versions are scrubbed too
            legacy = json.loads(stored)
            legacy["external"] = [{"kind": "mcp", "key": change.key, "before": base64.b64encode(change.before).decode(),
                                   "after": base64.b64encode(change.after).decode()}]
            journal.write_text(json.dumps(legacy), encoding="utf-8")
            self.assertEqual(scrub_committed_journals(data), 1)
            self.assertNotIn("before", json.loads(journal.read_text(encoding="utf-8"))["external"][0])
            self.assertEqual(scrub_committed_journals(data), 0)


if __name__ == "__main__":
    unittest.main()
