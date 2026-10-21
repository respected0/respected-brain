"""Secrets in session text: redaction shapes, the summariser prompt, and what lands in notes."""
import unittest

from respectedbrain.memory import flush as F
from respectedbrain.memory.redact import redact

SECRETS = {
    "openai": "sk-" + "Ab12Cd34Ef56Gh78Ij90Kl12",
    "anthropic": "sk-ant-" + "api03-Ab12Cd34Ef56Gh78Ij90Kl12",
    "github": "ghp_" + "Ab12Cd34Ef56Gh78Ij90Kl12Mn",
    "aws": "AKIA" + "ABCDEFGHIJKLMNOP",
    "bearer": "Bearer " + "abcdEFGH1234ijklMNOP5678",
    "jwt": "eyJhbGciOiJIUzI1NiJ9" + ".eyJzdWIiOiIxMjM0NTY3ODkwIn0" + ".dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U",
    "url-password": "postgres://admin:" + "S3cretPassw0rd" + "@db.internal/app",
    "json-key": '"apiKey": "' + "k9Zq8Xw7Vv6Uu5Tt4Ss3" + '"',
    "env-style": "DATABASE_PASSWORD=" + "hunter2hunter2",
    "private-key": "-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA\n-----END RSA PRIVATE KEY-----",
}
VALUES = {"openai": SECRETS["openai"], "anthropic": SECRETS["anthropic"], "github": SECRETS["github"], "aws": SECRETS["aws"],
          "bearer": "abcdEFGH1234ijklMNOP5678", "jwt": "dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U",
          "url-password": "S3cretPassw0rd", "json-key": "k9Zq8Xw7Vv6Uu5Tt4Ss3", "env-style": "hunter2hunter2", "private-key": "MIIEowIBAAKCAQEA"}


class RedactTest(unittest.TestCase):
    def test_every_credential_shape_is_removed(self):
        for name, text in SECRETS.items():
            with self.subTest(name):
                clean = redact(f"before {text} after")
                self.assertNotIn(VALUES[name], clean)
                self.assertIn("[REDACTED", clean)
                self.assertTrue(clean.startswith("before ") and clean.endswith(" after") or name == "private-key")

    def test_ordinary_text_is_untouched_and_redaction_is_idempotent(self):
        prose = "Toplantı notu: token sayısı 12, parola politikası gözden geçirilecek. Sık kullanılan anahtar: Enter."
        self.assertEqual(redact(prose), prose)
        once = redact("password=" + "hunter2hunter2")
        self.assertEqual(redact(once), once)

    def test_the_summariser_prompt_never_carries_a_credential(self):
        prompt = F.build_flush_prompt("kullanıcı: anahtarım " + SECRETS["openai"] + " ve DB_PASSWORD=" + "hunter2hunter2")
        self.assertNotIn(VALUES["openai"], prompt)
        self.assertNotIn("hunter2hunter2", prompt)


if __name__ == "__main__":
    unittest.main()
