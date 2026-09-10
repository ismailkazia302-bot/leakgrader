# Pricing Consistency Fix Report
Date: 2026-09-10
Branch: `feature/sprint1-accounts-database`
Target Environment: Local Sandbox / Pre-deployment Stage

---

## 1. Executive Summary

This fix resolves the discrepancy between the frontend homepage pricing cards and the backend database/entitlement plans (`PLAN_LIMITS`). The homepage now reflects the four official subscription tiers (**Free**, **Solo**, **Agency**, and **Scale**), matching backend plan limits, pricing amounts, feature capabilities, and telemetry tracking.

---

## 2. Old vs. New Pricing Comparison

| Dimension | Previous Homepage Display (Sprint 1.6) | Updated Backend-Aligned Display | Backend Alignment (`PLAN_LIMITS`) |
| :--- | :--- | :--- | :--- |
| **Plan 1** | *(Missing)* | **Free** ($0)<br>• 2 audits/mo<br>• Top findings preview<br>• Basic score<br>• No PDF / No white-label<br>CTA: "Start Free" &rarr; `/signup.html?plan=free` | `audit_limit: 2`, `pdf_download: False`, `white_label: False` |
| **Plan 2** | **Solo** ($29/mo)<br>• 25 audits/mo | **Solo** ($29/mo)<br>• 25 audits/mo<br>• Full findings + recommendations<br>• PDF report download<br>• Audit history<br>CTA: "Choose Solo" &rarr; `/signup.html?plan=solo` | `audit_limit: 25`, `pdf_download: True`, `white_label: False`, `audit_history: True` |
| **Plan 3** | **Pro** ($79/mo, Featured)<br>• 100 audits/mo | **Agency** ($79/mo, **Most Popular**)<br>• 100 audits/mo<br>• White-label PDF reports<br>• Your logo and branding<br>• 3 client workspaces<br>• 3 team members<br>CTA: "Choose Agency" &rarr; `/signup.html?plan=agency` | `audit_limit: 100`, `pdf_download: True`, `white_label: True`, `workspaces: 3`, `team_members: 3` |
| **Plan 4** | **Agency** ($199/mo)<br>• Unlimited audits | **Scale** ($199/mo)<br>• 400 audits/mo<br>• White-label reports<br>• 10 client workspaces<br>• 10 team members<br>• Scheduled rescans<br>• Priority support<br>CTA: "Choose Scale" &rarr; `/signup.html?plan=scale` | `audit_limit: 400`, `pdf_download: True`, `white_label: True`, `workspaces: 10`, `team_members: 10`, `scheduled_rescans: True` |

### Comparison Table Alignment
- Updated the **LeakGrader Starting Price** row from `$29/mo` to **`Free / $29+`**, recognizing the 2 free monthly audits tier while retaining accurate comparison across SEOptimer ($19/mo), Semrush ($129/mo), and Screaming Frog ($259/yr).

### Pricing Note
- Appended official pricing disclosure note: *"All prices in USD. Cancel anytime."* below the 4-card grid.

---

## 3. Plan Codes Confirmed Matching Backend

The plan codes configured on the frontend CTA elements and checkout telemetry are:
- `free`
- `solo`
- `agency`
- `scale`

These match the canonical keys in `engine/security_guard.py`:
```python
PLAN_LIMITS = {
    "free": {"audit_limit": 2, "pdf_download": False, "white_label": False, "workspaces": 1, "team_members": 1},
    "solo": {"audit_limit": 25, "pdf_download": True, "white_label": False, "workspaces": 1, "team_members": 1, "audit_history": True},
    "agency": {"audit_limit": 100, "pdf_download": True, "white_label": True, "workspaces": 3, "team_members": 3, "audit_history": True},
    "scale": {"audit_limit": 400, "pdf_download": True, "white_label": True, "workspaces": 10, "team_members": 10, "audit_history": True, "scheduled_rescans": True}
}
```

---

## 4. FAQ Consistency Verification

The FAQ accordion and JSON-LD `FAQPage` schema on `web/index.html` were audited for pricing and plan parity:
- **Question 2 (*Is it free to use?*)**: Confirmed states *"Yes. You get 2 free website audits every month. For full findings, PDF reports, and white-label branding, paid plans start at $29/month."* — **Consistent**
- **Question 6 (*What are white-label reports?*)**: Confirmed states *"On Agency and Scale plans, you can add your own logo, colors, and branding to audit reports..."* — **Consistent**
- **JSON-LD Schema**: Verified identical text in `<head>` structured data markup.

---

## 5. Analytics Telemetry Added

In `web/app.js`, a guarded click handler was attached to all `.btn-plan-select` elements:
```javascript
document.querySelectorAll('.btn-plan-select').forEach(btn => {
  btn.addEventListener('click', () => {
    const planName = btn.dataset.planName || btn.dataset.plan || btn.textContent.trim();
    if (typeof gtag === 'function') {
      gtag('event', 'pricing_cta_click', { label: planName });
    }
  });
});
```
- Triggers `pricing_cta_click` with `label`: `Free`, `Solo`, `Agency`, `Scale`.
- Fully guarded with `typeof gtag === 'function'`.

---

## 6. Mobile & Responsive Layout Verification

- **Desktop (>1080px)**: 4 columns (`grid-template-columns: repeat(4, 1fr)`), clean layout with 16px gap and 1240px container max-width.
- **Tablet (641px – 1080px, tested at 768px)**: 2 columns (`grid-template-columns: repeat(2, 1fr)`), balanced card pairs.
- **Mobile (<=640px, tested at 320px, 375px, 390px, 480px)**: 1 column (`grid-template-columns: 1fr`).
- **Touch Targets**: All CTA buttons (`.btn-plan-select`) enforce full width and minimum 44px height (`min-height: 44px`).
- **Badge Visibility**: "MOST POPULAR" gradient badge is displayed on the featured **Agency** card across all viewports.
- **Horizontal Overflow**: Verified zero horizontal scrolling on all breakpoints.

---

## 7. Regression Testing Results

All 4 test suites were executed sequentially:

| Test Suite | Purpose | Checks | Result |
| :--- | :--- | :--- | :--- |
| **Mobile Optimization** (`qa/verify_mobile_optimization.py`) | Mobile layout, clamp typography, touch targets, meta tags | 45 / 45 | **PASS (100%)** |
| **Pre-Deploy Security Gate** (`qa/test_pre_deploy_gate.py`) | SSRF rejection, route lockdown, webhooks, auth guards | 94 / 94 | **PASS (100%)** |
| **Sprint 1 Suite** (`qa/test_sprint1_suite.py`) | DB migration, auth, sessions, CSRF, entitlements, limits | 47 / 47 | **PASS (100%)** |
| **Sprint 1.5 Fixes** (`qa/test_sprint1_5_fixes.py`) | Audits DB persistence, limits, multi-tenant isolation, PDF | 25 / 25 | **PASS (100%)** |
| **Total Test Verification** | **End-to-End System Integrity** | **211 / 211** | **PASS (100%)** |

---

## 8. Final Verdict

**PRICING_ALIGNED**
