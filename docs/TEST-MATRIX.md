# ✅ Test Matrisi ve Kanıtın Sınırları

> Bu belge test düzenini ve neyin neyi kanıtladığını anlatır; aktif durum [PROJECT_STATUS](PROJECT_STATUS.md) içindedir.

## 1. Düzen

`tests/` paketi `src/respectedbrain` ile aynı alanlara bölünmüştür; dosya adları `test_*.py` biçimindedir.

| Klasör | Kapsam |
| --- | --- |
| `core/` | bağlam, yollar, kilitler, platform, CLI dağıtımı, Windows süreç/dosya korumaları |
| `vault/`, `briefing/`, `search/` | kasa kayıt defteri ve haritalar, sabah brifingi, FTS ve indeks tazeliği |
| `installation/` | setup, update/repair/uninstall, transaction, ertelenmiş işlem, sınır regresyonları |
| `integrations/` | istemci entegrasyonları, hook'lar, MCP kaydı, yapılandırma delta'sı, zamanlama, sağlayıcı izinleri |
| `memory/` | hafıza sözleşmeleri, olay günlüğü, transcript bütünlüğü, oturum betikleri, maskeleme |
| `maintenance/` | bakım araçları, restic yedeği/geri yükleme, git snapshot, sır tarama, kasa hijyeni |
| `rpp/` | Hub protokolü: sunucu, lifecycle, entegrasyon planı, hafıza op'ları ve izinleri |
| `security/` | ağ taşıması (DNS pinning, SSRF, son tarihler), girdi sınırları, yayın provenance'ı |
| `packaging/` | paket sözleşmesi, dondurulmuş dağıtım, build içeriği, POSIX paket sözleşmeleri, adlandırma |
| `scenarios/` | çapraz senaryo, sağlayıcı ve adversarial matrisler |
| `support/` | paylaşılan sahteler ve dosya yardımcıları (test değil) |
| `native/` | fiziksel paket smoke'u ve WSL köprü smoke'u (elle/CI'da paketle çalışır) |

`tests/__init__.py` her koşucu için HOME, USERPROFILE, APPDATA ve LOCALAPPDATA'yı geçici klasöre yönlendirir; hiçbir test
gerçek AI istemci ayarına veya kasa kayıt defterine ulaşamaz.

## 2. Çalıştırma

```powershell
python -m unittest discover -s tests -t .
python packaging/build_dist.py --platform windows --output dist
python -m unittest tests.packaging.test_distribution
python tests/native/smoke/platform_smoke.py --package dist/RespectedBrain --output native-smoke.json
```

`dist/` yoksa dağıtım testi yerelde açıklamalı atlanır; CI önce build alır ve testi zorunlu tutar (`CI` ortam değişkeni).

## 3. Neyi hangi test kanıtlar?

| Test sınıfı | Kanıtlar | Tek başına kanıtlamaz |
| --- | --- | --- |
| Birim/fixture | algoritma ve arayüz davranışı | gerçek sağlayıcı hesabı veya her OS |
| Paket sözleşmesi | checkout/PYTHONPATH'ten bağımsız import | native kurulum |
| Dondurulmuş dağıtım | launcher, kaynaklar, CLI smoke, hash ile kurcalama reddi | yayıncı imzası, AI cevap kalitesi |
| Fiziksel smoke | geçici köklerde kurulum, beş adaptör, update, sahipli uninstall | kullanıcının canlı kasası |
| Sağlayıcı adaptörü | hook/JSON/argv sözleşmesi | dış ürünün güncel sürümündeki gerçek login/kota |

Hub tarafındaki uçtan uca testler (`respected-hub/src-tauri/tests/brain_e2e.rs` vb.) aynı dondurulmuş paketi Hub'ın
yaşam döngüsünden geçirir. Gerçek kabul, doğru kasa ile bir test konuşmasının hook → daily → ikinci ajan bağlamına
yansımasıdır; [BOOTSTRAP](guides/BOOTSTRAP.md) kontrol sırasını anlatır. Çalıştırılmayan test başarılı diye yazılmaz.
