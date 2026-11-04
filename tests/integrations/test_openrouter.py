"""OpenRouter permission, credential, HTTP and cost contracts."""
from __future__ import annotations

from contextlib import redirect_stdout
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
import json
import os
from pathlib import Path
import stat
import threading
import unittest
from unittest import mock
from unittest.mock import patch

from respected_brain.cli import main
from respected_brain.core.config import ConfigStore
from respected_brain.providers import openrouter, runner
from tests.support.files import make_context


class _Handler(BaseHTTPRequestHandler):
    status = 200
    body: dict = {}
    calls: list[dict] = []

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        self.calls.append({
            "headers": dict(self.headers),
            "body": json.loads(self.rfile.read(length).decode("utf-8")),
        })
        payload = json.dumps(self.body).encode("utf-8")
        self.send_response(self.status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, *args):
        pass


class OpenRouterTest(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.ctx = make_context(self.root)

    def server(self, status=200, body=None):
        _Handler.status = status
        _Handler.body = body or {
            "choices": [{"message": {"content": "ozet"}}],
            "usage": {"prompt_tokens": 12, "completion_tokens": 3, "total_tokens": 15, "cost": 0.00042},
        }
        _Handler.calls = []
        server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(thread.join, 2)
        self.addCleanup(server.shutdown)
        return f"http://127.0.0.1:{server.server_address[1]}/v1/chat/completions"

    def test_auto_mode_never_reaches_a_paid_provider_without_opt_in(self):
        self.assertEqual(runner._available(None, {}), list(runner.LOCAL_PROVIDERS))
        self.assertNotIn("openrouter", runner._available(None, {"provider_allow_paid": False}))
        self.assertEqual(runner._available(None, {"provider_allow_paid": True})[-1], "openrouter")

    def test_explicit_selection_is_the_permission(self):
        preferences = {"summary_provider": "openrouter", "provider_fallback": False}
        self.assertEqual(runner._available(None, preferences), ["openrouter"])

    def test_missing_key_makes_no_network_call(self):
        config = ConfigStore(self.ctx.paths.data_root).update(
            lambda document: document["preferences"].update(summary_provider="openrouter", provider_fallback=False)
        )
        self.ctx = self.ctx.__class__(self.ctx.paths, config, self.ctx.resources)
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": ""}), patch("urllib.request.urlopen") as opened:
            text, error, provider = runner.run_model("prompt", self.ctx.paths.vault_root, "text", 5, ctx=self.ctx)
        self.assertEqual((text, error, provider), (None, "openrouter-key-missing", "openrouter"))
        opened.assert_not_called()

    def test_request_shape_response_and_cost_ledger(self):
        endpoint = self.server()
        openrouter.store_key(self.ctx.paths.data_root, "sk-or-test-secret")
        text, error = openrouter.complete(
            "merhaba", data_root=self.ctx.paths.data_root, model="openai/test-model",
            timeout=5, endpoint=endpoint, state_dir=self.ctx.paths.state_dir,
        )
        self.assertEqual((text, error), ("ozet", None))
        call = _Handler.calls[0]
        self.assertEqual(call["headers"]["Authorization"], "Bearer sk-or-test-secret")
        self.assertEqual(call["body"], {"model": "openai/test-model", "messages": [{"role": "user", "content": "merhaba"}]})
        ledger = (self.ctx.paths.state_dir / "provider-usage.jsonl").read_text(encoding="utf-8")
        record = json.loads(ledger)
        self.assertEqual((record["provider"], record["model"], record["total_tokens"], record["cost"]), ("openrouter", "openai/test-model", 15, 0.00042))
        self.assertNotIn("sk-or-test-secret", ledger)

    def test_provider_error_never_echoes_the_key(self):
        endpoint = self.server(status=500, body={"error": "sk-or-test-secret"})
        openrouter.store_key(self.ctx.paths.data_root, "sk-or-test-secret")
        text, error = openrouter.complete("prompt", data_root=self.ctx.paths.data_root, timeout=5, endpoint=endpoint)
        self.assertEqual((text, error), (None, "openrouter-http-500:network"))
        self.assertNotIn("sk-or-test-secret", error)

    def test_corrupt_credential_is_a_safe_error(self):
        path = openrouter.credential_path(self.ctx.paths.data_root)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"not-a-credential")
        with self.assertRaises(openrouter.CredentialError) as raised:
            openrouter.load_key(self.ctx.paths.data_root)
        self.assertEqual(raised.exception.code, "openrouter-key-unreadable")
        self.assertNotIn("not-a-credential", str(raised.exception))

    @unittest.skipUnless(os.name == "nt", "Window DPAPI only")
    def test_dpapi_round_trip(self):
        openrouter.store_key(self.ctx.paths.data_root, "sk-or-dpapi")
        self.assertEqual(openrouter.load_key(self.ctx.paths.data_root), "sk-or-dpapi")
        self.assertEqual(openrouter.status(self.ctx.paths.data_root)["protection"], "dpapi")
        self.assertNotIn(b"sk-or-dpapi", openrouter.credential_path(self.ctx.paths.data_root).read_bytes())

    @unittest.skipIf(os.name == "nt", "POSIX permissions only")
    def test_posix_credential_is_0600(self):
        openrouter.store_key(self.ctx.paths.data_root, "sk-or-posix")
        mode = stat.S_IMODE(openrouter.credential_path(self.ctx.paths.data_root).stat().st_mode)
        self.assertEqual(mode, 0o600)
        self.assertEqual(openrouter.load_key(self.ctx.paths.data_root), "sk-or-posix")

    def test_paid_fallback_runs_only_after_explicit_opt_in(self):
        self.ctx.config["preferences"].update(provider_allow_paid=True, summary_provider="auto")
        with patch.object(runner, "_command", return_value=None), patch.object(
            openrouter, "complete", return_value=("ozet", None)
        ) as paid:
            result = runner.run_model("prompt", self.ctx.paths.vault_root, "text", 5, ctx=self.ctx)
        self.assertEqual(result, ("ozet", None, "openrouter"))
        self.assertEqual(paid.call_count, 1)

        self.ctx.config["preferences"].update(provider_allow_paid=False)
        with patch.object(runner, "_command", return_value=None), patch.object(openrouter, "complete") as paid:
            result = runner.run_model("prompt", self.ctx.paths.vault_root, "text", 5, ctx=self.ctx)
        self.assertEqual(result, (None, "model-cli-missing", None))
        paid.assert_not_called()

    def test_cli_stores_and_clears_without_echoing_the_key(self):
        env = {
            **os.environ,
            "RESPECTED_APP_DIR": str(self.root / "app"),
            "RESPECTED_DATA_DIR": str(self.root / "data"),
        }
        with patch.dict(os.environ, env), patch("sys.stdin", io.StringIO("sk-or-cli\n")):
            output = io.StringIO()
            with redirect_stdout(output):
                code = main(["credential", "set", "openrouter"])
        self.assertEqual(code, 0)
        self.assertTrue(json.loads(output.getvalue())["configured"])
        self.assertNotIn("sk-or-cli", output.getvalue())
        self.assertEqual(openrouter.load_key(self.root / "data"), "sk-or-cli")

        output = io.StringIO()
        with patch.dict(os.environ, env), redirect_stdout(output):
            self.assertEqual(main(["credential", "clear", "openrouter"]), 0)
        self.assertFalse(json.loads(output.getvalue())["configured"])
        self.assertIsNone(openrouter.load_key(self.root / "data"))


if __name__ == "__main__":
    unittest.main()
