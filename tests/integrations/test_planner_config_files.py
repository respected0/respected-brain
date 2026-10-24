"""How the planner reads an AI tool's JSON config: blank files are empty objects, broken ones are refused by name."""
import codecs
import json
import unittest

from respected_brain.integrations import delta
from respected_brain.integrations.planning import _Planner


class Backend:
    def __init__(self, content):
        self.content = content

    def read(self, kind, key):
        return self.content


class PlannerConfigFileTest(unittest.TestCase):
    def test_missing_empty_whitespace_and_bom_only_files_are_empty_objects(self):
        for content in (None, b"", b"  \n", codecs.BOM_UTF8):
            with self.subTest(content=content):
                self.assertEqual(_Planner(Backend(content)).object("settings.json"), {})

    def test_bom_prefixed_json_is_read(self):
        self.assertEqual(_Planner(Backend(codecs.BOM_UTF8 + b'{"a": 1}')).object("settings.json"), {"a": 1})

    def test_broken_or_non_object_json_is_refused_and_names_the_file(self):
        for content in (b'{"a": ', b"[1]", b"nope"):
            with self.subTest(content=content), self.assertRaisesRegex(ValueError, "settings.json"):
                _Planner(Backend(content)).object("settings.json")

    def test_an_empty_config_that_gained_entries_is_reverted_to_an_empty_object(self):
        recorded = delta.make_delta(b"", b'{"enabledPlugins": {"respected-brain": true}}')
        self.assertEqual(delta.revert(b'{"enabledPlugins": {"respected-brain": true}}', recorded).strip(), b"{}")
        kept = delta.revert(b'{"enabledPlugins": {"respected-brain": true}, "mine": 2}', recorded)
        self.assertIn(b'"mine": 2', kept)
        self.assertNotIn(b"respected-brain", kept)

    def test_our_own_entry_is_removed_even_when_its_value_was_edited_by_hand(self):
        recorded = delta.make_delta(b'{"theme": "dark"}', b'{"theme": "dark", "market": {"source": {"path": "A"}}, "plugin": true}')
        edited = b'{"theme": "light", "market": {"source": {"path": "B"}}, "plugin": false, "mine": 1}'
        result = json.loads(delta.revert(edited, recorded))
        self.assertEqual(result, {"theme": "light", "mine": 1})

    def test_a_value_that_existed_before_and_was_changed_by_both_sides_is_still_a_conflict(self):
        recorded = delta.make_delta(b'{"mode": "a"}', b'{"mode": "b"}')
        with self.assertRaises(delta.DeltaConflict):
            delta.revert(b'{"mode": "c"}', recorded)


if __name__ == "__main__":
    unittest.main()
