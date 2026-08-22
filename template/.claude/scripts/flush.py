#!/usr/bin/env python3
"""Flush a Claude Code transcript into the vault's machine-written daily log."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time
from typing import Any, Callable, Sequence


SCRIPT_DIR = Path(__file__).resolve().parent
VAULT_ROOT = SCRIPT_DIR.parent.parent
STATE_DIR = SCRIPT_DIR / ".state"
MAX_TURNS = 30
MAX_TRANSCRIPT_CHARS = 15_000

INVALID_UNICODE_ESCAPE = re.compile(r"\\u(?![0-9a-fA-F]{4})")
INVALID_JSON_ESCAPE = re.compile(r'\\(?!["\\/bfnrtu])')


def _iso_now() -> str:
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        os.replace(temporary, path)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def write_health(state_dir: Path, error: str) -> None:
    """Record the latest flush failure without allowing reporting to crash."""
    try:
        _atomic_write_json(
            state_dir / "health.json",
            {
                "ts": int(time.time()),
                "component": "flush",
                "error": error,
            },
        )
    except OSError:
        pass


def _repair_invalid_json_escapes(raw: str) -> str:
    repaired = INVALID_UNICODE_ESCAPE.sub(r"\\\\u", raw)
    return INVALID_JSON_ESCAPE.sub(r"\\\\", repaired)


def load_hook_input(path: Path) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8")
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        value = json.loads(_repair_invalid_json_escapes(raw))
    if not isinstance(value, dict):
        raise ValueError("hook-input-not-object")
    return value


def _message_parts(record: dict[str, Any]) -> tuple[str | None, Any]:
    message = record.get("message")
    if isinstance(message, dict):
        role = message.get("role") or record.get("type")
        return role, message.get("content")
    return record.get("role") or record.get("type"), record.get("content")


def _text_from_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, dict):
        if content.get("type") == "text" and isinstance(content.get("text"), str):
            return content["text"]
        return ""
    if not isinstance(content, list):
        return ""

    text_parts = []
    for block in content:
        if not isinstance(block, dict):
            continue
        if block.get("type") != "text":
            continue
        text = block.get("text")
        if isinstance(text, str):
            text_parts.append(text)
    return "\n".join(text_parts)


def read_transcript(path: Path) -> list[tuple[str, str]]:
    """Return user and assistant text turns from a Claude JSONL transcript."""
    turns: list[tuple[str, str]] = []
    with path.open("r", encoding="utf-8") as transcript:
        for line_number, raw_line in enumerate(transcript, start=1):
            if not raw_line.strip():
                continue
            try:
                record = json.loads(raw_line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"transcript-jsonl-invalid:{line_number}"
                ) from exc
            if not isinstance(record, dict):
                continue
            role, content = _message_parts(record)
            if role not in {"user", "assistant"}:
                continue
            text = _text_from_content(content)
            flattened = re.sub(r"\s+", " ", text).strip()
            if flattened:
                turns.append((role, flattened))
    return turns


def format_turns(
    turns: Sequence[tuple[str, str]],
    max_turns: int = MAX_TURNS,
    max_chars: int = MAX_TRANSCRIPT_CHARS,
) -> tuple[str, int]:
    """Keep the newest complete turns and snap a character cut to a turn."""
    selected = list(turns[-max_turns:])
    rendered = "\n".join(
        f"**{'User' if role == 'user' else 'Assistant'}:** {text}"
        for role, text in selected
    )
    if len(rendered) <= max_chars:
        return rendered, len(selected)

    tentative_start = len(rendered) - max_chars
    boundary = rendered.find("\n**", tentative_start)
    if boundary != -1:
        rendered = rendered[boundary + 1 :]
    else:
        role, text = selected[-1]
        prefix = f"**{'User' if role == 'user' else 'Assistant'}:** "
        rendered = prefix + text[-max(0, max_chars - len(prefix)) :]
    return rendered, len(selected)


def build_flush_prompt(transcript: str) -> str:
    return f"""Aşağıdaki oturumu Türkçe ve kalıcı hafıza açısından özetle.

Yanıtın TAM OLARAK şu beş bölümden oluşsun:
## Bağlam
## Önemli Konuşmalar
## Alınan Kararlar
## Öğrenilenler
## Yapılacaklar

Somut kararları, tercihleri, sonuçları ve açık işleri koru.
Araç çağrılarını, tekrarı ve geçici ayrıntıları çıkar.
Kalıcı değeri olan hiçbir şey yoksa yalnızca FLUSH_BOS yaz.

OTURUM:
{transcript}
"""


def _load_json_object(path: Path, default: dict[str, Any]) -> dict[str, Any]:
    if not path.exists():
        return default
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("state-not-object")
    return value


def _is_recent_duplicate(
    state_dir: Path,
    session_id: str,
    now_epoch: float,
) -> bool:
    state = _load_json_object(state_dir / "last-flush.json", {})
    if state.get("session_id") != session_id:
        return False
    timestamp = state.get("ts")
    if not isinstance(timestamp, (int, float)):
        return False
    return abs(now_epoch - float(timestamp)) < 60


def _write_last_flush(state_dir: Path, session_id: str, now_epoch: float) -> None:
    _atomic_write_json(
        state_dir / "last-flush.json",
        {"session_id": session_id, "ts": int(now_epoch)},
    )


def _run_claude(prompt: str, vault_root: Path) -> tuple[str | None, str | None]:
    claude = shutil.which("claude")
    if claude is None:
        return None, "claude-cli-missing"

    environment = os.environ.copy()
    environment["BEYIN_INVOKED_BY"] = "beyin-scripts"
    try:
        with tempfile.TemporaryDirectory(prefix="beyin-flush-") as temporary:
            temporary_path = Path(temporary).resolve()
            try:
                inside_vault = (
                    os.path.commonpath([temporary_path, vault_root.resolve()])
                    == str(vault_root.resolve())
                )
            except ValueError:
                inside_vault = False
            if inside_vault:
                return None, "temporary-directory-inside-vault"
            result = subprocess.run(
                [
                    claude,
                    "-p",
                    "--model",
                    "haiku",
                    "--output-format",
                    "text",
                ],
                input=prompt,
                text=True,
                capture_output=True,
                cwd=temporary_path,
                env=environment,
                timeout=240,
                check=False,
            )
    except subprocess.TimeoutExpired:
        return None, "claude-timeout"
    except OSError:
        return None, "claude-exec-error"

    if result.returncode != 0:
        return None, f"claude-exit-{result.returncode}"
    return result.stdout.strip(), None


def _append_daily(
    vault_root: Path,
    summary: str,
    reason: str,
    now: dt.datetime,
) -> None:
    daily_dir = vault_root / "daily"
    daily_dir.mkdir(parents=True, exist_ok=True)
    date_text = now.strftime("%Y-%m-%d")
    daily_path = daily_dir / f"{date_text}.md"
    if not daily_path.exists():
        daily_path.write_text(
            f"# Günlük Log: {date_text}\n\n## Oturumlar\n",
            encoding="utf-8",
        )

    suffix = ", compaction öncesi" if reason == "precompact" else ""
    with daily_path.open("a", encoding="utf-8") as daily_file:
        daily_file.write(
            f"\n### Oturum ({now.strftime('%H:%M')}){suffix}\n\n"
            f"{summary}\n"
        )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _effective_hour(now: dt.datetime) -> int:
    fake_hour = os.environ.get("BEYIN_FAKE_HOUR")
    if fake_hour is None:
        return now.hour
    hour = int(fake_hour)
    if not 0 <= hour <= 23:
        raise ValueError("fake-hour-out-of-range")
    return hour


def maybe_trigger_compile(
    vault_root: Path = VAULT_ROOT,
    now: dt.datetime | None = None,
    popen_factory: Callable[..., Any] | None = None,
) -> bool:
    """Start one detached evening compile when daily content has changed."""
    current = now or dt.datetime.now().astimezone()
    if _effective_hour(current) < 18:
        return False

    state_dir = vault_root / ".claude" / "scripts" / ".state"
    compile_state = _load_json_object(
        state_dir / "compile-state.json",
        {"ingested": {}},
    )
    ingested = compile_state.get("ingested", {})
    if not isinstance(ingested, dict):
        raise ValueError("compile-state-ingested-invalid")

    daily_dir = vault_root / "daily"
    daily_paths = sorted(daily_dir.glob("*.md")) if daily_dir.exists() else []
    changed = any(
        ingested.get(path.name) != _sha256(path) for path in daily_paths
    )
    if not changed:
        return False

    state_dir.mkdir(parents=True, exist_ok=True)
    trigger = state_dir / f"compile-trigger-{current.strftime('%Y-%m-%d')}"
    try:
        descriptor = os.open(trigger, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        return False
    os.close(descriptor)

    environment = os.environ.copy()
    environment.pop("BEYIN_INVOKED_BY", None)
    launcher = popen_factory or subprocess.Popen
    launcher(
        [sys.executable, str(vault_root / ".claude" / "scripts" / "compile.py")],
        cwd=vault_root,
        env=environment,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    return True


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hook-input", required=True, type=Path)
    parser.add_argument(
        "--reason",
        choices=("sessionend", "precompact"),
        default="sessionend",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    if os.environ.get("BEYIN_INVOKED_BY"):
        return 0

    try:
        args = _parse_args(argv)
    except SystemExit as exc:
        if exc.code:
            write_health(STATE_DIR, "invalid-arguments")
        return 0

    now_epoch = time.time()
    try:
        hook_input = load_hook_input(args.hook_input)
        session_id = hook_input.get("session_id")
        transcript_value = hook_input.get("transcript_path")
        if not isinstance(session_id, str) or not session_id:
            raise ValueError("session-id-missing")
        if not isinstance(transcript_value, str) or not transcript_value:
            raise ValueError("transcript-path-missing")
        transcript_path = Path(transcript_value).expanduser()

        if _is_recent_duplicate(STATE_DIR, session_id, now_epoch):
            return 0

        turns = read_transcript(transcript_path)
        transcript, turn_count = format_turns(turns)
        minimum_turns = 5 if args.reason == "precompact" else 1
        if turn_count < minimum_turns:
            _write_last_flush(STATE_DIR, session_id, now_epoch)
            return 0

        _write_last_flush(STATE_DIR, session_id, now_epoch)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        error = str(exc) or exc.__class__.__name__
        write_health(STATE_DIR, f"input:{error}")
        return 0

    summary, error = _run_claude(build_flush_prompt(transcript), VAULT_ROOT)
    if error is not None:
        write_health(STATE_DIR, error)
        return 0
    if not summary or summary == "FLUSH_BOS":
        return 0

    try:
        current = dt.datetime.now().astimezone()
        _append_daily(VAULT_ROOT, summary, args.reason, current)
        maybe_trigger_compile(VAULT_ROOT, current)
    except (OSError, ValueError, json.JSONDecodeError):
        write_health(STATE_DIR, "daily-or-trigger-failed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
