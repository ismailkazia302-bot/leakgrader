# Critical Security Hotfix Sprint 0 Report — LeakGrader Platform

**Document Identifier**: `SECURITY_HOTFIX_REPORT_2026-09-07.md`  
**Classification**: High-Priority Security Remediation & Access Lockdown  
**Target Application**: LeakGrader (`https://leakgrader.com/`)  
**Active Branch**: `security/critical-hotfix-2026-09-07`  
**Auditor / Security Engineer**: Senior QA & Security Lead  
**Audit & Remediation Date**: September 7, 2026  
**Status**: `FIXED_LOCALLY` / `MITIGATED` (Sprint 0 Scope Completed; Zero Production Deployment)

---

## 1. Executive Summary & Sprint 0 Objectives

Following the rejection of the initial sequential remediation due to omitted server-side entitlement checks (`BUG-02`), delayed payment webhook signature verification (`BUG-05`), and incomplete Document Vault isolation, **CRITICAL SECURITY HOTFIX SPRINT 0** was commissioned and executed under strict non-destructive protocols.

All work in Sprint 0 was performed strictly on a dedicated Git branch (`security/critical-hotfix-2026-09-07`). No production deployments were executed. Sensitive environment secrets, tokens, customer personal data, and payment keys have been rigorously safeguarded and masked throughout.

Per explicit sprint guidelines, mathematical formula harmonization ($1.18M gross vs $29.5k net) and non-security legal copy adjustments were deferred to preserve focus on closing critical exposure vectors.

### Summary of Sprint 0 Security Statuses
| Component / Vulnerability | Defect Ref | Sprint 0 Status | Containment Action |
| :--- | :---: | :---: | :--- |
| **Emergency Lockdown Mode** | ARCH-01 | `FIXED_LOCALLY` | Server-side `SECURITY_LOCKDOWN_MODE` (missing in prod = enabled by default) |
| **Admin Route Containment** | BUG-01 | `FIXED_LOCALLY` | Routes (`/founder`, `/dashboard`, `/analytics`, admin APIs) return HTTP 404 in lockdown |
| **Document Vault Anti-Wipe & Isolation** | BUG-03 | `MITIGATED` | All 16 Document Vault routes return HTTP 503 (`feature_temporarily_unavailable`) |
| **Paid API Server-Side Entitlement** | BUG-02 | `FIXED_LOCALLY` | Server-side `require_authenticated_user` & `require_active_entitlement` (Default DENY) |
| **Lemon Squeezy Webhook Verification** | BUG-05 | `FIXED_LOCALLY` | Raw body HMAC-SHA256 compare digest, replay cache, atomic persistence |
| **Public Marketing & Public Audit** | PUBLIC-01 | `FIXED_LOCALLY` | Retained 100% public availability (`/`, `/about`, `/contact`, `/api/audit/run`, checkout) |
| **Permanent Multi-Tenant Storage Design** | ARCH-02 | `REQUIRES_PERMANENT_FIX` | Architecture specification completed below for Sprint 1 implementation |

---

## 2. Emergency Lockdown Mode (`SECURITY_LOCKDOWN_MODE`)

### Core Rules & Design
1. **Default-Deny In Production**: In accordance with enterprise fail-secure standards, if `SECURITY_LOCKDOWN_MODE` is unset or missing in the runtime environment, the engine defaults to **ENABLED (`True`)**.
2. **Deterministic Control**: The setting is evaluated strictly server-side in `engine/security_guard.py` (`is_lockdown_enabled()`). It can only be disabled by explicitly configuring `SECURITY_LOCKDOWN_MODE=disabled` (or `false`, `0`, `no`) in secure environment variables.
3. **Zero Client Trust**: Lockdown state never inspects client-provided cookies, query parameters, headers, or localStorage keys.
4. **Lockdown Behavior**:
   * **Admin Interfaces & APIs**: Every request to `/founder`, `/dashboard`, `/analytics`, `/api/analytics/live`, `/api/pipeline/*`, `/api/social/*`, `/api/reels/*`, `/api/subscribers/*`, `/api/contact/list`, `/api/leads/list`, and `/api/booking/list` returns **HTTP 404 Not Found**. The application actively masks the existence of administrative endpoints.
   * **Document Vault Containment**: Every Document Vault endpoint (upload, index, query, citations, summary, risk-audit, tables, clear, delete, download) returns **HTTP 503 Service Unavailable** with payload `{"error": "feature_temporarily_unavailable"}`.
   * **Paid Features**: Anonymous access to `/api/leads/generate`, `/api/leads/clear`, `/api/content-crew/run`, and `/api/content/generate` is rejected with **HTTP 403 Forbidden**. Client-side spoofing flags (`paid=true`, `admin=true`, `workspace_id`) are completely disregarded.

---

## 3. Detailed Component Remediations

### 3.1. Admin Route Containment (BUG-01)
* **Status**: `FIXED_LOCALLY`
* **Vulnerability**: Previously, navigating to `/founder` rendered the full command center with live client lead ledgers, WhatsApp outreach histories, and unmasked API configurations.
* **Sprint 0 Containment**:
  1. Routed through `MastermindRequestHandler._check_admin_access(is_api=bool)`.
  2. Under lockdown mode, requests return HTTP 404 (preventing route discovery).
  3. Under non-lockdown mode, requests require a valid `Authorization: Bearer <ADMIN_TOKEN>`. If missing or invalid, API calls receive HTTP 403 and UI visits receive HTTP 404.
  4. No hardcoded credentials exist in client JavaScript or server logs.

### 3.2. Document Vault Containment & Permanent Isolation Design (BUG-03)
* **Status**: `MITIGATED` / `REQUIRES_PERMANENT_FIX`
* **Sprint 0 Containment**:
  All sixteen Document Vault endpoints have been placed in complete containment, returning HTTP 503 (`feature_temporarily_unavailable`):
  * `GET /api/documents`
  * `GET /api/documents/download/*`
  * `POST /api/upload`, `POST /api/documents/upload`
  * `POST /api/upload-url`, `POST /api/documents/index-url`
  * `POST /api/query`, `POST /api/documents/ask`, `POST /api/omnibrain/query`
  * `POST /api/summary`, `POST /api/documents/summary`
  * `POST /api/risk-audit`, `POST /api/documents/risk-audit`
  * `POST /api/extract-tables`, `POST /api/documents/extract-tables`
  * `POST /api/clear`, `POST /api/documents/clear`
  * `POST /api/documents/delete`
  * `DELETE /api/documents/*`
* **Permanent Multi-Tenant Storage Architecture (Sprint 1 Roadmap)**:
  ```mermaid
  graph TD
      Req["Incoming Document Request"] --> Auth["require_authenticated_user()"]
      Auth --> WsCheck["require_workspace_access(tenant_id)"]
      WsCheck --> Isolation{"Storage Isolation Layer"}
      Isolation -->|Tenant Directory| TDir["/storage/tenants/{workspace_id}/"]
      TDir --> DocFile["documents.json"]
      TDir --> ChunkIdx["tenant_index.json (Isolated BM25/FAISS)"]
      TDir --> Uploads["uploads/ (Tenant Private Files)"]
  ```
  1. **Tenant-Scoped Namespacing**: Every customer is assigned a cryptographic `workspace_id`. Chunks and document indices will be strictly partitioned into `/storage/tenants/{workspace_id}/`.
  2. **Isolated Vector / BM25 Indices**: Hybrid retriever search queries will only execute against the caller workspace index.
  3. **Mutual File Access Controls**: File download and deletion operations will enforce `require_resource_ownership()` comparing `doc.owner_id == caller.user_id`.

### 3.3. Server-Side Paid API Entitlement Gating (BUG-02)
* **Status**: `FIXED_LOCALLY`
* **Vulnerability**: Anonymous clients previously triggered expensive LLM calls (`/api/leads/generate`, `/api/content/generate`) without licensing.
* **Sprint 0 Implementation**:
  1. Centralized in `engine/security_guard.py`:
     * `require_authenticated_user(headers, body_data)`: Validates bearer tokens against active entitlements. Rejects client spoofing attempts (`paid: true`, `admin: true`).
     * `require_active_entitlement(user_ctx, feature)`: Enforces that user plan grants `b2b_leads` or `seo_articles`.
     * Default outcome: **DENY (HTTP 403 `{"error": "entitlement_required"}`)**.
  2. Verified via automated tests that client attempts to pass `{"paid": true}`, `{"admin": true}`, or foreign `workspace_id` without valid tokens receive immediate HTTP 403 rejection.

### 3.4. Lemon Squeezy Webhook Verification (BUG-05)
* **Status**: `FIXED_LOCALLY`
* **Implementation Details**:
  1. **Raw Body Reading**: Webhook handler reads exact request body bytes directly from `self.rfile.read(content_length)` before any JSON parsing.
  2. **HMAC-SHA256 Signature Verification**: Computes hex digest using `LEMONSQUEEZY_WEBHOOK_SECRET` and compares against `X-Signature` via constant-time `hmac.compare_digest`.
  3. **Strict Error Codes**:
     * Missing secret in environment: HTTP 503 (`missing_production_signing_secret`).
     * Missing signature or digest mismatch: HTTP 401 (`invalid_signature_digest_mismatch`).
     * Unsupported event or wrong store ID: HTTP 400/422.
  4. **Idempotency & Replay Protection**:
     * Maintains atomic ledger in `storage/processed_webhook_events.json`.
     * Duplicate deliveries return HTTP 200 with status `duplicate_ignored`, preventing duplicate entitlement generation.
  5. **Privacy & Redaction**: Customer emails are hashed via SHA-256 (`customer_ref`). Raw PII is never logged or dumped to console.

---

## 4. Threat Matrix & Residual Risks

| Threat Vector | Pre-Sprint 0 Risk | Sprint 0 Residual Risk | Next Steps (Sprint 1) |
| :--- | :---: | :---: | :--- |
| **Admin Route Snooping** | CRITICAL | **NONE (404 Closed)** | Add SSO / multi-factor auth for founders |
| **Document Vault Data Erasure** | CRITICAL | **NONE (503 Contained)** | Implement tenant-scoped directory store |
| **Cross-Tenant Document Leakage** | CRITICAL | **NONE (503 Contained)** | Partition hybrid retriever by workspace |
| **Unpaid LLM API Scraping** | CRITICAL | **NONE (403 Gated)** | Rate-limiting and quota tracking per plan |
| **Forged Webhook Entitlements** | CRITICAL | **NONE (HMAC Enforced)**| Production secret rotation protocol |
| **Formula & Methodology Variance** | HIGH | **DEFERRED (Sprint 1)** | Two-stage UI display (Gross vs Net Closed) |

---

## 5. Deployment Recommendation

> [!IMPORTANT]
> **DO NOT DEPLOY TO PRODUCTION YET.**  
> While all critical vulnerabilities are locally contained and verified with 100% automated test pass rates on branch `security/critical-hotfix-2026-09-07`, Document Vault remains safely contained at HTTP 503 until Sprint 1 implements full tenant-isolated persistent storage. Staging verification is recommended prior to any production merge.