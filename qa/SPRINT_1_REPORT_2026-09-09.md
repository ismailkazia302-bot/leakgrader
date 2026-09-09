# Sprint 1 Completion Report: Database, Authentication & Subscription System

**Sprint**: Sprint 1  
**Date**: September 9, 2026  
**Active Branch**: `feature/sprint1-accounts-database`  
**Lockdown Status**: Active (`SECURITY_LOCKDOWN_MODE=enabled`, `LOCKDOWN_PHASE=full`)  
**Verdict**: `SPRINT_1_COMPLETE`  

---

## 1. Executive Summary

Sprint 1 delivers a production-grade multi-tenant PostgreSQL data tier, a Bcrypt-based user authentication engine, session management with CSRF protection, responsive user account & dashboard interfaces, and database-backed subscription entitlement accounting for LeakGrader.

All functionality was implemented and verified on the dedicated branch `feature/sprint1-accounts-database`. Crucially, emergency lockdown behavior was strictly preserved (`LOCKDOWN_PHASE` defaults to `full`), ensuring that the 94 existing security release tests pass with zero regressions alongside the 34 new Sprint 1 tests across two consecutive clean runs.

---

## 2. Files Created and Modified

### Created Files
| File Path | Component | Purpose |
|---|---|---|
| `db/schema.sql` | Database | DDL for all 9 PostgreSQL tables, foreign keys, and 12 performance indexes. |
| `db/connection.py` | Database | Thread-safe connection pool (`ThreadedConnectionPool`), timeout config, credential masking, and SQLite local adapter. |
| `db/migrate.py` | Database | Versioned, idempotent migration runner (`schema_migrations` tracking). |
| `engine/auth.py` | Authentication | Bcrypt hashing (rounds 12), signup, rate-limited login (5 per 15 min), sessions, CSRF, and password reset. |
| `web/login.html` | Frontend | User authentication sign-in form with error alerts and forgot password trigger. |
| `web/signup.html` | Frontend | User registration interface with client validation. |
| `web/dashboard.html` | Frontend | Authenticated customer dashboard displaying active plan, monthly usage meter, and recent audits. |
| `web/account.html` | Frontend | Profile management and password update interface. |
| `qa/test_sprint1_suite.py` | Testing | 34-test comprehensive suite covering database, auth, sessions, CSRF, reset, and entitlements. |
| `qa/SPRINT_1_DATABASE_SCHEMA_2026-09-09.md` | Deliverable | Schema documentation and table entity relationship specifications. |
| `qa/SPRINT_1_TEST_RESULTS_2026-09-09.md` | Deliverable | Comprehensive test matrix and double-run execution logs. |
| `qa/SPRINT_1_REPORT_2026-09-09.md` | Deliverable | This comprehensive executive report. |

### Modified Files
| File Path | Changes |
|---|---|
| `engine/security_guard.py` | Added `get_lockdown_phase()`, `PLAN_LIMITS`, `sync_webhook_to_db()` (transactional database persistence & idempotency), and `check_db_entitlement()`. |
| `engine/wsgi_security_middleware.py` | Added `/api/auth/*` handlers, static routing for `/login`, `/signup`, `/dashboard`, `/account`, and dual-phase lockdown integration. |
| `web/index.html` | Added dynamic navigation header (Login/Sign Up for guests; Dashboard/Logout for authenticated users). |

---

## 3. Database Schema

The database schema (`db/schema.sql`) implements 9 tables with foreign-key referential integrity:
1. `users`: UUID primary key, unique email, bcrypt hash (cost 12), timestamps.
2. `workspaces`: Tenant container with `owner_id` FK and plan identifier.
3. `workspace_members`: Membership mapping with `UNIQUE(workspace_id, user_id)`.
4. `sessions`: Server-side sessions with `session_token` UNIQUE, `csrf_token`, client metadata, 7-day expiry.
5. `subscriptions`: Lemon Squeezy subscription mapping with auto-renew and anniversary timestamps.
6. `entitlements`: Feature usage quotas (`feature = 'audit'`) and counts with `UNIQUE(workspace_id, feature)`.
7. `webhook_events`: Idempotent event ledger with `event_id UNIQUE` and payload hashes.
8. `audits`: Scan history linked to workspace and user.
9. `usage_events`: Feature consumption audit trail.

12 B-tree indexes were created on frequently queried columns (`users.email`, `sessions.session_token`, `sessions.expires_at`, `subscriptions.workspace_id`, etc.).

---

## 4. API Endpoints Added

| Endpoint | Method | Auth Required | CSRF Required | Description |
|---|:---:|:---:|:---:|---|
| `/api/auth/signup` | `POST` | No | No | Creates user, default workspace, free entitlement, and starts session. |
| `/api/auth/login` | `POST` | No | No | Bcrypt validation, 5 attempt / 15 min rate limit, session rotation. |
| `/api/auth/logout` | `POST` | Yes | No | Destroys session in database, clears HTTP cookie. |
| `/api/auth/me` | `GET` | Yes | No | Returns user profile, workspace, plan, usage count, and CSRF token. |
| `/api/auth/forgot-password` | `POST` | No | No | Generates 1-hour secure password reset token. |
| `/api/auth/reset-password` | `POST` | No | No | Validates reset token, updates hash, revokes all existing sessions. |
| `/api/auth/change-password` | `POST` | Yes | Yes | Updates password for active user, requires valid `X-CSRF-Token`. |

---

## 5. Test Results (Two Consecutive Executions)

| Suite | Run 1 Result | Run 2 Result | Total | Pass Rate |
|---|:---:|:---:|:---:|:---:|
| **Sprint 1 Suite (`qa/test_sprint1_suite.py`)** | 34 / 34 PASS | 34 / 34 PASS | 34 | 100.0% |
| **Security Gate (`qa/test_pre_deploy_gate.py`)** | 94 / 94 PASS | 94 / 94 PASS | 94 | 100.0% |
| **Combined** | **128 / 128 PASS** | **128 / 128 PASS** | **128** | **100.0%** |

---

## 6. Required Environment Variables (Names Only)

When provisioning on Render or staging environments, the following environment variables are required:
- `DATABASE_URL` (Connection string to Render PostgreSQL)
- `DB_POOL_MAX` (Optional, defaults to 20)
- `DB_CONNECT_TIMEOUT` (Optional, defaults to 5 seconds)
- `SECURITY_LOCKDOWN_MODE` (`enabled` or `disabled`)
- `LOCKDOWN_PHASE` (`full` or `auth_ready`)
- `LEMONSQUEEZY_WEBHOOK_SECRET` (HMAC secret for webhooks)
- `ENVIRONMENT` (`production`, `staging`, or `test`)

---

## 7. Migration Procedure

To apply migrations in staging or production:
1. Ensure `DATABASE_URL` is set in the service environment.
2. Execute the idempotent migration runner:
   ```bash
   python -m db.migrate
   ```
3. The runner checks `schema_migrations` and applies `db/schema.sql` safely within a transaction.

---

## 8. Remaining Work (Future Sprints)

1. **Email Delivery Provider**: Integrate Brevo/Resend for production password reset and verification emails (currently logged locally in test mode).
2. **Tenant Data Isolation**: Update document storage and dossiers to isolate file systems per `workspace_id`.
3. **Transition to `auth_ready`**: Once multi-tenant document vault isolation is completed in Sprint 2, switch `LOCKDOWN_PHASE=auth_ready` to enable self-serve accounts.

---

## 9. Final Verdict

```
================================================================================
FINAL VERDICT: SPRINT_1_COMPLETE
================================================================================
```
*All code changes remain safely on `feature/sprint1-accounts-database`. No deployments have occurred, no merges to main have been initiated, and lockdown remains fully active.*
