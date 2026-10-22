import os
import subprocess
import sys
import unittest
from pathlib import Path

from respected_brain.core.platform import ensure_user_environment


class UserEnvironmentTest(unittest.TestCase):
    def test_missing_variables_are_filled_and_set_ones_are_kept(self):
        folders = {"Profile": Path("C:/Users/x"), "RoamingAppData": Path("C:/Users/x/AppData/Roaming"), "LocalAppData": Path("C:/Users/x/AppData/Local")}
        env = {"APPDATA": "D:/kept"}
        ensure_user_environment(env, folders.__getitem__)
        self.assertEqual(env["APPDATA"], "D:/kept")
        self.assertEqual(Path(env["USERPROFILE"]), folders["Profile"])
        self.assertEqual(Path(env["LOCALAPPDATA"]), folders["LocalAppData"])

    def test_an_unreadable_folder_leaves_the_variable_unset(self):
        def read(name):
            raise OSError(name)
        env = {}
        ensure_user_environment(env, read)
        self.assertEqual(env, {})

    @unittest.skipUnless(os.name == "nt", "Windows trimmed hook environment")
    def test_a_process_with_a_trimmed_environment_still_finds_its_home(self):
        code = "from respected_brain.core.platform import ensure_user_environment as e; e(); from pathlib import Path; print(Path.home())"
        trimmed = {"SYSTEMROOT": os.environ["SYSTEMROOT"], "PYTHONPATH": os.pathsep.join(sys.path)}
        done = subprocess.run([sys.executable, "-c", code], env=trimmed, capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertTrue(Path(done.stdout.strip()).is_dir())


if __name__ == "__main__":
    unittest.main()
