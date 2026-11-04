#!/usr/bin/env python3
"""Çapraz Ajan Geçmiş Sohbet Madencisi - İkinci Beyin.

Yerel diskteki Claude Code, Google Antigravity ve OpenAI Codex oturum kayıtlarını
(JSONL) tarayarak ikinci beyin vault'una (daily/ veya inbox/dump) aktarır.
"""

from __future__ import annotations

from respected_brain.core.context import AppContext
from respected_brain.core.platform import path_within_vault
from respected_brain.maintenance import selected_vault, mutable_target, safe_walk
from respected_brain.maintenance._atomic import write_text_staged as _atomic_write_text
from respected_brain.memory.redact import redact

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
from typing import Any





class AgentHistoryMiner:
    """Yerel yapay zeka ajanlarının oturum geçmişlerini tarayan ve çıkaran motor."""

    def __init__(
        self,
        vault_root: Path,
        *,
        state_file: Path,
        temp_dir: Path | None = None,
        archive_dir: Path | None = None,
    ) -> None:
        self.vault_root = vault_root.resolve()
        self.state_file = mutable_target(None, state_file)
        self.temp_dir = temp_dir
        self.archive_dir = None
        if archive_dir is not None:
            archive = mutable_target(None, Path(archive_dir))
            if path_within_vault(archive, self.vault_root):
                raise ValueError("History archive must be outside the selected vault")
            self.archive_dir = archive
        self.imported_ids = self._load_state()

    def _load_state(self) -> set[str]:
        if self.state_file.is_file():
            try:
                data = json.loads(self.state_file.read_text(encoding="utf-8"))
                return set(data.get("imported_ids", []))
            except Exception:
                return set()
        return set()

    def _save_state(self) -> None:
        data = {"imported_ids": sorted(list(self.imported_ids))}
        _atomic_write_text(mutable_target(None, self.state_file), json.dumps(data, indent=2) + "\n")

    @staticmethod
    def _session_files(root: Path):
        for directory, _, names in safe_walk(root):
            for name in names:
                if name.endswith('.jsonl'):
                    yield Path(directory) / name

    def discover_antigravity_sessions(self) -> list[dict[str, Any]]:
        """Google Antigravity transcript.jsonl dosyalarını bulur."""
        sessions: list[dict[str, Any]] = []
        user_home = Path.home()
        antigravity_brain = user_home / ".gemini" / "antigravity-ide" / "brain"

        if not antigravity_brain.is_dir():
            return sessions

        for p in self._session_files(antigravity_brain):
            parts = p.relative_to(antigravity_brain).parts
            if len(parts) != 4 or parts[1:] != ('.system_generated', 'logs', 'transcript.jsonl'):
                continue
            # conversation id üst dizinlerden alınır
            conv_id = p.parents[2].name
            try:
                stat = p.stat()
                mtime = dt.datetime.fromtimestamp(stat.st_mtime)
                sessions.append({
                    "agent": "antigravity",
                    "id": f"antigravity_{conv_id}",
                    "path": p,
                    "mtime": mtime,
                })
            except OSError:
                continue

        return sessions

    def discover_claude_sessions(self) -> list[dict[str, Any]]:
        """Claude Code geçmiş oturumlarını bulur."""
        sessions: list[dict[str, Any]] = []
        user_home = Path.home()
        claude_dir = user_home / ".claude"

        if not claude_dir.is_dir():
            return sessions

        # Claude projelerindeki jsonl kayıtları
        for p in self._session_files(claude_dir):
            if "session" in p.name.lower() or "transcript" in p.name.lower() or len(p.stem) == 36:
                try:
                    stat = p.stat()
                    mtime = dt.datetime.fromtimestamp(stat.st_mtime)
                    sessions.append({
                        "agent": "claude",
                        "id": f"claude_{p.stem}",
                        "path": p,
                        "mtime": mtime,
                    })
                except OSError:
                    continue

        return sessions

    def discover_codex_sessions(self) -> list[dict[str, Any]]:
        """OpenAI Codex geçmiş oturumlarını bulur."""
        sessions: list[dict[str, Any]] = []
        user_home = Path.home()
        codex_dir = user_home / ".codex" / "sessions"

        if not codex_dir.is_dir():
            return sessions

        for p in self._session_files(codex_dir):
            try:
                stat = p.stat()
                mtime = dt.datetime.fromtimestamp(stat.st_mtime)
                sessions.append({
                    "agent": "codex",
                    "id": f"codex_{p.stem}",
                    "path": p,
                    "mtime": mtime,
                })
            except OSError:
                continue

        return sessions

    def parse_session(self, session_info: dict[str, Any]) -> dict[str, Any] | None:
        """JSONL dosyasını okuyup kullanıcı mesajlarını ve önemli kararları imbikten geçirir."""
        file_path = mutable_target(None, session_info["path"])
        agent = session_info["agent"]
        user_inputs: list[str] = []
        model_thoughts_or_summaries: list[str] = []
        event_time: dt.datetime | None = None

        try:
            with file_path.open("r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if not isinstance(record, dict):
                        continue
                    if event_time is None:
                        raw_time = record.get("created_at") or record.get("timestamp")
                        if isinstance(raw_time, str) and raw_time:
                            try:
                                event_time = dt.datetime.fromisoformat(raw_time.replace("Z", "+00:00"))
                            except ValueError:
                                pass

                    # Antigravity formatı
                    if agent == "antigravity":
                        msg_type = record.get("type", "")
                        content = str(record.get("content", "")).strip()
                        if msg_type == "USER_INPUT" and content:
                            user_inputs.append(content)
                        elif msg_type == "PLANNER_RESPONSE" and content:
                            if len(content) > 30 and not content.startswith("{"):
                                # sadece ilk 300 karakteri kaydet (özet için)
                                model_thoughts_or_summaries.append(content[:300].strip())

                    # Standart / Codex / Claude formatları
                    else:
                        message = record.get('message')
                        payload = record.get('payload')
                        entry = message if isinstance(message, dict) else payload if isinstance(payload, dict) else record
                        role = record.get("role") or record.get("source") or entry.get('role') or ""
                        if entry.get('type') == 'user_message':
                            role = 'user'
                        elif entry.get('type') == 'agent_message':
                            role = 'assistant'
                        raw = entry.get('content') or entry.get('text') or entry.get('message') or ''
                        if isinstance(raw, list):
                            content = '\n'.join(item.get('text', '') for item in raw if isinstance(item, dict) and isinstance(item.get('text'), str)).strip()
                        else:
                            content = raw.strip() if isinstance(raw, str) else ''
                        if role in ("user", "USER_EXPLICIT") and content:
                            user_inputs.append(content)
                        elif role in ("assistant", "MODEL") and content:
                            if len(content) > 30:
                                model_thoughts_or_summaries.append(content[:300].strip())

        except Exception:
            return None

        if not user_inputs:
            return None

        user_inputs = [redact(text) for text in user_inputs]
        summaries = [redact(text) for text in model_thoughts_or_summaries[:5]]
        title = redact(user_inputs[0][:100].replace("\n", " ").strip())
        # XML taglerini ve özel karakterleri temizle
        title = re.sub(r"<[^>]+>", "", title)
        title = re.sub(r"[#*`_\[\]]", "", title).strip() or "İsimsiz Oturum"
        title = title[:60].strip()

        return {
            "id": session_info["id"],
            "agent": agent,
            "title": title,
            "mtime": session_info["mtime"],
            "timestamp": event_time or session_info["mtime"],
            "source": str(file_path),
            "user_inputs": user_inputs,
            "summaries": summaries,
        }

    def preview_session(self, session_info: dict[str, Any]) -> dict[str, Any] | None:
        """Bir oturumun yazmadan önceki, maskelenmiş önizlemesini döndürür."""
        parsed = self.parse_session(session_info)
        if parsed is None:
            return None
        timestamp = parsed["timestamp"]
        return {
            "agent": parsed["agent"],
            "id": parsed["id"],
            "source": parsed["source"],
            "date": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "turns": len(parsed["user_inputs"]),
            "summary": parsed["title"],
            "already_imported": parsed["id"] in self.imported_ids,
        }

    def archive_session(self, parsed: dict[str, Any]) -> Path | None:
        """Açıkça etkinleştirildiyse redakte edilmiş transcript arşivini 0600 ile yazar."""
        if self.archive_dir is None or not parsed.get("source"):
            return None
        source = mutable_target(None, Path(parsed["source"]))
        identity_hash = hashlib.sha256(str(parsed["id"]).encode("utf-8")).hexdigest()[:16]
        target = self.archive_dir / f"{parsed['agent']}_{identity_hash}.jsonl"
        if not path_within_vault(target, self.archive_dir):
            raise ValueError("History archive path escapes its directory")
        _atomic_write_text(target, redact(source.read_text(encoding="utf-8", errors="replace")), temp_dir=self.temp_dir)
        os.chmod(target, 0o600)
        return target

    def import_session(self, parsed: dict[str, Any], target_folder: str = "daily") -> Path:
        """Ayrıştırılan oturumu vault içine markdown dosyası olarak yazar."""
        timestamp = parsed.get("timestamp") or parsed["mtime"]
        date_str = timestamp.strftime("%Y-%m-%d")
        time_str = timestamp.strftime("%H:%M:%S")

        title = redact(str(parsed["title"]))
        user_inputs = [redact(str(text)) for text in parsed["user_inputs"]]
        summaries = [redact(str(text)) for text in parsed["summaries"]]

        safe_slug = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in title)[:35]
        safe_slug = safe_slug.strip("._-") or "session"
        safe_agent_slug = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in parsed["agent"])[:30].strip("._-") or "agent"
        identity_hash = hashlib.sha256(str(parsed['id']).encode('utf-8')).hexdigest()[:16]
        filename = f"{date_str}_{safe_agent_slug}_{safe_slug}_{identity_hash}.md"

        if target_folder == "inbox":
            out_dir = self.vault_root / "📥 000-Inbox" / "Dump"
        else:
            out_dir = self.vault_root / "daily"

        if not path_within_vault(out_dir, self.vault_root):
            raise ValueError('History output escapes selected vault')
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / filename

        inputs_rendered = "\n".join(f"- {u[:200]}" for u in user_inputs[:10])
        summaries_rendered = "\n\n".join(f"> {s}..." for s in summaries)

        safe_title = json.dumps(title, ensure_ascii=False)
        safe_agent = json.dumps(parsed["agent"], ensure_ascii=False)
        safe_id = json.dumps(parsed["id"], ensure_ascii=False)
        safe_source = json.dumps(str(parsed.get("source", "")), ensure_ascii=False)

        content = (
            f"---\n"
            f"title: {safe_title}\n"
            f'created: "{date_str} {time_str}"\n'
            f'valid_at: "{date_str}"\n'
            f'recorded_at: "{dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}"\n'
            f"type: session-history\n"
            f"status: imported\n"
            f"agent: {safe_agent}\n"
            f"session_id: {safe_id}\n"
            f"source_file: {safe_source}\n"
            f"review_status: pending\n"
            f"freshness: dated\n"
            f'tags: ["gecmis-import", {safe_agent}]\n'
            f"---\n\n"
            f"# {title}\n\n"
            f"**Kaynak Ajan:** `{parsed['agent']}`  \n"
            f"**Tarih:** `{date_str} {time_str}`  \n"
            f"**Oturum Kimliği:** `{parsed['id']}`\n\n"
            f"## Kullanıcı İstekleri / Sorulan Konular\n\n"
            f"{inputs_rendered}\n\n"
            f"## Önemli Çıktılar ve Kararlar\n\n"
            f"{summaries_rendered}\n"
        )

        if not path_within_vault(out_file, self.vault_root):
            raise ValueError('History output contains a link')
        if out_file.exists():
            normalize = lambda text: re.sub(r'^recorded_at:.*$', '', text, flags=re.MULTILINE)
            if normalize(out_file.read_text(encoding='utf-8')) != normalize(content):
                raise ValueError(f'History note already exists or was edited: {out_file}')
        else:
            with out_file.open('x', encoding='utf-8', newline='\n') as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
        os.utime(out_file, (timestamp.timestamp(), timestamp.timestamp()))
        self.archive_session(parsed)
        was_imported = parsed['id'] in self.imported_ids
        self.imported_ids.add(parsed["id"])
        try:
            self._save_state()
        except Exception:
            if not was_imported:
                self.imported_ids.discard(parsed['id'])
            raise
        return out_file


def main(argv=None, *, ctx: AppContext | None = None) -> int:
    parser = argparse.ArgumentParser(description="Çapraz Ajan Geçmiş Madencisi")
    parser.add_argument("--source", choices=["all", "claude", "antigravity", "codex"], default="all", help="Taranacak ajan")
    parser.add_argument("--vault", type=Path, default=None, help="Vault kök dizini")
    parser.add_argument("--limit", type=int, default=10, help="Maksimum işlenecek oturum")
    parser.add_argument("--target", choices=["daily", "inbox"], default="daily", help="Hedef klasör")
    parser.add_argument("--session-id", action="append", default=[], help="Açıkça seçilen oturum; tekrarlanabilir")
    parser.add_argument("--apply", action="store_true", help="Seçilen oturumları yaz")
    parser.add_argument("--archive", action="store_true", help="Redakte edilmiş transcript arşivini de yaz")
    parser.add_argument("--dry-run", action="store_true", help="Geriye uyumlu: önizleme varsayılandır")
    parser.add_argument("--force", action="store_true", help="Önizlemede daha önce aktarılmış olanları da göster")

    args = parser.parse_args(argv)
    vault = selected_vault(ctx, args.vault)
    if ctx is None:
        raise ValueError("Agent history requires an explicit data context")
    archive_dir = ctx.paths.data_root / "archives" / "agent-history" if args.archive else None
    miner = AgentHistoryMiner(
        vault,
        state_file=ctx.paths.state_dir / "imported_sessions.json",
        temp_dir=ctx.paths.cache_dir,
        archive_dir=archive_dir,
    )

    candidates: list[dict[str, Any]] = []
    if args.source in ("all", "antigravity"):
        candidates.extend(miner.discover_antigravity_sessions())
    if args.source in ("all", "claude"):
        candidates.extend(miner.discover_claude_sessions())
    if args.source in ("all", "codex"):
        candidates.extend(miner.discover_codex_sessions())

    # Tarihe göre en yeniden eskiye sırala
    candidates.sort(key=lambda x: x["mtime"], reverse=True)

    print(f"Toplam {len(candidates)} ajan oturum dosyası bulundu.")

    selected = set(args.session_id)
    if args.apply and not selected:
        print("Yazma reddedildi: --apply için en az bir --session-id seçin.")
        return 2
    if args.apply:
        by_id = {candidate["id"]: candidate for candidate in candidates}
        missing = [session_id for session_id in args.session_id if session_id not in by_id]
        if missing:
            print("Oturum bulunamadı: " + ", ".join(missing))
            return 2
        imported_count = 0
        for session_id in dict.fromkeys(args.session_id):
            parsed = miner.parse_session(by_id[session_id])
            if parsed is None:
                print(f"[Atlandı] {session_id}: okunabilir kullanıcı mesajı yok")
                continue
            written_file = miner.import_session(parsed, target_folder=args.target)
            print(f"[Aktarıldı] {written_file.name} ({parsed['agent']})")
            imported_count += 1
        print(f"\nİşlem tamamlandı: {imported_count} seçili oturum vault'a aktarıldı.")
        return 0

    previewed = 0
    skipped_count = 0
    for candidate in candidates:
        if selected and candidate["id"] not in selected:
            continue
        if not selected and previewed >= max(args.limit, 0):
            break
        if not selected and not args.force and candidate["id"] in miner.imported_ids:
            skipped_count += 1
            continue
        preview = miner.preview_session(candidate)
        if preview is None:
            continue
        marker = " [zaten aktarılmış]" if preview["already_imported"] else ""
        print(
            f"[Önizleme] {preview['agent'].upper()} | {preview['date']} | {preview['id']} | "
            f"{preview['turns']} tur | {preview['summary']}{marker}\n"
            f"  kaynak: {preview['source']}"
        )
        previewed += 1
    print(
        f"\nÖnizleme bitti: {previewed} oturum gösterildi, {skipped_count} zaten aktarılmış. "
        "Yazmak için --apply --session-id <kimlik> kullanın."
    )
    return 0
