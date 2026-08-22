#!/usr/bin/env python3
"""Self-contained tests for the v2 flush and compile scripts."""

from __future__ import annotations

import datetime as dt
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import uuid


REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE_SCRIPTS = REPO_ROOT / "template" / ".claude" / "scripts"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Modül yüklenemedi: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


FLUSH = load_module("beyin_flush_test", SOURCE_SCRIPTS / "flush.py")


class ScriptsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="beyin-tests-")
        self.root = Path(self.temporary.name)
        self.vault = self.root / "vault"
        self.scripts = self.vault / ".claude" / "scripts"
        self.state = self.scripts / ".state"
        self.daily = self.vault / "daily"
        self.knowledge = self.vault / "knowledge"
        self.bin_dir = self.root / "bin"
        self.scripts.mkdir(parents=True)
        self.state.mkdir()
        self.daily.mkdir()
        self.knowledge.mkdir()
        self.bin_dir.mkdir()
        shutil.copy2(SOURCE_SCRIPTS / "flush.py", self.scripts / "flush.py")
        shutil.copy2(SOURCE_SCRIPTS / "compile.py", self.scripts / "compile.py")
        (self.knowledge / "index.md").write_text(
            "# Bilgi İndeksi\n", encoding="utf-8"
        )
        self.stub_log = self.root / "claude-calls.jsonl"
        self._write_claude_stub()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _write_claude_stub(self) -> None:
        stub = self.bin_dir / "claude"
        stub.write_text(
            """#!/usr/bin/env python3
import json
import os
from pathlib import Path
import sys

prompt = sys.stdin.read()
log_path = os.environ.get("BEYIN_TEST_LOG")
if log_path:
    with Path(log_path).open("a", encoding="utf-8") as log:
        log.write(json.dumps({
            "argv": sys.argv[1:],
            "cwd": os.getcwd(),
            "guard": os.environ.get("BEYIN_INVOKED_BY"),
            "prompt": prompt,
        }, ensure_ascii=False) + "\\n")
output = os.environ.get("BEYIN_TEST_OUTPUT", "derleme tamamlandı")
if output:
    print(output)
raise SystemExit(int(os.environ.get("BEYIN_TEST_EXIT", "0")))
""",
            encoding="utf-8",
        )
        stub.chmod(0o755)

    def _environment(self, **overrides: str) -> dict[str, str]:
        environment = os.environ.copy()
        environment.pop("BEYIN_INVOKED_BY", None)
        environment["PATH"] = f"{self.bin_dir}{os.pathsep}{environment['PATH']}"
        environment["BEYIN_TEST_LOG"] = str(self.stub_log)
        environment["BEYIN_FAKE_HOUR"] = "0"
        environment.update(overrides)
        return environment

    def _write_transcript(
        self,
        turns: list[tuple[str, object]],
        name: str = "transcript.jsonl",
    ) -> Path:
        transcript = self.root / name
        with transcript.open("w", encoding="utf-8") as target:
            for role, content in turns:
                target.write(
                    json.dumps(
                        {
                            "type": role,
                            "message": {"role": role, "content": content},
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )
        return transcript

    def _write_hook(self, session_id: str, transcript: Path) -> Path:
        hook = self.root / f"hook-{uuid.uuid4().hex}.json"
        hook.write_text(
            json.dumps(
                {
                    "session_id": session_id,
                    "transcript_path": str(transcript),
                }
            ),
            encoding="utf-8",
        )
        return hook

    def _run_flush(
        self,
        hook: Path,
        reason: str = "sessionend",
        **environment: str,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(self.scripts / "flush.py"),
                "--hook-input",
                str(hook),
                "--reason",
                reason,
            ],
            cwd=self.vault,
            env=self._environment(**environment),
            text=True,
            capture_output=True,
            timeout=10,
            check=False,
        )

    def _run_compile(
        self,
        *arguments: str,
        **environment: str,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(self.scripts / "compile.py"), *arguments],
            cwd=self.vault,
            env=self._environment(**environment),
            text=True,
            capture_output=True,
            timeout=10,
            check=False,
        )

    def _stub_calls(self) -> list[dict[str, object]]:
        if not self.stub_log.exists():
            return []
        return [
            json.loads(line)
            for line in self.stub_log.read_text(encoding="utf-8").splitlines()
        ]

    def test_transcript_extraction_turn_and_character_caps(self) -> None:
        turns = []
        for number in range(35):
            role = "user" if number % 2 == 0 else "assistant"
            content = [
                {"type": "thinking", "thinking": "gizli"},
                {"type": "text", "text": f"turn {number}"},
                {"type": "tool_use", "name": "ignored"},
            ]
            turns.append((role, content))
        transcript = self._write_transcript(turns)
        extracted = FLUSH.read_transcript(transcript)
        rendered, count = FLUSH.format_turns(extracted)
        self.assertEqual(count, 30)
        self.assertNotIn("turn 4", rendered)
        self.assertIn("turn 5", rendered)
        self.assertNotIn("gizli", rendered)

        long_turns = [
            ("user" if number % 2 == 0 else "assistant", f"id{number}:" + "x" * 700)
            for number in range(30)
        ]
        capped, capped_count = FLUSH.format_turns(long_turns)
        self.assertEqual(capped_count, 30)
        self.assertLessEqual(len(capped), 15_000)
        self.assertTrue(capped.startswith("**"))
        self.assertRegex(capped, r"^\*\*(User|Assistant):\*\* id\d+:")

    def test_flush_bos_appends_nothing_and_records_dedup(self) -> None:
        transcript = self._write_transcript([("user", "yalnızca selam")])
        hook = self._write_hook("bos-session", transcript)
        result = self._run_flush(hook, BEYIN_TEST_OUTPUT="FLUSH_BOS")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(list(self.daily.glob("*.md")), [])
        last_flush = json.loads(
            (self.state / "last-flush.json").read_text(encoding="utf-8")
        )
        self.assertEqual(last_flush["session_id"], "bos-session")

    def test_daily_skeleton_creation_and_claude_contract(self) -> None:
        transcript = self._write_transcript(
            [("user", "karar aldık"), ("assistant", "uygulandı")]
        )
        hook = self._write_hook("daily-session", transcript)
        summary = "## Bağlam\nKalıcı özet"
        result = self._run_flush(hook, BEYIN_TEST_OUTPUT=summary)
        self.assertEqual(result.returncode, 0, result.stderr)
        daily_files = list(self.daily.glob("*.md"))
        self.assertEqual(len(daily_files), 1)
        body = daily_files[0].read_text(encoding="utf-8")
        self.assertTrue(body.startswith(f"# Günlük Log: {daily_files[0].stem}"))
        self.assertIn("## Oturumlar", body)
        self.assertIn("### Oturum (", body)
        self.assertIn(summary, body)

        calls = self._stub_calls()
        self.assertEqual(len(calls), 1)
        self.assertEqual(
            calls[0]["argv"],
            ["-p", "--model", "haiku", "--output-format", "text"],
        )
        self.assertEqual(calls[0]["guard"], "beyin-scripts")
        self.assertNotEqual(Path(str(calls[0]["cwd"])), self.vault)

    def test_dedup_guard_avoids_second_call_and_append(self) -> None:
        transcript = self._write_transcript([("user", "aynı oturum")])
        hook = self._write_hook("duplicate-session", transcript)
        first = self._run_flush(hook, BEYIN_TEST_OUTPUT="özet")
        second = self._run_flush(hook, BEYIN_TEST_OUTPUT="özet")
        self.assertEqual(first.returncode, 0)
        self.assertEqual(second.returncode, 0)
        self.assertEqual(len(self._stub_calls()), 1)
        daily_body = next(self.daily.glob("*.md")).read_text(encoding="utf-8")
        self.assertEqual(daily_body.count("### Oturum ("), 1)

    def test_precompact_minimum_turns(self) -> None:
        transcript = self._write_transcript(
            [("user", "bir"), ("assistant", "iki"), ("user", "üç")]
        )
        hook = self._write_hook("short-precompact", transcript)
        result = self._run_flush(hook, reason="precompact")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(self._stub_calls(), [])
        self.assertTrue((self.state / "last-flush.json").exists())

    def test_trigger_hour_changed_hash_and_single_claim(self) -> None:
        daily_path = self.daily / "2026-08-22.md"
        daily_path.write_text("ilk sürüm", encoding="utf-8")
        digest = hashlib.sha256(daily_path.read_bytes()).hexdigest()
        (self.state / "compile-state.json").write_text(
            json.dumps({"ingested": {daily_path.name: digest}}),
            encoding="utf-8",
        )
        launches = []

        def fake_popen(*args, **kwargs):
            launches.append((args, kwargs))
            return object()

        os.environ["BEYIN_FAKE_HOUR"] = "19"
        try:
            unchanged = FLUSH.maybe_trigger_compile(
                self.vault,
                dt.datetime(2026, 8, 22, 19, 0),
                fake_popen,
            )
            self.assertFalse(unchanged)
            daily_path.write_text("değişti", encoding="utf-8")
            os.environ["BEYIN_FAKE_HOUR"] = "17"
            too_early = FLUSH.maybe_trigger_compile(
                self.vault,
                dt.datetime(2026, 8, 22, 17, 0),
                fake_popen,
            )
            self.assertFalse(too_early)
            os.environ["BEYIN_FAKE_HOUR"] = "19"
            claimed = FLUSH.maybe_trigger_compile(
                self.vault,
                dt.datetime(2026, 8, 22, 19, 0),
                fake_popen,
            )
            claimed_twice = FLUSH.maybe_trigger_compile(
                self.vault,
                dt.datetime(2026, 8, 22, 19, 1),
                fake_popen,
            )
        finally:
            os.environ.pop("BEYIN_FAKE_HOUR", None)

        self.assertTrue(claimed)
        self.assertFalse(claimed_twice)
        self.assertEqual(len(launches), 1)
        launch_environment = launches[0][1]["env"]
        self.assertNotIn("BEYIN_INVOKED_BY", launch_environment)
        self.assertTrue(
            (self.state / "compile-trigger-2026-08-22").exists()
        )

    def test_compile_flock_exclusion(self) -> None:
        (self.daily / "2026-08-20.md").write_text("log", encoding="utf-8")
        lock_path = self.state / "compile.lock"
        with lock_path.open("a+", encoding="utf-8") as lock_file:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            result = self._run_compile("--dry-run")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertEqual(self._stub_calls(), [])

    def test_compile_hash_skip_on_unchanged_log(self) -> None:
        daily_path = self.daily / "2026-08-20.md"
        daily_path.write_text("kalıcı günlük", encoding="utf-8")
        first = self._run_compile()
        second = self._run_compile()
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(len(self._stub_calls()), 1)
        state = json.loads(
            (self.state / "compile-state.json").read_text(encoding="utf-8")
        )
        expected = hashlib.sha256(daily_path.read_bytes()).hexdigest()
        self.assertEqual(state["ingested"][daily_path.name], expected)
        call = self._stub_calls()[0]
        self.assertEqual(
            call["argv"],
            [
                "-p",
                "--model",
                "sonnet",
                "--output-format",
                "text",
                "--permission-mode",
                "acceptEdits",
                "--allowedTools",
                "Read,Write,Edit,Glob,Grep",
            ],
        )
        self.assertEqual(Path(str(call["cwd"])).resolve(), self.vault.resolve())
        self.assertEqual(call["guard"], "beyin-scripts")

    def test_compile_stops_batch_on_first_failure(self) -> None:
        (self.daily / "2026-08-19.md").write_text("bir", encoding="utf-8")
        (self.daily / "2026-08-20.md").write_text("iki", encoding="utf-8")
        result = self._run_compile(BEYIN_TEST_EXIT="7")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(self._stub_calls()), 1)
        state = json.loads(
            (self.state / "compile-state.json").read_text(encoding="utf-8")
        )
        self.assertEqual(state["ingested"], {})
        self.assertEqual(state["last_status"], "fail:claude-exit-7")
        health = json.loads(
            (self.state / "health.json").read_text(encoding="utf-8")
        )
        self.assertEqual(health["component"], "compile")

    def test_recursion_guard_exits_both_scripts(self) -> None:
        missing_hook = self.root / "does-not-exist.json"
        environment = self._environment(BEYIN_INVOKED_BY="outer")
        flush_result = subprocess.run(
            [
                sys.executable,
                str(self.scripts / "flush.py"),
                "--hook-input",
                str(missing_hook),
            ],
            cwd=self.vault,
            env=environment,
            text=True,
            capture_output=True,
            timeout=10,
            check=False,
        )
        compile_result = subprocess.run(
            [sys.executable, str(self.scripts / "compile.py")],
            cwd=self.vault,
            env=environment,
            text=True,
            capture_output=True,
            timeout=10,
            check=False,
        )
        self.assertEqual(flush_result.returncode, 0)
        self.assertEqual(compile_result.returncode, 0)
        self.assertEqual(self._stub_calls(), [])
        self.assertFalse((self.state / "health.json").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
