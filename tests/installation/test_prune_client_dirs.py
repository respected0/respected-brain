import tempfile, unittest
from pathlib import Path

from respectedbrain.installation.uninstall import prune_empty_client_dirs


class PruneClientDirsTest(unittest.TestCase):
    def test_removes_empty_skill_folders_but_keeps_client_roots_and_foreign_files(self):
        with tempfile.TemporaryDirectory() as raw:
            home = Path(raw)
            (home / ".claude/skills/a").mkdir(parents=True)
            (home / ".agents/skills/a").mkdir(parents=True)
            (home / ".cursor/skills/b").mkdir(parents=True)
            (home / ".cursor/skills/foreign.txt").write_text("x")
            (home / "Desktop").mkdir()
            prune_empty_client_dirs([home / ".claude/skills/a/SKILL.md", home / ".agents/skills/a/SKILL.md",
                                     home / ".cursor/skills/b/SKILL.md", home / "Desktop/Respected Brain.lnk"])
            self.assertTrue((home / ".claude").is_dir() and not (home / ".claude/skills").exists())
            self.assertFalse((home / ".agents").exists())
            self.assertTrue((home / ".cursor/skills/foreign.txt").is_file() and not (home / ".cursor/skills/b").exists())
            self.assertTrue((home / "Desktop").is_dir())


if __name__ == "__main__":
    unittest.main()
