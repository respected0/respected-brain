"""Package-owned MCP server; stdout contains JSONRPC only."""
from __future__ import annotations
import json
import os
from pathlib import Path
import re
import sys
from typing import Any
from respectedbrain import __version__
from respectedbrain.core.platform import path_within_vault
from respectedbrain.core.coordination import guarded_writer
from respectedbrain.search.engine import SearchEngine
from ..notes import MAX_NOTE_BYTES, note_path, read_note
from .tools import WRITE_TOOLS, tool_definitions

def _detect_vault_identity(ctx):
    from ..global_config import identity_settings
    settings = identity_settings(ctx)
    return str(settings["OS_NAME"]), str(settings["COMPANION"])


WRITE_OFF = "Hata: Not yazma izni kapalı. Kullanıcı, SecondBrain ayarlarında 'MCP ile not kaydetmeye izin ver' (mcp_write) seçeneğini açmalıdır."


class RespectedMcpServer:
    """Respected Brain Vault MCP stdio Sunucusu."""

    SERVER_NAME = "respected-vault-mcp"
    SERVER_VERSION = __version__
    PROTOCOL_VERSION = "2024-11-05"

    def __init__(self, ctx) -> None:
        self.ctx = ctx
        self.vault_root = ctx.paths.vault_root
        self.os_name, self.companion_name = _detect_vault_identity(ctx)
        self.search_engine = SearchEngine(ctx)

    MAX_NOTE_BYTES = MAX_NOTE_BYTES

    def _safe_resolve(self, relative_path: str) -> Path | None:
        return note_path(self.vault_root, relative_path)

    def _read_optional(self, relative: str, max_chars: int | None = None) -> str:
        try:
            return read_note(self.vault_root, relative, max_chars=max_chars)
        except (OSError, ValueError):
            return ''

    def _validate_arguments(self, name, arguments) -> None:
        if not isinstance(arguments, dict):
            raise ValueError('arguments must be an object')
        manifest = next((tool for tool in self.get_tools_manifest() if tool['name'] == name), None)
        if manifest is None:
            return
        schema = manifest['inputSchema']
        for required in schema.get('required', []):
            if required not in arguments:
                raise ValueError('missing argument: ' + required)
        for key, value in arguments.items():
            specification = schema['properties'].get(key)
            if specification is None:
                continue
            kind = specification['type']
            valid = ((kind == 'string' and isinstance(value, str)) or
                     (kind == 'integer' and type(value) is int) or
                     (kind == 'array' and isinstance(value, list) and all(isinstance(v, str) for v in value)))
            if not valid or ('enum' in specification and value not in specification['enum']):
                raise ValueError('invalid argument: ' + key)
        if name in {'respected_quick_capture', 'respected_remember'}:
            if not arguments.get('title', '').strip() or not arguments.get('content', '').strip():
                raise ValueError('title and content cannot be empty')
            if arguments.get('scope') == 'project' and not arguments.get('project', '').strip():
                raise ValueError('project is required for project scope')

    def _write_enabled(self) -> bool:
        """Saving notes through MCP is a user permission (setting `mcp_write`, default off), read fresh on every call."""
        try:
            from respectedbrain.core.config import ConfigStore
            return (ConfigStore(self.ctx.paths.data_root).read().get("preferences") or {}).get("mcp_write") is True
        except Exception:
            return False

    def _save_inbox_note(self, name: str, arguments: dict[str, Any]) -> str:
        """Both write tools land in one fixed inbox (never Knowledge/Projects), with ownership front matter and a revert record."""
        import uuid
        from respectedbrain.rpp import memory_write as writes
        title = str(arguments.get("title", "")).strip()
        body = str(arguments.get("content", "")).strip()
        tags = arguments.get("tags", [])
        if not 1 <= len(title) <= 120 or not body or len(body) > 20000:
            return "Hata: Başlık 1-120, içerik 1-20000 karakter olmalı."
        if len(tags) > 8 or not all(re.fullmatch(r"[\w-]{1,32}", t) for t in tags):
            return "Hata: En fazla 8 etiket; her biri 1-32 harf, rakam, _ veya -."
        if name == "respected_remember":
            confidence = arguments.get("confidence", "unverified")
            if confidence == "verified":  # a model cannot vouch for its own note
                confidence = "inferred"
            supersedes = ", ".join(json.dumps(str(s)[:200], ensure_ascii=False) for s in arguments.get("supersedes", [])[:20])
            extra = ["type: lesson", f"scope: {arguments.get('scope', 'general')}", f"confidence: {confidence}",
                     f"project: {json.dumps(str(arguments.get('project', ''))[:100], ensure_ascii=False)}", f"supersedes: [{supersedes}]"]
        else:
            extra = ["type: capture", "status: inbox"]
        extra.append("review: pending")
        operation_id = "mcp-" + uuid.uuid4().hex[:24]
        try:
            result = writes.write_mcp(self.ctx, operation_id, title, body, tags, extra)
        except writes.MemoryOpError as error:
            return f"Hata: {error.message}"
        return (f"Başarılı: Not '{result['path']}' gelen kutusuna kaydedildi (kullanıcı incelemesi bekliyor; kalıcı bilgiye kendiliğinden "
                f"geçmez). Geri almak için respected_revert_note işlem kimliği: {operation_id}")

    def get_tools_manifest(self) -> list[dict[str, Any]]:
        """Sunulan araçlar; not yazan araçlar yalnızca kullanıcı izin verdiyse görünür."""
        tools = self._all_tools()
        if self._write_enabled():
            return tools
        return [tool for tool in tools if tool["name"] not in WRITE_TOOLS]

    def _all_tools(self) -> list[dict[str, Any]]:
        return tool_definitions(self.os_name, self.companion_name)

    @guarded_writer(busy_result=None)
    def call_tool(self, name: str, arguments: dict[str, Any]) -> str:
        """İlgili aracı çalıştırıp metin yanıtı döndürür."""
        try:
            self._validate_arguments(name, arguments)
        except ValueError as error:
            return f'Hata: {error}'
        if name == "respected_search":
            query = arguments.get("query", "")
            limit = max(0, min(100, arguments.get("limit", 5)))
            category = arguments.get("category")
            results = self.search_engine.search(query, limit=limit, category=category)
            if not results:
                return f"'{query}' sorgusu için {self.os_name} içinde eşleşen not bulunamadı."

            lines = [f"### {self.os_name} Arama Sonuçları: '{query}' ({len(results)} sonuç)\n"]
            for r in results:
                lines.append(f"- **[{r['title']}]({r['path']})** (Kategori: `{r['category']}`, Skor: {r['score']})")
                if r.get("snippet"):
                    lines.append(f"  > {r['snippet']}\n")
            return "\n".join(lines)

        elif name == "respected_get_note":
            rel_path = arguments.get("path", "")
            target = self._safe_resolve(rel_path)
            if not target or not target.is_file():
                return f"Hata: '{rel_path}' dosyası {self.os_name} vault'u içinde bulunamadı."
            try:
                if target.stat().st_size > self.MAX_NOTE_BYTES:
                    return f"Hata: '{rel_path}' çok büyük ({target.stat().st_size} bayt). Güvenlik sınırı: {self.MAX_NOTE_BYTES} bayt."
                content = read_note(self.vault_root, rel_path)
                return f"### Dosya: {rel_path}\n\n{content}"
            except Exception as e:
                return f"Dosya okunurken hata oluştu: {e}"

        elif name == "respected_get_decisions":
            project = arguments.get("project")
            # 1. 500-Knowledge, Projects ve Companion altındaki karar ve kuralları ara
            search_query = f"{project} karar" if project else "karar mimari kural ADR"
            results = self.search_engine.search(search_query, limit=8)
            kurallar_text = ""
            rules = self._read_optional('🔮 850-Companion/Kurallar.md', 2000)
            if rules:
                kurallar_text = f"\n\n### Aktif Kurallar (Kurallar.md):\n{rules}"

            lines = [f"### {self.os_name} Karar ve Mimari Kayıtları:\n"]
            for r in results:
                lines.append(f"- **{r['title']}** (`{r['path']}`): {r['snippet']}")
            lines.append(kurallar_text)
            return "\n".join(lines)

        elif name == "respected_get_companion_context":
            companion_dir = self.vault_root / "🔮 850-Companion"
            files_to_read = [
                ("Core", companion_dir / "Core.md"),
                ("Last-Session", companion_dir / "Last-Session.md"),
                ("Kurallar", companion_dir / "Kurallar.md"),
                ("Threads", companion_dir / "Threads.md"),
            ]
            parts = [f"## {self.os_name} — {self.companion_name} Derin Hafıza Özeti\n"]
            for label, fpath in files_to_read:
                content = self._read_optional(fpath.relative_to(self.vault_root).as_posix())
                if content:
                    parts.append(f"### {label}\n{content.strip()}\n")
                else:
                    parts.append(f"### {label}\n(Mevcut değil)\n")
            return "\n".join(parts)

        elif name in ("respected_quick_capture", "respected_remember"):
            if not self._write_enabled():
                return WRITE_OFF
            return self._save_inbox_note(name, arguments)

        elif name == "respected_revert_note":
            if not self._write_enabled():
                return WRITE_OFF
            from respectedbrain.rpp import memory_write as writes
            try:
                outcome = writes.revert_mcp(self.ctx, str(arguments.get("operation_id", "")))
            except writes.MemoryOpError as error:
                return f"Hata: {error.message}"
            return "Başarılı: Not geri alındı." if not outcome.get("already_gone") else "Başarılı: Not zaten yok."

        elif name == "respected_expand":
            target_str = arguments.get("title_or_path", "").strip()
            target_path = self._safe_resolve(target_str)
            if not target_path or not target_path.is_file():
                if '/' in target_str or '\\' in target_str or ':' in target_str or '\0' in target_str:
                    return 'Hata: Geçersiz veya bulunamayan not yolu.'
                found = []
                target_stem = Path(target_str).stem.lower()
                for root, dirs, files in os.walk(self.vault_root):
                    dirs[:] = [d for d in dirs if path_within_vault(Path(root) / d, self.vault_root)]
                    for filename in files:
                        p = Path(root) / filename
                        if p.suffix == '.md' and p.stem.lower() == target_stem and self._safe_resolve(p.relative_to(self.vault_root).as_posix()):
                            found.append(p)
                if not found:
                    return f"'{target_str}' ile eşleşen bir not {self.os_name} içinde bulunamadı."
                if len(found) > 1:
                    return 'Hata: Birden fazla not eşleşti; göreceli dosya yolunu belirtin.'
                target_path = found[0]

            rel_target = target_path.relative_to(self.vault_root)

            try:
                content = read_note(self.vault_root, rel_target.as_posix())
            except Exception as e:
                return f"Not okunurken hata oluştu: {e}"

            outbound = []
            outbound_raw = re.findall(r"\[\[(.*?)\]\]", content)
            for link in outbound_raw:
                clean_link = link.split("|")[0].split("#")[0].strip()
                if clean_link and clean_link not in outbound:
                    outbound.append(clean_link)

            # SQLite FTS5 tabanlı anında backlink sorgusu (sıfır disk taraması)
            raw_backlinks = self.search_engine.get_backlinks(rel_target.as_posix())
            raw_backlinks = list(dict.fromkeys([*raw_backlinks, *self.search_engine.get_backlinks(target_path.stem)]))
            if not raw_backlinks:
                self.search_engine.index_vault()
                raw_backlinks = self.search_engine.get_backlinks(rel_target.as_posix())
                raw_backlinks = list(dict.fromkeys([*raw_backlinks, *self.search_engine.get_backlinks(target_path.stem)]))
            backlinks = [b for b in raw_backlinks if Path(b).as_posix() != rel_target.as_posix()]

            lines = [
                f"### {self.os_name} Grafik Komşuluğu: `{rel_target}`\n",
                f"**📤 Dış Bağlantılar (Bu nottan gidenler - {len(outbound)}):**",
            ]
            if outbound:
                for out in outbound:
                    lines.append(f"- `[[{out}]]`")
            else:
                lines.append("- (Dış bağlantı bulunamadı)")

            lines.append(f"\n**📥 Geri Bağlantılar (Bu nota gelenler - {len(backlinks)}):**")
            if backlinks:
                for back in backlinks:
                    lines.append(f"- `[[{back}]]`")
            else:
                lines.append("- (Geri bağlantı bulunamadı)")

            return "\n".join(lines)

        else:
            return f"Bilinmeyen araç çağrısı: {name}"

    def run_stdio(self) -> None:
        """Handle one JSON-RPC request per line and survive malformed clients."""
        for line in sys.stdin:
            if not line.strip():
                continue
            try:
                req = json.loads(line)
            except (ValueError, UnicodeError):
                self._send({'jsonrpc': '2.0', 'id': None, 'error': {'code': -32700, 'message': 'Parse error'}})
                continue
            if (not isinstance(req, dict) or req.get('jsonrpc') != '2.0'
                    or not isinstance(req.get('method'), str)
                    or ('id' in req and req['id'] is not None and type(req['id']) not in (str, int))):
                self._send({'jsonrpc': '2.0', 'id': None, 'error': {'code': -32600, 'message': 'Invalid request'}})
                continue
            if 'id' not in req:
                continue
            req_id, method, params = req['id'], req['method'], req.get('params', {})
            if not isinstance(params, dict):
                self._send({'jsonrpc': '2.0', 'id': req_id, 'error': {'code': -32602, 'message': 'Invalid params'}})
                continue
            try:
                if method == 'initialize':
                    result = {'protocolVersion': self.PROTOCOL_VERSION, 'capabilities': {'tools': {}},
                              'serverInfo': {'name': self.SERVER_NAME, 'version': self.SERVER_VERSION}}
                elif method == 'ping':
                    result = {}
                elif method == 'tools/list':
                    result = {'tools': self.get_tools_manifest()}
                elif method == 'tools/call':
                    name, arguments = params.get('name'), params.get('arguments', {})
                    if not isinstance(name, str):
                        raise ValueError('Invalid tool name')
                    self._validate_arguments(name, arguments)
                    text = self.call_tool(name, arguments)
                    if text is None:  # the writer lease is held by an install/update/repair
                        text = 'Hata: Hafıza şu anda bakımda (kurulum/güncelleme sürüyor); birazdan tekrar deneyin.'
                    result = {'content': [{'type': 'text', 'text': text}],
                              'isError': text.startswith(('Hata', 'Bilinmeyen', 'Not yazılırken', 'Ders kaydedilirken', 'Dosya okunurken', 'Not okunurken'))}
                else:
                    self._send({'jsonrpc': '2.0', 'id': req_id, 'error': {'code': -32601, 'message': 'Method not found'}})
                    continue
                self._send({'jsonrpc': '2.0', 'id': req_id, 'result': result})
            except ValueError:
                self._send({'jsonrpc': '2.0', 'id': req_id, 'error': {'code': -32602, 'message': 'Invalid params'}})
            except Exception:
                self._send({'jsonrpc': '2.0', 'id': req_id, 'error': {'code': -32603, 'message': 'Tool execution failed'}})

    def _send(self, data: dict[str, Any]) -> None:
        body = json.dumps(data, ensure_ascii=False)
        sys.stdout.write(body + "\n")
        sys.stdout.flush()


def serve(ctx):
    RespectedMcpServer(ctx).run_stdio()
    return 0
