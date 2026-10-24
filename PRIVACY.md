# Gizlilik: Respected Brain

Bu metin Brain `0.1.0-beta.1` için geçerlidir (2026-10-24). Brain'in koduna bakarak yazıldı; kod değişirse metin de değişir.

## Kısaca

- Brain **hesap istemez, telemetri ya da kullanım istatistiği göndermez**, Respected'e hiçbir veri iletmez.
- Notlarınız ve verileriniz bilgisayarınızda durur. Dışarı yalnızca aşağıdaki tabloda yazanlar çıkar.
- Oturumları özetleyen şey Brain değil, **sizin kurduğunuz AI aracıdır**: metin o aracın sağlayıcısına gider.

## Bilgisayarınızda ne saklanır

| Ne | Nerede |
|---|---|
| Program | `%LOCALAPPDATA%\Respected\RespectedBrain\app` |
| Ayarlar, dizin, kurulum kaydı, günlükler, yedekler | `%LOCALAPPDATA%\Respected\RespectedBrain\data` |
| Notlarınız (oturum özetleri, günlükler, bilgi notları) | Kurulumda seçtiğiniz kasa klasörü (varsayılan `Belgeler\RespectedOS`), düz Markdown |

Bağlandığınız AI araçlarının (Claude, Codex vb.) yerel oturum dökümleri, Brain'in hook'ları tarafından **bilgisayarınızda
okunur**; yalnızca bağlantısını açtığınız araçlar için.

## Bilgisayardan ne çıkar, kime gider

| Ne zaman | Ne gider | Nereye |
|---|---|---|
| Oturum bitince (hafıza yakalama **Otomatik** ise, ya da "Şimdi yakala" dediğinizde) | Oturum dökümü, bilinen gizli bilgi kalıpları (anahtar, belirteç, özel anahtar gibi) maskelendikten sonra özetlenmek üzere | Özetleyici olarak seçtiğiniz AI aracı ve onun sağlayıcısı. Bu aktarım o aracın ve sağlayıcının kendi şartlarına tabidir |
| Sabah özeti zamanlandıysa | Kasadaki notlardan derlenen brifing metni | Aynı AI aracı ve sağlayıcısı |
| Anlamsal aramayı **onaylarsanız**, bir kez | Hiçbir kişisel veri; yalnızca indirme isteği | `github.com` (llama.cpp çalışma ortamı) ve `huggingface.co` (bge-m3 modeli, yaklaşık 460 MB). Sonraki aramalar yerelde çalışır, notlarınız bilgisayardan çıkmaz |
| Web adresi içe aldığınızda | Verdiğiniz adrese sıradan bir web isteği | O adresin sunucusu |
| Git anlık görüntüsü yayınlamayı yapılandırdıysanız | Taranmış kasa içeriği | Sizin belirttiğiniz uzak depo |
| Kurucuda "Respected Hub ile devam et" seçerseniz | Sürüm sorgusu ve Hub kurucusunun indirilmesi | `github.com` / `api.github.com` |

Hafıza yakalamayı **Elle** yaparsanız hiçbir oturum kendiliğinden işlenmez.

## Dürüst sınırlar

- Maskeleme bilinen kalıpları yakalar; her gizli bilgiyi yakalamayı **garanti etmez**. Çok hassas bir projede ilgili aracın
  bağlantısını kapatın ya da hafıza yakalamayı Elle yapın.
- Özetin sağlayıcıda ne kadar süre tutulduğunu Brain bilmez ve denetleyemez; bu, AI aracınızın hesap ayarlarına bağlıdır.
- Bu metin hukuki danışmanlık ya da sözleşme metni değildir; neyin nereye gittiğini anlatır.

## Silme

Kaldırmak programı ve AI araçlarınıza eklediği girdileri siler. Ayarlar ve çalışma verisi varsayılan olarak kalır;
"çalışma verileri de silinsin" seçeneğiyle ya da `uninstall --purge` ile silinir. **Not kasanız hiçbir durumda silinmez.**
Sağlayıcıya giden özet metnini silmek için o sağlayıcıya başvurmanız gerekir.

## Soru ve bildirim

[GitHub Issues](https://github.com/respected0/respected-brain/issues)
