---
name: kod-orkestrasyon
description: Çoklu AI model orkestrasyonu (Worktree izolasyonu). "orkestrasyon", "modeli işçi olarak çalıştır", "worktree'de dene" için kullan.
---

# Kod Orkestrasyonu (Respected Orchestrator)

SecondBrain artık kod orkestrasyonu yapmaz; bu iş ayrı ürün **Respected Orchestrator**'ın görevidir. Hub'da Orchestrator → "AI araçlarından kullan (MCP)" bölümünden bağlandıysa bu araçta `orchestrator_*` MCP araçları görünür.

## Kurallar
1. Ağır kodlama/refactoring işini `orchestrator_task_start` ile başlat; işçi model izole bir çalışma alanında çalışır, gerçek ağaca dokunmaz.
2. İlerlemeyi `orchestrator_progress`, kanıtı `orchestrator_evidence` ile oku.
3. Yamayı yalnızca kullanıcı onayıyla `orchestrator_apply` ile uygula (evidence'taki `patch_sha256` gerekir).
4. Master/işçi rolleri sabit değildir: kullanıcı veya Hub varsayılanı hangi modeli seçtiyse o kullanılır.
5. Tekrar kullanılabilir bir karar veya bilgi çıkarsa (görev geçmişi değil) `orchestrator_memory_note` ile SecondBrain gelen kutusuna not bırak; yalnızca kullanıcı Hub'da yazma iznini açtıysa çalışır.

Orchestrator MCP bağlı değilse kullanıcıdan Hub'da bağlamasını iste; eski `respectedbrain orchestrate` komutu kaldırıldı.
