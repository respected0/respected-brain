import unittest
from pathlib import Path
from unittest import mock

from respected_brain.integrations import planning
from respected_brain.integrations.backend import IntegrationProfile

ARGV = ["C:/Users/Some One/app/respected-brain.exe", "hook", "--provider", "codex"]


class HookCommandTextTest(unittest.TestCase):
    def profile(self, platform="windows-native"):
        return IntegrationProfile(platform, (ARGV[0],), Path.home())

    def test_a_spaced_path_uses_its_short_name_when_there_is_one(self):
        with mock.patch.object(planning, "_short_path", return_value="C:/Users/SOMEON~1/app/respected-brain.exe"):
            for render in (planning.bare_command_text, planning.codex_command_text):
                self.assertEqual(render(self.profile(), ARGV), "C:/Users/SOMEON~1/app/respected-brain.exe hook --provider codex")

    def test_codex_uses_the_call_operator_when_no_short_name_exists(self):
        with mock.patch.object(planning, "_short_path", side_effect=lambda path: path):
            self.assertTrue(planning.codex_command_text(self.profile(), ARGV).startswith('& "C:/Users/Some One/app/respected-brain.exe"'))
            self.assertTrue(planning.bare_command_text(self.profile(), ARGV).startswith('"'))  # Antigravity has no such form

    def test_other_platforms_keep_the_plain_command(self):
        profile = IntegrationProfile("posix", ("/opt/respected-brain",), Path.home())
        self.assertEqual(planning.codex_command_text(profile, ["/opt/respected-brain", "hook"]), planning.command_text(profile, ["/opt/respected-brain", "hook"]))


if __name__ == "__main__":
    unittest.main()
