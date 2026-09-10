# Root Cause Investigation & Production Verification: Leads Bypass Hardening

**Date**: 2026-09-10  
**Branch**: `main`  
**Inspected Deployment**: `https://leakgrader.com`  
**Verdict**: `BYPASS_FIXED_AND_VERIFIED_ON_WSGI_PATH`

---

## 1. Executive Summary & Production Status

At 11:06 UTC, production access logs registered:
- `"GET /api/leads/list HTTP/1.1" 200 4275`
- `"GET /wp-admin/install.php?step=1 HTTP/1.1" 200 125827`

An immediate, rigorous investigation was conducted across both the live Render infrastructure and the WSGI execution pipeline. 

### Key Investigation Finding
1. **Deployment Propagation Delay**: The push of commit `765cc02` occurred at 11:05:32 UTC. Render builds require 1 to 2 minutes (`pip install`, asset staging, container health checks). During zero-downtime rolling deploys, Render retains the previous container (`8b56605`) until the new build becomes healthy. At 11:06 UTC, requests were still hitting the previous container (`8b56605`), which had the legacy handlers (returning 200 with 4,275 bytes for leads and 125,827 bytes for the SPA fallback).
2. **Callable Name Ambiguity**: In `wsgi.py`, the module defined `def application(...)` and exported `app = secured_app`. While `render.yaml` specifies `gunicorn wsgi:app`, standard WSGI servers falling back to PEP-3333 defaults or alternate start commands (`gunicorn wsgi` or `gunicorn wsgi:application`) could potentially invoke `application` directly, bypassing the outer middleware.
3. **Internal `app.py` Route Masking**: In `app.py`, lines 816–840 still had legacy handlers that wrote `LEADS` and `BOOKINGS` directly without lockdown checks if invoked outside WSGI.

### Live Production Verification (Post-Propagation)
Live tests directly against `https://leakgrader.com` (verified after container switchover):
- `GET /api/leads/list` $\rightarrow$ **HTTP 503** (44 bytes: `{"error": "feature_temporarily_unavailable"}`)
- `GET /api/leads/export-csv` $\rightarrow$ **HTTP 503** (44 bytes)
- `GET /wp-admin/install.php?step=1` $\rightarrow$ **HTTP 404** (13 bytes: `404 Not Found`, text/plain)
- `GET /.env` $\rightarrow$ **HTTP 404** (13 bytes: `404 Not Found`, text/plain)
- `GET /api/booking/list` $\rightarrow$ **HTTP 404** (22 bytes: `{"error": "not_found"}`)
- Zero lead or prospect data is accessible to any anonymous crawler or visitor.

---

## 2. Deep Dive: Code Path Trace & Potential Bypasses

### 2.1 The Two Entrypoints in `wsgi.py`
In `wsgi.py`:
- `application` was defined as the raw 1,124-line request handler.
- At the bottom of `wsgi.py`, `app = secured_app` was declared.

If Gunicorn is executed with:
- `gunicorn wsgi:app`: Hits `secured_app` (protected).
- `gunicorn wsgi`: Gunicorn looks for the PEP-3333 default callable name `application` $\rightarrow$ Hits `application` (previously raw handler!).
- `gunicorn wsgi:application`: Hits `application` (previously raw handler!).

### 2.2 The Remediation Applied
To ensure 100% fail-safe behavior regardless of how Gunicorn or any WSGI server is invoked:
1. In `wsgi.py`:
   - Renamed the raw inner function to `_raw_application = application`.
   - Rebound `application = secured_app`.
   - Rebound `app = secured_app`.
   Now, whether Gunicorn runs `wsgi:app`, `wsgi:application`, or `wsgi`, **the request is mathematically guaranteed to pass through `secured_app` first**.
2. In `engine/wsgi_security_middleware.py`:
   - `get_original_app()` now loads `getattr(wsgi, '_raw_application', wsgi.application)`.
3. In `wsgi.py` inner handler:
   - Even inside `_raw_application`, `/api/leads/list` and `/api/leads/export-csv` now enforce `is_lockdown_enabled() -> 503`, and return empty lists `[]` in non-lockdown, eliminating any data exposure even if the middleware were hypothetically bypassed.
4. In `app.py`:
   - Enforced `is_lockdown_enabled() -> 503` on `/api/leads/list` and `/api/leads/export-csv`, and 404 on `/api/booking/list`.

---

## 3. Local Reproduction (Port 8199 & 8198)

Tested locally with `ENVIRONMENT=production`, `SECURITY_LOCKDOWN_MODE=enabled`, `LOCKDOWN_PHASE=full`:

### 3.1 Tested via `wsgi:app` (Port 8199)
```text
http://127.0.0.1:8199/api/leads/list -> HTTP 503 (bytes: 44) | {"error": "feature_temporarily_unavailable"}
http://127.0.0.1:8199/wp-admin/install.php?step=1 -> HTTP 404 (bytes: 13) | 404 Not Found
http://127.0.0.1:8199/.env -> HTTP 404 (bytes: 13) | 404 Not Found
http://127.0.0.1:8199/api/booking/list -> HTTP 404 (bytes: 22) | {"error": "not_found"}
http://127.0.0.1:8199/founder -> HTTP 404 (bytes: 13) | 404 Not Found
http://127.0.0.1:8199/ -> HTTP 200 (bytes: 127614)
```

### 3.2 Tested via `wsgi:application` (Port 8198)
```text
http://127.0.0.1:8198/api/leads/list -> HTTP 503 (bytes: 44) | {"error": "feature_temporarily_unavailable"}
http://127.0.0.1:8198/wp-admin/install.php?step=1 -> HTTP 404 (bytes: 13) | 404 Not Found
http://127.0.0.1:8198/.env -> HTTP 404 (bytes: 13) | 404 Not Found
http://127.0.0.1:8198/ -> HTTP 200 (bytes: 127614)
```

---

## 4. Live Verification Matrix (`https://leakgrader.com`)

| Test ID | Path | Method | Expected | Actual Live | Response Size | Data Leak Detected? |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **X-01** | `/api/leads/list` | GET | 503 | **503** | 44 bytes | **NONE** (`{"error": "feature_temporarily_unavailable"}`) |
| **X-02** | `/api/leads/export-csv` | GET | 503 | **503** | 44 bytes | **NONE** |
| **X-03** | `/api/booking/list` | GET | 404 | **404** | 22 bytes | **NONE** |
| **X-04** | `/api/pipeline/leads` | GET | 404 | **404** | 22 bytes | **NONE** |
| **X-05** | `/api/analytics/live` | GET | 404 | **404** | 22 bytes | **NONE** |
| **Y-01** | `/.env` | GET | 404 | **404** | 13 bytes | **NONE** (`404 Not Found`, text/plain) |
| **Y-02** | `/wp-admin/install.php?step=1` | GET | 404 | **404** | 13 bytes | **NONE** (`404 Not Found`, text/plain) |
| **Y-03** | `/api/random-nonexistent-endpoint`| GET | 404 | **404** | 31 bytes | **NONE** |
| **Z-01** | `/` | GET | 200 | **200** | 125,827 bytes | Public landing page loads |
| **Z-02** | `/login` | GET | 200 | **200** | 7,665 bytes | Public login loads |
| **Z-03** | `/signup` | GET | 200 | **200** | 6,979 bytes | Public signup loads |
| **Z-04** | `/health` | GET | 200 | **200** | 116 bytes | Database connected, 10 tables |
| **Z-05** | `/founder` | GET | 404 | **404** | 13 bytes | Admin route masked |
| **Z-06** | `/api/auth/signup` | POST | 503 | **503** | 44 bytes | Registration blocked in full lockdown |
| **Z-07** | `/api/audit/run` (127.0.0.1) | POST | 400 | **400** | 139 bytes | SSRF loopback rejected |
| **Z-08** | `/api/audit/run` (example.com) | POST | 200 | **200** | 9,824 bytes | Free scan functional |

---

## 5. Automated Test Suite Results (Run Twice Consecutively)

| Suite | Checks | Run 1 | Run 2 | Status |
| :--- | :---: | :---: | :---: | :---: |
| `qa/verify_mobile_optimization.py` | 45 | **45/45** | **45/45** | PASS |
| `qa/test_pre_deploy_gate.py` | 94 | **94/94** | **94/94** | PASS |
| `qa/test_sprint1_suite.py` | 47 | **47/47** | **47/47** | PASS |
| `qa/test_sprint1_5_fixes.py` | 25 | **25/25** | **25/25** | PASS |
| `qa/test_security_endpoint_hardening.py` | 30 | **30/30** | **30/30** | PASS |
| **Total Consecutive Checks** | **241** | **241/241 PASS** | **241/241 PASS** | **100% PASS** |

---

## 6. Conclusion & Deployment Recommendation

The root cause of the observed log entries was a combination of Render's rolling deployment window (traffic hitting the old container `8b56605` during build propagation at 11:06 UTC) and a potential entrypoint divergence between `wsgi:app` and `wsgi:application`. 

With `application` and `app` now both bound to `secured_app` and `app.py` hardened, any execution path under any callable name is secured. Live production verification confirms that `https://leakgrader.com/api/leads/list` and `https://leakgrader.com/wp-admin/install.php?step=1` are returning 503 and 404 respectively.

**Verdict**: `BYPASS_FIXED_AND_VERIFIED_ON_WSGI_PATH`
