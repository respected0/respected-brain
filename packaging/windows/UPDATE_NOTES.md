Respected Brain'e hoş geldiniz. AI araçları güçlüdür ama unutkandır: her oturum sıfırdan başlar, üç konuşma önce verdiğiniz karar kaybolur, aracı değiştirince her şeyi yeniden anlatırsınız. Brain hafızayı araca değil kendi not kasanıza koyar: araç değişir, hafıza kalır.

Bu ilk beta sürümde her şey yenidir:

- Oturum özetleri: AI oturumlarınız özetlenip kasanızdaki günlüğe yazılır.
- Bilgi derleme: Günlüklerden bağlantılı bilgi notları (dizin, kavramlar, bağlantılar) derlenir.
- Yeni oturumda bağlam: Oturum açılırken kararlarınız, kurallarınız ve ilgili notlar aracınıza verilir.
- Çoklu araç: Claude Code, Codex ve Antigravity gerçek oturumlarla doğrulandı; Gemini CLI ve Cursor deneyseldir. Aynı kasayı birden çok araç kullanabilir.
- Düz Markdown, Obsidian uyumlu kasa: Hazır klasör düzeni ve not şablonlarıyla gelir; masaüstü kısayolu kasayı doğrudan Obsidian'da açar, kasa Obsidian'da hiç açılmadıysa uyarı verilir.
- Arama: SQLite FTS5 tam metin arama. İsteğe bağlı yerel anlamsal arama Hub'dan açılır (yaklaşık 460 MB model indirilir, sorgular bilgisayarınızda çalışır, notlarınız dışarı çıkmaz).
- MCP: AI aracınız kasada arar ve not okur. Yazma izni verirseniz yalnızca gelen kutusuna, geri alınabilir not yazar.
- Sabah özeti: İsterseniz seçtiğiniz saatte (varsayılan 08:00) zamanlanmış görev olarak çalışır; asistan size kendi verdiğiniz adla hitap eder.
- Hazır beceriler: Hafıza sağlık kontrolü, eski ChatGPT ve Claude sohbetlerini içe aktarma, ajan geçmişi tarama, gelen kutusu düzenleme, derin araştırma, karar sınama, örüntü çıkarma, yazılım kalite kontrolü ve Obsidian görünüm düzenleme.
- Özetleyici seçimi: Model işleri bilgisayarınızdaki AI aracının komut satırıyla yapılır; ek API anahtarı gerekmez. İsterseniz bir araç başarısız olunca sıradakine geçilir.
- Yedekleme: restic ile kasa yedeği alıp doğrulama ve yeni bir klasöre geri yükleme; Git anlık görüntüsü (önce önizleme).
- Güvenli kurulum: Kurulum, onarım ve kaldırma geri alınabilir bir işlem günlüğüyle yapılır. Brain AI araçlarının ayar dosyasına yalnızca kendi girdilerini ekler ve kaldırır; kasanız hiçbir işlemle silinmez.
- Tek başına ya da Hub ile: Kurucu iki yol sunar; kurulumdan sonra onar, güncelle, ayar değiştir ve kaldır işlemleri Hub olmadan da yapılır. Python ve yönetici izni gerekmez.
- Güncelleme yedekli: Bir şey ters giderse önceki sürüm ve ayarlar kendiliğinden geri yüklenir.
- Hesap yok, telemetri yok: Notlarınız yalnızca sizin kasanızdadır.
