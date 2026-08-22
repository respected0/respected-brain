#!/usr/bin/env python3
"""Compile changed daily logs into the vault's durable knowledge base."""

from __future__ import annotations

import argparse
import datetime as dt
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from typing import Any, Sequence


SCRIPT_DIR = Path(__file__).resolve().parent
VAULT_ROOT = SCRIPT_DIR.parent.parent
STATE_DIR = SCRIPT_DIR / ".state"

COMPILE_PROMPT = """BELLEK ŞEMASI KURALLARI
- Kavram dosyası knowledge/concepts/<ascii-kebab-slug>.md yolunda olmalı.
- YAML frontmatter alanları title, aliases, tags, sources, created, updated olmalı;
  sources günlük dosya adlarının listesi olmalı.
- Kavram gövdesi sırasıyla # Title, 2-4 cümlelik çekirdek açıklama,
  ## Önemli Noktalar altında 3-5 madde, ## Detaylar,
  ## İlgili Kavramlar altında en az iki wikilink ve her bağlantının nasıl
  ilişkili olduğunu anlatan bir cümle, son olarak ## Kaynaklar içermeli.
- Anlamlı kavram bağlantıları knowledge/connections/<a>--<b>.md yolunda,
  connects: [a, b] frontmatter alanı ve ## Bağlantı ile ## Ana Fikir
  bölümleriyle tutulmalı.
- knowledge/index.md tablosunun sütunları Makale | Özet | Kaynak |
  Güncellendi olmalı ve her makale için tek satır bulunmalı.
- knowledge/log.md girdisi `## [<ISO ts>] compile | <daily file>` başlığı,
  oluşturulan ve güncellenen listeleri ile 2-3 cümlelik not içermeli.

GÜNCEL KNOWLEDGE/INDEX.MD
{index_text}

GÜNLÜK DOSYASI: {daily_name}
{daily_body}

TALİMATLAR
1. Günlükten kalıcı değeri olan 2-6 kavram çıkar. Her kavram için yukarıdaki
   şemaya göre makale oluştur veya mevcut makaleyi güncelle.
2. İki kavram önemsiz olmayan biçimde bağlanıyorsa bağlantı dosyasını oluştur
   veya güncelle.
3. knowledge/index.md tablosunda her makale için tek satır tut; mevcut satırı
   yerinde güncelle. knowledge/log.md dosyasına bu derleme için tek blok ekle.
4. Verilen indeks önceden yüklenmiş tek bağlamdır. Yalnızca belirli aday
   makaleleri Grep ve Read ile incele. Knowledge dizinini topluca okuma.
5. Makaleleri kullanıcının dili olan Türkçe yaz. Slug değerlerini ASCII
   kebab-case biçiminde yaz.
6. Yeni bilgi mevcut bir makaleyle çelişiyorsa çelişkili kopya ekleme. Makaleyi
   düzeltilmiş duruma güncelle ve gövdesinde `Güncelleme: ...` notuyla düzeltmeyi
   belirt.
7. Kaynak listelerinde bu günlük dosyasını kullan: {daily_name}
8. Log zaman damgası olarak şunu kullan: {iso_timestamp}
"""


def _iso_now() -> str:
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        os.replace(temporary, path)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def write_health(state_dir: Path, error: str) -> None:
    try:
        _atomic_write_json(
            state_dir / "health.json",
            {
                "ts": int(time.time()),
                "component": "compile",
                "error": error,
            },
        )
    except OSError:
        pass


def _default_state() -> dict[str, Any]:
    return {
        "ingested": {},
        "last_run": "",
        "last_status": "ok",
        "runs": [],
    }


def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return _default_state()
    state = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(state, dict):
        raise ValueError("compile-state-not-object")
    ingested = state.get("ingested", {})
    runs = state.get("runs", [])
    if not isinstance(ingested, dict) or not isinstance(runs, list):
        raise ValueError("compile-state-schema-invalid")
    normalized = _default_state()
    normalized.update(state)
    normalized["ingested"] = ingested
    normalized["runs"] = runs[-20:]
    return normalized


def _save_state(path: Path, state: dict[str, Any]) -> None:
    state["runs"] = state.get("runs", [])[-20:]
    _atomic_write_json(path, state)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def changed_daily_logs(
    vault_root: Path,
    ingested: dict[str, str],
) -> list[tuple[Path, str]]:
    daily_dir = vault_root / "daily"
    if not daily_dir.exists():
        return []
    changed = []
    for path in sorted(daily_dir.glob("*.md"), key=lambda item: item.name):
        digest = _sha256(path)
        if ingested.get(path.name) != digest:
            changed.append((path, digest))
    return changed


def build_compile_prompt(
    index_text: str,
    daily_name: str,
    daily_body: str,
    timestamp: str,
) -> str:
    return COMPILE_PROMPT.format(
        index_text=index_text,
        daily_name=daily_name,
        daily_body=daily_body,
        iso_timestamp=timestamp,
    )


def _run_claude(prompt: str, vault_root: Path) -> str | None:
    claude = shutil.which("claude")
    if claude is None:
        return "claude-cli-missing"

    environment = os.environ.copy()
    environment["BEYIN_INVOKED_BY"] = "beyin-scripts"
    try:
        result = subprocess.run(
            [
                claude,
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
            input=prompt,
            text=True,
            capture_output=True,
            cwd=vault_root,
            env=environment,
            timeout=900,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return "claude-timeout"
    except OSError:
        return "claude-exec-error"
    if result.returncode != 0:
        return f"claude-exit-{result.returncode}"
    return None


def _append_run(
    state: dict[str, Any],
    timestamp: str,
    daily_name: str,
    status: str,
) -> None:
    state.setdefault("runs", []).append(
        {"ts": timestamp, "daily_file": daily_name, "status": status}
    )
    state["runs"] = state["runs"][-20:]


def _record_failure(
    state_path: Path,
    state: dict[str, Any],
    daily_name: str,
    reason: str,
) -> None:
    timestamp = _iso_now()
    state["last_run"] = timestamp
    state["last_status"] = f"fail:{reason}"
    _append_run(state, timestamp, daily_name, f"fail:{reason}")
    try:
        _save_state(state_path, state)
    except OSError:
        pass
    write_health(STATE_DIR, reason)


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--include-today",
        action="store_true",
        help="Uyumluluk bayrağı; günlüklerin tümü varsayılan olarak dahildir.",
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

    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        lock_file = (STATE_DIR / "compile.lock").open("a+", encoding="utf-8")
    except OSError:
        write_health(STATE_DIR, "lock-open-failed")
        return 0

    with lock_file:
        try:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return 0
        except OSError:
            write_health(STATE_DIR, "lock-failed")
            return 0

        state_path = STATE_DIR / "compile-state.json"
        try:
            state = load_state(state_path)
            changed = changed_daily_logs(VAULT_ROOT, state["ingested"])
        except (OSError, ValueError, json.JSONDecodeError):
            write_health(STATE_DIR, "state-or-daily-read-failed")
            return 0

        if args.dry_run:
            for daily_path, _digest in changed:
                print(daily_path.name)
            return 0

        if not changed:
            state["last_run"] = _iso_now()
            state["last_status"] = "ok"
            try:
                _save_state(state_path, state)
            except OSError:
                write_health(STATE_DIR, "state-write-failed")
            return 0

        for daily_path, digest in changed:
            timestamp = _iso_now()
            try:
                index_path = VAULT_ROOT / "knowledge" / "index.md"
                index_text = (
                    index_path.read_text(encoding="utf-8")
                    if index_path.exists()
                    else ""
                )
                daily_body = daily_path.read_text(encoding="utf-8")
            except OSError:
                _record_failure(
                    state_path,
                    state,
                    daily_path.name,
                    "source-read-failed",
                )
                return 0

            prompt = build_compile_prompt(
                index_text,
                daily_path.name,
                daily_body,
                timestamp,
            )
            error = _run_claude(prompt, VAULT_ROOT)
            if error is not None:
                _record_failure(state_path, state, daily_path.name, error)
                return 0

            state["ingested"][daily_path.name] = digest
            state["last_run"] = timestamp
            state["last_status"] = "ok"
            _append_run(state, timestamp, daily_path.name, "ok")
            try:
                _save_state(state_path, state)
            except OSError:
                write_health(STATE_DIR, "state-write-failed")
                return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
