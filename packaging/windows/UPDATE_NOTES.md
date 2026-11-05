Respected Brain'e hoş geldiniz. AI araçları güçlüdür ama unutkandır: her oturum sıfırdan başlar, üç konuşma önce verdiğiniz karar kaybolur, aracı değiştirince her şeyi yeniden anlatırsınız. Brain hafızayı araca değil kendi not kasanıza koyar: araç değişir, hafıza kalır.

beta.2'de neler değişti:

- Güncelleme verinizi ve kasanızı yerinde korur; beta.1 kaydınız beta.2'ye taşınır.
- Gemini CLI kaldırıldı, Antigravity kullanılır; güncelleme eski Gemini hook girdilerini temizler.
- Bağlam artık görev bazlı ve token bütçelidir: yeni oturuma tüm hafıza değil, ilgili kısım verilir.
- Arama daha güvenilir: parça tabanlı tam metin arama, alaka eşiği, güven ve zamana göre sıralama; MCP açıkken dizin kasayı yaklaşık 1 sn içinde kendiliğinden tazeler.
- Kararların yaşam döngüsü: yerine geçme, geçerlilik tarihi ve çelişki incelemesi; gelen kutusunda kabul, ret, düzeltme ve erteleme.
- Geçmiş oturumları önizleyerek, gizli bilgileri maskeleyerek ve tekrar almadan içe aktarma.
- Dışarıdan gelen metin inert işaretlenir; hafıza zehirlenmesi ve gizlilik saldırılarına karşı testler eklendi.
- Daha anlaşılır sağlık denetimi ve kurtarma kontrolleri; oturum özeti başı ve sonu birlikte değerlendirir.
- İsteğe bağlı OpenRouter özetleyicisi: varsayılan ücretsiz modeldir, ücretli modele yalnızca siz açıkça izin verirseniz geçilir.
- Linux x64 dondurulmuş paketi (WSL2 üzerinde doğrulandı); macOS ve bare-metal Linux henüz doğrulanmadı.
- Hesap yok, telemetri yok: Notlarınız yalnızca sizin kasanızdadır.
