# Critical Pre-Merge WSGI Security Verification Report

**Audit Date**: September 9, 2026  
**Repository**: `mastermind/omnibrain` (LeakGrader)  
**Target Branch**: `security/critical-hotfix-2026-09-07`  
**Inspected File**: `omnibrain/wsgi.py` (1,124 lines)  
**Final Verdict**: `WSGI_REQUIRES_FIX`  

---

## Executive Summary

A comprehensive line-by-line inspection of `wsgi.py` reveals that **deploying `gunicorn wsgi:app` to production would completely bypass all security lockdown and entitlement protections implemented in Sprint 0, Sprint 0.5, and Sprint 0.7.**

`wsgi.py` does not import an `app` object from `app.py`, nor does it delegate requests to `MastermindRequestHandler`. Instead, `wsgi.py` defines its own standalone WSGI callable (`application`) containing duplicate route implementations that **lack any calls to `engine/security_guard.py`**.

---

## Detailed Answers to Verification Questions

### 1. Structure and Nature of `wsgi.py`
`wsgi.py` is an independent 1,124-line WSGI application originally created on September 3, 2026 (`commit 800c24d`) to allow Gunicorn execution on Render.
- Lines 1–49: Import engines and data helpers from `app.py`.
- Lines 51–1114: Standalone WSGI `application(environ, start_response)` containing hardcoded route matching (`if path in ... elif path == ...`).
- Line 1116: `app = application` (Gunicorn entry point).

### 2. Does `wsgi.py` import the `app` object from `app.py`?
**NO.**
There is no `app` object in `app.py` (`app.py` defines `MastermindRequestHandler(BaseHTTPRequestHandler)`).
The exact import statement at lines 15–24 of `wsgi.py` is:
```python
from app import (
    ALL_DOCUMENTS, ALL_CHUNKS, BOOKINGS, LEADS, AUDITS,
    RETRIEVER, INTELLIGENCE, LEAD_AGENT, BOOKING_AGENT,
    CONTENT_CREW, AUDIT_ENGINE, SEO_ENGINE, PAYMENT_ENGINE, GROWTH_AGENT, PLANS,
    ANALYTICS_DASHBOARD, WEBSITE_MANAGER, SOCIAL_POSTER, SENTINEL_AGENT,
    TRAFFIC_BLASTER, VIRAL_REEL_STUDIO, COMPETITOR_SPY, SECURITY_HEADERS,
    CONTACT_ENGINE, PIPELINE_ORCHESTRATOR, STORAGE_DIR, PIPELINE_MAIL_DISPATCHER,
    WEB_DIR, save_index, save_bookings, save_leads, save_audits, load_all_data,
    start_autonomous_cloud_growth_daemon
)
```
`wsgi.py` creates its own callable at line 51:
```python
def application(environ, start_response):
    ...
```
and aliases it at line 1116:
```python
app = application
```

### 3. Does the imported app object include the security middleware?
**NO.**
- `MastermindRequestHandler` is never instantiated or called by `wsgi.py`.
- `engine.security_guard` is **not imported** anywhere in `wsgi.py`.
- `is_lockdown_enabled()` is **never invoked** in `wsgi.py`.
- `validate_url_ssrf_safe()` is **never invoked** in `wsgi.py`.
- `require_authenticated_user()`, `require_admin()`, and `require_active_entitlement()` are **never invoked** in `wsgi.py`.

### 4. Complete Request Path Trace
When Render executes `gunicorn wsgi:app --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120`:

```text
Incoming HTTP Request
       │
       ▼
Gunicorn Worker Process
       │
       ▼
wsgi.py : application(environ, start_response)
       │
       ├───────────────────────────────────────────────────────┐
       ▼                                                       ▼
[CRITICAL VULNERABILITY]                                  Static Assets / Fallback
Route matches directly inside wsgi.py:                   • /founder is NOT hidden (404);
• POST /api/leads/generate -> executes and returns 200     it falls through to line 1098
  (Locks and tokens completely bypassed!)                  and returns index.html (200 OK)!
• POST /api/upload -> accepts uploads up to 10MB;
  returns 200 (Lockdown 503 bypassed!)
• POST /api/audit/run -> executes without SSRF checks;
  returns 200 (SSRF defenses bypassed!)
       │
       ▼
security_guard.py is NEVER EXECUTED.
```

### 5. Multi-Process Concurrency & `threading.RLock()` in Lockdown Mode
- **Lockdown File Writes**: In `app.py`, lockdown mode strictly disables file writes:
  - Document vaults, lead generation, booking clearing, and checkout creation return fail-closed HTTP 503 without disk I/O.
  - Public scanner persistence is disabled: `if not is_lockdown_enabled(): save_audits()`.
- **`_SECURITY_LOCK = threading.RLock()`**:
  - `_SECURITY_LOCK` is only used in `engine/security_guard.py` during webhook processing (`verify_lemonsqueezy_webhook`).
  - Disk persistence in `security_guard.py` uses `_atomic_json_dump` (temporary file write followed by `os.replace` rename), which provides filesystem-level atomic rename semantics on POSIX/Linux.
  - Since lockdown mode suppresses file writes for public and protected endpoints, cross-process RLock limitations under Gunicorn `--workers 2` do not compromise lockdown integrity.

### 6. Discrepancy Between Sprint 0.7 QA and WSGI Production Target
- The Sprint 0.7 black-box test suite (`qa/test_pre_deploy_gate.py`) starts `python app.py` as an OS subprocess and validates `MastermindRequestHandler`.
- All 89 passing security checks tested `app.py`.
- Neither `render.yaml` nor `Procfile` executes `python app.py`; both execute `gunicorn wsgi:app`.
- Consequently, deploying `main` with the current `Procfile` / `render.yaml` would run an unpatched `wsgi.py` and leave production unprotected.

---

## Required Remediation Options

To make production safe for deployment, one of the following two actions must be taken before pushing:

### Option A (Recommended & Immediate): Update Start Command
Update `Procfile` and `render.yaml` (and Render Dashboard Settings → Start Command) to execute `app.py` directly:
```bash
python app.py
```
Because `app.py` is already a multi-threaded HTTP server (`ThreadingHTTPServer`) with full socket binding on `$PORT`, complete SSRF filtering, lockdown fail-closed gating, and 89/89 automated tests verifying it.

### Option B: Protect `wsgi.py` via WSGI Security Middleware
Import `is_lockdown_enabled`, `validate_url_ssrf_safe`, and `require_admin` into `wsgi.py` and install an interceptor at the top of `application(environ, start_response)` to enforce fail-closed lockdown, route hiding, and SSRF filtering identically to `app.py`.

---

## Verdict

```
================================================================================
VERDICT: WSGI_REQUIRES_FIX
================================================================================
Do NOT merge to main or push to GitHub until either the Render Start Command
is aligned to python app.py or wsgi.py is fully patched with the security guard.
================================================================================
```
