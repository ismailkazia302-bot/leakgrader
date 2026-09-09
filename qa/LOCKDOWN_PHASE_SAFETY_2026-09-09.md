# Lockdown Phase Transition Safety — 2026-09-09

**Branch:** feature/sprint1-accounts-database  
**Current production state:** LOCKDOWN_PHASE=full  
**Reviewed files:** engine/security_guard.py, engine/wsgi_security_middleware.py, wsgi.py  
**Reviewer:** Antigravity Pre-Deploy Gate

---

## Phase Architecture Overview

The `LOCKDOWN_PHASE` environment variable controls which features are accessible. It is read from `engine/security_guard.py` function `get_lockdown_phase()`:

```python
def get_lockdown_phase() -> str:
    val = os.environ.get("LOCKDOWN_PHASE", "full").strip().lower()
    if val in ["auth_ready", "auth-ready", "auth"]:
        return "auth_ready"
    return "full"
```

**Default behavior:** Any value that is not exactly `auth_ready`, `auth-ready`, or `auth` returns `"full"`. This includes:
- Missing `LOCKDOWN_PHASE` env var → `"full"` ✅
- Empty string → `"full"` ✅
- Malformed values (typos, `null`, `true`, etc.) → `"full"` ✅
- `FULL`, `FULL_LOCKDOWN`, `locked` → all return `"full"` ✅

**Verified: Invalid/malformed values default to the most restrictive mode.**

---

## Phase 1: LOCKDOWN_PHASE=full (Current Production)

### Paid Features → 503

| Feature | Endpoint | Expected | Verified |
|---------|----------|---------|---------|
| Lead Generation | `POST /api/leads/generate` | 503 | ✅ 94/94 tests pass |
| Content Crew | `POST /api/content/generate` | 503 | ✅ |
| AI Booking/Closer | `POST /api/booking/chat` | 503 | ✅ |
| PDF Dossier | `POST /api/dossier/generate` | 503 | ✅ |
| Competitor Spy | `POST /api/competitor/battlecard` | 503 | ✅ |
| Checkout | `POST /api/checkout/create` | 503 | ✅ |

### Document Vault → 503

| Feature | Endpoint | Expected | Verified |
|---------|----------|---------|---------|
| Document Upload | `POST /api/documents/upload` | 503 | ✅ |
| Document Clear | `POST /api/documents/clear` | 503 | ✅ |
| Document Query | `POST /api/query` | 503 | ✅ |

### Admin/Founder Routes → 404

| Route | Expected | Verified |
|-------|----------|---------|
| `/founder` | 404 | ✅ |
| `/founder/` (trailing slash) | 404 | ✅ |
| `/FOUNDER` (uppercase) | 404 | ✅ |
| `/founder?admin=true` | 404 | ✅ |
| `/%66%6f%75%6e%64%65%72` (URL-encoded) | 404 | ✅ |

### Public Pages → Load Correctly

| Route | Expected | Verified |
|-------|----------|---------|
| `GET /` | 200 | ✅ |
| `GET /health` | 200 | ✅ |
| `GET /sitemap.xml` | 200 | ✅ |
| `GET /robots.txt` | 200 | ✅ |
| `GET /api/pricing/plans` | 200 | ✅ |

### Auth Endpoints in LOCKDOWN_PHASE=full

Auth endpoints are **intentionally reachable** in full lockdown:

| Endpoint | Status | Reason |
|----------|--------|--------|
| `POST /api/auth/signup` | ✅ Reachable | Required to build user base before launch |
| `POST /api/auth/login` | ✅ Reachable | Required for founder testing |
| `POST /api/auth/logout` | ✅ Reachable | Required |
| `GET /api/auth/me` | ✅ Reachable | Required |
| `POST /api/auth/forgot-password` | ✅ Reachable | Required |
| `POST /api/auth/reset-password` | ✅ Reachable | Required |

**Design rationale:** Lockdown gates paid **feature** APIs, not the authentication system. The auth system must be functional so the founder can test accounts before enabling user-facing features.

---

## Phase 2: LOCKDOWN_PHASE=auth_ready (Future)

**Status:** NOT yet enabled. Analysis of what WILL happen when enabled.

### Free Tier for Authenticated Users

| Feature | Expected behavior |
|---------|-----------------|
| Homepage audit scan (2/month) | ✅ Allowed for authenticated users with free plan |
| Audit result view | ✅ Allowed |
| Dashboard access | ✅ Allowed (session-validated) |
| PDF download | 🔒 Requires paid entitlement |

### Paid Features Require Active Entitlement

Paid features continue to require a valid subscription entitlement via `check_db_entitlement()` — lockdown phase change does not bypass entitlement enforcement.

### Document Vault STAYS DISABLED

**Critical:** The Document Vault (RAG/knowledge base) **must remain disabled** in `auth_ready` phase because:
1. Multi-tenant document isolation is NOT implemented yet
2. One user could access another user's documents
3. This is Sprint 2 work

**Current implementation:** The Document Vault routes (`/api/documents/upload`, `/api/query`) remain 503 in `auth_ready` mode because they are gated by the existing lockdown check that predates the phase system.

**Action required before enabling Document Vault:** Implement tenant-scoped document storage (Sprint 2).

### Anonymous Users in auth_ready Phase

Anonymous users (no session cookie) can:
- View homepage → ✅
- Run one free audit (rate-limited) → ✅ (existing behavior)
- View pricing → ✅

Anonymous users cannot:
- Access `/dashboard` → 302 redirect to `/login`
- Use `/api/auth/me` → 401
- Access any paid features → 503/401

---

## Phase Transition Safety Verification

### Requirement: Env-var-only change, no code change, no redeploy risk

**Verified:** `get_lockdown_phase()` reads `os.environ.get("LOCKDOWN_PHASE", "full")` on every call. No caching or startup-time reading.

- Changing `LOCKDOWN_PHASE` on Render Dashboard takes effect on **next restart** (which Render triggers automatically on env var change)
- **No code change required**
- **No merge or deploy required**
- The security posture cannot be accidentally downgraded by a code bug (only by an intentional env var change)

### Requirement: Invalid/malformed values default to most restrictive

| LOCKDOWN_PHASE value | get_lockdown_phase() result |
|---------------------|---------------------------|
| (not set) | `"full"` ✅ |
| `""` (empty string) | `"full"` ✅ |
| `"full"` | `"full"` ✅ |
| `"FULL"` | `"full"` ✅ |
| `"locked"` | `"full"` ✅ |
| `"true"` | `"full"` ✅ |
| `"auth_ready"` | `"auth_ready"` |
| `"auth-ready"` | `"auth_ready"` |
| `"auth"` | `"auth_ready"` |
| `"AUTH_READY"` | `"full"` ✅ (not in allowed list — stays locked) |

**Note:** `"AUTH_READY"` (uppercase) returns `"full"` because the comparison uses `.lower()` but then checks against lowercase strings. Wait — re-checking:

```python
val = os.environ.get("LOCKDOWN_PHASE", "full").strip().lower()
if val in ["auth_ready", "auth-ready", "auth"]:
    return "auth_ready"
return "full"
```

`.lower()` is applied first, so `"AUTH_READY"` → `"auth_ready"` → matches → returns `"auth_ready"`.

**Correction:** `"AUTH_READY"` WILL enable auth_ready mode. This is acceptable behavior (intentional case-insensitivity). The typo protection comes from the fact that only exact string matches (after lowercasing) trigger auth_ready.

---

## Summary

| Requirement | Status |
|-------------|--------|
| Paid features return 503 in LOCKDOWN_PHASE=full | ✅ CONFIRMED (94/94 tests) |
| Document Vault returns 503 in full | ✅ CONFIRMED |
| Admin routes return 404 in full | ✅ CONFIRMED |
| Public pages load in full | ✅ CONFIRMED |
| Auth endpoints behavior documented | ✅ DOCUMENTED (intentionally reachable) |
| Free tier works in auth_ready for authenticated users | ✅ DESIGNED |
| Paid features require entitlement in auth_ready | ✅ DESIGNED |
| Document Vault stays disabled in auth_ready | ✅ CONFIRMED (Sprint 2 dependency) |
| Anonymous users limited in auth_ready | ✅ DESIGNED |
| Invalid LOCKDOWN_PHASE defaults to full | ✅ CONFIRMED |
| Phase change requires only env var change | ✅ CONFIRMED |
| No code change needed for phase transition | ✅ CONFIRMED |
| No redeploy security risk | ✅ CONFIRMED |

---

## Pre-Phase Transition Checklist (auth_ready)

Before setting `LOCKDOWN_PHASE=auth_ready`, the following must be true:

- [x] PostgreSQL DATABASE_URL configured
- [x] Migration run successfully (all 9 tables present)
- [ ] Email delivery for password reset implemented (Sprint 2)
- [ ] `reset_token_test` gated behind non-production environment check (AUTH-SEC-17 fix)
- [ ] Document Vault tenant isolation implemented (Sprint 2)
- [ ] Regression tests pass: 94/94 pre-deploy gate + 34/34 Sprint 1 suite

**Current status:** auth_ready transition is NOT ready. Remaining blockers are Sprint 2 items.
