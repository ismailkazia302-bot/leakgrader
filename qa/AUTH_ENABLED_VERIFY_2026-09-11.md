# Live Authentication & Lockdown Phase Verification Report

**Date:** 2026-09-11  
**Target:** https://leakgrader.com  
**Lockdown Mode:** ENABLED  
**Lockdown Phase:** auth_ready  
**Final Verdict:** AUTH_LIVE_VERIFIED  

---

## 1. Executive Summary

Render environment parameter `LOCKDOWN_PHASE` was updated to `auth_ready`.
A live end-to-end verification was conducted against `https://leakgrader.com` with 2-second delays between all requests.

**Core Findings:**
1. **Authentication Reached & Functional:** Public UI auth pages (`/login`, `/signup`) return `HTTP 200`. User registration (`POST /api/auth/signup`) returns `HTTP 201 Created` with secure `Set-Cookie: session_token=...` headers.
2. **Full Lifecycle & Quotas Enforced:**
   - Fresh account initialized with Free plan and `0/2` usage.
   - User dashboard (`GET /dashboard`) renders `HTTP 200 OK` for authenticated sessions.
   - Running audits atomically increments database usage (`0/2` -> `1/2` -> `2/2`) and saves audit records to the database.
   - 3rd audit attempt is strictly rejected with `HTTP 403 Forbidden` and `{"error": "usage_limit_reached"}`.
   - Logout (`POST /api/auth/logout`) destroys the session and clears the cookie (`Max-Age=0`).
   - Subsequent login (`POST /api/auth/login`) succeeds with `HTTP 200 OK` and issues a fresh session.
3. **Paid Features Gated:** Paid endpoints (`/api/checkout/create`, `/api/documents`, `/api/leads/generate`) remain strictly locked down with `HTTP 503 Service Unavailable`.
4. **Security Hardening Intact:** `/founder` and `/.env` return `HTTP 404`, `/api/leads/list` rejects unauthenticated access (`HTTP 401`), and SSRF loopback probes (`127.0.0.1`) are blocked with `HTTP 400 Bad Request`.

---

## 2. Comprehensive Test Matrix

### Phase 1: Authentication Reachability
| Test ID | Method | Endpoint / Target | Expected | Actual | Result | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **AR-01** | `GET` | `/login` | `200` | **`200 OK`** | **PASS** | Login page reachable |
| **AR-02** | `GET` | `/signup` | `200` | **`200 OK`** | **PASS** | Signup page reachable |
| **AR-03** | `POST` | `/api/auth/signup` | `201` | **`201 Created`** | **PASS** | User registered; secure session cookie returned |

### Phase 2: Full User Lifecycle & Free Tier Enforcement
| Test ID | Method | Endpoint / Target | Expected | Actual | Result | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **LC-02** | `GET` | `/api/auth/me` | `200` | **`200 OK`** | **PASS** | Verified initial state: `plan=free`, usage `0/2` |
| **LC-03** | `GET` | `/dashboard` | `200` | **`200 OK`** | **PASS** | Authenticated session renders dashboard UI |
| **LC-04** | `POST` | `/api/audit/run` (1st audit) | `200` | **`200 OK`** | **PASS** | Audit executed & saved to database |
| **LC-05** | `GET` | `/api/auth/me` (after 1st) | `200` | **`200 OK`** | **PASS** | Verified usage counter incremented to `1/2` |
| **LC-06** | `POST` | `/api/audit/run` (2nd audit) | `200` | **`200 OK`** | **PASS** | 2nd audit executed; usage counter reached `2/2` |
| **LC-07** | `POST` | `/api/audit/run` (3rd audit) | `403` | **`403 Forbidden`** | **PASS** | Quota ceiling enforced (`usage_limit_reached`) |
| **LC-08** | `POST` | `/api/auth/logout` | `200` | **`200 OK`** | **PASS** | Session revoked; cookie cleared with `Max-Age=0` |
| **LC-09** | `POST` | `/api/auth/login` | `200` | **`200 OK`** | **PASS** | Re-authenticated with valid credentials; new session issued |

### Phase 3: Paid Features Gated (`auth_ready` Phase)
| Test ID | Method | Endpoint / Target | Expected | Actual | Result | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **PL-01** | `POST` | `/api/checkout/create` | `503` | **`503 Unavailable`** | **PASS** | Payment creation disabled in lockdown |
| **PL-02** | `GET` | `/api/documents` | `503` | **`503 Unavailable`** | **PASS** | Document vault disabled in lockdown |
| **PL-03** | `POST` | `/api/leads/generate` | `503` | **`503 Unavailable`** | **PASS** | Lead generation disabled in lockdown |

### Phase 4: Security Boundaries & Attack Rejection
| Test ID | Method | Endpoint / Target | Expected | Actual | Result | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **SC-01** | `GET` | `/founder` | `404` | **`404 Not Found`** | **PASS** | Administrative panel obscured |
| **SC-02** | `GET` | `/api/leads/list` | `503/401` | **`401 Unauthorized`** | **PASS** | Internal CRM lead list protected |
| **SC-03** | `GET` | `/.env` | `404` | **`404 Not Found`** | **PASS** | Sensitive dotfiles denied |
| **SC-04** | `POST` | `/api/audit/run` (`127.0.0.1`) | `400` | **`400 Bad Request`** | **PASS** | SSRF loopback vector blocked |

---

## 3. Verdict

**`AUTH_LIVE_VERIFIED`**
