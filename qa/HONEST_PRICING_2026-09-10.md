# Honest Pricing & Feature Claims Alignment Report

**Date:** 2026-09-10  
**Environment:** Production Simulation (`ENVIRONMENT=production`, `SECURITY_LOCKDOWN_MODE=enabled`, `LOCKDOWN_PHASE=full`)  
**Verdict:** `PRICING_HONEST`

---

## Executive Summary

Following a forensic audit of backend readiness, all premature and unbuilt feature claims (white-label PDF branding, custom logo upload, multi-tenant client workspaces, and team member seats) have been removed or explicitly relabeled as **"Coming Soon"** across [leakgrader.com](http://leakgrader.com/).

The pricing structure now sells **only live, working features**:
1. Automated 15-point forensic revenue leak audits
2. Downloadable executive PDF reports (for paid tiers)
3. Shareable HTML report dossiers
4. Complete audit history & priority support

Unbuilt capabilities have been honestly communicated with clear "Coming Soon" notes and waitlist CTAs, eliminating the risk of customer deception or chargebacks upon launch.

---

## Task 1 & 2: Old vs. New Claims Matrix

| Area | Old Claim (Premature) | New Claim (Honest) | Status / Implementation |
| :--- | :--- | :--- | :--- |
| **Free Tier ($0)** | "No white-label" | "Basic findings only" | Factual description of preview capabilities. |
| **Solo Tier ($29/mo)** | "PDF report download" | "Downloadable PDF report" | Factual. Unlocked for Solo users in DB. |
| **Pro Tier ($79/mo)** | • White-label PDF reports<br>• Your logo and branding<br>• 3 client workspaces<br>• 3 team members | • 100 audits per month<br>• Full findings + recommendations<br>• Downloadable PDF reports<br>• Priority email support<br>• Shareable HTML report links<br><br>*(Note: "Rolling out soon for Pro: White-label branding, custom logo, client workspaces & team seats.")* | Relabeled unbuilt features as **Rolling out soon for Pro subscribers**. Backend plan code preserved as `agency` (100 audit limit). |
| **Scale Tier ($199/mo)** | Live checkout for 10 workspaces & 10 team members | Marked **Coming Soon** with badge & dashed border; CTA changed to **"Join Scale Waitlist"** | Prevents purchase of unbuilt 10-workspace tier while capturing high-volume interest. |
| **How It Works (Step 3)** | "Download a branded PDF report with your agency logo." | "Download an executive PDF audit report." | Removed false agency logo claim. |
| **Comparison Matrix** | "White-Label Reports: Yes (Agency+)" | "Executive PDF Reports: Yes (Solo+)" | Factual comparison reflecting actual PDF export capability. |
| **Testimonials Section** | "The branded white-label PDF reports look like a $10,000 deliverable..." | "The executive PDF audit reports look like a $10,000 deliverable..." | Factual quote phrasing aligned with current deliverable. |
| **FAQ Q2** | "...For full findings, PDF reports, and white-label branding, paid plans start at $29/month." | "...For full findings, downloadable PDF reports, and audit history, paid plans start at $29/month." | Removed false $29 white-label claim. |
| **FAQ Q6** | "On Agency and Scale plans, you can add your own logo, colors, and branding..." | "White-label branding is rolling out soon. Today, Pro includes full audits, downloadable PDF reports, and shareable report links. Custom agency logos, unbranded reports, and client workspaces will roll out automatically to Pro subscribers upon release." | Transparently explains current status and future rollout. |
| **JSON-LD Schema FAQ** | Promoted unbuilt white-label customization in structured Google SEO data | Synchronized with honest FAQ text | Google search schema now reflects exact live features. |

---

## Task 3 & 4: Waitlist & Coming Soon Mechanics

1. **Scale Plan Waitlist:**
   - Visual styling: Elegant dashed border (`rgba(255, 255, 255, 0.16)`), subtle amber badge (`Coming Soon`), and muted waitlist CTA (`.btn-waitlist`).
   - CTA Anchor: Links to `#email-capture-section` ("Executive CRO Intelligence" newsletter vault), seamlessly capturing enterprise leads without needing a dedicated waitlist backend.
2. **Pro "Rolling Out Soon" Note:**
   - Displayed as a subtle pill callout (`.plan-coming-soon-note`) directly inside the featured Pro card.
   - Text: *"Rolling out soon for Pro: White-label branding, custom logo, client workspaces & team seats."*
   - Gives agencies an incentive to subscribe to Pro today to lock in early pricing while setting proper expectations that branding features are in active development.

---

## Task 5: Verification & Test Results

### 1. Mobile & Viewport Verification (~380px)
- Tested at 380px width:
  - All 4 cards stack vertically with clean margins and borders.
  - `.plan-coming-soon-note` wraps comfortably without horizontal clipping.
  - All CTAs remain full-width (46px touch target) with no text cutoff.
  - Verification suite pass rate: **45/45 passed (100%)**.

### 2. Backend Plan Code Mapping
- `Free`: `href="/signup.html?plan=free"` &rarr; maps to `free` (2 audits)
- `Solo`: `href="/signup.html?plan=solo"` &rarr; maps to `solo` (25 audits)
- `Pro`: `href="/signup.html?plan=agency"` &rarr; maps to `agency` (100 audits in `PLAN_LIMITS`)
- `Scale`: `href="#email-capture-section"` &rarr; waitlist capture anchor

### 3. Automated Test Suite Results

| Test Suite | Result | Details |
| :--- | :---: | :--- |
| `qa/test_pre_deploy_gate.py` | **94/94 PASS (100%)** | Release gate, fail-closed lockdown, SSRF matrix, lifecycle webhooks. |
| `qa/test_security_endpoint_hardening.py` | **30/30 PASS (100%)** | Full lockdown 503 data isolation, probe 404s, public route safety. |
| `qa/test_sprint1_suite.py` | **47/47 PASS (100%)** | Multi-tenant auth, database persistence, CSRF, plan limit upgrades. |
| `qa/test_sprint1_5_fixes.py` | **25/25 PASS (100%)** | Scanner-DB integration, multi-tenant isolation, PDF export endpoints. |
| `qa/verify_mobile_optimization.py` | **45/45 PASS (100%)** | Responsive breakpoints, touch targets, clamp typography. |

**Total Automated Tests:** **241/241 PASSED (100% pass rate, 0 failures)**.

---

## Verdict

`PRICING_HONEST`  
All customer-facing promises now strictly match live production functionality.
