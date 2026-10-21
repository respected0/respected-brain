from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from respectedbrain.rpp import memory_grants as grants


class MemoryGrantsTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)

    def make(self, grant_id: str = "grant-0001", **kw):
        return grants.create(self.root, grant_id, kw.pop("label", "Orchestrator"), "vault-1", **kw)

    def test_round_trip(self) -> None:
        made = self.make(max_results=5)
        self.assertTrue(made["token"].startswith("rbm_"))
        public = grants.verify(self.root, made["token"])
        self.assertEqual(public["grant_id"], "grant-0001")
        self.assertEqual(public["vault_id"], "vault-1")
        self.assertEqual(public["max_results"], 5)
        self.assertNotIn("token_sha256", public)

    def test_only_hash_on_disk(self) -> None:
        made = self.make()
        text = (self.root / grants.GRANTS_FILE).read_text(encoding="utf-8")
        self.assertNotIn(made["token"], text)
        self.assertIn(grants._hash(made["token"]), text)

    def test_denials_identical(self) -> None:
        made = self.make()
        grants.revoke(self.root, "grant-0001")
        messages = set()
        for token in ("rbm_wrong", "", made["token"], None):
            with self.assertRaises(grants.GrantError) as ctx:
                grants.verify(self.root, token)
            self.assertEqual(ctx.exception.code, "PERMISSION_DENIED")
            messages.add(ctx.exception.message)
        self.assertEqual(messages, {"Memory access is not authorized."})

    def test_verify_without_file_denied(self) -> None:
        with self.assertRaises(grants.GrantError) as ctx:
            grants.verify(self.root, "rbm_x")
        self.assertEqual(ctx.exception.message, "Memory access is not authorized.")

    def test_duplicate_grant_id(self) -> None:
        self.make()
        grants.revoke(self.root, "grant-0001")
        with self.assertRaises(grants.GrantError) as ctx:
            self.make()
        self.assertEqual(ctx.exception.code, "GRANT_EXISTS")

    def test_limit(self) -> None:
        for i in range(grants.MAX_ACTIVE):
            self.make(f"grant-{i:04d}")
        with self.assertRaises(grants.GrantError) as ctx:
            self.make("grant-over1")
        self.assertEqual(ctx.exception.code, "GRANT_LIMIT")
        grants.revoke(self.root, "grant-0000")
        self.make("grant-over1")

    def test_validation(self) -> None:
        bad = [
            dict(grant_id="short", label="ok", vault_id="v"),
            dict(grant_id="bad id!!!!", label="ok", vault_id="v"),
            dict(grant_id="grant-0001", label="", vault_id="v"),
            dict(grant_id="grant-0001", label="x" * 81, vault_id="v"),
            dict(grant_id="grant-0001", label="bad/label", vault_id="v"),
            dict(grant_id="grant-0001", label="ok", vault_id=""),
            dict(grant_id="grant-0001", label="ok", vault_id="v", max_results=0),
            dict(grant_id="grant-0001", label="ok", vault_id="v", max_results=21),
        ]
        for kwargs in bad:
            with self.assertRaises(grants.GrantError, msg=str(kwargs)) as ctx:
                grants.create(self.root, **kwargs)
            self.assertEqual(ctx.exception.code, "BAD_REQUEST")
        self.assertFalse((self.root / grants.GRANTS_FILE).exists())

    def test_corrupt_file(self) -> None:
        path = self.root / grants.GRANTS_FILE
        for content in ("{not json", "[]", '{"grants": {}}', '{"grants": [1]}'):
            path.write_text(content, encoding="utf-8")
            with self.assertRaises(grants.GrantError) as ctx:
                self.make()
            self.assertEqual(ctx.exception.code, "GRANTS_CORRUPT")
            self.assertEqual(path.read_text(encoding="utf-8"), content)
            with self.assertRaises(grants.GrantError) as ctx:
                grants.verify(self.root, "rbm_x")
            self.assertEqual(ctx.exception.code, "PERMISSION_DENIED")

    def test_revoke(self) -> None:
        self.make()
        self.assertEqual(grants.revoke(self.root, "grant-0001"), {"grant_id": "grant-0001", "revoked": True})
        self.assertEqual(grants.revoke(self.root, "grant-0001"), {"grant_id": "grant-0001", "revoked": True})
        with self.assertRaises(grants.GrantError) as ctx:
            grants.revoke(self.root, "nope-nope-1")
        self.assertEqual(ctx.exception.code, "GRANT_NOT_FOUND")

    def test_list_public_hides_hashes(self) -> None:
        made = self.make()
        listed = grants.list_public(self.root)
        self.assertEqual(len(listed), 1)
        self.assertNotIn("token_sha256", listed[0])
        self.assertNotIn(made["token"], str(listed))
        self.assertFalse(listed[0]["revoked"])


if __name__ == "__main__":
    unittest.main()
