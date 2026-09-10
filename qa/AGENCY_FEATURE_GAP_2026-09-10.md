# Agency Plan Feature Gap & Readiness Audit

**Audit Date:** 2026-09-10  
**Scope:** Investigation of Agency Plan ($79/mo) promises vs. actual backend & frontend implementation  
**Verdict:** `AGENCY_PLAN_HAS_GAPS`

---

## Executive Summary

The marketing and pricing sections promise high-ticket agency features for the **Agency Plan ($79/mo)**:
- 100 audits/month
- White-label PDF reports
- Custom agency logo and branding
- 3 client workspaces
- 3 team members
- Client presentation mode

Our forensic audit reveals that while the **core scanner, database persistence, plan limit expansion (100 audits), and basic PDF download binary are fully operational**, the **agency-specific customization, white-labeling, multi-workspace creation, and team collaboration features are NOT BUILT**.

If authentication were enabled and a customer paid $79 today, **4 out of the 6 core promises would fail to be delivered**.

---

## Task 1 — White-Label PDF Reports

**Investigated:** `engine/pdf_dossier.py`, `engine/wsgi_security_middleware.py` (lines 488–553)

| Check | Finding | Code Evidence |
| :--- | :--- | :--- |
| **1. Does the PDF include LeakGrader branding?** | **YES (Hardcoded)** | `pdf_dossier.py:335`: `"LEAKGRADER EXECUTIVE REVENUE LEAK DOSSIER"`<br>`pdf_dossier.py:370`: `"Prepared autonomously by LeakGrader.com"`<br>`pdf_dossier.py:218`: `<div class="logo">LEAKGRADER / EXECUTIVE REPORT</div>` |
| **2. Is there ANY way to inject a custom agency logo?** | **NO** | `generate_audit_pdf(audit_data)` and `generate_dossier_html(audit_data)` take only raw audit metrics. Neither function accepts `logo`, `logo_url`, `agency_name`, or `branding` parameters. |
| **3. Can agency colors/name replace LeakGrader branding?** | **NO** | Styles, title tags, headers, and footer attribution links (`https://leakgrader.com/report/{audit_id}`) are completely static strings in the generator. |
| **Classification** | **PARTIAL** | Basic PDF generation works, but **zero white-labeling logic exists**. |

---

## Task 2 — Logo Upload & Branding Storage

**Investigated:** `db/schema.sql`, `engine/auth.py`, `engine/wsgi_security_middleware.py`, `app.py`

| Check | Finding | Code Evidence |
| :--- | :--- | :--- |
| **1. Is there any logo/file upload feature for agencies?** | **NO** | The only file upload route in the codebase is `/api/documents/upload` for Doc Vault text/PDF ingestion. There is no route for uploading images or branding assets. |
| **2. Is there storage for uploaded logos (DB column, file storage)?** | **NO** | The `workspaces` table in `db/schema.sql` only has: `id`, `name`, `owner_id`, `plan`, `created_at`, `updated_at`. No `logo_url`, `brand_color`, or `custom_domain` columns exist. |
| **3. Is it wired to the PDF/report?** | **NO** | No pipeline exists between workspace settings and PDF generation. |
| **Classification** | **NOT_BUILT** | **0% implemented.** |

---

## Task 3 — Client Workspaces

**Investigated:** `db/schema.sql`, `engine/auth.py`, `engine/security_guard.py`

| Check | Finding | Code Evidence |
| :--- | :--- | :--- |
| **1. Can a user CREATE multiple workspaces?** | **NO** | A single default workspace (`{full_name}'s Workspace`) is created on signup. There is no `POST /api/workspaces` endpoint or creation modal. |
| **2. Can they SWITCH between workspaces in the UI?** | **NO** | No workspace switcher exists in `index.html`, `dashboard.html`, or `account.html`. `engine/auth.py:220` hardcodes `ORDER BY w.created_at ASC LIMIT 1`. |
| **3. Are audits/data scoped per workspace?** | **YES (In Database)** | `audits.workspace_id` is a foreign key to `workspaces.id`. Lookups enforce `WHERE workspace_id = %s`. Data isolation by workspace is architecturally sound. |
| **4. Is the "3 workspaces" limit enforced for Agency plan?** | **NO** | `PLAN_LIMITS["agency"]["workspaces"] = 3` exists as an inert constant in `engine/security_guard.py:788`. Because additional workspaces cannot be created, the limit is never evaluated. |
| **Classification** | **PARTIAL** | Database schema and audit scoping exist, but **workspace creation, switching, and management are NOT BUILT**. |

---

## Task 4 — Team Members & Collaboration

**Investigated:** `db/schema.sql`, `engine/auth.py`

| Check | Finding | Code Evidence |
| :--- | :--- | :--- |
| **1. Is there a team invite feature?** | **NO** | No `/api/workspace/invite` or `/api/team/invite` route exists. No invite email dispatch or UI exists. |
| **2. Is `workspace_members` table used?** | **Only for Owner on Signup** | `engine/auth.py:291` inserts a single row for the owner on registration (`role = 'owner'`). The table is never queried, joined, or mutated anywhere else. |
| **3. Can an agency invite 3 members? Do they get access?** | **NO** | Zero team onboarding mechanism exists. |
| **4. Is the limit enforced?** | **NO** | `PLAN_LIMITS["agency"]["team_members"] = 3` exists in configuration only. |
| **Classification** | **NOT_BUILT** | Table schema exists, but **feature logic is 0% implemented**. |

---

## Task 5 — Honest Gap Report & Customer Impact Analysis

### Gap Matrix

| Promised Agency Feature | Built Status | What Is Actually Built | What Is Missing | Rough Effort to Complete |
| :--- | :---: | :--- | :--- | :---: |
| **100 Audits / Month** | **FULLY_BUILT** | Entitlement expands to 100 on upgrade; DB usage counter increments; 403 blocks on 101st audit. | Nothing. Fully functional. | 0 days (Done) |
| **White-Label PDF Reports** | **PARTIAL** | Generates valid self-contained PDF 1.4 binary stream with 15 diagnostic checkpoints. | LeakGrader branding is hardcoded; no white-label override; no unbranded mode. | ~1 day |
| **Custom Agency Logo & Branding** | **NOT_BUILT** | None. | DB columns (`logo_url`, `brand_color`), upload API, UI upload button, dynamic PDF rendering. | ~2 days |
| **3 Client Workspaces** | **PARTIAL** | `workspaces` table exists; audits scoped by `workspace_id`. | Workspace creation API, workspace switcher UI, active workspace session tracking, limit enforcement. | ~2.5 days |
| **3 Team Members** | **NOT_BUILT** | `workspace_members` table exists in SQL schema. | Invite API, email invitations, member acceptance flow, team list UI, RBAC authorization. | ~3.5 days |
| **Client Presentation Mode** | **PARTIAL** | `/report/<audit_id>` renders clean full-page HTML dashboard for owner. | Displays LeakGrader header logo & verification link rather than agency presentation wrapper. | ~0.5 days |

---

### What Happens If a Customer Pays $79 for Agency Today?

| Customer Expectation | Actual Experience Today | Broken Promise? |
| :--- | :--- | :---: |
| Run up to 100 audits/month | ✅ Gets 100 audits, accurately tracked in DB | **NO** |
| Download audit PDFs | ✅ Downloads valid PDF reports from dashboard | **NO** |
| Put their agency logo on reports | ❌ Report permanently says **"LEAKGRADER EXECUTIVE REPORT"** | ⚠️ **BROKEN** |
| Hide LeakGrader from their clients | ❌ Footer explicitly reads **"Prepared autonomously by LeakGrader.com"** | ⚠️ **BROKEN** |
| Create 3 separate client workspaces | ❌ Locked to 1 single personal workspace; cannot create client spaces | ⚠️ **BROKEN** |
| Invite 2 team members to their plan | ❌ No invite button; cannot add team members | ⚠️ **BROKEN** |

---

## Recommended Action Plan

Before enabling auth or launching the Agency plan publicly, choose one of two paths:

### Option A: Honest Messaging Alignment (Fastest — 0 code changes)
Update the Agency pricing card on the homepage to reflect current reality:
- 100 audits per month
- Full findings + recommendations
- PDF report downloads
- Priority email support
- *Move "White-label & Custom Branding" and "Team Collaboration" to "Coming in Sprint 2"*.

### Option B: Build the Gaps (Sprint 1.7 / Sprint 2 — ~7-9 days total)
1. **Milestone 1 (White-Label & Logo — 3 days):**
   - Add `logo_url`, `brand_name` to `workspaces`.
   - Add logo upload endpoint and wire to `generate_audit_pdf` & `generate_dossier_html`.
2. **Milestone 2 (Workspaces & Teams — 5 days):**
   - Add workspace CRUD & switcher.
   - Add member invite flow and email triggers.
