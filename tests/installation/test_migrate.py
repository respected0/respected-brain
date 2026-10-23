import json
import shutil
import tempfile
import unittest
from pathlib import Path

from respected_brain.core.errors import FoundationError
from respected_brain.installation.migrate import CURRENT, SHIPPED, STEPS, migrate_data


# one folder per published release: the data files that release wrote, copied from a real install and never edited
RELEASES = Path(__file__).resolve().parents[1] / "fixtures" / "releases"


def write(path, document):
    path.write_text(json.dumps(document), encoding="utf-8")


class MigrateTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.data = Path(temporary.name)

    def test_current_files_are_left_alone_and_missing_files_are_skipped(self):
        write(self.data / "config.json", {"schema_version": CURRENT["config.json"], "keep": 1})
        before = (self.data / "config.json").read_bytes()
        self.assertEqual(migrate_data(self.data), [])
        self.assertEqual((self.data / "config.json").read_bytes(), before)

    def test_old_format_moves_step_by_step_and_the_original_is_kept(self):
        write(self.data / "memory-grants.json", {"schema_version": 1, "grants": ["a"]})
        steps = {("memory-grants.json", 1): lambda d: {**d, "grants": [{"id": g} for g in d["grants"]]}}
        self.assertEqual(migrate_data(self.data, current={"memory-grants.json": 2}, steps=steps), ["memory-grants.json"])
        self.assertEqual(json.loads((self.data / "memory-grants.json").read_text()), {"schema_version": 2, "grants": [{"id": "a"}]})
        self.assertEqual(json.loads((self.data / "memory-grants.json.v1.bak").read_text())["grants"], ["a"])
        self.assertEqual(migrate_data(self.data, current={"memory-grants.json": 2}, steps=steps), [])

    def test_newer_unknown_or_unmigratable_data_is_refused_untouched(self):
        for document, current in (({"schema_version": 9}, 3), ({"x": 1}, 3), ({"schema_version": 1}, 3)):
            with self.subTest(document=document):
                write(self.data / "config.json", document)
                before = (self.data / "config.json").read_bytes()
                with self.assertRaises(FoundationError):
                    migrate_data(self.data, current={"config.json": current}, steps={})
                self.assertEqual((self.data / "config.json").read_bytes(), before)
                self.assertFalse(list(self.data.glob("*.bak")))

    def test_registry_has_a_step_for_every_older_version(self):
        for name, target in CURRENT.items():
            for version in range(SHIPPED[name], target):
                self.assertIn((name, version), STEPS, f"{name}: no step {version} -> {version + 1}")

    def test_every_published_release_moves_to_the_current_format_and_then_stays_put(self):
        releases = sorted(path for path in RELEASES.iterdir() if path.is_dir())
        self.assertTrue(releases, "tests/fixtures/releases is empty")
        for release in releases:
            with self.subTest(release=release.name):
                data = self.data / release.name
                shutil.copytree(release, data)
                names = [path.name for path in data.glob("*.json")]
                migrate_data(data)
                for name in names:
                    self.assertEqual(json.loads((data / name).read_text("utf-8"))["schema_version"], CURRENT[name], name)
                settled = {path.name: path.read_bytes() for path in data.glob("*.json")}
                self.assertEqual(migrate_data(data), [], "a second run must change nothing")
                self.assertEqual({path.name: path.read_bytes() for path in data.glob("*.json")}, settled)

    def test_the_first_release_data_is_kept_as_a_fixture(self):
        for name, version in SHIPPED.items():
            found = [json.loads(path.read_text("utf-8")).get("schema_version") for path in RELEASES.glob(f"*/{name}")]
            self.assertIn(version, found, f"{name}: add the file of the release that shipped format {version} to tests/fixtures/releases")


if __name__ == "__main__":
    unittest.main()
