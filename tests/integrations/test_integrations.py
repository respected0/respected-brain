"""Existing integration behavior behind explicit immutable-package/data/vault context."""
from __future__ import annotations
import contextlib
import importlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from respected_brain.core.context import AppContext
from respected_brain.core.paths import AppPaths
from respected_brain.core.resources import ResourceCatalog
from respected_brain.core.errors import OwnershipConflict
from respected_brain.integrations.backend import ExternalChange, IntegrationProfile
from tests.support.files import snapshot
from tests.support.fakes import IntegrationFixture


class FoundationIntegrationsTest(IntegrationFixture, unittest.TestCase):
    @unittest.skipUnless(__import__('os').name == 'nt', 'Windows junction boundary')
    def test_external_lock_and_override_junctions_are_refused(self):
        import os
        import subprocess
        renderer = importlib.import_module('respected_brain.integrations.rendering')
        with tempfile.TemporaryDirectory() as outside_name:
            outside = Path(outside_name)
            (outside / 'instructions.md').write_text('outside instructions', encoding='utf-8')
            backend = self.backend()
            self.data.mkdir(parents=True, exist_ok=True)
            lock = self.data / 'external-locks'
            subprocess.run(['cmd', '/c', 'mklink', '/J', str(lock), str(outside)], check=True, capture_output=True)
            try:
                with self.assertRaises(OwnershipConflict):
                    backend.apply(ExternalChange('file', str(self.home / 'new.json'), None, b'new'))
                self.assertFalse((self.home / 'new.json').exists())
                self.assertEqual([p.name for p in outside.iterdir()], ['instructions.md'])
            finally:
                os.rmdir(lock)
            override = self.ctx.paths.overrides_dir
            override.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run(['cmd', '/c', 'mklink', '/J', str(override), str(outside)], check=True, capture_output=True)
            try:
                with self.assertRaises(OwnershipConflict):
                    renderer.managed_rule(self.ctx)
                with self.assertRaises(OwnershipConflict):
                    renderer.skill_writes(self.ctx, [self.home / 'skills'])
            finally:
                os.rmdir(override)

    def test_native_command_timeout_is_bounded_and_reported(self):
        import subprocess
        from respected_brain.core.errors import FoundationError
        backend = self.backend()
        with mock.patch.object(backend, '_windows'), mock.patch('respected_brain.integrations.backend.shutil.which', return_value='powershell.exe'), mock.patch('respected_brain.integrations.backend.subprocess.run', side_effect=subprocess.TimeoutExpired('powershell.exe', 30)) as command:
            with self.assertRaises(FoundationError):
                backend._powershell('fixture')
            self.assertEqual(command.call_args.kwargs['timeout'], 30)

    def test_disabled_options_produce_no_new_registration(self):
        renderer = importlib.import_module('respected_brain.integrations.rendering')
        before = snapshot(self.root)
        changes = renderer.plan_integrations(self.ctx, self.profile, {'global': False, 'mcp': False, 'schedule': False, 'shortcut': False}, self.backend())
        self.assertEqual(changes, ())
        self.assertEqual(snapshot(self.root), before)

    def test_native_hooks_and_notify_preserve_existing_user_data(self):
        renderer = importlib.import_module('respected_brain.integrations.rendering')
        codex = self.home / '.codex'
        codex.mkdir()
        original = 'My own rules\n'
        (codex / 'AGENTS.md').write_text(original, encoding='utf-8')
        (codex / 'config.toml').write_text('model = "custom"\nnotify = ["other-notifier.exe", "turn-ended"]\n', encoding='utf-8')
        before = snapshot(self.root)
        changes = renderer.plan_integrations(self.ctx, self.profile, {'global': True}, self.backend())
        self.assertEqual(snapshot(self.root), before)
        after = {row.key: row.after.decode('utf-8') for row in changes if row.after is not None}
        self.assertTrue(after[str(codex / 'AGENTS.md')].startswith(original))
        self.assertNotIn(str(codex / 'hooks.json'), after)
        bundle = next(text for key, text in after.items() if key.replace(chr(92), '/').endswith('plugin/plugin/hooks/codex.json'))
        hooks = json.loads(bundle)
        command = hooks['hooks']['SessionStart'][-1]['hooks'][0]['command']
        self.assertIn(str(self.app / 'respected-brain.exe'), command)
        self.assertIn(self.ctx.paths.vault_id, command)
        self.assertNotIn('.py', command)
        self.assertNotIn('python', command)
        self.assertIn('model = "custom"', after[str(codex / 'config.toml')])
        chain = self.ctx.paths.state_dir / 'codex-notify-chain.json'
        self.assertEqual(json.loads(after[str(chain)])['argv'], ['other-notifier.exe', 'turn-ended'])

    def test_native_mcp_preserves_unknown_servers_and_settings(self):
        renderer = importlib.import_module('respected_brain.integrations.rendering')
        path = self.home / '.cursor/mcp.json'
        path.parent.mkdir()
        path.write_text(json.dumps({'mcpServers': {'other': {'command': 'other.exe'}}, 'setting': {'keep': True}}), encoding='utf-8')
        changes = renderer.plan_integrations(self.ctx, self.profile, {'mcp': True}, self.backend())
        row = next(row for row in changes if row.key == str(path))
        document = json.loads(row.after)
        self.assertEqual(document['mcpServers']['other'], {'command': 'other.exe'})
        self.assertEqual(document['setting'], {'keep': True})
        entry = document['mcpServers']['respected-brain']
        self.assertEqual(entry['command'], str(self.app / 'respected-brain.exe'))
        self.assertEqual(entry['args'], ['mcp', '--vault-id', self.ctx.paths.vault_id])

    def test_backend_cas_restore_does_not_overwrite_user_changed_record(self):
        backend = self.backend()
        path = self.home / 'settings.json'
        path.write_bytes(b'original')
        change = ExternalChange('file', str(path), b'original', b'ours')
        backend.apply(change)
        self.assertEqual(backend.read('file', str(path)), b'ours')
        path.write_bytes(b'user edit')
        with self.assertRaises(OwnershipConflict):
            backend.restore(change)
        self.assertEqual(path.read_bytes(), b'user edit')

    def test_backend_rejects_stale_plan_before_write(self):
        backend = self.backend()
        path = self.home / 'settings.json'
        path.write_bytes(b'user edit')
        with self.assertRaises(OwnershipConflict):
            backend.apply(ExternalChange('file', str(path), b'old', b'ours'))
        self.assertEqual(path.read_bytes(), b'user edit')

    def test_uuid_instruction_override_precedes_package_defaults(self):
        renderer = importlib.import_module('respected_brain.integrations.rendering')
        override = self.ctx.paths.overrides_dir / 'instructions.md'
        override.parent.mkdir(parents=True)
        override.write_text('My personalized instructions', encoding='utf-8')
        changes = renderer.plan_integrations(self.ctx, self.profile, {'global': True}, self.backend())
        agents = next(row for row in changes if row.key == str(self.home / '.codex/AGENTS.md'))
        self.assertIn('My personalized instructions', agents.after.decode('utf-8'))

    def test_hook_protocol_uses_selected_uuid_state_and_stable_session_id(self):
        bridge = importlib.import_module('respected_brain.integrations.hooks.bridge')
        before_app = snapshot(self.app)
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            result = bridge.dispatch(self.ctx, provider='cursor', event='prompt', argv=[], stdin=json.dumps({'conversationId': 'session-one', 'cwd': str(self.root / 'project')}))
        self.assertEqual(json.loads(result), {})
        self.assertEqual(stdout.getvalue(), '')
        counts = [p for p in self.ctx.paths.state_dir.glob('prompt_count.*') if not p.name.endswith('.lock')]
        self.assertEqual(len(counts), 1)
        self.assertEqual(counts[0].read_text(encoding='utf-8').strip(), '1')
        self.assertEqual(snapshot(self.app), before_app)

    def test_mcp_stdout_is_protocol_only(self):
        module = importlib.import_module('respected_brain.integrations.mcp.server')
        output = io.StringIO()
        incoming = io.StringIO(json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': 'initialize'}) + '\n')
        with mock.patch('sys.stdin', incoming), contextlib.redirect_stdout(output):
            result = module.serve(self.ctx)
        self.assertEqual(result, 0)
        payload = json.loads(output.getvalue())
        self.assertEqual(payload['jsonrpc'], '2.0')
        self.assertEqual(payload['id'], 1)
        self.assertNotIn('DEBUG', output.getvalue())

    def test_schedule_uses_stable_uuid_and_provider_free_launcher(self):
        from respected_brain.integrations.scheduling.service import plan_schedule
        backend = mock.Mock()
        backend.read.return_value = None
        changes = plan_schedule(self.ctx, self.profile, backend)
        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0].kind, "task")
        self.assertIn(self.ctx.paths.vault_id, changes[0].key)
        text = changes[0].after.decode("utf-8")
        self.assertIn("respected-brain.exe", text)
        self.assertIn("briefing --vault-id", text)
        self.assertNotIn("python", text)
        self.assertNotIn(".py", text)
        self.assertIn("IgnoreNew", text)
        self.assertIn("StartWhenAvailable", text)

    def test_codex_notify_preserves_chained_json_argument_without_path_rewrite(self):
        from respected_brain.integrations.hooks.codex_notify import dispatch
        chain = self.ctx.paths.state_dir / "codex-notify-chain.json"
        chain.parent.mkdir(parents=True)
        chain.write_text(json.dumps({"argv": ["other.exe", "turn-ended"]}), encoding="utf-8")
        payload = json.dumps({"thread-id": "session", "client": "codex_exec", "cwd": "C:\\project"})
        with mock.patch("respected_brain.integrations.hooks.codex_notify.subprocess.Popen") as spawn:
            result = dispatch(self.ctx, argv=["--chain-file", str(chain), payload], stdin="")
        self.assertEqual(result, "")
        self.assertEqual(spawn.call_args.args[0], ["other.exe", "turn-ended", payload])

    def test_mcp_antigravity_schemas_are_planned_without_search_cache_creation(self):
        from respected_brain.integrations.rendering import plan_integrations
        (self.home / ".gemini").mkdir()
        before = snapshot(self.root)
        changes = plan_integrations(self.ctx, self.profile, {"mcp": True}, self.backend())
        names = {Path(row.key).name for row in changes}
        self.assertIn("instructions.md", names)
        self.assertIn("respected_search.json", names)
        self.assertEqual(snapshot(self.root), before)

    def test_wsl_profile_validates_launcher_inside_wsl(self):
        from respected_brain.integrations.rendering import plan_integrations
        from respected_brain.core.errors import FoundationError
        profile = IntegrationProfile("windows-wsl", ("/opt/respected-brain",), self.home)
        with mock.patch("respected_brain.integrations.rendering.subprocess.run", return_value=mock.Mock(returncode=1)) as runner:
            with self.assertRaises(FoundationError):
                plan_integrations(self.ctx, profile, {"global": True}, self.backend())
        argv = runner.call_args.args[0]
        self.assertEqual(argv[:4], ["wsl.exe", "--", "sh", "-c"])
        self.assertEqual(argv[-1], "/opt/respected-brain")

    @unittest.skipUnless(__import__("os").name == "nt", "Windows native registration")
    def test_native_task_and_shortcut_roundtrip_canonical_ownership(self):
        import uuid
        from respected_brain.integrations.backend import ExternalChange, canonical_json, canonical_task_xml
        from respected_brain.integrations.scheduling.service import _windows_xml
        from respected_brain.core.errors import FoundationError
        backend = self.backend()
        key = "RespectedBrain-FoundationTest-" + str(uuid.uuid4())
        try:
            backend._task_read("RespectedBrain-FoundationTest-Availability-" + str(uuid.uuid4()))
        except FoundationError as error:
            self.skipTest("Task Scheduler root is unavailable on this host: " + str(error))
        after = canonical_task_xml(_windows_xml(str(self.app / "respected-brain.exe"), "briefing --vault-id " + self.ctx.paths.vault_id))
        try:
            backend.apply(ExternalChange("task", key, None, after))
            self.assertEqual(backend.read("task", key), after)
            backend.restore(ExternalChange("task", key, None, after))
            self.assertIsNone(backend.read("task", key))
        finally:
            if backend.read("task", key) is not None:
                backend._write("task", key, None)
        path = self.home / "Desktop/test.lnk"
        descriptor = canonical_json({"target": str(self.app / "respected-brain.exe"), "arguments": "serve --vault-id " + self.ctx.paths.vault_id, "working_directory": str(self.app), "description": "test", "icon_location": "", "window_style": 1, "hotkey": ""})
        try:
            backend.apply(ExternalChange("shortcut", str(path), None, descriptor))
            self.assertEqual(backend.read("shortcut", str(path)), descriptor)
            backend.restore(ExternalChange("shortcut", str(path), None, descriptor))
        finally:
            path.unlink(missing_ok=True)

    @unittest.skipUnless(__import__("os").name == "nt", "Windows native registration")
    def test_native_registry_preserves_unknown_typed_values_and_children(self):
        import uuid
        import winreg
        from respected_brain.integrations.backend import ExternalChange, canonical_json
        backend = self.backend()
        key = "HKCU\\Software\\RespectedBrain-FoundationTest-" + str(uuid.uuid4())
        probe_name = "Software\\RespectedBrain-FoundationTest-Availability-" + str(uuid.uuid4())
        try:
            probe = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, probe_name, 0, winreg.KEY_WRITE)
            probe.Close()
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, probe_name)
        except OSError as error:
            self.skipTest("Native HKCU registry writes are unavailable on this host: " + str(error))
        value = {"values": {"Unknown": {"type": winreg.REG_DWORD, "data": 17}}, "subkeys": {"User": {"values": {"Binary": {"type": winreg.REG_BINARY, "data": {"base64": "AAEC"}}}, "subkeys": {}}}}
        after = canonical_json(value)
        try:
            backend.apply(ExternalChange("registry", key, None, after))
            self.assertEqual(backend.read("registry", key), after)
            backend.restore(ExternalChange("registry", key, None, after))
            self.assertIsNone(backend.read("registry", key))
        finally:
            if backend.read("registry", key) is not None:
                backend._write("registry", key, None)

    def test_systemd_backend_read_reports_actual_activation_and_propagates_failure(self):
        from respected_brain.integrations.backend import canonical_json
        from respected_brain.core.errors import FoundationError
        backend = self.backend()
        outputs = [mock.Mock(returncode=0, stdout=b"enabled\n", stderr=b""), mock.Mock(returncode=0, stdout=b"active\n", stderr=b"")]
        with mock.patch("respected_brain.integrations.backend.subprocess.run", side_effect=outputs):
            self.assertEqual(backend.read("task", "systemd:respected-test.timer"), canonical_json({"enabled": True, "active": True}))
        with mock.patch("respected_brain.integrations.backend.subprocess.run", return_value=mock.Mock(returncode=1, stdout=b"", stderr=b"activation failed")):
            with self.assertRaises(FoundationError):
                backend._write("task", "systemd:respected-test.timer", canonical_json({"enabled": True, "active": True}))

    def test_managed_identity_uses_registered_uppercase_settings(self):
        from respected_brain.core.context import AppContext
        from respected_brain.integrations.rendering import managed_rule
        ctx = AppContext(self.ctx.paths, {"vaults": {self.ctx.paths.vault_id: {"settings": {"OS_NAME": "AdaOS", "COMPANION": "AdaCompanion", "USER_NAME": "Ada", "USER_BIO": "Researcher"}}}}, self.ctx.resources)
        text = managed_rule(ctx)
        self.assertIn("# AdaOS", text)
        self.assertIn("Sen AdaCompanion, Ada", text)
        self.assertIn("Researcher", text)
        self.assertNotIn("{{", text)

    def test_persistent_posix_registration_rejects_python_launcher(self):
        from respected_brain.integrations.rendering import plan_integrations
        profile = IntegrationProfile("posix", ("python3", "-m", "respected_brain"), self.home)
        with self.assertRaises(ValueError):
            plan_integrations(self.ctx, profile, {"global": True}, self.backend())

    def test_reentrant_hook_does_not_create_any_technical_state(self):
        from respected_brain.integrations.hooks.bridge import dispatch
        before = snapshot(self.root)
        with mock.patch.dict("os.environ", {"RESPECTED_INVOKED_BY": "codex"}):
            self.assertEqual(dispatch(self.ctx, provider="cursor", event="prompt", argv=[], stdin="{}"), "")
        self.assertEqual(snapshot(self.root), before)

    def test_schedule_planner_refuses_unknown_record_at_uuid_task_name(self):
        from respected_brain.integrations.scheduling.service import plan_schedule, _windows_xml
        from respected_brain.integrations.backend import canonical_task_xml
        backend = mock.Mock()
        backend.read.return_value = canonical_task_xml(_windows_xml("third-party.exe", "user task"))
        with self.assertRaises(OwnershipConflict):
            plan_schedule(self.ctx, self.profile, backend)

    def test_shortcut_planner_refuses_unrelated_existing_user_shortcut(self):
        from respected_brain.integrations.rendering import plan_integrations
        backend = mock.Mock()
        backend.read.return_value = b"[InternetShortcut]\r\nURL=https://example.com/mine\r\n"   # the person's own file under our name
        with self.assertRaises(OwnershipConflict):
            plan_integrations(self.ctx, self.profile, {"shortcut": True}, backend)

    def test_the_shortcut_is_a_direct_obsidian_link_named_after_the_vault(self):
        from urllib.parse import quote
        from respected_brain.integrations.rendering import plan_integrations
        rows = plan_integrations(self.ctx, self.profile, {"shortcut": True}, self.backend())
        row = next(row for row in rows if row.kind == "shortcut")
        name = self.ctx.paths.vault_root.name
        self.assertEqual(Path(row.key).name, f"Obsidian - {name}.url")
        self.assertEqual(row.after.decode("utf-8").splitlines()[:2], ["[InternetShortcut]", "URL=obsidian://open?vault=" + quote(name, safe="")])

    def test_mcp_registration_preserves_unknown_entry_fields(self):
        from respected_brain.integrations.rendering import plan_integrations
        path = self.home / ".cursor/mcp.json"
        path.parent.mkdir()
        entry = {"command": str(self.app / "respected-brain.exe"), "args": ["mcp", "--vault-id", self.ctx.paths.vault_id], "env": {"USER_SETTING": "keep"}, "disabled": False}
        path.write_text(json.dumps({"mcpServers": {"respected-brain": entry}}), encoding="utf-8")
        rows = plan_integrations(self.ctx, self.profile, {"mcp": True}, self.backend())
        row = next(row for row in rows if row.key == str(path))
        self.assertEqual(json.loads(row.after)["mcpServers"]["respected-brain"]["env"], {"USER_SETTING": "keep"})

    def test_loose_skill_copies_changed_by_the_user_are_left_alone(self):
        from respected_brain.integrations.rendering import plan_integrations
        path = self.home / ".agents/skills/brain-doktor/SKILL.md"
        path.parent.mkdir(parents=True)
        path.write_bytes(b"user custom skill")
        before = snapshot(self.root)
        self.assertNotIn(str(path), {row.key for row in plan_integrations(self.ctx, self.profile, {"global": True}, self.backend())})
        self.assertEqual(snapshot(self.root), before)

    def test_loose_skill_copies_from_before_the_plugin_are_retired(self):
        from respected_brain.integrations.rendering import plan_integrations
        from respected_brain.installation.ownership import OwnershipManifest, manifest_document
        path = self.home / ".agents/skills/brain-doktor/SKILL.md"
        path.parent.mkdir(parents=True)
        path.write_bytes(self.ctx.resources.read_text("skills/brain-doktor/SKILL.md").encode())
        rows = plan_integrations(self.ctx, self.profile, {"global": True}, self.backend())
        self.assertIsNone(next(row.after for row in rows if row.key == str(path)))
        path.write_bytes(b"previous owned version")
        self.data.mkdir(parents=True, exist_ok=True)
        record = ExternalChange("file", str(path), None, b"previous owned version")
        (self.data / "install-manifest.json").write_text(json.dumps(manifest_document(OwnershipManifest(3, (), (record,)))), encoding="utf-8")
        rows = plan_integrations(self.ctx, self.profile, {"global": True}, self.backend())
        self.assertIsNone(next(row.after for row in rows if row.key == str(path)))

    def test_global_hooks_refuse_spoofed_managed_flags_and_preserve_empty_user_groups(self):
        from respected_brain.integrations.rendering import plan_integrations
        path=self.home / ".claude/settings.json"
        path.parent.mkdir()
        path.write_text(json.dumps({"hooks":{"SessionStart":[{"hooks":[{"command":"third-party.exe --global-hook --provider claude"}]}]}}),encoding="utf-8")
        with self.assertRaises(OwnershipConflict):
            plan_integrations(self.ctx,self.profile,{"global":True},self.backend())
        user={"matcher":"user-empty","hooks":[]}
        path.write_text(json.dumps({"hooks":{"SessionStart":[user]},"custom":True}),encoding="utf-8")
        rows=plan_integrations(self.ctx,self.profile,{"global":True},self.backend())
        after=json.loads(next(row.after for row in rows if row.key==str(path)))
        self.assertIn(user,after["hooks"]["SessionStart"])
        self.assertTrue(after["custom"])

    def test_generated_mcp_tool_files_cannot_replace_unowned_content(self):
        from respected_brain.integrations.rendering import plan_integrations
        path=self.home / ".gemini/antigravity-ide/mcp/respected-brain/instructions.md"
        path.parent.mkdir(parents=True)
        path.write_bytes(b"my own MCP instructions")
        before=snapshot(self.root)
        with self.assertRaises(OwnershipConflict):
            plan_integrations(self.ctx,self.profile,{"mcp":True},self.backend())
        self.assertEqual(snapshot(self.root),before)

    def test_native_obsidian_shortcut_is_written_read_back_and_removed_as_a_plain_file(self):
        from respected_brain.integrations.backend import ExternalChange, NativeBackend
        from respected_brain.integrations.rendering import obsidian_shortcut
        backend = NativeBackend(self.root / "data")
        path = self.home / "Desktop" / "Obsidian - Vault.url"
        path.parent.mkdir(parents=True, exist_ok=True)
        text = obsidian_shortcut("Vault", self.home / "no-obsidian.exe").encode("utf-8")
        backend.apply(ExternalChange("shortcut", str(path), None, text))
        self.assertEqual(backend.read("shortcut", str(path)), text)
        self.assertEqual(path.read_bytes(), text)
        backend.restore(ExternalChange("shortcut", str(path), None, text))
        self.assertFalse(path.exists())

    def test_the_shortcut_gets_obsidians_icon_when_obsidian_is_installed(self):
        from respected_brain.integrations.rendering import obsidian_shortcut
        exe = self.home / "Obsidian.exe"
        exe.write_bytes(b"MZ")
        self.assertIn(f"IconFile={exe}", obsidian_shortcut("Vault", exe))
        self.assertNotIn("IconFile", obsidian_shortcut("Vault", self.home / "missing.exe"))

if __name__ == '__main__':
    unittest.main()


class HookCommandQuotingTest(unittest.TestCase):
    """Claude Code runs hooks through Git Bash when present: an unquoted Windows path loses its backslashes and the hook never runs."""

    def test_windows_hook_commands_quote_the_program_for_cmd_and_git_bash(self):
        import shutil
        import subprocess
        from types import SimpleNamespace
        from respected_brain.integrations.rendering import command_text
        profile = SimpleNamespace(platform="windows-native")
        plain = command_text(profile, [r"C:\Apps\Respected\respected-brain.exe", "hook", "--vault-id", "x"])
        spaced = command_text(profile, [r"C:\Program Files\R\respected-brain.exe", "hook"])
        self.assertEqual(plain, r'"C:\Apps\Respected\respected-brain.exe" hook --vault-id x')
        self.assertEqual(spaced, r'"C:\Program Files\R\respected-brain.exe" hook')
        bash = shutil.which("bash")
        if bash:  # the quoted form survives the shell that Claude Code uses on Windows
            echoed = subprocess.run([bash, "-c", plain.replace("respected-brain.exe", "x").replace('"C:', 'echo "C:', 1)], capture_output=True, text=True).stdout
            self.assertIn(r"C:\Apps\Respected\x", echoed)
        self.assertEqual(command_text(SimpleNamespace(platform="posix"), ["/a b/x", "hook"]), "'/a b/x' hook")
