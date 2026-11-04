"""MCP tool definitions (names, descriptions, input schemas); no server state needed."""
from __future__ import annotations
from typing import Any

WRITE_TOOLS = {"respected_quick_capture", "respected_remember", "respected_revert_note"}


def tool_definitions(os_name: str, companion_name: str) -> list[dict[str, Any]]:
    return [
        {
            "name": "respected_search",
            "description": (
                "Kalıcı ikinci beyin vault'undaki notlarda hızlı, anlamsal ve tam metin arama yapar. "
                "Başka projelerde kod yazarken mimari kararları, hafıza kayıtlarını veya teknik notları bulmak için kullan."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Aranacak anahtar kelime, soru veya konu"},
                    "limit": {"type": "integer", "description": "Döndürülecek maksimum sonuç sayısı (varsayılan: 5)", "default": 5},
                    "category": {"type": "string", "description": "Filtrelenecek klasör/kategori (örn: '🧠 500-Knowledge', '🏰 300-Projects')"},
                },
                "required": ["query"],
            },
        },
        {
            "name": "respected_recall",
            "description": (
                "Görev bazlı, token bütçeli kısa hafıza bağlamı döndürür: sıralı kaynak yolları ve isteğe bağlı odaklı özet. "
                "Tam metin gerekirse dönen yolu respected_get_note ile aç; bu araç not gövdesini döndürmez."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "task": {"type": "string", "description": "Yapılan görev, soru veya aranan konu"},
                    "budget_tokens": {"type": "integer", "description": "Bağlam için yaklaşık token bütçesi (varsayılan: 600, en fazla 4000)", "default": 600},
                    "limit": {"type": "integer", "description": "Değerlendirilecek en fazla kaynak sayısı (varsayılan: 5, en fazla: 20)", "default": 5},
                    "detail": {"type": "string", "enum": ["short", "summary"], "description": "short: yalnızca başlık/yol; summary: odaklı parça ile", "default": "summary"},
                    "category": {"type": "string", "description": "Filtrelenecek klasör/kategori (örn: '🧠 500-Knowledge')"},
                },
                "required": ["task"],
            },
        },
        {
            "name": "respected_get_note",
            "description": "Vault içindeki belirli bir markdown notunun tam metnini okur.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Vault köküne göre göreceli not yolu (örn: '🧠 500-Knowledge/Mimari.md')"},
                },
                "required": ["path"],
            },
        },
        {
            "name": "respected_get_decisions",
            "description": "Kasa içinde kayıtlı mimari kararları, kuralları ve ADR özetlerini getirir.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "project": {"type": "string", "description": "İsteğe bağlı: Belirli bir projenin adı (örn: 'brain')"},
                    "include_history": {"type": "boolean", "description": "Yerine geçilmiş ve çelişkili eski kararları da listele"},
                },
                "required": [],
            },
        },
        {
            "name": "respected_get_companion_context",
            "description": f"{companion_name} / {os_name} derin hafıza özetini getirir (Core ilkeleri, Kurallar.md, Last-Session ve açık Threads).",
            "inputSchema": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
        {
            "name": "respected_insights",
            "description": (
                "Salt-okunur hafiza icgoruleri: ogrenim adaylarindan skill onerileri, coklu-agent devir baglami, "
                "kasa saglik/tekrar/celiski raporu ve istege bagli redakte ajan arsivi aramasi. Hicbir sey yazmaz."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "view": {
                        "type": "string",
                        "enum": ["all", "skills", "sessions", "handoff", "health"],
                        "description": "Sorgulanacak gorunum (varsayilan: all)",
                        "default": "all",
                    },
                    "query": {"type": "string", "description": "view=sessions icin aranacak metin"},
                    "provider": {"type": "string", "description": "handoff gorunumunde yalnizca bu saglayiciyi kullan"},
                    "budget_tokens": {"type": "integer", "description": "Devir baglami token butcesi (en fazla 4000)", "default": 600},
                    "limit": {"type": "integer", "description": "Liste siniri (varsayilan: 10)", "default": 10},
                },
                "required": [],
            },
        },
        {
            "name": "respected_quick_capture",
            "description": "(Yalnızca kullanıcı izin verdiyse) Dış bir projede çalışırken ikinci beyin vault'unun MCP gelen kutusuna yeni bir not bırakır; kullanıcı incelemeden kalıcı bilgiye geçmez.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Not başlığı"},
                    "content": {"type": "string", "description": "Notun gövde metni"},
                    "tags": {"type": "array", "items": {"type": "string"}, "description": "İsteğe bağlı etiketler"},
                },
                "required": ["title", "content"],
            },
        },
        {
            "name": "respected_remember",
            "description": (
                "(Yalnızca kullanıcı izin verdiyse) Dış projede öğrenilen kuralı, teknik kısıtı veya gotcha'yı epistemik "
                "sözleşmeyle (scope, confidence, supersedes) MCP gelen kutusuna öneri olarak kaydeder; kullanıcı onaylayana kadar kalıcı bilgi sayılmaz."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Dersin veya kuralın başlığı"},
                    "content": {"type": "string", "description": "Detaylı açıklama, bağlam veya kod örneği"},
                    "scope": {
                        "type": "string",
                        "enum": ["project", "platform", "general"],
                        "description": "Kapsam: 'project' (yalnızca bu proje), 'platform' (örn: ios, react, flutter), 'general' (evrensel kural)",
                        "default": "general",
                    },
                    "confidence": {
                        "type": "string",
                        "enum": ["verified", "inferred", "unverified"],
                        "description": "Güvenilirlik: 'verified' (kodla test edildi), 'inferred' (çıkarım), 'unverified' (şüpheli)",
                        "default": "unverified",
                    },
                    "supersedes": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "İsteğe bağlı: Bu kuralın geçersiz kıldığı eski kural veya not isimleri",
                    },
                    "project": {"type": "string", "description": "İsteğe bağlı proje adı (scope: project ise zorunlu)"},
                    "tags": {"type": "array", "items": {"type": "string"}, "description": "İsteğe bağlı etiketler"},
                },
                "required": ["title", "content"],
            },
        },
        {
            "name": "respected_expand",
            "description": (
                "Belirli bir notun komşuluk grafiğini getirir: Notun içinden dışarıya verilen bağlantılar (outbound links) "
                "ve kasadaki diğer notlardan bu nota verilen geri bağlantılar (backlinks)."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "title_or_path": {"type": "string", "description": "İncelenecek notun başlığı veya dosya yolu (örn: 'React Gotchas' veya '🧠 500-Knowledge/React.md')"},
                },
                "required": ["title_or_path"],
            },
        },
        {
            "name": "respected_revert_note",
            "description": "respected_quick_capture / respected_remember ile kaydedilen bir notu (düzenlenmediyse) geri alır.",
            "inputSchema": {
                "type": "object",
                "properties": {"operation_id": {"type": "string", "description": "Kayıt sırasında dönen işlem kimliği"}},
                "required": ["operation_id"],
            },
        },
    ]
