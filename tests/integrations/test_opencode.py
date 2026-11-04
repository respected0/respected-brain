"""OpenCode: read-only detection, opencode.json MCP registration, local plugin and capture bridge."""
import contextlib
import io
import json
from pathlib import Path
import shutil
import subprocess
from unittest import TestCase

from respected_brain.core.errors import OwnershipConflict
from respected_brain.integrations import rendering
from respected_brain.integrations.hooks import bridge
from respected_brain.memory import flush
from tests.support.fakes import IntegrationFixture


class OpenCodeFixture(IntegrationFixture):

    def setUp(self):
        super().setUp()
        (self.home / ".config/opencode").mkdir(parents=True)

    def apply(self, rows):
        backend = self.backend()
        for row in rows:
            backend.apply(row)
        return backend


class DetectionAndMcpTest(OpenCodeFixture, TestCase):

    def test_opencode_is_detected_from_its_config_folder(self):
        self.assertTrue(rendering.detect_clients(self.profile)["opencode"])
        self.assertEqual(rendering.mcp_client_of(self.home / ".config/opencode/opencode.json"), "opencode")

    def test_mcp_registration_uses_the_local_shape_and_preserves_other_keys(self):
        path = self.home / ".config/opencode/opencode.json"
        path.write_text(json.dumps({"theme": "dark", "mcp": {"other": {"type": "remote", "url": "https://example.test"}}}), encoding="utf-8")
        self.apply(rendering.plan_integrations(self.ctx, self.profile, {"mcp": True, "clients": ["opencode"]}, self.backend()))
        document = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(document["theme"], "dark")
        self.assertEqual(document["mcp"]["other"], {"type": "remote", "url": "https://example.test"})
        entry = document["mcp"]["respected-brain"]
        self.assertEqual(entry["type"], "local")
        self.assertTrue(entry["enabled"])
        self.assertEqual(entry["command"], [str(self.app / "respected-brain.exe"), "mcp", "--vault-id", self.ctx.paths.vault_id])
        self.assertEqual(rendering.plan_integrations(self.ctx, self.profile, {"mcp": True, "clients": ["opencode"]}, self.backend()), ())

    def test_a_different_existing_registration_is_a_conflict(self):
        path = self.home / ".config/opencode/opencode.json"
        path.write_text(json.dumps({"mcp": {"respected-brain": {"type": "local", "command": ["someone-else"]}}}), encoding="utf-8")
        with self.assertRaises(OwnershipConflict):
            rendering.plan_integrations(self.ctx, self.profile, {"mcp": True, "clients": ["opencode"]}, self.backend())

    def test_a_machine_without_opencode_is_not_given_its_folder(self):
        shutil.rmtree(self.home / ".config/opencode")
        rows = rendering.plan_integrations(self.ctx, self.profile, {"mcp": True, "clients": ["opencode"]}, self.backend())
        self.assertFalse(any(str(row.key).endswith("opencode.json") for row in rows))
        self.assertFalse((self.home / ".config/opencode").exists())


class PluginTest(OpenCodeFixture, TestCase):

    def plan(self):
        return rendering.plan_integrations(self.ctx, self.profile, {"global": True, "clients": ["opencode"]}, self.backend())

    def test_the_plugin_is_installed_filled_and_stable(self):
        self.apply(self.plan())
        path = self.home / ".config/opencode/plugins/respected-brain.js"
        source = path.read_text(encoding="utf-8")
        self.assertNotIn("__COMMAND__", source)
        self.assertNotIn("__TRANSCRIPT_DIRECTORY__", source)
        self.assertIn(json.dumps(str(self.app / "respected-brain.exe"))[1:-1], source)
        self.assertIn("--provider\", \"opencode\"", source)
        self.assertIn(str(self.ctx.paths.data_root / "vaults" / self.ctx.paths.vault_id / "integrations/opencode/transcripts").replace("\\", "\\\\"), source)
        self.assertEqual(self.plan(), ())

    def test_the_rendered_plugin_is_valid_javascript(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("node is not installed")
        self.apply(self.plan())
        result = subprocess.run([node, "--check", str(self.home / ".config/opencode/plugins/respected-brain.js")], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


class V2HookTest(OpenCodeFixture, TestCase):

    def test_the_v2_context_hook_appends_a_system_text_part(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("node is not installed")
        helper = self.root / "context-helper.js"
        helper.write_text('process.stdout.write(JSON.stringify({additionalContext: "memory"}))\n', encoding="utf-8")
        source = self.ctx.resources.read_text("integrations/opencode-plugin.js")
        source = source.replace("__COMMAND__", json.dumps([node, str(helper)])).replace(
            "__TRANSCRIPT_DIRECTORY__", json.dumps(str(self.root / "transcripts")))
        plugin = self.root / "plugin.mjs"
        plugin.write_text(source, encoding="utf-8")
        harness = self.root / "harness.mjs"
        harness.write_text(
            "import * as plugin from " + json.dumps(plugin.as_uri()) + ";\n"
            "const hooks = {};\n"
            "const ctx = {session: {hook(name, fn) { hooks[name] = fn; return {dispose() {}}; }},\n"
            "  event: {subscribe({signal}) { return (async function* () { while (!signal.aborted) await new Promise(r => setTimeout(r, 5)); })(); }}};\n"
            "const dispose = await plugin.default.setup(ctx);\n"
            "const input = {sessionID: 'ses-1', system: []};\n"
            "await hooks.context(input);\n"
            "process.stdout.write(JSON.stringify(input.system));\n"
            "await dispose();\n",
            encoding="utf-8")
        result = subprocess.run([node, str(harness)], capture_output=True, text=True, timeout=60)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), [{"type": "text", "text": "memory"}])


class BridgeAndTranscriptTest(OpenCodeFixture, TestCase):

    def test_opencode_output_is_additional_context(self):
        for context, expected in (("memory", {"additionalContext": "memory"}), ("", {})):
            with self.subTest(context=context):
                stream = io.StringIO()
                with contextlib.redirect_stdout(stream):
                    bridge.output("opencode", "start", context)
                self.assertEqual(json.loads(stream.getvalue()), expected)

    def test_opencode_payload_keeps_its_provider_and_session(self):
        payload = bridge.normalize("opencode", {"session_id": "ses-1", "cwd": str(self.root)}, vault_root=self.vault)
        self.assertEqual(payload["respected_provider"], "opencode")
        self.assertEqual(payload["session_id"], "ses-1")

    def test_the_plugin_transcript_is_recognised_and_read(self):
        path = self.ctx.paths.data_root / "vaults" / self.ctx.paths.vault_id / "integrations/opencode/transcripts/ses-1.jsonl"
        path.parent.mkdir(parents=True)
        path.write_text(
            json.dumps({"message": {"role": "user", "content": "kalici karar"}}) + "\n"
            + json.dumps({"message": {"role": "assistant", "content": "not edildi"}}) + "\n",
            encoding="utf-8",
        )
        self.assertEqual(flush._transcript_provider(path), "opencode")
        self.assertEqual(flush.read_transcript(path), [("user", "kalici karar"), ("assistant", "not edildi")])


if __name__ == "__main__":
    import unittest
    unittest.main()
