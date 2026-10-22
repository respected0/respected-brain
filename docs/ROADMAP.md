# Brain: gelecekte yapılacaklar

Ürün beklentisiyle bugünkü durum arasındaki açıklar (2026-10-22 değerlendirmesi). Yapılan madde işaretlenir ya da silinir.

## Tüm AI'lar tek hafıza

- [ ] **OpenCode** desteği: hook ve MCP kaydı (`integrations/`), özetleyici olarak `providers/runner.py`.
- [ ] **OpenRouter / API tabanlı modeller**: bugün özetleme yalnızca kurulu AI aracının komut satırıyla yapılıyor; API
  anahtarıyla doğrudan model çağırma yok. Çin modelleri (DeepSeek, Qwen, GLM, Kimi) de bu yoldan gelir.
- [ ] **ChatGPT** (masaüstü/web): hook yok; yalnızca MCP üzerinden ne kadar bağlanabileceği araştırılmalı.
- [ ] **Gerçek oturumla doğrulama**: bugün gerçek oturumla sınanan yalnızca Claude Code. Codex, Gemini, Cursor, Antigravity
  yalnızca test verisiyle sınandı (`ARCHITECTURE.md` §9).

## Token tasarrufu

- [ ] Harcanan token'ı ölçmek ve raporlamak: bugün yalnızca üst sınırlar var (oturum başı bağlam 16.000 karakter,
  `memory/lifecycle.py`), oturum başına ne kadar bağlam gönderildiği ve ne kadar tasarruf edildiği görünmüyor.

## Dosyayı kolay bulma

- [ ] Dizin anlık değil: oturum dışında düzenlenen not bir sonraki oturumda ya da günlük görevde dizine girer.
- [ ] Anlamsal arama: her sorguda sunucu başlıyor (2,6–4,2 sn), karma sonuçlarda alaka eşiği yok, çalışma ortamı yalnızca
  Windows x64.

## Araştırmaya dayalı tasarım

- [ ] Rakip analizi ve araştırma belgesi: Mem0, Letta, Zep, Obsidian eklentileri gibi hafıza ürünleriyle karşılaştırma ve
  kararların dayandığı makaleler/ölçümler yazılı değil.

## Ölü kod

- [ ] Fonksiyon düzeyinde kullanılmayan kod taraması (modül düzeyinde temiz; fonksiyon düzeyine bakılmadı).

## Ürün ve yayın

- [ ] Kurucuyu Authenticode ile imzalamak (SmartScreen uyarısı).
- [ ] macOS / Linux / WSL: kod ve betikler var, derlenmiyor ve CI'da sınanmıyor.
