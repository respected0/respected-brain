#!/usr/bin/env python3
"""BR-019: real POSIX/WSL contracts that Windows simulations cannot prove."""
from __future__ import annotations

import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
from respected_brain.core import platform as RUNTIME
from respected_brain.integrations.planning import wsl_path

POSIX_ONLY = unittest.skipIf(os.name == "nt", "real POSIX execution is required")


class Br019PosixPlatformTest(unittest.TestCase):
    @POSIX_ONLY
    def test_detached_child_gets_its_own_session(self):
        child = subprocess.Popen(
            [sys.executable, "-c", "import os, sys, time; print(os.getsid(0)); sys.stdout.flush(); time.sleep(30)"],
            stdout=subprocess.PIPE, text=True, **RUNTIME.detached_process_options(),
        )
        try:
            self.assertEqual(child.stdout.readline().strip(), str(os.getsid(child.pid)))
            self.assertNotEqual(os.getsid(child.pid), os.getsid(0))
        finally:
            child.kill()
            child.wait(timeout=10)

    @POSIX_ONLY
    def test_sensitive_claim_file_is_owner_only_and_single_winner(self):
        with tempfile.TemporaryDirectory() as temporary:
            claim = Path(temporary) / "claim"
            self.assertTrue(RUNTIME.create_exclusive_claim(claim))
            self.assertFalse(RUNTIME.create_exclusive_claim(claim))
            self.assertEqual(stat.S_IMODE(claim.stat().st_mode) & 0o077, 0)

    @POSIX_ONLY
    def test_real_symlink_escape_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            vault, outside = base / "vault", base / "outside"
            vault.mkdir()
            outside.mkdir()
            (vault / "linked").symlink_to(outside, target_is_directory=True)
            inside = vault / "note.md"
            inside.write_text("x", encoding="utf-8")
            self.assertTrue(RUNTIME.path_within_vault(inside, vault))
            self.assertFalse(RUNTIME.path_within_vault(vault / "linked" / "note.md", vault))

    def test_wsl_windows_user_root_and_path_conversion(self):
        self.assertEqual(wsl_path(r"C:\Users\Ada\Documents\Brain"), "/mnt/c/Users/Ada/Documents/Brain")
        self.assertEqual(RUNTIME.windows_user_root(Path("/mnt/c/Users/Ada/Documents/Brain")), Path("/mnt/c/Users/Ada"))
        self.assertIsNone(RUNTIME.windows_user_root(Path("/mnt/d/Projects/Brain")))
        self.assertIsNone(RUNTIME.windows_user_root(Path("/home/ada/brain")))

    @POSIX_ONLY
    def test_source_cli_hook_returns_each_provider_contract(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            vault = root / "vault"
            vault.mkdir()
            env = {**os.environ, "HOME": str(root / "home"), "RESPECTED_APP_DIR": str(root / "app"),
                   "RESPECTED_DATA_DIR": str(root / "data"), "PYTHONUTF8": "1",
                   "PYTHONPATH": os.pathsep.join(filter(None, (str(ROOT / "src"), os.environ.get("PYTHONPATH"))))}
            registered = subprocess.run([sys.executable, "-m", "respected_brain", "vault", "register", str(vault)],
                                        env=env, capture_output=True, text=True, timeout=60)
            self.assertEqual(registered.returncode, 0, registered.stderr)
            for provider, key in (("claude", "hookSpecificOutput"), ("gemini", "hookSpecificOutput"),
                                  ("cursor", "additional_context"), ("antigravity", "injectSteps"),
                                  ("opencode", "additionalContext")):
                with self.subTest(provider=provider):
                    result = subprocess.run(
                        [sys.executable, "-m", "respected_brain", "hook", "--vault", str(vault),
                         "--provider", provider, "--event", "start"],
                        input="{}\n", env=env, capture_output=True, text=True, timeout=60,
                    )
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertIn(key, json.loads(result.stdout))


if __name__ == "__main__":
    unittest.main()
