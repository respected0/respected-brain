import unittest

from respected_brain.integrations.global_config import strip_grouped_hooks
from respected_brain.integrations.plugin import register_claude, register_codex


class PluginRegistrationTest(unittest.TestCase):
    def test_strip_removes_only_brain_handlers_and_empty_events(self):
        brain = {"command": "brain.exe hook --provider claude --event start --global-hook"}
        user = {"command": "mine.exe"}
        document = {"hooks": {"SessionStart": [{"hooks": [brain, user]}], "Stop": [{"hooks": [brain]}]}, "keep": 1}
        strip_grouped_hooks(document, "claude")
        self.assertEqual(document, {"hooks": {"SessionStart": [{"hooks": [user]}]}, "keep": 1})
        only = {"hooks": {"Stop": [{"hooks": [brain]}]}}
        self.assertEqual(strip_grouped_hooks(only, "claude"), {})

    def test_claude_registration_keeps_other_plugins(self):
        settings = {"enabledPlugins": {"other@x": True}}
        register_claude(settings, "C:/bundle")
        self.assertEqual(settings["enabledPlugins"], {"other@x": True, "respected-brain@respected-brain": True})
        self.assertEqual(settings["extraKnownMarketplaces"]["respected-brain"]["source"], {"source": "directory", "path": "C:/bundle"})

    def test_codex_registration_is_idempotent_and_keeps_other_tables(self):
        original = 'model = "x"\n\n[plugins."other@y"]\nenabled = true\n'
        once = register_codex(original, "C:/bundle")
        self.assertEqual(register_codex(once, "C:/bundle"), once)
        self.assertIn('[plugins."other@y"]\nenabled = true', once)
        self.assertIn("source = 'C:/bundle'", once)
        moved = register_codex(once, "D:/moved")
        self.assertNotIn("C:/bundle", moved)
        self.assertEqual(moved.count("[marketplaces.respected-brain]"), 1)


class InstallPluginsTest(unittest.TestCase):
    def setUp(self):
        import tempfile
        from pathlib import Path
        from unittest import mock
        from respected_brain.integrations.backend import IntegrationProfile
        self.home = Path(tempfile.mkdtemp())
        self.addCleanup(__import__("shutil").rmtree, self.home, True)
        self.profile = IntegrationProfile("posix", ("/opt/respected-brain",), self.home)
        self.ctx = mock.Mock()
        self.ctx.paths.data_root = self.home / "data"
        self.ctx.paths.vault_id = "93e9e921-3334-4a6a-a381-1d4c42a9d405"
        patch = mock.patch.dict("os.environ", {"RESPECTED_SKIP_CLIENT_PLUGINS": ""})
        patch.start()
        self.addCleanup(patch.stop)

    def install(self, desired, which, run):
        from respected_brain.integrations.plugin import install_plugins
        return install_plugins(self.ctx, self.profile, desired, which=which, run=run)

    def test_runs_marketplace_add_and_install_for_selected_clients(self):
        from unittest import mock
        run = mock.Mock(return_value=mock.Mock(returncode=0))
        self.assertEqual(self.install({"global": True}, lambda name: "/bin/" + name, run), ())
        commands = [call.args[0] for call in run.call_args_list]
        self.assertEqual([c[1:3] for c in commands], [["plugin", "marketplace"], ["plugin", "install"], ["plugin", "add"]])
        self.assertEqual(commands[1][3], "respected-brain@respected-brain")
        self.assertEqual(run.call_args.kwargs["env"]["USERPROFILE"], str(self.home))
        self.assertEqual(run.call_args.kwargs["env"]["CODEX_HOME"], str(self.home / ".codex"))
        self.assertNotEqual(run.call_args_list[0].kwargs["env"].get("CODEX_HOME"), str(self.home / ".codex"))  # only Codex gets it

    def test_missing_cli_unselected_client_and_disabled_global_are_skipped(self):
        from unittest import mock
        run = mock.Mock()
        self.assertEqual(self.install({"global": True}, lambda name: None, run), ())
        self.assertEqual(self.install({"global": True, "clients": ["codex"]}, lambda name: "/bin/" + name, mock.Mock(return_value=mock.Mock(returncode=0))), ())
        self.assertEqual(self.install({"global": False}, lambda name: "/bin/" + name, run), ())
        run.assert_not_called()

    def test_failure_is_reported_and_stops_that_client_only(self):
        from unittest import mock
        run = mock.Mock(side_effect=[mock.Mock(returncode=1), mock.Mock(returncode=0)])
        failed = self.install({"global": True}, lambda name: "/bin/" + name, run)
        self.assertEqual(failed, ("claude plugin marketplace",))
        self.assertEqual(run.call_count, 2)
        self.assertEqual(self.install({"global": True}, lambda name: "/bin/" + name, mock.Mock(side_effect=OSError)), ("claude plugin marketplace", "codex plugin add"))


if __name__ == "__main__":
    unittest.main()
