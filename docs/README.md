# 📚 Respected Brain — Belge Merkezi

| İhtiyaç | Okuma sırası |
| --- | --- |
| Programı tanımak | [Ana README](../README.md) → [Mimari](ARCHITECTURE.md) |
| Kurmak ve ilk konuşmayı yapmak | [Kurulum](guides/SETUP.md) → [Windows](guides/SETUP-WINDOWS.md) → [İlk çalıştırma](guides/BOOTSTRAP.md) |
| Günlük kullanmak | [Günlük kullanım](guides/DAILY_USE.md) → [Çoklu AI](guides/MULTI_AI.md) |
| Ayar/kasa değiştirmek | [Yapılandırma](guides/CONFIGURATION.md) |
| Bakım | [Yedekleme](guides/BACKUP.md), [Güncelleme](guides/UPDATE.md), [Kaldırma](guides/UNINSTALL.md), [Sorun giderme](guides/TROUBLESHOOTING.md) |
| Kod geliştirmek | [Geliştirici rehberi](development/README.md) → [Komut kataloğu](development/CLI.md) |
| Hangi garanti uygulanıyor? | [Davranış sözleşmesi](SPECIFICATION.md) → [Güvenlik sınırları](SECURITY.md) |
| Ne doğrulandı, ne açık? | [Proje durumu](PROJECT_STATUS.md) → [Test matrisi](TEST-MATRIX.md) |

```text
docs/
├── ARCHITECTURE.md      Kaynak, kurulum ve veri düzeni
├── SPECIFICATION.md     Davranış kuralları ve kabul sınırları
├── PROJECT_STATUS.md    Tek aktif ürün durumu ve açık sınırlar
├── SECURITY.md          Uygulanan korumalar ve açık sınırlar
├── TEST-MATRIX.md       Test düzeni, komutlar ve kanıtın sınırları
├── guides/              Kullanıcı rehberleri
├── development/         CLI ve geliştirici akışı
└── decisions/           Onaylı tasarım kararları
```

Kural: ürün davranışı kod ve testle, durum yalnız PROJECT_STATUS içinde anlatılır; kod değişince ilgili rehber ve karar
aynı değişiklikte güncellenir. Hedef, uygulanmış özellik ve doğrulanmış sonuç birbirinin yerine yazılmaz.
