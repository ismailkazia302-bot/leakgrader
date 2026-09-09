# Sprint 1 Auth Security Review — 2026-09-09

**Branch:** feature/sprint1-accounts-database  
**Files reviewed:** engine/auth.py, wsgi.py (auth endpoints), engine/security_guard.py  
**Reviewer:** Antigravity Pre-Deploy Gate  

---

## 1. Passwords

### 1.1 bcrypt Cost Factor
**Finding:** `engine/auth.py` line 35:
```python
salt = bcrypt.gensalt(rounds=12)
```
Cost factor 12 confirmed. Industry standard minimum is 10; 12 is appropriate for production.  
**Severity: ✅ PASS**

### 1.2 Password Logging
**Finding:** Searched all of `engine/auth.py` — password values are never passed to `logger.*` calls. The `login()` function receives `password` and passes it only to `verify_password()` which uses bcrypt's `checkpw()`. No plaintext password appears in any log call.  
**Severity: ✅ PASS**

### 1.3 Password in Responses
**Finding:** All API responses return `user` dict containing only `id`, `email`, `full_name`, `plan`, `workspace_id`. The `password_hash` field is never included in any response. Verified in `signup()` (line 257) and `login()` (line 323).  
**Severity: ✅ PASS**

---

## 2. Sessions

### 2.1 Cryptographically Secure Token Generation
**Finding:** `engine/auth.py` lines 93–94:
```python
session_token = secrets.token_urlsafe(32)  # 256 bits of entropy
csrf_token = secrets.token_hex(32)          # 256 bits of entropy
```
`secrets` module uses OS CSPRNG. 32 bytes = 256 bits of entropy. Sufficient for production.  
**Severity: ✅ PASS**

### 2.2 Cookie Security Flags
**Finding:** `engine/auth.py` lines 427–431:
```python
def build_cookie_header(session_token, max_age=604800):
    is_prod = os.environ.get("ENVIRONMENT", "").lower() == "production"
    secure_flag = "; Secure" if is_prod else ""
    return f"session_token={session_token}; Path=/; Max-Age={max_age}; HttpOnly; SameSite=Lax{secure_flag}"
```
- `HttpOnly`: ✅ Present — prevents JavaScript XSS theft
- `Secure`: ✅ Present in production (when `ENVIRONMENT=production`)
- `SameSite=Lax`: ✅ Present — CSRF protection for cross-site navigations
- `Path=/`: ✅ Correct scope

**LOW RISK:** `SameSite=Strict` would be more restrictive. `Lax` is acceptable and more user-friendly (allows cross-site GET navigations). Not a blocker.

**Severity: ✅ PASS (LOW note on SameSite=Lax vs Strict)**

### 2.3 Server-Side Session Storage
**Finding:** Sessions stored in `sessions` database table with columns: `id`, `user_id`, `session_token` (UNIQUE), `csrf_token`, `expires_at`, `ip_address`, `user_agent`. Server validates session_token against database on every request. No JWT or stateless tokens used.  
**Severity: ✅ PASS**

### 2.4 Session Expiry
**Finding:** Sessions expire after 7 days (`timedelta(days=7)`). `validate_session()` checks `expires_at > NOW()`. `cleanup_expired_sessions()` is called on every `validate_session()` invocation to purge old records.  
**Severity: ✅ PASS**

### 2.5 Session Rotation on Login
**Finding:** `engine/auth.py` lines 303–307: On each new login, all existing sessions for that user are **deleted** before a new session is issued:
```python
cur.execute("DELETE FROM sessions WHERE user_id = %s;", (user_id,))
```
This forces single-session-per-user and invalidates any stolen old sessions on re-login.  
**Severity: ✅ PASS**

---

## 3. CSRF

### 3.1 CSRF Token on State-Changing Endpoints
**Finding:** `engine/auth.py` lines 410–424: `validate_csrf()` checks `X-CSRF-Token` header against the stored `csrf_token` in the session.

The auth endpoints (`/api/auth/login`, `/api/auth/signup`) are **excluded from CSRF** because they are pre-authentication (no session exists yet). This is the correct standard behavior.

State-changing endpoints that require an active session should call `validate_csrf()` — this is implemented in `wsgi.py` auth route handlers for logout and `/api/auth/me`.

**MEDIUM FINDING:** The CSRF check should be confirmed applied to ALL state-changing authenticated endpoints (e.g., `/api/auth/reset-password` if session-authenticated). If only tested in Sprint 1 on auth endpoints, post-login API endpoints from Sprint 2+ must also enforce CSRF.  
**Severity: ⚠️ MEDIUM — Recommend documenting which Sprint 2+ endpoints require CSRF enforcement**

### 3.2 Timing-Safe Token Comparison
**Finding:** `engine/auth.py` line 424:
```python
return hmac.compare_digest(header_csrf.strip(), session_info["csrf_token"].strip())
```
`hmac.compare_digest` provides constant-time comparison, preventing timing attacks.  
**Severity: ✅ PASS**

---

## 4. Rate Limiting

### 4.1 Login Rate Limit
**Finding:** `engine/auth.py` lines 47–70:
- Window: 15 minutes
- Limit: 5 failed attempts per email per window
- Storage: In-memory dict with `threading.Lock()` protection
- Response: HTTP 429 on 6th attempt

Verified by Sprint 1 test AUTH-LOGIN-03: 5 failed attempts → 6th returns 429 ✅

**MEDIUM FINDING:** Rate limiting is **in-memory only**. In a multi-worker/multi-process production deployment (Gunicorn with `--workers 2`), rate limit counters are not shared across workers. An attacker could brute-force using a round-robin across 2 workers (10 attempts per 15 min instead of 5).

**Not a Sprint 1 blocker** — current deployment is low-traffic. Document for Sprint 2: add Redis-backed distributed rate limiting or sticky sessions.  
**Severity: ⚠️ MEDIUM — Multi-worker rate limit isolation**

### 4.2 Password Reset Rate Limiting
**Finding:** `forgot_password()` does not implement explicit rate limiting. It always returns the same success message (enumeration-safe), but does not limit how many reset tokens can be generated per IP or per email.

**MEDIUM FINDING:** An attacker could flood the reset endpoint, filling `_RESET_TOKENS` (in-memory) until memory is exhausted, or overwhelm email delivery (once email is implemented). Recommend adding per-email rate limit (e.g., max 3 resets per hour).  
**Severity: ⚠️ MEDIUM — Password reset not rate-limited**

---

## 5. SQL Injection

### 5.1 Parameterized Queries
**Finding:** All SQL in `engine/auth.py` and `engine/security_guard.py` uses parameterized queries with `%s` placeholders passed to `cur.execute(sql, params)`. Reviewed 100% of SQL statements — no string concatenation or f-string interpolation used in SQL.

Representative example:
```python
cur.execute("SELECT id FROM users WHERE LOWER(email) = %s;", (email,))
```
**Severity: ✅ PASS — No SQL injection vectors found**

---

## 6. Password Reset

### 6.1 Tokens Are Single-Use
**Finding:** `engine/auth.py` line 389: `_RESET_TOKENS.pop(token, None)` — token is removed from the dict immediately upon consumption, before the password is updated. Cannot be reused.  
**Severity: ✅ PASS**

### 6.2 Tokens Expire
**Finding:** `engine/auth.py` line 362: `expiry = time.time() + 3600` (1 hour). Line 387: `entry["expires_at"] > now` check before consuming.  
**Severity: ✅ PASS**

### 6.3 All Sessions Invalidated After Reset
**Finding:** `engine/auth.py` lines 401–405:
```python
cur.execute("DELETE FROM sessions WHERE user_id = %s;", (user_id,))
```
All active sessions are deleted after a successful password reset. Confirmed by Sprint 1 test RESET-04.  
**Severity: ✅ PASS**

### 6.4 Reset Token Exposure
**Finding:** `engine/auth.py` line 369:
```python
logger.info(f"[TEST_ONLY] Generated password reset token for {email}: {token}")
resp["reset_token_test"] = token
```
The `reset_token_test` field is returned in the API response body AND logged. This is **intentional for test mode only** (Sprint 1 has no email delivery yet). 

**HIGH FINDING:** `reset_token_test` is exposed in the API response in **all environments**, not gated by `ENVIRONMENT=test`. If this endpoint is reachable in production before email delivery is implemented, an attacker could request a reset for any email and observe the token in the response.

**REQUIRED FIX BEFORE AUTH_READY PHASE:** Gate `reset_token_test` on `ENVIRONMENT not in ["production"]`. The logger line is acceptable (logs are not user-facing), but the response field must be suppressed in production.

**Severity: 🔴 HIGH — reset_token_test exposed in production API response**

---

## 7. Lockdown Phase and Auth Endpoints

### 7.1 Auth Endpoints in LOCKDOWN_PHASE=full

**Finding:** In `LOCKDOWN_PHASE=full` (current production state), the following auth endpoints are **reachable** (not blocked by the lockdown):
- `POST /api/auth/signup` → 200/201
- `POST /api/auth/login` → 200/401
- `POST /api/auth/logout` → 200
- `GET /api/auth/me` → 200/401
- `POST /api/auth/forgot-password` → 200
- `POST /api/auth/reset-password` → 200/400

**Intended behavior:** Auth endpoints are intentionally reachable in `full` lockdown mode. The lockdown gates **paid feature APIs** (leads, content crew, booking, etc.) at 503. Auth is a prerequisite for the `auth_ready` phase transition and must be accessible.

This is **by design** and documented in `LOCKDOWN_PHASE_SAFETY_2026-09-09.md`.

**Severity: ✅ PASS — Intended behavior**

---

## Summary of Findings

| ID | Area | Severity | Finding |
|----|------|----------|---------|
| AUTH-SEC-01 | bcrypt cost=12 | ✅ PASS | Confirmed cost factor 12 |
| AUTH-SEC-02 | Password logging | ✅ PASS | No plaintext passwords logged |
| AUTH-SEC-03 | Password in responses | ✅ PASS | password_hash never returned |
| AUTH-SEC-04 | CSPRNG session tokens | ✅ PASS | secrets.token_urlsafe(32) |
| AUTH-SEC-05 | Cookie flags | ✅ PASS | HttpOnly, Secure (prod), SameSite=Lax |
| AUTH-SEC-06 | Server-side sessions | ✅ PASS | DB-backed, not JWT |
| AUTH-SEC-07 | Session expiry | ✅ PASS | 7-day TTL enforced |
| AUTH-SEC-08 | Session rotation | ✅ PASS | All old sessions deleted on login |
| AUTH-SEC-09 | CSRF enforcement | ⚠️ MEDIUM | Must confirm Sprint 2+ endpoints enforce it |
| AUTH-SEC-10 | Timing-safe comparison | ✅ PASS | hmac.compare_digest |
| AUTH-SEC-11 | Login rate limit | ⚠️ MEDIUM | In-memory only; not shared across workers |
| AUTH-SEC-12 | Reset rate limit | ⚠️ MEDIUM | forgot_password not rate-limited |
| AUTH-SEC-13 | SQL injection | ✅ PASS | 100% parameterized queries |
| AUTH-SEC-14 | Reset token single-use | ✅ PASS | Popped on consumption |
| AUTH-SEC-15 | Reset token expiry | ✅ PASS | 1-hour TTL |
| AUTH-SEC-16 | Session invalidation on reset | ✅ PASS | All sessions deleted |
| **AUTH-SEC-17** | **reset_token_test in prod** | **🔴 HIGH** | **Exposed in API response in all environments** |
| AUTH-SEC-18 | Auth endpoints in lockdown | ✅ PASS | Intentionally reachable |

---

## Required Fix Before auth_ready Phase

**AUTH-SEC-17 — CRITICAL FOR PRODUCTION AUTH:**

In `engine/auth.py` line 369–370, gate the test token:
```python
# Current (UNSAFE in production):
resp["reset_token_test"] = token

# Required fix:
if os.environ.get("ENVIRONMENT", "production").lower() not in ["production"]:
    resp["reset_token_test"] = token
```

This fix must be applied and committed before enabling `LOCKDOWN_PHASE=auth_ready`.

**No other CRITICAL issues found.** MEDIUM issues are acceptable for current `LOCKDOWN_PHASE=full` (no real users yet) but must be addressed before general availability.
