# Brain: gelecekte yapılacaklar

Ürün beklentisiyle bugünkü durum arasındaki açıklar. Yapılan madde silinir.

## Tüm AI'lar tek hafıza

- [x] **OpenCode** desteği: hook ve MCP kaydı (`integrations/`). Yerel plugin, JSONL döküm ve
  `additionalContext` köprüsü eklendi; OpenCode v2.2.3 ile gerçek oturumda plugin yüklemesi, MCP el sıkışması ve
  transcript doğrulandı (`docs/ROADMAP-EXECUTION.md` BR-016). v1 `server` fallback'i ve araç yürütmesi smoke kapsamı dışında.
- [ ] **OpenRouter / API tabanlı modeller — bloke**: `providers/openrouter.py` adaptörü, `credential set openrouter`
  kasası ve testler hazır. Gerçek ücretli çağrı, API anahtarı olmadığı için doğrulanmadı; `auto` modunda ücretli
  sağlayıcıya geçilmez, açık `summary_provider=openrouter` veya `provider_allow_paid=true` gerekir. Çin modelleri bu yoldan gelir.
- [x] **ChatGPT (masaüstü/web) — kişisel hesap için bloke**: hook yok; custom MCP/full MCP yalnızca Business,
  Enterprise ve Edu müşterileri için ChatGPT web'de. Kişisel hesap/masaüstü için belgelenmiş bir yol yok; ayrıntı
  `docs/RESEARCH.md` ChatGPT MCP bölümünde.
- [x] **Cursor gerçek oturum**: BR-021 ile transcript ve flush gerçek `cursor-agent` oturumunda doğrulandı.
- [ ] **Gemini CLI gerçek oturum**: CLI bu makinede (Windows ve WSL) kurulu değil; hook ve test verisi hazır, gerçek oturum yok.

## Token tasarrufu

- [x] Tasarruf karşılaştırması: BR-022 ile full not 1103.458 token, compact-600 47.452 token ve aynı pass oranı %98;
  ölçülen azalma %95.7. compact-60 29.186 token ama pass %80; doğruluk kaybı gizlenmiyor.

## Dosyayı kolay bulma

- [ ] Dizin anlık değil: dosya izleyici yok; normal aramada sorgu öncesi stale kontrolü ve refresh var, salt-okunur MCP
  eski sonucu filtreler. Oturum dışı düzenleme bir sonraki sorguda, oturumda ya da günlük görevde dizine girer.
- [x] Anlamsal arama (isteğe bağlı): `MIN_SCORE=0.25` uygulanıyor; yönetilen `llama.zip` yalnızca Windows x64.
  Diğer platformlarda `llama` sağlayıcısı `PLATFORM_UNSUPPORTED` ile erkenden reddedilir ve `ollama` önerilir; Windows
  dışında `.exe` indirilmez. Her sorguda sunucu başlatma bilinçli sınırdır; yerel model etkin değilken FTS5 kullanılır.

## Araştırmaya dayalı tasarım

- [x] Rakip analizi ve araştırma belgesi: `docs/RESEARCH.md` Mem0, Letta, Zep ve Obsidian/Smart Connections ile
  karşılaştırmayı kaynak URL'leri ve erişim tarihiyle belgeliyor; doğrulanmamış iddialar ayrıca işaretlendi.

## Ürün ve yayın

- [ ] Kurucuyu Authenticode ile imzalamak (SmartScreen uyarısı). Üretim kod imzalama sertifikası yok; yalnızca
  self-signed `CN=Respected Test Signer` test sertifikası var ve bu SmartScreen güveni sağlamaz.
- [ ] macOS / Linux / WSL: Windows x64 ve WSL2 üzerinde Linux x64 dondurulmuş paketleri doğrulandı (BR-030);
  WSL2/Linux kaynak testleri gerçek (BR-019/BR-020), Ubuntu kaynak testi ve Linux frozen build/smoke job'ları CI
  matrisinde (BR-026/BR-031).
  macOS gerçek donanım, bare-metal Linux ve uzak CI doğrulaması açık.

## Güncelleme

- [x] Migration sözleşmesi: biçimi değiştiren ilk sürümde `STEPS` tablosuna eski sürüm için adım eklenecek; tablo yalnızca
  `SHIPPED`–`CURRENT` arasındaki gerçek boşlukları taşır ve spekülatif adım içermez. Bugün tüm biçimler güncel olduğu için
  tablo boş; invariant testi bunu zorlar. Her yayında gerçek veri dosyaları `tests/fixtures/releases/<sürüm>/` altına
  kopyalanır ve tanınmayan dosya kabul edilmez (sözleşme §4).
