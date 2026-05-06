---
phase: 29
slug: dashboard
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-05-06
---

# Phase 29 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (backend); no frontend test framework (no jest/vitest detected) |
| **Config file** | `backend/tests/` — no pytest.ini, run from backend root |
| **Quick run command** | `cd backend && python -m pytest tests/test_market_endpoints.py -x -q` |
| **Full suite command** | `cd backend && python -m pytest tests/ -x -q` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd backend && python -m pytest tests/test_market_endpoints.py -x -q`
- **After every plan wave:** Run `cd backend && python -m pytest tests/ -x -q`
- **Before `/gsd:verify-work`:** Full backend suite green + manual browser verification of all 4 widgets
- **Max feedback latency:** ~10 seconds (backend tests only; frontend is manual smoke)

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 29-01-01 | 01 | 1 | DASH-01/02/03 | integration (backend) | `cd backend && python -m pytest tests/test_market_endpoints.py -x -q` | ✅ | ⬜ pending |
| 29-01-02 | 01 | 1 | DASH-01 | manual smoke | Open browser → verify BIST100 banner visible with value + % change | N/A | ⬜ pending |
| 29-01-03 | 01 | 1 | DASH-02 | manual smoke | Open browser → verify 6 forex pairs with rates and directional arrows | N/A | ⬜ pending |
| 29-01-04 | 01 | 1 | DASH-03 | manual smoke | Open browser → verify 5 gold forms (gram, ons, çeyrek, yarım, tam) with TRY prices | N/A | ⬜ pending |
| 29-02-01 | 02 | 2 | DASH-04 | manual smoke | Open browser → verify portfolio placeholder card with "Henüz portföy eklenmedi" | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

None — existing infrastructure covers all backend requirements. `tests/test_market_endpoints.py` from Phase 28 already validates all three market endpoints. Frontend has no automated test framework.

*Existing infrastructure covers all phase requirements.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| BIST100 banner renders with value + change_pct | DASH-01 | No frontend test framework | Start app, open `/`, verify banner shows endeks değeri + renkli % değişim |
| Forex widget renders 6 pairs with arrows | DASH-02 | No frontend test framework | Verify 6 rows: USD, EUR, GBP, CNY, JPY, CHF each with price + ▲/▼ |
| Gold widget renders 5 forms with TRY prices | DASH-03 | No frontend test framework | Verify gram, ons, çeyrek, yarım, tam rows with TRY prices; change shows "—" (no backend data) |
| Portfolio placeholder renders | DASH-04 | No frontend test framework | Verify placeholder card with "Henüz portföy eklenmedi" heading + explanatory copy |
| Auto-refresh at 30s | DASH-01/02/03 | Timing-based | Wait 30s, verify network tab shows new API calls to /market/bist100, /market/forex, /market/gold |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
