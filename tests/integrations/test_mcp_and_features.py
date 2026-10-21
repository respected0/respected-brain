#!/usr/bin/env python3
"""Respected Brain yeni nesil yeteneklerin testleri.

Test edilen bileşenler:
1. SQLite FTS5 yerel arama motoru (SearchEngine)
2. Global MCP Vault Sunucusu (RespectedMcpServer)
3. Çapraz Ajan Geçmiş Madencisi (AgentHistoryMiner)
4. Bi-Temporal ve AI-First Not Şablonu
5. Yeni Düşünme ve Madencilik Becerileri (Skills)
"""

from __future__ import annotations

import datetime as dt
import json
import re
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
from respectedbrain.integrations.mcp.server import RespectedMcpServer
from respectedbrain.maintenance.ingestion.mine_agent_history import AgentHistoryMiner

from respectedbrain.search.engine import SearchEngine
from tests.support.files import make_context


class SearchEngineTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.vault = Path(self.temp_dir.name)
        (self.vault / "knowledge").mkdir(parents=True)
        (self.vault / "🏰 300-Projects").mkdir(parents=True)

        # Örnek test notları
        (self.vault / "knowledge" / "Python_Mimarisi.md").write_text(
            "---\ntitle: Python Mimarisi\ntags: [python, backend]\nvalid_at: 2026-09-01\nfreshness: timeless\n---\n"
            "# Python Mimarisi\nİkinci beyin mimarisinde Python standart kütüphanesi tercih edilir.",
            encoding="utf-8",
        )
        (self.vault / "🏰 300-Projects" / "Auth_ADR.md").write_text(
            "---\ntitle: Auth Kararı\ntags: [auth, security]\nvalid_at: 2026-09-02\nfreshness: dated\n---\n"
            "# Auth Kararı\nJWT token yerine oturum tabanlı cookie kararı alındı.",
            encoding="utf-8",
        )

        self.technical = tempfile.TemporaryDirectory()
        self.addCleanup(self.technical.cleanup)
        self.engine = SearchEngine(make_context(Path(self.technical.name), self.vault))
        self.addCleanup(lambda: __import__("shutil").rmtree(self.vault.parent / (self.vault.name + "-data"), ignore_errors=True))

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_indexing_and_search(self) -> None:
        stats = self.engine.index_vault()
        self.assertEqual(stats["indexed"], 2)
        self.assertEqual(stats["deleted"], 0)

        # Arama testi
        results = self.engine.search("Python mimarisi")
        self.assertTrue(len(results) >= 1)
        self.assertEqual(results[0]["title"], "Python Mimarisi")
        self.assertIn("standart kütüphanesi", results[0]["snippet"])

        # Auth araması
        auth_results = self.engine.search("token cookie")
        self.assertTrue(len(auth_results) >= 1)
        self.assertEqual(auth_results[0]["title"], "Auth Kararı")

    def test_incremental_skip(self) -> None:
        self.engine.index_vault()
        # İkinci indekslemede dosyalar değişmediği için atlanmalı
        stats2 = self.engine.index_vault()
        self.assertEqual(stats2["indexed"], 0)
        self.assertEqual(stats2["skipped"], 2)

    def test_category_filter(self) -> None:
        self.engine.index_vault()
        res = self.engine.search("karar", category="🏰 300-Projects")
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["title"], "Auth Kararı")

    def test_search_handles_malformed_fts_queries(self):
        """Unclosed quotes or raw FTS5 operators must not crash search engine."""
        self.engine.index_vault()
        # Should gracefully return results or empty list without raising sqlite3.OperationalError
        res1 = self.engine.search('"unclosed quote')
        self.assertIsInstance(res1, list)
        res2 = self.engine.search('AND OR NOT *')
        self.assertIsInstance(res2, list)

    def test_search_non_existent_category_returns_empty(self):
        self.engine.index_vault()
        res = self.engine.search("Python", category="NonExistentCategory")
        self.assertEqual(res, [])


class McpServerTest(unittest.TestCase):
    def enable_writes(self, enabled: bool = True) -> None:
        """The user's explicit permission (setting mcp_write); the server reads it fresh on every call."""
        from respectedbrain.core.config import ConfigStore
        ConfigStore(self.server.ctx.paths.data_root).update(lambda document: document.setdefault("preferences", {}).__setitem__("mcp_write", enabled))

    def mcp_notes(self):
        return sorted((self.vault / "🔮 850-Companion" / "Inbox" / "MCP").glob("*.md"))

    @unittest.skipUnless(__import__('os').name == 'nt', 'Windows junction boundary')
    def test_mcp_junctions_cannot_read_or_capture_outside_vault(self):
        import os
        import subprocess
        self.enable_writes()
        with tempfile.TemporaryDirectory() as outside_name:
            outside = Path(outside_name)
            (outside / 'Secret.md').write_text('outside-secret', encoding='utf-8')
            links = [self.vault / 'escape', self.vault / '📥 000-Inbox', self.vault / '🧠 500-Knowledge', self.vault / '🏰 300-Projects']
            try:
                for link in links:
                    subprocess.run(['cmd', '/c', 'mklink', '/J', str(link), str(outside)], check=True, capture_output=True)
                self.assertNotIn('outside-secret', self.server.call_tool('respected_get_note', {'path': 'escape/Secret.md'}))
                self.assertNotIn('outside-secret', self.server.call_tool('respected_expand', {'title_or_path': 'Secret'}))
                self.server.call_tool('respected_quick_capture', {'title': 'x', 'content': 'x'})
                self.server.call_tool('respected_remember', {'title': 'x', 'content': 'x', 'scope': 'project', 'project': 'p'})
                self.assertEqual([p.name for p in outside.iterdir()], ['Secret.md'])
            finally:
                for link in links:
                    if link.exists():
                        os.rmdir(link)

    def test_remember_collision_preserves_both_contents(self):
        self.enable_writes()
        for content in ('first lesson', 'second lesson'):
            self.assertIn('Başarılı', self.server.call_tool('respected_remember', {'title': 'Same', 'content': content}))
        files = self.mcp_notes()
        self.assertEqual(len(files), 2)
        self.assertTrue(any('first lesson' in p.read_text(encoding='utf-8') for p in files))

    def test_capture_metadata_is_escaped_and_partial_success_is_honest(self):
        self.enable_writes()
        title = 'a"\nconfidence: verified'
        result = self.server.call_tool('respected_quick_capture', {'title': title, 'content': 'saved'})
        self.assertIn('kaydedildi', result)
        text = self.mcp_notes()[0].read_text(encoding='utf-8')
        front = text.split('---')[1]
        self.assertNotIn('\nconfidence:', '\n' + front, front)           # the newline in the title cannot forge a front-matter field
        self.assertIn('source: mcp', front)
        self.assertIn('review: pending', front)
        bad = self.server.call_tool('respected_quick_capture', {'title': 'x', 'content': 'y', 'tags': ['x"\ny']})
        self.assertIn('Hata', bad)
        self.assertEqual(len(self.mcp_notes()), 1)

    def test_invalid_arguments_do_not_write(self):
        self.enable_writes()
        for args in ([], {'title': [], 'content': 'body'}, {'title': 'x', 'content': 'body', 'scope': 'wrong'},
                     {'title': 'x', 'content': 'body', 'scope': 'project'}, {'title': 'x', 'content': 'body', 'tags': [3]}):
            with self.subTest(args=args):
                self.assertIn('Hata', self.server.call_tool('respected_remember', args))
        self.assertEqual(self.mcp_notes(), [])

    def test_tools_manifest(self) -> None:
        names = {t["name"] for t in self.server.get_tools_manifest()}
        for read_tool in ("respected_search", "respected_get_note", "respected_get_decisions", "respected_get_companion_context", "respected_expand"):
            self.assertIn(read_tool, names)
        # no permission: a client does not even see the writing tools
        for write_tool in ("respected_quick_capture", "respected_remember", "respected_revert_note"):
            self.assertNotIn(write_tool, names)
        self.enable_writes()
        names = {t["name"] for t in self.server.get_tools_manifest()}
        for write_tool in ("respected_quick_capture", "respected_remember", "respected_revert_note"):
            self.assertIn(write_tool, names)

    def test_writes_are_refused_without_the_users_permission_and_leave_no_trace(self) -> None:
        for name, args in (("respected_quick_capture", {"title": "t", "content": "c"}), ("respected_remember", {"title": "t", "content": "c"}),
                           ("respected_revert_note", {"operation_id": "mcp-" + "0" * 24})):
            out = self.server.call_tool(name, args)
            self.assertTrue(out.startswith("Hata"), out)
            self.assertIn("mcp_write", out)
        self.assertFalse((self.vault / "🔮 850-Companion" / "Inbox").exists())
        self.assertFalse((self.vault / "🧠 500-Knowledge").exists())
        self.assertFalse((self.vault / "📥 000-Inbox").exists())
        self.enable_writes()
        self.enable_writes(False)                       # switching it off again closes the door immediately
        self.assertTrue(self.server.call_tool("respected_quick_capture", {"title": "t", "content": "c"}).startswith("Hata"))

    def test_quick_capture_tool(self) -> None:
        self.enable_writes()
        out = self.server.call_tool(
            "respected_quick_capture",
            {"title": "Yeni Fikir", "content": "Harika bir test fikri", "tags": ["fikir", "test"]},
        )
        self.assertIn("Başarılı", out)
        files = self.mcp_notes()
        self.assertEqual(len(files), 1)
        text = files[0].read_text(encoding="utf-8")
        self.assertIn("Harika bir test fikri", text)
        for field in ("source: mcp", "grant: mcp", "review: pending", "type: capture"):
            self.assertIn(field, text)
        self.assertFalse((self.vault / "📥 000-Inbox" / "Dump").exists())

    def test_remember_tool_epistemic(self) -> None:
        self.enable_writes()
        out = self.server.call_tool(
            "respected_remember",
            {
                "title": "React Render Gotcha",
                "content": "useEffect içinde setState yaparken dependency array'e dikkat et.",
                "scope": "platform",
                "confidence": "verified",
                "supersedes": ["Eski React Kuralı"],
                "tags": ["react", "frontend"],
            },
        )
        self.assertIn("Başarılı", out)
        content = self.mcp_notes()[0].read_text(encoding="utf-8")
        self.assertIn("scope: platform", content)
        self.assertIn("confidence: inferred", content)          # a model cannot vouch for its own note
        self.assertNotIn("confidence: verified", content)
        self.assertIn('supersedes: ["Eski React Kuralı"]', content)
        self.assertFalse((self.vault / "🧠 500-Knowledge").exists())   # never straight into curated knowledge

    def test_remember_tool_cannot_target_projects_or_leave_the_inbox(self) -> None:
        self.enable_writes()
        out = self.server.call_tool("respected_remember", {"title": "../../Malicious Traversal", "content": "Malicious content",
                                                           "scope": "project", "project": "../../malicious_dir"})
        self.assertIn("Başarılı", out)
        self.assertFalse((self.vault.parent / "malicious_dir").exists())
        self.assertFalse((self.vault / "🏰 300-Projects").exists())
        for note in self.mcp_notes():
            self.assertEqual(note.parent, self.vault / "🔮 850-Companion" / "Inbox" / "MCP")

    def test_a_written_note_can_be_reverted_until_the_user_edits_it(self) -> None:
        self.enable_writes()
        first = self.server.call_tool("respected_quick_capture", {"title": "one", "content": "c1"})
        second = self.server.call_tool("respected_quick_capture", {"title": "two", "content": "c2"})
        first_id, second_id = (re.search(r"mcp-[0-9a-f]{24}", text).group(0) for text in (first, second))
        self.assertIn("geri alındı", self.server.call_tool("respected_revert_note", {"operation_id": first_id}))
        self.assertEqual(len(self.mcp_notes()), 1)
        self.mcp_notes()[0].write_text(self.mcp_notes()[0].read_text(encoding="utf-8") + "\nuser edit\n", encoding="utf-8")
        refused = self.server.call_tool("respected_revert_note", {"operation_id": second_id})
        self.assertTrue(refused.startswith("Hata"), refused)
        self.assertEqual(len(self.mcp_notes()), 1)                  # the edited note stays
        self.assertTrue(self.server.call_tool("respected_revert_note", {"operation_id": "mcp-" + "f" * 24}).startswith("Hata"))
        self.assertTrue(self.server.call_tool("respected_revert_note", {"operation_id": "../x"}).startswith("Hata"))

    def test_oversized_or_flooding_writes_are_bounded(self) -> None:
        self.enable_writes()
        self.assertTrue(self.server.call_tool("respected_quick_capture", {"title": "big", "content": "x" * 20001}).startswith("Hata"))
        self.assertTrue(self.server.call_tool("respected_quick_capture", {"title": "t" * 121, "content": "c"}).startswith("Hata"))
        self.assertEqual(self.mcp_notes(), [])

    def test_expand_ambiguous_titles_need_explicit_path(self):
        for folder in ('a', 'b'):
            (self.vault / folder).mkdir()
            (self.vault / folder / 'Same.md').write_text('x', encoding='utf-8')
        self.assertIn('Birden fazla', self.server.call_tool('respected_expand', {'title_or_path': 'Same'}))

    def test_absolute_note_paths_are_refused(self):
        self.assertIsNone(self.server._safe_resolve('/🔮 850-Companion/Core.md'))

    def test_search_tool_lists_hits_or_reports_none(self) -> None:
        out = self.server.call_tool("respected_search", {"query": "Direkt"})
        self.assertIn("Arama Sonuçları", out)
        self.assertIn("Kurallar", out)
        self.assertIn("eşleşen not bulunamadı", self.server.call_tool("respected_search", {"query": "zzzqqq"}))

    def test_decisions_tool_returns_records_and_active_rules(self) -> None:
        out = self.server.call_tool("respected_get_decisions", {})
        self.assertIn("Karar ve Mimari Kayıtları", out)
        self.assertIn("Direkt ol", out)

    def test_stdio_lists_tools_serves_calls_and_rejects_unknown_methods(self):
        import io
        from unittest.mock import patch
        calls = [('tools/list', {}), ('tools/call', {'name': 'respected_get_note', 'arguments': {'path': '🔮 850-Companion/Core.md'}}),
                 ('tools/call', {'name': 'unknown_tool_xyz', 'arguments': {}}), ('nope', {})]
        requests = [json.dumps({'jsonrpc': '2.0', 'id': index, 'method': method, 'params': params})
                    for index, (method, params) in enumerate(calls, 1)]
        output = io.StringIO()
        with patch('sys.stdin', io.StringIO('\n'.join(requests))), patch('sys.stdout', output):
            self.server.run_stdio()
        listing, note, unknown, missing = [json.loads(line) for line in output.getvalue().splitlines()]
        self.assertIn('respected_search', [tool['name'] for tool in listing['result']['tools']])
        self.assertFalse(note['result']['isError'])
        self.assertIn('Companion düşünme ortağı', note['result']['content'][0]['text'])
        self.assertTrue(unknown['result']['isError'])
        self.assertEqual(missing['error']['code'], -32601)

    def test_stdio_errors_do_not_stop_next_request(self):
        import io
        from unittest.mock import patch
        requests = ['{bad', '[]', json.dumps({'jsonrpc':'2.0','id':1,'method':'tools/call','params': []}),
                    json.dumps({'jsonrpc':'2.0','method':'ping'}),
                    json.dumps({'jsonrpc':'2.0','id':2,'method':'ping'})]
        output = io.StringIO()
        with patch('sys.stdin', io.StringIO('\n'.join(requests))), patch('sys.stdout', output):
            self.server.run_stdio()
        replies = [json.loads(line) for line in output.getvalue().splitlines()]
        self.assertEqual(len(replies), 4)
        self.assertEqual([r['error']['code'] for r in replies[:3]], [-32700, -32600, -32602])
        self.assertEqual(replies[-1]['id'], 2)

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.vault = Path(self.temp_dir.name)
        (self.vault / "🔮 850-Companion").mkdir(parents=True)
        (self.vault / "🔮 850-Companion" / "Core.md").write_text("# Core\nCompanion düşünme ortağı.", encoding="utf-8")
        (self.vault / "🔮 850-Companion" / "Kurallar.md").write_text("- kural: Direkt ol", encoding="utf-8")
        (self.vault / "🔮 850-Companion" / "Last-Session.md").write_text("Son oturum özeti.", encoding="utf-8")
        (self.vault / "🔮 850-Companion" / "Threads.md").write_text("Açık konular.", encoding="utf-8")

        self.technical = tempfile.TemporaryDirectory()
        self.addCleanup(self.technical.cleanup)
        self.server = RespectedMcpServer(make_context(Path(self.technical.name),self.vault))
        self.server.search_engine.index_vault()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_unknown_tool_returns_error_message(self) -> None:
        out = self.server.call_tool("unknown_tool_xyz", {})
        self.assertIn("Bilinmeyen araç", out)

    def test_companion_context_tool(self) -> None:
        out = self.server.call_tool("respected_get_companion_context", {})
        self.assertIn("Companion düşünme ortağı", out)
        self.assertIn("Direkt ol", out)
        self.assertIn("Son oturum özeti", out)

    def test_safe_note_read_and_path_traversal(self) -> None:
        # Geçerli okuma
        out = self.server.call_tool("respected_get_note", {"path": "🔮 850-Companion/Core.md"})
        self.assertIn("Companion düşünme ortağı", out)

        # Path traversal atağı engellenmeli
        attack_out = self.server.call_tool("respected_get_note", {"path": "../../etc/passwd"})
        self.assertIn("bulunamadı", attack_out)

    def test_expand_tool(self) -> None:
        # Test için birbirine bağlı iki not oluşturalım
        knowledge_dir = self.vault / "🧠 500-Knowledge"
        knowledge_dir.mkdir(parents=True, exist_ok=True)
        (knowledge_dir / "NodeA.md").write_text("# Node A\nBu not [[NodeB]] bağlantısı içerir.", encoding="utf-8")
        (knowledge_dir / "NodeB.md").write_text("# Node B\nBu not da [[NodeA]] bağlantısı taşır.", encoding="utf-8")

        out = self.server.call_tool("respected_expand", {"title_or_path": "NodeA"})
        self.assertIn("Dış Bağlantılar", out)
        self.assertIn("[[NodeB]]", out)
        self.assertIn("Geri Bağlantılar", out)
        self.assertIn("NodeB.md", out)


class AgentHistoryMinerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.vault = Path(self.temp_dir.name)
        (self.vault / "daily").mkdir(parents=True)
        self.technical = tempfile.TemporaryDirectory()
        self.addCleanup(self.technical.cleanup)
        self.miner = AgentHistoryMiner(self.vault, state_file=Path(self.technical.name) / "imported_sessions.json")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_parse_and_import(self) -> None:
        # Sahte JSONL oturumu
        session_file = Path(self.temp_dir.name) / "test_session.jsonl"
        records = [
            {"type": "USER_INPUT", "content": "<USER_REQUEST>Python FTS5 nasıl kurulur?</USER_REQUEST>"},
            {"type": "PLANNER_RESPONSE", "content": "SQLite FTS5 dahili olarak mevcuttur ve hafiftir."},
        ]
        with session_file.open("w", encoding="utf-8") as f:
            for r in records:
                f.write(json.dumps(r) + "\n")

        session_info = {
            "agent": "antigravity",
            "id": "antigravity_test123",
            "path": session_file,
            "mtime": dt.datetime.now(),
        }

        parsed = self.miner.parse_session(session_info)
        self.assertIsInstance(parsed, dict)
        self.assertEqual(parsed["agent"], "antigravity")
        self.assertIn("Python FTS5 nasıl kurulur?", parsed["title"])
        self.assertTrue(any("SQLite FTS5" in s for s in parsed.get("summaries", [])))

        written_file = self.miner.import_session(parsed, target_folder="daily")
        self.assertIsInstance(written_file, Path)
        self.assertTrue(written_file.is_file())
        content = written_file.read_text(encoding="utf-8")
        self.assertIn("antigravity_test123", content)
        self.assertIn("valid_at:", content)
        self.assertIn("freshness: dated", content)

        # Tekrar import edilmemeli (deduplication)
        self.assertIn("antigravity_test123", self.miner.imported_ids)

    def test_parse_session_empty_and_corrupt_records(self) -> None:
        """Empty session file or corrupt JSON lines must not raise unhandled exceptions."""
        session_file = Path(self.temp_dir.name) / "corrupt_session.jsonl"
        session_file.write_text("{not valid json\n", encoding="utf-8")

        session_info = {
            "agent": "codex",
            "id": "corrupt_123",
            "path": session_file,
            "mtime": dt.datetime.now(),
        }
        parsed = self.miner.parse_session(session_info)
        # Should gracefully return None or safe dict without crashing
        self.assertTrue(parsed is None or isinstance(parsed, dict))


class TemplateAndSkillsTest(unittest.TestCase):
    def test_note_template_has_bitemporal_and_aifirst(self) -> None:
        note_template = ROOT / "src/respectedbrain/resources/vault-template" / "📋 Templates" / "Note.md"
        self.assertTrue(note_template.is_file())
        content = note_template.read_text(encoding="utf-8")
        self.assertIn("valid_at:", content)
        self.assertIn("recorded_at:", content)
        self.assertIn("freshness:", content)
        self.assertIn("Gelecek Ajan İçin", content)

    def test_new_skills_exist_and_valid(self) -> None:
        skills_to_check = ["secondbrain-meydan-oku", "secondbrain-oruntu", "ajan-gecmis-tara"]
        for s in skills_to_check:
            for skill_dir in [ROOT / "src/respectedbrain/resources/skills"]:
                skill_file = skill_dir / s / "SKILL.md"
                self.assertTrue(skill_file.is_file(), f"Skill file missing: {skill_file}")
                text = skill_file.read_text(encoding="utf-8")
                self.assertTrue(text.startswith("---"))
                self.assertIn(f"name: {s}", text)
                self.assertIn("description:", text)

    def test_skills_map_within_lifecycle_cap(self) -> None:
        skills_map = ROOT / "src/respectedbrain/resources/vault-template" / "🎯 100-Command-Center" / "Skills-Map.md"
        self.assertTrue(skills_map.is_file())
        text = skills_map.read_text(encoding="utf-8")
        self.assertLessEqual(
            len(text),
            1500,
            f"Skills-Map.md ({len(text)} chars) exceeds the 1,500-char lifecycle hook cap, which triggers truncation notes.",
        )

    def test_note_template_has_epistemic_fields(self) -> None:
        note_template = ROOT / "src/respectedbrain/resources/vault-template" / "📋 Templates" / "Note.md"
        self.assertTrue(note_template.is_file())
        content = note_template.read_text(encoding="utf-8")
        self.assertIn("scope:", content)
        self.assertIn("confidence:", content)
        self.assertIn("supersedes:", content)

    def test_scan_open_loops(self) -> None:
        from respectedbrain.briefing.service import _scan_open_loops

        with tempfile.TemporaryDirectory() as td:
            v_root = Path(td)
            # 1. 300-Projects altında açık todo
            p_dir = v_root / "🏰 300-Projects" / "ProjectAlpha"
            p_dir.mkdir(parents=True)
            (p_dir / "Tasks.md").write_text("# Tasks\n- [ ] Database migration yap\n- [x] Schema tasarla\n", encoding="utf-8")

            # 2. Daily log altında açık todo
            d_dir = v_root / "daily"
            d_dir.mkdir(parents=True)
            (d_dir / "2026-09-06.md").write_text("# Günlük\n- [ ] Sarah ile 1:1 yap\n", encoding="utf-8")

            # 3. Inbox dump
            i_dir = v_root / "📥 000-Inbox" / "Dump"
            i_dir.mkdir(parents=True)
            (i_dir / "meeting.md").write_text("# Meeting\n", encoding="utf-8")

            loops_text = _scan_open_loops(v_root)
            self.assertIn("Database migration yap", loops_text)
            self.assertIn("Sarah ile 1:1 yap", loops_text)
            self.assertIn("İşlenmeyi bekleyen", loops_text)

    def test_precompact_transcript_backup(self) -> None:
        from respectedbrain.memory import lifecycle

        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
            v_root = Path(td)
            (v_root / "🔮 850-Companion").mkdir(parents=True)
            (v_root / "🔮 850-Companion" / "Last-Session.md").write_text("## Session: test\n", encoding="utf-8")
            s_dir = v_root / ".claude" / "scripts" / ".state"
            s_dir.mkdir(parents=True)

            # Geçici sahte transkript dosyası
            fake_transcript = Path(td) / "fake_transcript.jsonl"
            fake_transcript.write_text('{"type": "message", "content": "hello"}\n', encoding="utf-8")

            payload = {
                "session_id": "session-xyz123",
                "transcript_path": str(fake_transcript),
            }
            from unittest.mock import patch
            import dataclasses
            ctx = make_context(Path(td) / "runtime", v_root / "vault")
            ctx = dataclasses.replace(ctx, config={**ctx.config, "preferences": {"archive_transcripts": True}})  # the opt-in
            # The transcript lives outside the selected vault; only its (redacted) backup is written, in the data root.
            with patch.object(lifecycle, "_launch_flush"):
                lifecycle._finish_session(ctx.paths.vault_root, ctx.paths.state_dir, payload, "precompact", dt.datetime.now(), "antigravity", ctx)

            logs_dir = ctx.paths.data_root / "session-archive"
            self.assertTrue(logs_dir.is_dir())
            backed_files = list(logs_dir.glob("*.jsonl"))
            self.assertEqual(len(backed_files), 1)
            self.assertIn("hello", backed_files[0].read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
