"""MCP editor registration safety through readonly plans and CAS writes."""
import json
from pathlib import Path
from unittest import TestCase
from tests.support.fakes import IntegrationFixture
from tests.support.files import snapshot
from respected_brain.integrations.rendering import plan_integrations
from respected_brain.core.errors import OwnershipConflict

class TestMcpRegistration(IntegrationFixture, TestCase):
    def apply(self, rows):
        backend = self.backend()
        for row in rows:
            backend.apply(row)

    def test_a_tool_that_is_not_on_the_computer_is_left_alone(self):
        import shutil
        for name in (".codex", ".gemini", ".cursor", ".codeium", "AppData/Roaming/Claude"):
            shutil.rmtree(self.home / name)
        before = snapshot(self.root)
        rows = plan_integrations(self.ctx, self.profile, {"global": True, "mcp": True}, self.backend())
        self.assertEqual(snapshot(self.root), before)
        self.assertTrue(rows)
        for row in (row for row in rows if Path(row.key).is_relative_to(self.home)):
            for absent in (".codex", ".gemini", ".cursor", ".codeium", "Claude"):
                self.assertNotIn(absent, Path(row.key).relative_to(self.home).parts[:3], row.key)
        self.apply(rows)
        self.assertFalse(any((self.home / name).exists() for name in (".codex", ".gemini", ".cursor", ".codeium", "AppData/Roaming/Claude")))

    def test_one_apply_settles_every_selected_tool(self):
        desired = {"global": True, "mcp": True}
        self.apply(plan_integrations(self.ctx, self.profile, desired, self.backend()))
        self.assertEqual(plan_integrations(self.ctx, self.profile, desired, self.backend()), ())

    def test_update_mcp_json_preserves_existing_servers(self):
        path = self.home / ".cursor/mcp.json"
        path.parent.mkdir(exist_ok=True)
        original = {"mcpServers": {"existing_mcp": {"command": "npx", "args": ["-y", "some-tool"]}}, "other_setting": True}
        path.write_text(json.dumps(original), encoding="utf-8")
        self.apply(plan_integrations(self.ctx, self.profile, {"mcp": True}, self.backend()))
        loaded = json.loads(path.read_text(encoding="utf-8"))
        self.assertTrue(loaded["other_setting"])
        self.assertEqual(loaded["mcpServers"]["existing_mcp"], original["mcpServers"]["existing_mcp"])
        entry = loaded["mcpServers"]["respected-brain"]
        self.assertEqual(entry["command"], str(self.app / "respected-brain.exe"))
        self.assertEqual(entry["args"], ["mcp", "--vault-id", self.ctx.paths.vault_id])

    def test_register_all_editors_in_fake_environment(self):
        cline = self.home / "AppData/Roaming/Code/User/globalStorage/saoudrizwan.claude-dev"
        cline.mkdir(parents=True)
        roo = cline.with_name("rooveterinaryinc.roo-cline")
        roo.mkdir(exist_ok=True)
        self.apply(plan_integrations(self.ctx, self.profile, {"mcp": True}, self.backend()))
        for path in (self.home / ".claude.json", self.home / ".cursor/mcp.json", self.home / ".codeium/windsurf/mcp_config.json", self.home / "AppData/Roaming/Claude/claude_desktop_config.json", cline / "settings/cline_mcp_settings.json", roo / "settings/roo_mcp_settings.json"):
            self.assertIn("respected-brain", json.loads(path.read_text(encoding="utf-8"))["mcpServers"])

    def test_disabled_client_registration_leaves_every_user_file_unchanged(self):
        before = snapshot(self.root)
        self.assertEqual(plan_integrations(self.ctx, self.profile, {"mcp": False}, self.backend()), ())
        self.assertEqual(snapshot(self.root), before)

    def test_corrupt_json_fails_closed_without_mutating_preview(self):
        path = self.home / ".cursor/mcp.json"
        path.parent.mkdir(exist_ok=True)
        path.write_bytes(b"{ this is not valid json : ;")
        before = snapshot(self.root)
        with self.assertRaises(ValueError):
            plan_integrations(self.ctx, self.profile, {"mcp": True}, self.backend())
        self.assertEqual(snapshot(self.root), before)

    def test_antigravity_dual_registration(self):
        (self.home / ".gemini").mkdir(exist_ok=True)
        rows = plan_integrations(self.ctx, self.profile, {"mcp": True}, self.backend())
        self.apply(rows)
        path = self.home / ".gemini/config/mcp_config.json"
        self.assertIn("respected-brain", json.loads(path.read_text(encoding="utf-8"))["mcpServers"])
        directory = self.home / ".gemini/antigravity-ide/mcp/respected-brain"
        self.assertTrue((directory / "instructions.md").is_file())
        tool = json.loads((directory / "respected_search.json").read_text(encoding="utf-8"))
        self.assertEqual(tool["name"], "respected_search")
        self.assertEqual(tool["parameters"]["type"], "object")


class TestMcpServerName(IntegrationFixture, TestCase):

    def test_the_server_introduces_itself_by_the_product_name(self):
        from respected_brain.integrations.mcp.server import RespectedMcpServer
        self.assertEqual(RespectedMcpServer.SERVER_NAME, "Respected Brain")
