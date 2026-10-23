# Brain: gelecekte yapılacaklar

Ürün beklentisiyle bugünkü durum arasındaki açıklar (2026-10-23 itibarıyla). Yapılan madde silinir.

## Tüm AI'lar tek hafıza

- [ ] **OpenCode** desteği: hook ve MCP kaydı (`integrations/`), özetleyici olarak `providers/runner.py`. Bu makinede OpenCode
  kurulu değil; gerçek oturumla doğrulanamadığı için yazılmadı.
- [ ] **OpenRouter / API tabanlı modeller**: bugün özetleme yalnızca kurulu AI aracının komut satırıyla yapılıyor; API
  anahtarıyla doğrudan model çağırma yok. Anahtarın nerede saklanacağı (ayar şeması `secret` alanı mı, Windows kimlik
  kasası mı) ve fiyat/sağlayıcı seçimi karar bekliyor. Çin modelleri (DeepSeek, Qwen, GLM, Kimi) de bu yoldan gelir.
- [ ] **ChatGPT** (masaüstü/web): hook yok; yalnızca MCP üzerinden ne kadar bağlanabileceği araştırılmalı.
- [ ] **Gemini CLI ve Cursor gerçek oturumla doğrulama**: yalnızca test verisiyle sınandı (`ARCHITECTURE.md` §9).

## Token tasarrufu

- [ ] Tasarruf karşılaştırması: `stats` oturum başına gönderilen bağlamı ölçer, ama "bağlamsız" bir temel olmadığı için
  tasarruf hesaplamaz. Anlamlı bir temel (örneğin aynı işin hafızasız tekrarı) tanımlanmalı.

## Dosyayı kolay bulma

- [ ] Dizin anlık değil: oturum dışında düzenlenen not bir sonraki oturumda ya da günlük görevde dizine girer.
- [ ] Anlamsal arama: her sorguda sunucu başlıyor (2,6–4,2 sn), karma sonuçlarda alaka eşiği yok, çalışma ortamı yalnızca
  Windows x64.

## Araştırmaya dayalı tasarım

- [ ] Rakip analizi ve araştırma belgesi: Mem0, Letta, Zep, Obsidian eklentileri gibi hafıza ürünleriyle karşılaştırma ve
  kararların dayandığı makaleler/ölçümler yazılı değil.

## Ürün ve yayın

- [ ] Kurucuyu Authenticode ile imzalamak (SmartScreen uyarısı). Kod imzalama sertifikası gerekir; yok.
- [ ] macOS / Linux / WSL: kod ve betikler var, derlenmiyor ve CI'da sınanmıyor. Bu geliştirme makinesi Windows.

## Güncelleme

- [ ] Biçimi değiştiren ilk sürümde `installation/migrate.py` içindeki `STEPS` tablosuna eski sürüm için taşıma adımı
  eklenmeli (mekanizma ve test hazır; bugün gönderilmiş tüm biçimler güncel olduğu için adım yok).
