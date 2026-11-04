# Rakip analizi ve ara?t?rma notlar?

Bu belge, Respected Brain'in haf?za ve ba?lam yakla??m?n? benzer ?r?nlerle kar??la?t?r?r. Her d?? iddia kaynak URL'si ve eri?im tarihiyle birlikte verilir. Do?rulanamayan iddialar a??k?a i?aretlenir.

- Eri?im tarihi: 2026-11-04 (Europe/Istanbul)
- Kapsam: Mem0 Open Source, Letta, Zep, Obsidian/Smart Connections, ChatGPT MCP
- Y?ntem: ?r?nlerin kendi belgelerinden okuma; HTTP durum kodu ve sayfa metni do?rulamas?. Ba??ms?z benchmark ?al??t?r?lmad?.

## Kaynak do?rulamas?

| Kaynak | URL | HTTP | Do?rulanan |
|---|---|---|---|
| Mem0 Open Source | https://docs.mem0.ai/open-source/overview | 200 | Self-hosted motor, metadata filtresi, reranker, async memory, multimodal, REST/OpenAI uyumu |
| Letta | https://docs.letta.com/ | 200 | Stateful agent platformu, a??k kaynak agent harness, self-hosting, MCP/ACP, konu?ma ve haf?za y?netimi |
| Zep | https://help.getzep.com/ | 200 | Kurumsal ba?lam katman?, temporal Context Graphs, Graphiti a??k kaynak temporal bilgi grafi?i |
| Obsidian eklentileri | https://obsidian.md/plugins | 200 | 9.932 eklenti, 978 tema; "AI" kategorisinde 1.182 eklenti |
| Smart Connections FAQ | https://smartconnections.app/smart-connections/faq/ | 200 | ?cretsiz ?ekirdek, yerel-?ncelikli kullan?m, iste?e ba?l? Pro; Smart Chat ayr? eklenti |
| ChatGPT custom MCP | https://help.openai.com/en/articles/12584461-connecting-custom-mcp-servers-in-chatgpt | 200 | Custom MCP/full MCP yaln?zca Business, Enterprise ve Edu m??terileri i?in ChatGPT web'de; mobilde yok |

## ?r?n kar??la?t?rmas?

| ?r?n | Konum / da??t?m | Haf?za modeli | G??l? y?n | Respected Brain i?in anlam? |
|---|---|---|---|---|
| **Mem0 OSS** | Kendi altyap?nda; y?netilen platformla ayn? motor | LLM + embedding + vekt?r deposu; metadata filtreleri, reranker, async memory | Olgun SDK/REST y?zeyi, ?oklu vekt?r deposu ve sa?lay?c? deste?i | Vekt?r/reranker katman? i?in referans; ancak varsay?lan kurulumda OpenAI anahtar? ve harici model ?a?r?s? var |
| **Letta** | Bulut veya self-hosted | Stateful agent; konu?malar, MemFS, payla??lan haf?za | Agent ya?am d?ng?s? ve ba?lam y?netimi g??l?; MCP/ACP entegrasyonu | Agent ?er?evesi olarak g??l?, fakat ?r?n?n oda?? not kasas? de?il agent platformu |
| **Zep** | Y?netilen kurumsal servis; Graphiti a??k kaynak | Temporal Context Graphs; i? verisi, dok?man ve konu?malar? birle?tirme | Kurumsal y?neti?im, zaman boyutlu grafik, kaynak izlenebilirli?i | Grafik/zaman modeli ilham verici; y?netilen servis ve kurumsal kullan?m varsay?m? yerel-?ncelikli ?r?ne do?rudan ta??namaz |
| **Obsidian + Smart Connections** | Yerel Obsidian kasas?; iste?e ba?l? Pro | Yerel notlar ?zerinde benzerlik/ili?ki arama; Smart Chat ayr? eklenti | Kullan?c?n?n dosyalar?na do?rudan ba?l?, yerel-?ncelikli, geni? eklenti ekosistemi | En yak?n kullan?c? deneyimi; farkl? AI ara?lar?ndan otomatik ba?lam ve kan?tl? ba?lam b?t?esi sunmuyor |
| **Respected Brain** | Yerel Windows/WSL/Linux; Obsidian kasas? + AI hook'lar? | Deterministik JSONL/Markdown; redaksiyon ve inertle?tirme; s?r taramas?; kan?tl? progressive context | ?oklu AI arac?ndan tek haf?za, dosya sahipli?i, geri al?nabilir i?lem, ?l??lm?? ba?lam b?t?esi | Rakip de?il, bu ?r?nlerin aras?ndaki bo?lu?u doldurur: yerel kasa + ara? ba??ms?z hook + denetlenebilir ??kt? |

## Respected Brain'in ayr??t??? noktalar

1. **Yerel-?ncelikli ve dosya sahipli?i:** Notlar kullan?c?n?n Obsidian kasas?nda kal?r; ?r?n kendi veritaban?n? zorunlu k?lmaz. Kald?rma/onar?m insan notlar?n?n ?zerine yazmaz; sahiplik kayd? ve i?lem g?nl??? tutulur.
2. **Ara? ba??ms?z hook'lar:** Codex, Claude Code, Cursor, OpenCode, Antigravity ve Gemini i?in ayn? haf?za; tek sa?lay?c?ya kilitlenme yok. Her arac?n kendi transcript bi?imi ayr? ??z?l?r.
3. **Deterministik ve denetlenebilir ??kt?:** JSONL transcript, Markdown not ve durum dosyalar?; hash ve idempotent i?e alma ile tekrar ?retim kontrol edilir.
4. **G?venlik s?n?rlar?:** S?r taramas?, redaksiyon ve inertle?tirme; AI ??kt?s? do?rudan ?al??t?r?labilir talimat olarak kabul edilmez.
5. **Kan?tl? ba?lam b?t?esi:** BR-012 fixture'?nda full not 1103.458 token, compact-600 47.452 token ve ayn? pass oran? (%98); tasarruf %95.7 olarak ?l??ld?. D???k b?t?e (compact-60) %80 pass ile do?ruluk kayb?n? gizlemez.
6. **MCP + hook birlikte:** MCP ara? y?zeyi ve oturum hook'lar? ayn? haf?zay? payla??r; yaln?zca sohbet i?i MCP'ye ba??ml? de?ildir.

## ChatGPT MCP ayrıntısı

ChatGPT için iki ayrı soru var: (1) oturum başında otomatik bağlam enjekte eden bir hook var mı, (2) MCP sunucusu bağlanabilir mi?

- **Hook yok.** İncelenen OpenAI yardım sayfası yalnızca custom MCP sunucusu bağlama ve araç çağırma akışını anlatır; masaüstü veya web için oturum başlangıcı/transcript hook'u tanımlamaz.
- **Custom MCP yalnızca Business, Enterprise ve Edu müşterileri için ChatGPT web'de.** Sayfa aynen şunu söyler: "Custom MCP server connections and full MCP support are available for ChatGPT Business and Enterprise/Edu customers on ChatGPT web." Mobilde custom MCP yoktur.
- **Kişisel hesaplarda custom MCP bağlantısı belgelenmemiştir.** Business dışındaki kişisel planlar için bir yol gösterilmez; bu nedenle Respected Brain'in kişisel ChatGPT masaüstü/web oturumuna otomatik hafıza vermesi bugün uygulanabilir değildir.
- **MCP araç çağrısı otomatik hafıza değildir.** Modelin aracı ne zaman çağıracağına karar vermesi gerekir; oturum başında deterministik bağlam enjeksiyonu ve transcript yakalama garanti edilmez.
- **Uygun kurumsal çalışma alanı için yapılabilecek:** Respected Brain MCP sunucusunu (`respected-brain mcp`) yönetici tarafından eklenebilir hale getirmek. Bu, kişisel hesaplar için bir çözüm değildir ve bu depoda uygulanmış sayılmaz.

**Karar:** kişisel ChatGPT masaüstü/web için hook veya desteklenen MCP yolu yok; madde bloke olarak kapatılır. Kurumsal Business/Enterprise/Edu web senaryosu ayrı bir ürün kararı gerektirir.

## Kararlar

- **Vekt?r veritaban? ve harici embedding zorunlu hale getirilmeyecek.** Mem0/Zep'in g??l? oldu?u bu alan, yerel-?ncelikli ve anahtars?z ?al??ma hedefiyle ?eli?ir. ?ste?e ba?l? sa?lay?c? adapt?r? ileride ayr? bir madde olarak de?erlendirilebilir.
- **Agent framework'? benimsenmeyecek.** Letta'n?n stateful agent modeli farkl? bir ?r?n kategorisidir; Respected Brain ara?lar?n yan?nda haf?za katman? olarak kal?r.
- **Zaman grafi?i ?imdilik eklenmeyecek.** Zep'in temporal grafik yakla??m? de?erli; ancak mevcut JSONL/Markdown + dizin modeli geri al?nabilirlik ve basitlik avantaj?n? koruyor. Ger?ek bir kullan?c? ihtiyac? ?l??lmeden grafik altyap?s? eklenmez.
- **Obsidian eklentisi ile rekabet edilmeyecek.** Smart Connections kasa i?i aramada g??l?; Respected Brain farkl? AI ara?lar? aras?nda k?pr? ve oturum haf?zas? olarak konumlan?r.
- **ChatGPT ki?isel hesaplar i?in hook/MCP iddias? kurulmayacak.** Custom MCP yaln?zca Business/Enterprise/Edu web'de; masa?st? veya ki?isel hesap i?in belgelenmi? bir yol yok.

## Do?rulanmam?? / riskler

- Zep'in belirli bir gecikme (?r. sub-200 ms) iddias? bu belgede kullan?lmad?; eri?ilen sayfada do?rulanmad?.
- Smart Connections'?n hangi ?zelliklerinin Pro'ya ait oldu?u yaln?zca FAQ d?zeyinde okundu; s?r?m bazl? ayr?nt? do?rulanmad?.
- Mem0'?n varsay?lan OSS kurulumu harici LLM/embedding anahtar? gerektirir; tamamen anahtars?z yerel ?al??t??? iddia edilmedi.
- Hi?bir ?r?n i?in ba??ms?z h?z/do?ruluk benchmark'? ?al??t?r?lmad?. Respected Brain say?lar? yaln?zca kendi BR-012 fixture'?na aittir.
- ChatGPT MCP sayfas? 2026-11-04'te 200 d?nd?; plan/?zellik ko?ullar? OpenAI taraf?ndan de?i?ebilir.

## Kaynaklar

- Mem0 Open Source Overview ? https://docs.mem0.ai/open-source/overview (2026-11-04)
- Letta Documentation ? https://docs.letta.com/ (2026-11-04)
- Zep Documentation ? https://help.getzep.com/ (2026-11-04)
- Obsidian Community Plugins ? https://obsidian.md/plugins (2026-11-04)
- Smart Connections FAQ ? https://smartconnections.app/smart-connections/faq/ (2026-11-04)
- Connecting custom MCP servers in ChatGPT ? https://help.openai.com/en/articles/12584461-connecting-custom-mcp-servers-in-chatgpt (2026-11-04)
