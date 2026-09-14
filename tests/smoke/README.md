# Physical Host Smoke

Runner yalnız geçici bir HOME ve vault kullanır. Gerçek vault'a, profile veya ajan ayarlarına yazmaz.
Kurulum, beş sağlayıcı adaptörü, iki turn upsert, iki update ve managed-only uninstall kapılarını sınar.

```powershell
# Windows Native
.\tests\smoke\windows-native.ps1 --output .\smoke-windows.json
```

```sh
# Saf WSL / Linux / macOS
sh ./tests/smoke/wsl.sh --output ./smoke-wsl.json
sh ./tests/smoke/linux.sh --output ./smoke-linux.json
sh ./tests/smoke/macos.sh --output ./smoke-macos.json
```

Başarı için süreç kodu `0`, JSON içindeki `overall` değeri `VERIFIED` ve her kontrol `VERIFIED`
olmalıdır. Kanıt dosyası sistem bilgisi ve süreleri içerir; prompt/transkript gövdesini içermez.
