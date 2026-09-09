# PostgreSQL Database Schema Specification (Sprint 1)

**Date**: September 9, 2026  
**Target Database**: Render PostgreSQL 15+ (Production) / SQLite3 (Local Dialect Adapter)  
**Migration File**: `db/schema.sql`  
**Migration Runner**: `db/migrate.py`  
**Status**: VERIFIED & TESTED  

---

## 1. Schema Overview

The database architecture is designed for multi-tenant isolation, session security, robust subscription accounting, and idempotent webhook ingestion.

```
+----------------+        1:N       +----------------------+
|     users      | ---------------- |      workspaces      |
+----------------+                  +----------------------+
        |                                       |
        | 1:N                                   | 1:N
        v                                       v
+----------------+                  +----------------------+
|    sessions    |                  |  workspace_members   |
+----------------+                  +----------------------+
        |                                       |
        | 1:N                                   | 1:N
        v                                       v
+----------------+                  +----------------------+
| subscriptions  | <--------------- |     entitlements     |
+----------------+                  +----------------------+
        |                                       |
        v                                       v
+----------------+                  +----------------------+
| webhook_events |                  |     usage_events     |
+----------------+                  +----------------------+
```

---

## 2. Table Specifications

### 1. `users`
Core user identity and authentication credentials.
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    email_verified BOOLEAN DEFAULT FALSE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_login_at TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT TRUE
);
```
- **Security Invariant**: `password_hash` stores Bcrypt hashes with cost factor 12. Plaintext passwords are never persisted.
- **Index**: `idx_users_email` on `users(email)` for sub-millisecond lookup during login and duplicate checking.

---

### 2. `workspaces`
Tenant boundary container.
```sql
CREATE TABLE workspaces (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    owner_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    plan VARCHAR(50) DEFAULT 'free',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```
- **Plans**: `free`, `solo`, `agency`, `scale`.

---

### 3. `workspace_members`
Multi-tenant team membership mapping.
```sql
CREATE TABLE workspace_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(50) DEFAULT 'member',
    invited_at TIMESTAMPTZ DEFAULT NOW(),
    accepted_at TIMESTAMPTZ,
    UNIQUE(workspace_id, user_id)
);
```
- **Roles**: `owner`, `admin`, `member`.

---

### 4. `sessions`
Server-side stateful session tokens with CSRF binding.
```sql
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    csrf_token VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    last_active_at TIMESTAMPTZ DEFAULT NOW(),
    ip_address INET,
    user_agent TEXT
);
```
- **Session Lifetime**: 7 days (`expires_at = NOW() + INTERVAL '7 days'`).
- **Rotation**: Rotated on every successful login; previous session purged.
- **Indexes**: `idx_sessions_session_token` on `sessions(session_token)`, `idx_sessions_expires_at` on `sessions(expires_at)`.

---

### 5. `subscriptions`
Lemon Squeezy subscription state mapping.
```sql
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    lemon_squeezy_subscription_id VARCHAR(255) UNIQUE,
    lemon_squeezy_customer_id VARCHAR(255),
    lemon_squeezy_order_id VARCHAR(255),
    plan VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    auto_renew BOOLEAN DEFAULT TRUE,
    current_period_start TIMESTAMPTZ,
    current_period_end TIMESTAMPTZ,
    cancelled_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```
- **Statuses**: `active`, `past_due`, `paused`, `cancelled`, `expired`, `inactive`.
- **Indexes**: `idx_subscriptions_workspace_id`, `idx_subscriptions_ls_id`.

---

### 6. `entitlements`
Feature quotas and usage tracking.
```sql
CREATE TABLE entitlements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    subscription_id UUID REFERENCES subscriptions(id) ON DELETE SET NULL,
    feature VARCHAR(100) NOT NULL,
    usage_limit INTEGER,
    usage_count INTEGER DEFAULT 0,
    usage_reset_at TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(workspace_id, feature)
);
```
- **Plan Limits**:
  - Free: `2` audits/month
  - Solo: `25` audits/month
  - Agency: `100` audits/month
  - Scale: `400` audits/month
- **Reset Logic**: Automatically resets `usage_count = 0` on subscription anniversary (`usage_reset_at`).
- **Index**: `idx_entitlements_workspace_id`.

---

### 7. `webhook_events`
Idempotent webhook ledger preventing replay attacks.
```sql
CREATE TABLE webhook_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id VARCHAR(255) UNIQUE NOT NULL,
    event_name VARCHAR(255) NOT NULL,
    payload_hash VARCHAR(64) NOT NULL,
    subscription_id VARCHAR(255),
    processed_at TIMESTAMPTZ DEFAULT NOW(),
    status VARCHAR(50) DEFAULT 'processed'
);
```
- **Idempotency**: Enforced at database level via `UNIQUE(event_id)`.
- **Indexes**: `idx_webhook_events_event_id`, `idx_webhook_events_payload_hash`.

---

### 8. `audits`
Persisted scan history linked to workspace and user.
```sql
CREATE TABLE audits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE SET NULL,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    domain VARCHAR(500) NOT NULL,
    competitor_domain VARCHAR(500),
    scan_type VARCHAR(50) DEFAULT 'single',
    results JSONB,
    score INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```
- **Indexes**: `idx_audits_workspace_id`, `idx_audits_created_at`.

---

### 9. `usage_events`
Granular feature consumption audit log.
```sql
CREATE TABLE usage_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE SET NULL,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    feature VARCHAR(100) NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```
- **Indexes**: `idx_usage_events_workspace_id`, `idx_usage_events_created_at`.

---

## 3. Migration Procedure

Migrations are executed via `python -m db.migrate` or on application startup.
1. Connects to `DATABASE_URL` (using `ThreadedConnectionPool`).
2. Creates `schema_migrations` table if not present.
3. Checks if `001_initial_schema` has been applied.
4. Executes statements in `db/schema.sql` inside a database transaction.
5. Records migration completion in `schema_migrations`.
6. Subsequent runs detect version `001_initial_schema` and exit cleanly without modifying tables.
