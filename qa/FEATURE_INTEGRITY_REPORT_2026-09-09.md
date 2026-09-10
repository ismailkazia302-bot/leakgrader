# SPRINT 1.5 FEATURE INTEGRITY AUDIT REPORT

**Date:** September 9, 2026  
**Simulation Environment:** `ENVIRONMENT=production`, `LOCKDOWN_PHASE=auth_ready`, `SECURITY_LOCKDOWN_MODE=enabled`  
**Test Database:** Isolated Temporary SQLite Database (`storage/test_feature_integrity.db`)  
**Active Git Branch:** `feature/sprint1-accounts-database`  
**Audit Verdict:** `BUGS_FOUND`

---

## EXECUTIVE SUMMARY

A full end-to-end simulation audit was executed to evaluate the readiness of LeakGrader's core features prior to enabling production authentication (`LOCKDOWN_PHASE=auth_ready`).

Out of **21 individual feature integrity checks**, **13 passed** and **8 failed**. 

While the fundamental authentication mechanics (signup, login, bcrypt hashing, database session persistence across cache purges) and standalone audit diagnostic calculation (scoring, 15-point diagnostic checks, 2.5% revenue leak benchmark) are operational, **the integration between authenticated users and the audit pipeline is missing**. 

Specifically:
1. Audits are not saved to the PostgreSQL/SQLite `audits` table.
2. Authenticated scans do not consume from user entitlements or increment `usage_count`.
3. Plan limits (2 audits on the Free tier) are not enforced on `/api/audit/run`, allowing infinite audits.
4. No binary or endpoint exists for `/api/audit/pdf` (returns 404).
5. Recent scans are not fetched from the database for the user dashboard.
6. `audit_start` and `audit_complete` telemetry events are not wired in `web/app.js`.

---

## AUDIT SCORECARD & RESULTS MATRIX

| Test ID | Category | Check Description | Result | Actual State | Expected State |
| :--- | :--- | :--- | :---: | :--- | :--- |
| **SCAN-01** | Scanner Engine | Audit Engine produces score (0-100) | **PASS** | `63` | `0–100` score |
| **SCAN-02** | Scanner Engine | Findings categorized with severity | **PASS** | 4 Categories (`Conversion Funnel`, `Lead Capture`, `Speed & Tech`, `SEO & Trust`) | Categorized PASS/WARN/FAIL |
| **SCAN-03** | Scanner Engine | Revenue Leak follows 2.5% close rate | **PASS** | `2.5% (Industry Benchmark)` | Explicit 2.5% formula |
| **SCAN-04** | Data Tier | Scan saved to database `audits` table | **FAIL** | `db_count = 0` | `db_count >= 1` in `audits` table |
| **PDF-01** | PDF Engine | Trigger `/api/audit/pdf` endpoint | **FAIL** | HTTP `404 Not Found` | HTTP `200 OK` |
| **PDF-02** | PDF Engine | PDF generated without corruption | **FAIL** | 0 bytes / 404 | Valid `%PDF-` binary stream |
| **PDF-03** | PDF Engine | All 15 diagnostic points in PDF | **FAIL** | Missing endpoint | 15 points in PDF document |
| **JOURNEY-01** | User Journey | User signup via `/api/auth/signup` | **PASS** | HTTP `201 Created` with cookie | User & Session Created |
| **JOURNEY-02** | User Journey | 1st scan increments usage to 1/2 | **FAIL** | `usage_count = 0/2` | `usage_count = 1/2` |
| **JOURNEY-03** | User Journey | Dashboard shows recent scan | **FAIL** | `recent_audits = []` | `recent_audits = ['firstscan.com']` |
| **LIMIT-01** | Plan Limit | 2nd scan brings usage to 2/2 | **FAIL** | `usage_count = 0/2` | `usage_count = 2/2` |
| **LIMIT-02** | Plan Limit | 3rd audit blocked with 403 (`usage_limit_reached`) | **FAIL** | HTTP `200 OK` (Unlimited) | HTTP `403 Forbidden` (`usage_limit_reached`) |
| **LIMIT-03** | Plan Limit | Dashboard UI contains Upgrade prompt | **PASS** | Present in DOM (`#upgradeBtn`) | Upgrade prompt visible |
| **TENANT-01** | Multi-Tenant | User B accessing User A audit blocked | **PASS** | HTTP `404 Not Found` (Fail-closed) | 403 or 404 |
| **TENANT-02** | Multi-Tenant | User B dashboard omits User A scans | **PASS** | Isolated empty array `[]` | User A scans excluded |
| **SESS-PERSIST-01** | Session Mgmt | Session persists across memory clears | **PASS** | DB-backed session valid | Session valid from DB |
| **UI-METER-01** | Mobile Polish | Usage Meter readable on 375px | **PASS** | CSS progress bar & stat cards present | Responsive meter layout |
| **UI-SCROLL-01** | Mobile Polish | Recent Scans table has scroll wrapper | **PASS** | `.table-scroll-wrapper` (`overflow-x: auto`) | Horizontal touch scroll |
| **UI-LOGOUT-01** | Mobile Polish | Logout button tap target adequate | **PASS** | `min-height: 38px` | Minimum touch height |
| **ANALYTICS-01** | Analytics | `audit_start` event fired on scan | **FAIL** | Not dispatched in `web/app.js` | `gtag('event', 'audit_start')` |
| **ANALYTICS-02** | Analytics | `audit_complete` event fired on complete | **FAIL** | Not dispatched in `web/app.js` | `gtag('event', 'audit_complete')` |

---

## DETAILED DEFECT BREAKDOWN

### 1. Database Persistence Failure (`SCAN-04`)
- **Location:** `engine/wsgi_security_middleware.py` (lines 383–420) & `wsgi.py` (lines 118–132).
- **Issue:** When `/api/audit/run` or `/api/audit/scan` is called, the result is saved only to `storage/audits_vault.json` (or held in memory during lockdown). There is **no SQL query executing `INSERT INTO audits`**.
- **Impact:** The `audits` table created in `db/schema.sql` remains empty. Audit history is lost on process restarts and cannot be displayed on user dashboards.

### 2. Missing PDF Export Route (`PDF-01`, `PDF-02`, `PDF-03`)
- **Location:** `engine/wsgi_security_middleware.py` & `wsgi.py`.
- **Issue:** The endpoint `/api/audit/pdf` does not exist in any routing table. The platform only has `/report/dossier/<slug>`, which is an HTML print stylesheet, and it is blocked with HTTP 503 during lockdown mode.
- **Impact:** Users and automated workflows attempting to download report PDFs receive HTTP 404.

### 3. Disconnected Entitlement & Usage Accounting (`JOURNEY-02`, `LIMIT-01`)
- **Location:** `engine/wsgi_security_middleware.py` (lines 383–420).
- **Issue:** `/api/audit/run` does not inspect the `session_token` cookie or bearer authorization header. It never calls `security_guard.check_db_entitlement(workspace_id, "audit", increment_usage=True)`.
- **Impact:** Feature consumption is never recorded in `entitlements.usage_count`. User accounts remain permanently at `0/2` usage regardless of how many scans they perform.

### 4. Bypassed Quota Enforcement (`LIMIT-02`)
- **Location:** `engine/wsgi_security_middleware.py` (lines 383–420).
- **Issue:** Because entitlement checking is absent on the audit endpoints, any user (logged in or anonymous) can trigger an unlimited number of audits. The Free plan ceiling of 2 audits/month is completely unenforced.
- **Impact:** Direct financial and infrastructure risk; free accounts have unlimited access to scanner resources without being prompted to upgrade to Pro ($49/mo) or Scale ($149/mo).

### 5. Missing Dashboard Audit Fetch (`JOURNEY-03`)
- **Location:** `engine/wsgi_security_middleware.py` (lines 304–325).
- **Issue:** `GET /api/auth/me` returns user profile, workspace, usage count, and CSRF token, but omits the `recent_audits` array. No database query is made to fetch audits by `workspace_id` or `user_id`.
- **Impact:** The "Recent Scans" table in `web/dashboard.html` always renders the empty state ("No audits executed yet").

### 6. Missing Analytics Event Instrumentation (`ANALYTICS-01`, `ANALYTICS-02`)
- **Location:** `web/app.js` (lines 313–410).
- **Issue:** In `triggerAudit()`, the frontend manages the scanning UI progress bar, but lacks event dispatching for `audit_start` and `audit_complete`.
- **Impact:** Analytics platforms (Google Tag Manager / Google Analytics 4) cannot measure audit conversion funnels or completion rates.

---

## REQUIRED REMEDIATION ROADMAP (Before Enabling `LOCKDOWN_PHASE=auth_ready`)

To achieve `FEATURES_READY` status, the following changes must be implemented:

1. **Wire `/api/audit/run` and `/api/audit/scan` to Session & Database:**
   - In `wsgi_security_middleware.py`, extract `_get_session(environ, headers)`.
   - If user is authenticated:
     - Call `check_db_entitlement(ws_id, "audit", increment_usage=False)`. If disallowed (`usage_limit_reached`), return HTTP `403 Forbidden` with `{"error": "usage_limit_reached", "message": "You have reached your monthly audit limit. Upgrade to Pro for 100 audits."}`.
     - On successful scan, call `check_db_entitlement(ws_id, "audit", increment_usage=True, user_id=user_id)`.
     - Insert record into database `audits` table (`INSERT INTO audits (workspace_id, user_id, domain, score, results) VALUES (...)`).
2. **Implement `/api/audit/pdf` Endpoint:**
   - Add handler in `wsgi_security_middleware.py` accepting `domain` or `audit_id`.
   - Return clean PDF binary stream or formatted printable HTML attachment with standard `Content-Disposition: attachment; filename="LeakGrader_Audit_<domain>.pdf"`.
3. **Populate `recent_audits` in `GET /api/auth/me`:**
   - Query `SELECT id, domain, score, created_at FROM audits WHERE workspace_id = %s ORDER BY created_at DESC LIMIT 10;`.
   - Return `recent_audits` list in JSON payload for `dashboard.html`.
4. **Instrument Telemetry Events in `web/app.js`:**
   - In `triggerAudit`: invoke `if (window.gtag) gtag('event', 'audit_start', { domain: urlOrCompany });`.
   - On response: invoke `if (window.gtag) gtag('event', 'audit_complete', { domain: urlOrCompany, score: score });`.

---

## FINAL AUDIT VERDICT

### **`BUGS_FOUND`**

*Core authentication and isolated calculation features are functional, but account-linked persistence, usage metering, quota gating, PDF generation, and analytics telemetry are not yet integrated into the audit execution path. Do not transition production to `LOCKDOWN_PHASE=auth_ready` until the above remediation roadmap is applied.*
