# Fiziksel paket smoke'u

Derlenmiş paketi gerçek işletim sisteminde, yalnızca geçici bir HOME ve geçici bir kasa ile sınar; gerçek kasaya,
profile ya da AI aracı ayarlarına yazmaz. Kapılar: kurulum, beş sağlayıcı uyarlayıcısı, iki tur yazımı, kurucu ile
güncelleme ve onarım, yalnızca sahipli girdileri kaldıran kaldırma.

```powershell
# Windows
.\tests\native\smoke\windows-native.ps1 --output .\smoke-windows.json
```

```sh
# WSL / Linux / macOS (doğrulanmadı)
sh ./tests/native/smoke/wsl.sh --output ./smoke-wsl.json
sh ./tests/native/smoke/linux.sh --output ./smoke-linux.json
sh ./tests/native/smoke/macos.sh --output ./smoke-macos.json
```

Başarı: çıkış kodu `0`, JSON'daki `overall` değeri `VERIFIED` ve her kontrol `VERIFIED`. Kanıt dosyası sistem bilgisi ve
süreleri içerir; istem ya da döküm metni içermez.
