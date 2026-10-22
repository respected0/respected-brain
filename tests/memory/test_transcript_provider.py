import unittest
from pathlib import Path

from respected_brain.memory.flush import _transcript_provider


class TranscriptProviderTest(unittest.TestCase):
    def test_every_client_folder_names_its_own_provider(self):
        home = Path("C:/Users/x")
        cases = {
            "codex": home / ".codex/sessions/rollout-1.jsonl",
            "claude": home / ".claude/projects/p/s.jsonl",
            "cursor": home / ".cursor/projects/p/s.jsonl",
            "gemini": home / ".gemini/tmp/h/chats/s.json",
            "antigravity": home / ".gemini/antigravity-ide/brain/c/.system_generated/logs/transcript.jsonl",
        }
        for provider, path in cases.items():
            with self.subTest(provider=provider):
                self.assertEqual(_transcript_provider(path), provider)

    def test_the_agy_cli_is_antigravity_not_gemini(self):
        path = Path("C:/Users/x/.gemini/antigravity-cli/brain/c/.system_generated/logs/transcript_full.jsonl")
        self.assertEqual(_transcript_provider(path), "antigravity")

    def test_unknown_locations_name_no_provider(self):
        self.assertIsNone(_transcript_provider(Path("C:/work/s.jsonl")))


if __name__ == "__main__":
    unittest.main()
