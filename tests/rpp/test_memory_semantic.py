"""Opt-in local semantic search through RPP, against a fake loopback embedding service (no real model needed)."""

from __future__ import annotations

import json
import os
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from respectedbrain.rpp import server as rpp
from respectedbrain.core.config import ConfigStore
from respectedbrain.rpp.integrations import _context
from respectedbrain.search import freshness, semantic

CONCEPTS = [("car", "automobile", "vehicle"), ("cat", "feline", "kitten"), ("sql", "database", "sqlite")]


def vec(text: str) -> list[float]:
    words = [w.strip(".,#") for w in text.casefold().split()]
    return [float(sum(w in group for w in words)) + 0.01 for group in CONCEPTS]


class Fake(BaseHTTPRequestHandler):
    models: list[str] = []
    seen: list[str] = []

    def log_message(self, *args):
        pass

    def reply(self, body):
        data = json.dumps(body).encode()
        self.send_response(200)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        self.reply({"models": [{"name": m + ":latest"} for m in Fake.models]})

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        if self.path == "/api/pull":
            Fake.models.append(body["model"])
            self.reply({"status": "success"})
        else:
            Fake.seen.extend(body["input"])
            self.reply({"embeddings": [vec(t) for t in body["input"]]})


class SemanticTest(unittest.TestCase):
    def setUp(self):
        Fake.models, Fake.seen = [], []
        self.server = HTTPServer(("127.0.0.1", 0), Fake)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        temporary = tempfile.TemporaryDirectory(prefix="rpp-sem-")
        self.addCleanup(temporary.cleanup)
        base = Path(temporary.name).resolve()
        self.data, self.vault = base / "data", base / "vault"
        self.data.mkdir()
        self.vault.mkdir()
        (self.vault / "garage.md").write_text("# Garage\nThe automobile needs new tires.\n", encoding="utf-8")
        (self.vault / "pets.md").write_text("# Pets\nOur kitten is a lovely feline.\n", encoding="utf-8")
        (self.vault / "db.md").write_text("# Storage\nWe picked sqlite as the database.\n", encoding="utf-8")
        patcher = patch.dict(os.environ, {"RESPECTED_APP_DIR": str(base / "app"), "RESPECTED_DATA_DIR": str(self.data)})
        patcher.start()
        self.addCleanup(patcher.stop)

        def mutate(document):
            vault_id = str(uuid4())
            document["vaults"][vault_id] = {"path": str(self.vault)}
            document["active_vault_id"] = vault_id
        ConfigStore(self.data).update(mutate)
        _, self.ctx = _context(self.data, {})
        self.endpoint = f"http://127.0.0.1:{self.server.server_port}"

    def call(self, op, payload=None, operation_id=None):
        request = {"rpp": "1.1", "op": op, "payload": payload or {}}
        if operation_id:
            request["operation_id"] = operation_id
        return rpp.serve(json.dumps(request), data_root=str(self.data))

    def enable(self):
        semantic.save_config(self.data, {**semantic.load_config(self.data), "enabled": True, "provider": "ollama", "model": "nomic-embed-text", "endpoint": self.endpoint})

    def token(self):
        return self.call("memory.grant", {"label": "t"}, "op-grant-0001")["result"]["token"]

    def recall(self, token, query, **extra):
        return self.call("memory.recall", {"token": token, "query": query, **extra})

    def test_off_by_default_and_fts_unchanged(self):
        self.assertEqual(self.call("memory.semantic.status")["result"]["state"], "off")
        freshness.refresh_now(self.ctx)
        token = self.token()
        found = self.recall(token, "automobile")["result"]
        self.assertEqual(found["search"]["mode"], "fts")
        self.assertEqual(Fake.seen, [])  # nothing is embedded while the feature is off
        self.assertEqual(self.recall(token, "x", mode="semantic")["error"]["code"], "SEMANTIC_OFF")

    def test_endpoint_must_be_loopback(self):
        for url in ("http://example.com", "https://127.0.0.1", "http://10.0.0.5:11434", "http://user@127.0.0.1"):
            with self.assertRaises(semantic.SemanticError):
                semantic.check_endpoint(url)

    def test_enable_pull_build_and_semantic_recall(self):
        self.enable()
        self.assertEqual(self.call("memory.semantic.status")["result"]["state"], "model_missing")
        self.assertTrue(self.call("memory.semantic.pull", {"confirm": True})["ok"])
        self.assertEqual(self.call("memory.semantic.pull", {})["error"]["code"], "BAD_REQUEST")
        refreshed = freshness.refresh_now(self.ctx)
        self.assertEqual(refreshed["semantic"]["embedded"], 3)
        self.assertEqual(self.call("memory.semantic.status")["result"]["state"], "ready")
        token = self.token()
        # "vehicle" is in none of the notes: FTS finds nothing, the semantic ranking finds the garage note
        self.assertEqual(self.recall(token, "vehicle", mode="fts")["result"]["count"], 0)
        auto = self.recall(token, "vehicle")["result"]
        self.assertEqual(auto["results"][0]["path"], "garage.md")
        self.assertEqual(auto["search"]["semantic"], "ok")
        self.assertIn("automobile", auto["results"][0]["snippet"])

    def test_incremental_build_and_edited_notes_are_dropped(self):
        self.enable()
        self.call("memory.semantic.pull", {"confirm": True})
        freshness.refresh_now(self.ctx)
        Fake.seen.clear()
        freshness.refresh_now(self.ctx)
        self.assertEqual(Fake.seen, [])  # unchanged notes are not embedded again
        (self.vault / "garage.md").write_text("# Garage\nNothing about it now.\n", encoding="utf-8")
        found = self.recall(self.token(), "vehicle")["result"]
        self.assertNotIn("garage.md", [r["path"] for r in found["results"]])  # edited after indexing: the hash check drops it

    def test_service_down_falls_back_to_fts(self):
        self.enable()
        self.call("memory.semantic.pull", {"confirm": True})
        freshness.refresh_now(self.ctx)
        token = self.token()
        semantic.save_config(self.data, {**semantic.load_config(self.data), "endpoint": "http://127.0.0.1:9"})
        found = self.recall(token, "automobile")["result"]
        self.assertEqual(found["results"][0]["path"], "garage.md")
        self.assertEqual((found["search"]["mode"], found["search"]["semantic"]), ("fts", "unavailable"))
        self.assertFalse(self.recall(token, "automobile", mode="semantic")["ok"])

    def test_configure_needs_confirmation_and_validates_model(self):
        self.assertFalse(self.call("memory.semantic.configure", {"enabled": True})["ok"])
        self.assertFalse(self.call("memory.semantic.configure", {"confirm": True, "enabled": True, "model": "../x y"})["ok"])
        done = self.call("memory.semantic.configure", {"confirm": True, "enabled": True})
        self.assertTrue(done["ok"], done)
        self.assertEqual((done["result"]["provider"], done["result"]["state"], done["result"]["download_mb"]), ("llama", "model_missing", semantic.DOWNLOAD_MB))
        self.assertFalse(self.call("memory.semantic.configure", {"confirm": True, "enabled": True, "model": "unknown"})["ok"])

    def test_pinned_download_is_verified_and_archives_cannot_escape(self):
        import hashlib, zipfile
        source = self.data / "payload.bin"
        source.write_bytes(b"model-bytes")
        good = hashlib.sha256(b"model-bytes").hexdigest()
        target = self.data / "out" / "m.gguf"
        with self.assertRaises(semantic.SemanticError) as bad:
            semantic._download(source.as_uri(), target, "0" * 64, 11)
        self.assertEqual(bad.exception.code, "DOWNLOAD_CORRUPT")
        self.assertFalse(target.exists() or list(target.parent.glob("*.part")))
        semantic._download(source.as_uri(), target, good, 11)
        self.assertEqual(target.read_bytes(), b"model-bytes")
        evil = self.data / "evil.zip"
        with zipfile.ZipFile(evil, "w") as bundle:
            bundle.writestr("../escape.txt", "x")
        with self.assertRaises(semantic.SemanticError):
            semantic._extract(evil, self.data / "runtime")
        self.assertFalse((self.data / "escape.txt").exists())


if __name__ == "__main__":
    unittest.main()
