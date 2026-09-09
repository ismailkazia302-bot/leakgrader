# Sprint 1 Security Fix & Auth Hardening Report — 2026-09-09

**Branch:** `feature/sprint1-accounts-database`  
**Date:** 2026-09-09  
**Status:** ✅ AUTH_FIX_VERIFIED_READY_FOR_DB_SETUP  

---

## 1. Auth Endpoint Reachability in LOCKDOWN_PHASE=full

During `LOCKDOWN_PHASE=full` (with lockdown mode enabled), all routes matching `/api/auth/*` are intercepted by `engine/wsgi_security_middleware.py` (lines 250–253) before reaching inner application logic:

```python
if path_lower.startswith("/api/auth/"):
    if is_lockdown_enabled() and get_lockdown_phase() == "full":
        return _send_response(start_response, 503, body_dict={"error": "feature_temporarily_unavailable"})
```

### Exact Endpoint Behavior Matrix

| Endpoint | Method | Phase: `full` | Phase: `auth_ready` | Non-Lockdown | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `/api/auth/signup` | POST | **503 Blocked** | **201 / 400 / 409** | **201 / 400 / 409** | Gated by middleware in `full`; creates user & session in `auth_ready` |
| `/api/auth/login` | POST | **503 Blocked** | **200 / 401 / 429** | **200 / 401 / 429** | Gated by middleware in `full`; rate-limited (5 per 15 min) in `auth_ready` |
| `/api/auth/logout` | POST | **503 Blocked** | **200 OK** | **200 OK** | Gated by middleware in `full`; invalidates session in `auth_ready` |
| `/api/auth/me` | GET | **503 Blocked** | **200 / 401** | **200 / 401** | Gated by middleware in `full`; returns user & entitlements in `auth_ready` |
| `/api/auth/forgot-password` | POST | **503 Blocked** | **200 / 400** | **200 / 400** | Gated by middleware in `full`; rate-limited, generic response in `auth_ready` |
| `/api/auth/reset-password` | POST | **503 Blocked** | **200 / 400** | **200 / 400** | Gated by middleware in `full`; single-use token consumption in `auth_ready` |
| `/api/auth/change-password` | POST | **503 Blocked** | **200 / 401 / 403** | **200 / 401 / 403** | Gated by middleware in `full`; CSRF validated in `auth_ready` |

### UI Routes in `LOCKDOWN_PHASE=full`

- `GET /signup` / `GET /signup.html`: **200 OK** (Serves static signup interface)
- `GET /login` / `GET /login.html`: **200 OK** (Serves static login interface)
- `GET /dashboard` / `GET /dashboard.html`: **404 Not Found** (Route hidden while in `full` lockdown to preserve black-box isolation)

---

## 2. AUTH-SEC-17 Fix Details (Reset Token Exposure Remediation)

### Root Cause
Previously, `engine/auth.py` line 369 unconditionally appended `"reset_token_test"` to the dictionary returned by `forgot_password()`, and logged the token regardless of environment.

### Remediation Applied
In `engine/auth.py` (`forgot_password`):
1. **Production Masking:** When `ENVIRONMENT=production` (or any non-test/local environment), `reset_token_test` is strictly omitted from the response dictionary.
2. **Environment Restriction:** The token is included in the response and logged via `logger.info` **only** when `ENVIRONMENT` is explicitly `'local'` or `'test'`.
3. **Account Enumeration Prevention:** The API returns an identical generic response regardless of whether the email exists in the database:
   ```json
   {"message": "If an account exists, a reset link has been sent."}
   ```
4. **Token Generation & Storage:** In production, the cryptographic token (`secrets.token_urlsafe(32)`) is generated and stored in memory with an expiration timestamp (`time.time() + 3600`), but its value is never logged or returned over the wire.
5. **Single-Use Enforcement:** `reset_password()` executes `_RESET_TOKENS.pop(token, None)` upon first consumption. Any subsequent reset attempt with the same token returns `400 Bad Request` (`"Invalid or expired password reset token"`).
6. **Expiration:** `reset_password()` verifies `entry["expires_at"] > now`. Expired tokens return `400 Bad Request`.

---

## 3. Forgot-Password Rate Limiting Details

### Architecture & Implementation
In `engine/auth.py`:
- **Email Limit:** Maximum 3 reset requests per 15 minutes per email address.
- **IP Limit:** Maximum 5 reset requests per 15 minutes per IP address.
- **Window:** Sliding window of 900 seconds (`15 * 60`).
- **Timing & Enumeration Resistance:** When rate limits are triggered, the API returns the exact same generic response:
  ```json
  {"message": "If an account exists, a reset link has been sent."}
  ```
  with HTTP status `200 OK`. No reset token is generated or stored, and no internal state is revealed to an attacker.
- **Middleware Integration:** `engine/wsgi_security_middleware.py` extracts the client IP address (`HTTP_X_FORWARDED_FOR` or `REMOTE_ADDR`) and forwards it to `auth.forgot_password(email, ip_address=client_ip)`.

### Multi-Worker Concurrency Note
- Current implementation uses thread-safe in-memory dictionaries (`_FORGOT_ATTEMPTS_EMAIL`, `_FORGOT_ATTEMPTS_IP`) protected by `threading.Lock()`.
- **Limitation:** In-memory tracking is local to each Gunicorn worker process.
- **Sprint 2 Roadmap:** Rate limiting must be transitioned to a PostgreSQL table (`rate_limits`) or Redis cluster to ensure shared tracking across multi-worker environments.

---

## 4. Login Rate Limiting Multi-Worker Risk Assessment

- **Current State:** Login rate limiting is implemented in `engine/auth.py` (`_check_rate_limit`, `_record_failed_login`) using an in-memory dictionary (`_LOGIN_ATTEMPTS`) with a 5-failed-attempt threshold per 15-minute window.
- **Per-Worker Verification:** Within a single worker or low-worker deployment, failed logins correctly accumulate and trigger HTTP 429.
- **Multi-Worker Risk:** With Gunicorn configured for `--workers 2`, an attacker could alternate requests between workers to achieve up to 10 attempts before lockout.
- **Resolution Plan (Sprint 2):** A designated code comment has been added to `engine/auth.py` flagging this for migration to a shared PostgreSQL table or Redis in Sprint 2.

---

## 5. Regression Test Results (Two Consecutive Executions)

### Run 1

| Suite | Tests Executed | Passed | Failed | Success Rate |
| :--- | :--- | :--- | :--- | :--- |
| `qa/test_sprint1_suite.py` | 40 | 40 | 0 | **100.0%** |
| `qa/test_pre_deploy_gate.py` | 94 | 94 | 0 | **100.0%** |

### Run 2

| Suite | Tests Executed | Passed | Failed | Success Rate |
| :--- | :--- | :--- | :--- | :--- |
| `qa/test_sprint1_suite.py` | 40 | 40 | 0 | **100.0%** |
| `qa/test_pre_deploy_gate.py` | 94 | 94 | 0 | **100.0%** |

**Total passing tests across both suites:** 134/134 on both runs (identical results).

### Key Test Coverage Breakdown
- `RESET-PROD-01`: Confirmed reset token is omitted in `ENVIRONMENT=production`
- `RESET-PROD-02`: Confirmed identical generic message for existing & non-existing users
- `RESET-01`: Confirmed reset token issued in `ENVIRONMENT=test`
- `RESET-02`: Confirmed invalid token rejection (400)
- `RESET-03`: Confirmed valid password reset updates database (200)
- `RESET-SINGLE-USE`: Confirmed token cannot be reused once consumed (400)
- `RESET-EXPIRED`: Confirmed expired token is rejected (400)
- `RESET-04`: Confirmed password reset invalidates all active user sessions
- `RESET-05`: Confirmed login succeeds with new password
- `RESET-RATE-01`: Confirmed forgot-password rate limit triggers after 3 email attempts
- `RESET-RATE-02`: Confirmed forgot-password rate limit triggers after 5 IP attempts
- `DB-01` to `DB-02`: Database migration & 9-table schema verification
- `SSRF-01` to `SSRF-19`: 19 SSRF vectors blocked
- `RT-01` to `RT-21`: Route and method lockdown enforcement
- `LC-01` to `LC-10`: Lemon Squeezy webhook lifecycle verification
- `MW-01` to `MW-05`: WSGI security middleware enforcement

---

## 6. Remaining Sprint 2 Roadmap Items

1. **Email Delivery Provider:** Integrate transactional email service (SendGrid / Postmark / AWS SES) to dispatch real password reset links containing the generated tokens.
2. **Distributed Rate Limiting:** Migrate login and forgot-password rate limits from in-memory dicts to a shared PostgreSQL table or Redis instance.
3. **Document Vault Multi-Tenant Isolation:** Implement workspace-scoped document partitions before unlocking the Document Vault in `auth_ready` phase.
4. **CSRF Audit:** Ensure all newly created authenticated mutation endpoints in Sprint 2 call `auth.validate_csrf()`.

---

## 7. Final Verdict

# ✅ AUTH_FIX_VERIFIED_READY_FOR_DB_SETUP
