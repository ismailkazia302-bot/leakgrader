# Real-Data Audit Engine Upgrade & Compliance Report

**Date:** 2026-09-11  
**Branch:** `feature/real-audit-engine`  
**Deploy Status:** Staged locally (NOT deployed; awaiting user approval)  
**Lockdown Mode:** Intact (`LOCKDOWN_PHASE=auth_ready`)  
**Verdict:** `REAL_AUDIT_READY`

---

## 1. Overview & Architecture

The audit engine has been upgraded from simulated checks to a **hybrid real-data engine** powered by:
1. **Google PageSpeed Insights API v5 (Lighthouse)**: Real mobile & desktop Core Web Vitals (LCP, CLS, TBT, FCP, Speed Index) and category scores (Performance, Accessibility, SEO, Best Practices) with 24-hour disk caching.
2. **Real-Time On-Page HTML Forensic Analyzer**: Gathers concrete proof/evidence from fetched HTML (HTTPS, Viewport, Title, Description, OpenGraph, Twitter, JSON-LD Schema, Form fields, Click-to-call, WhatsApp, Live Chat widgets, Headings, Image alts, Favicon, Calendar booking).
3. **Defensible Transparent Scoring**: Explicit breakdown displaying raw scores and weights (40% Performance, 20% Accessibility, 20% SEO, 20% Conversion).
4. **Honest Prioritized Recommendations**: Ranked High → Medium → Low, with observed evidence, plain-language commercial rationale, and specific technical remedies.
5. **SSRF Guard Protection**: Target URLs are strictly validated against private, loopback, and cloud metadata ranges before calling Google PSI or fetching HTML.

---

## 2. Real vs. Estimated Data Matrix

| Metric / Checkpoint | Data Source | Measurement Method | Defensible Qualification |
|---|---|---|---|
| **Core Web Vitals (LCP, CLS, TBT, FCP)** | Real Google PageSpeed API | Lighthouse lab simulation (mobile + desktop) | Real measured timing vs Google CWV thresholds (Good, Needs Improvement, Poor) |
| **Performance Score** | Real Google PageSpeed API | Lighthouse Performance Category (0–100) | Directly from Google PSI; marked "Pending / Unavailable" on API rate limits |
| **Accessibility Score** | Real Google PageSpeed API / On-Page | Lighthouse Accessibility or semantic HTML checks | Evaluates viewport, tap targets, image alts, headings, contrast |
| **SEO & Structure** | Real Google PSI + On-Page | Lighthouse SEO + Meta, OpenGraph & Schema | Verified presence & character lengths of title, description, schema, tags |
| **Form Friction Fields** | Real On-Page HTML | Visible `<input>`, `<select>`, `<textarea>` count | Counted once, strictly consistent across findings and recommendations |
| **Click-to-Call (`tel:`)** | Real On-Page HTML | Regex search for `href="tel:..."` | Proof carries the exact telephone link found or notes absence |
| **WhatsApp Direct Link** | Real On-Page HTML | Regex for `wa.me/`, `api.whatsapp.com` | Only claimed if truly discovered in page source; no fabricated bot claims |
| **Live Chat Widgets** | Real On-Page HTML | Signatures for 11 vendors (Intercom, Crisp, etc.) | Verified vendor presence or clean absence |
| **Calendar Booking** | Real On-Page HTML | Links for Cal.com, Calendly, ChiliPiper | Verified scheduling link or notes absence |
| **Monthly Revenue Opportunity** | Benchmark Formula | $Traffic \times 8\% \times 68.4\% \times 72\% \times 2.5\% \times Deal$ | Displayed as a **RANGE** with explicit benchmark methodology disclaimer |

---

## 3. Google PageSpeed Insights Integration & Rate Limits

- **Endpoint:** `https://www.googleapis.com/pagespeedonline/v5/runPagespeed`
- **Environment Variable:** `PAGESPEED_API_KEY` (optional). If set, passed securely as `&key=...`. The key is never logged, printed, or sent to client browsers.
- **Quota & Error Handling:**
  - Works without API key at lower per-IP rate limits.
  - Automatically retries once on HTTP 5xx errors after a 1.5-second backoff.
  - On HTTP 429 (rate limit) or timeouts, the audit engine **gracefully falls back**: it completes the audit using real on-page forensic signals, transparently adjusts score weights, and marks Core Web Vitals as `"Pending / Unavailable"`.
- **24-Hour Cache:** Results are cached in `data/pagespeed_cache.json` per domain. Repeated scans within 24 hours return instantaneously without making duplicate API requests.
- **SSRF Safety:** `validate_url_ssrf_safe` is invoked *before* any call to the PageSpeed API or HTML fetcher, preventing outbound probes to private/internal infrastructure.

---

## 4. Transparent Scoring Formulation

### A. When PageSpeed Insights is Available
$$\text{Overall Score} = 0.40 \times \text{Performance} + 0.20 \times \text{Accessibility} + 0.20 \times \text{SEO} + 0.20 \times \text{Conversion}$$

### B. When PageSpeed Insights is Rate-Limited or Timed Out
$$\text{Overall Score} = 0.40 \times \text{On-Page SEO} + 0.30 \times \text{Accessibility Forensics} + 0.30 \times \text{Conversion Signals}$$
*(Performance is explicitly marked "Omitted / Rate-Limited" in the score breakdown card so users know why it was excluded).*

---

## 5. Report Structure & UI Updates

- **Dark Theme Preserved:** Matches the established dark slate palette (`#06080e`, `#0c101c`, `#38bdf8`, `#10b981`).
- **Score Breakdown Grid:** Clean 4-column card display showing score, percentage weight, and verified data source.
- **Google Core Web Vitals Table:** Real values for LCP, CLS, TBT, FCP, Speed Index with color-coded status badges and Google good thresholds.
- **Prioritized Actionable Recommendations:** High → Medium → Low with:
  - Observed Evidence (proof)
  - Why It Matters (commercial impact)
  - Specific Implementation Fix
- **Consistent Metric Synchronization:** Form fields, opportunity range, and diagnostic points match identically across homepage UI, client-side scorecards, server-rendered `/report/<slug>`, and Executive PDF exports.

---

## 6. Test Suite Results (100% Pass)

### 6.1 Real-Data Audit Engine Suite (`qa/test_real_audit_engine.py`)
- `test_01_example_com_audit`: **PASS** (15 diagnostic checkpoints with real evidence)
- `test_02_real_site_python_org`: **PASS** (Real title, form fields, and headings verified)
- `test_03_no_unbuilt_features_or_unlabeled_claims`: **PASS** (0 occurrences of WhatsApp Closer or Directory Hub)
- `test_04_form_field_count_consistency`: **PASS** (Exact match between root count and checkpoint #6)
- `test_05_psi_timeout_resilience`: **PASS** (Graceful fallback on PSI timeout)
- `test_06_ssrf_blocking_before_psi`: **PASS** (Loopback, metadata, and private ranges blocked)
- `test_07_dossier_html_and_pdf_generation`: **PASS** (Valid HTML dossier & PDF 1.4 binary stream)

### 6.2 Existing Security & Regression Test Suites
| Test Suite | Path | Result |
|---|---|:---:|
| **Pre-Deploy Gate Suite** | `qa/test_pre_deploy_gate.py` | **94 / 94 PASS (100%)** |
| **Security Endpoint Hardening** | `qa/test_security_endpoint_hardening.py` | **30 / 30 PASS (100%)** |
| **Sprint 1 Auth & Subscriptions** | `qa/test_sprint1_suite.py` | **47 / 47 PASS (100%)** |
| **Sprint 1.5 Fixes Black-Box** | `qa/test_sprint1_5_fixes.py` | **25 / 25 PASS (100%)** |
| **Mobile Optimization Suite** | `qa/verify_mobile_optimization.py` | **45 / 45 PASS (100%)** |
| **Real Audit Engine Suite** | `qa/test_real_audit_engine.py` | **7 / 7 PASS (100%)** |
| **TOTAL** | | **248 / 248 PASS (100%)** |

---

## 7. Verdict & Next Actions

- **Verdict:** `REAL_AUDIT_READY`
- **Current Branch:** `feature/real-audit-engine`
- **Deployment Status:** **STOPPED and holding** on `feature/real-audit-engine`. Awaiting user review and approval before merging or deploying to production.
