import tempfile
import unittest
from pathlib import Path

from respected_brain.integrations.hooks.bridge import antigravity_session_from_transcript


class AntigravitySessionTest(unittest.TestCase):
    def test_both_transcript_names_give_the_conversation_key(self):
        with tempfile.TemporaryDirectory() as name:
            for product, filename in (("antigravity-ide", "transcript.jsonl"), ("antigravity-cli", "transcript.jsonl"), ("antigravity-cli", "transcript_full.jsonl")):
                logs = Path(name) / ".gemini" / product / "brain" / "dfd1496c-0f1b-428c-8137-fff6b06751bc" / ".system_generated" / "logs"
                logs.mkdir(parents=True, exist_ok=True)
                (logs / filename).write_text("{}\n", encoding="utf-8")
                with self.subTest(product=product, filename=filename):
                    self.assertEqual(antigravity_session_from_transcript(str(logs / filename)), "dfd1496c-0f1b-428c-8137-fff6b06751bc")

    def test_other_file_names_give_no_key(self):
        with tempfile.TemporaryDirectory() as name:
            logs = Path(name) / ".gemini" / "antigravity-cli" / "brain" / "c1" / ".system_generated" / "logs"
            logs.mkdir(parents=True, exist_ok=True)
            (logs / "notes.jsonl").write_text("{}\n", encoding="utf-8")
            self.assertEqual(antigravity_session_from_transcript(str(logs / "notes.jsonl")), "")


if __name__ == "__main__":
    unittest.main()
