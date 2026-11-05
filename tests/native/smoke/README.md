# Fiziksel paket smoke'u

Derlenmiş paketi gerçek işletim sisteminde, yalnızca geçici bir HOME ve geçici bir kasa ile sınar; gerçek kasaya,
profile ya da AI aracı ayarlarına yazmaz. Kapılar: kurulum, beş sağlayıcı uyarlayıcısı, iki tur yazımı, kurucu ile
güncelleme ve onarım, yalnızca sahipli girdileri kaldıran kaldırma.

```powershell
# Windows
.\tests\native\smoke\windows-native.ps1 --output .\smoke-windows.json
```

```bash
# WSL2 Ubuntu / Linux
python3 packaging/build_dist.py --platform linux --output dist-linux
python tests/native/smoke/platform_smoke.py --package dist-linux/RespectedBrain --output smoke-linux.json
```

Windows x64 ve WSL2 Ubuntu üzerinde doğrulandı; bare-metal Linux ve macOS henüz doğrulanmadı. Smoke, `respected_brain`
paketini içe aktarabilen bir Python ortamında çalıştırılmalıdır.

Başarı: çıkış kodu `0`, JSON'daki `overall` değeri `VERIFIED` ve her kontrol `VERIFIED`. Kanıt dosyası sistem bilgisi ve
süreleri içerir; istem ya da döküm metni içermez.
