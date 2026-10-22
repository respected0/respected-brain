"""A client that only reformats our JSON file is not a user change; different data still is."""
import json
import unittest
from pathlib import Path
from types import SimpleNamespace

from respected_brain.core.errors import OwnershipConflict
from respected_brain.integrations.planning import _assert_owned_replacement


class _Planner:
    def __init__(self, files):
        self.files = files

    def read(self, path, kind="file"):
        return self.files.get(Path(path))


class TestOwnedReplacement(unittest.TestCase):
    path = Path("tool.json")
    data = {"name": "respected_search", "parameters": {"type": "object"}}

    def check(self, current):
        ctx = SimpleNamespace(paths=SimpleNamespace(data_root=Path("data")))
        baseline = json.dumps(self.data, indent=2).encode()
        _assert_owned_replacement(ctx, _Planner({self.path: current}), self.path, baseline, kind="mcp")

    def test_minified_copy_of_our_file_is_still_ours(self):
        self.check(json.dumps(self.data, separators=(",", ":")).encode())

    def test_changed_data_is_a_user_change(self):
        with self.assertRaises(OwnershipConflict):
            self.check(json.dumps({**self.data, "name": "other"}).encode())

    def test_non_json_content_is_a_user_change(self):
        with self.assertRaises(OwnershipConflict):
            self.check(b"not json")


if __name__ == "__main__":
    unittest.main()
