# Retrospective — Stalize

Living retrospective. Updated after each milestone.

---

## Milestone: v6.0 — Karar Güvenliği & Sistem Olgunlaşması

**Shipped:** 2026-05-14  
**Phases:** 5 (43–47) | **Plans:** 13 | **Timeline:** 2 days

### What Was Built

- Phase 43: `safeLabel()` karar dili dönüşümü, skor bileşen dökümü, volatilite uyarısı
- Phase 44: `/backtest` sayfası — KPI kartlar, 7 sütunlu sinyal tablosu, 3 filtre
- Phase 45: Stale data banner, son güncelleme saati, AI tarih notu, fundamental dönem badge
- Phase 46: CSS-only sektör bar chart, yoğunlaşma uyarıları, risk özet kartı
- Phase 47: exit_reason/invalidation_condition Alembic migration, zorunlu çıkış nedeni formu, kapalı poz. stats

### What Worked

- **Plan checker → tek iterasyon:** Her plan ilk checker çalışmasında ya PASS aldı ya da tek spesifik blocker ile döndü (Phase 47: GET serialization eksikliği). Planner kalitesi yüksek.
- **Verifier sonuçları hızlı:** 5 faz verificasyonu da `passed` çıktı — executor'lar planı tam uyguladı.
- **Inline execution (Phase 47 Wave 2/3):** Subagent token limiti sonrası inline geçiş sorunsuz çalıştı; plan dosyaları yeterince ayrıntılıydı.
- **47-CONTEXT.md planlamayı hızlandırdı:** discuss-phase kararları planner'a doğrudan geçerek araştırma atlama (`--skip-research`) mümkün oldu.

### What Was Inefficient

- **safeLabel tekrarı:** Shared utility'e taşınmadı; 5 dosyada kopyalandı. Plan checker bunu yakalamadı, integration checker sonradan buldu.
- **Phase 47 subagent token limiti:** Wave 2 executor usage limitine çarptı. Workaround: inline execution — çalışıyor ama ideal değil.
- **REQUIREMENTS.md GUNLUK checkboxları:** Phase 47 tamamlandıktan sonra checkboxlar güncellenmemişti; complete-milestone sırasında fark edildi. Plan summaries'in otomatik checkbox update tetiklemesi gerekebilir.

### Patterns Established

- `--skip-research` flag: CONTEXT.md yeterince detaylıysa araştırma atlanabilir (3/5 fazda kullanıldı).
- Backend nullable column pattern: `inspector.get_columns()` guard ile idempotent Alembic migration (006→007 zinciri).
- `useMemo` + null guard pattern: Stats bar ve concentration alerts için güvenli türetilmiş state.
- Integration checker sonrası audit: Cross-phase wiring sorunları (serialization eksikliği, safeLabel duplikasyonu) doğrulandı.

### Key Lessons

1. **GET serialization her zaman kontrol et:** Pydantic modeli + ORM column + save logic tamamlanıyorsa, GET response dict'i de güncellenmeli. Plan checker bunu checklist olarak eklemeli.
2. **Checker BLOCK → plan dosyasını düzelt, yeniden spawn etme:** Plan dosyası düzenlenip orijinal planner agent'ına SendMessage yerine yeni executor spawn etmek daha verimli.
3. **Token limit risk:** Büyük inline execution (47-02 gibi çok adımlı) için subagent yerine doğrudan inline execution tercih et — context daha temiz.

### Cost Observations

- Model mix: opus (planner), sonnet (checker, verifier, integration, executor)
- 5 faz × ~4 agent spawn = ~20 subagent çağrısı
- Inline Wave 3 execution: orchestrator context'inde yürütüldü, subagent maliyeti yok

---

## Cross-Milestone Trends

| Milestone | Phases | Plans | Duration | Requirements | Pass Rate |
|-----------|--------|-------|----------|-------------|-----------|
| v6.0 | 5 | 13 | 2 gün | 23/23 | 5/5 faz passed |

*Daha fazla milestone tamamlandıkça tablo büyüyecek.*
