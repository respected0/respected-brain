# 0.0.1 Manual Acceptance

Bu kontrol listesi otomatik testlerin yerine geçmez; gerçek ajan UI/CLI davranışını ve Obsidian
deneyimini doğrular. Önce ayrı bir test vault'u kullan. Kanıt dosyaları prompt veya transkript
gövdesi içermez.

## Her platformda ortak kabul

1. Repoyu güncelle ve platform smoke'u çalıştır. JSON `overall: VERIFIED` olmalı.
2. Test vault'unu Obsidian'da aç; Türkçe/emoji içeren bir dosya adı oluşturup yeniden aç.
3. Kullandığın her ajanda şu iki mesajı ayrı ayrı gönder:
   - `Test kararı: 0.0.1 kabul turu başladı. Bunu yalnız özetle.`
   - `İkinci turn: karar geçerli, yeni görev ekleme.`
4. Her yanıt sonrasında en fazla 120 saniye içinde `daily/YYYY-MM-DD.md` dosyasını kontrol et.
   Aynı oturum için tek `### Oturum` olmalı; ikinci turn yeni blok eklemek yerine aynı bloğu
   güncellemeli. Elle eklediğin bir satır kaybolmamalı.
5. Ajanı kapatıp yeniden aç. `Last-Session`, `Threads`, kurallar ve knowledge index bağlama
   gelmeli; ham sağlayıcı sohbet geçmişinin taşınması beklenmez.
6. Özetleyici CLI'ı geçici olarak PATH'ten kaldır veya başarısız bir stub ile değiştir. Olay
   kaybolmamalı; sonraki başarılı start/turn catch-up ile günlük tamamlanmalı.
7. Global ayarlara alakasız bir hook/kural ekle; global kurucuyu iki kez çalıştır ve uninstall yap.
   Kullanıcı girdisi korunmalı. Var olan Codex `notify` komutu kurulumda zincirlenmeli, uninstall'da
   geri yüklenmeli.

## Windows Native

```powershell
.\tests\smoke\windows-native.ps1 --output .\smoke-windows.json
```

- WSL kapalıyken veya PATH'te yokken test vault'u çalışmalı.
- `.beyin/config.json` içindeki platform `windows-native` olmalı.
- Üretilen hook komutlarında `wsl.exe`, `bash` ve `.sh` bulunmamalı.
- Microsoft Store `python.exe` aliası gerçek Python sanılmamalı.

## Saf WSL

WSL Linux home'u altında clone edilmiş repo içinde:

```sh
sh ./tests/smoke/wsl.sh --output ./smoke-wsl.json
```

- JSON host alanı `wsl`, profil `portable` olmalı.
- Test vault'u `/home/...` altında çalışmalı; Windows path zorunluluğu olmamalı.
- `python3 tests/run_all.py` ve iki shell paketi de geçmeli.

## Hibrit Windows + WSL

Windows PowerShell'de:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tests\hybrid_wsl_smoke.ps1
```

- Vault Windows diskinde olmalı ve WSL karşılığı `/mnt/<drive>/...` olarak çözülmeli.
- Üretilen hook `wsl.exe --cd` kullanmalı.
- WSL motorunun yazdığı günlük aynı Windows vault'unda Obsidian tarafından görülmeli.

## Saf Linux VM

```sh
sh ./tests/smoke/linux.sh --output ./smoke-linux.json
python3 tests/run_all.py
```

- JSON host `linux`, profil `portable` olmalı; `WSL_DISTRO_NAME` boş olmalı.
- Masaüstü seçeneği açıksa `.desktop` dosyası executable olmalı ve Obsidian URI'sini açmalı.
- systemd user yoksa cron fallback açıkça raporlanmalı; sessiz başarı verilmemeli.

## macOS

```sh
sh ./tests/smoke/macos.sh --output ./smoke-macos.json
python3 tests/run_all.py
```

- JSON host `macos`, profil `portable` olmalı.
- Masaüstü launcher `.webloc` olmalı; çift tıklamada doğru Obsidian vault'u açmalı.
- LaunchAgent plist `plutil -lint` ile geçmeli ve login sonrası briefing çalışmalı.
- Claude `Stop`, Cursor `afterAgentResponse`, Gemini `AfterAgent`, Codex `notify` ve
  Antigravity `Stop` için ortak günlük davranışı ayrı ayrı gözlenmeli.

## Sonuç kaydı

Her cihaz için OS sürümü, Python sürümü, ajan/CLI sürümü, JSON evidence dosyası, başarısız adım ve
ekran görüntüsü bağlantısını kaydet. Çalıştırılmayan platform veya gerçek ajan hesabı `NOT VERIFIED`
kalır; otomatik adapter testi fiziksel ajan testinin yerine `VERIFIED` yazılmaz.
