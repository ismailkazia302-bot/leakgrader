# Independent Test-Integrity & Verification Review
**Review Date:** September 7, 2026  
**Auditor:** Senior QA Engineer / Independent Security Verification Auditor  
**Working Branch:** `security/critical-hotfix-2026-09-07`  
**Target Platform:** LeakGrader (`https://leakgrader.com/`)  

---

## 1. Executive Verdict

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║   INDEPENDENT AUDIT VERDICT: ⚠️ TEST_SUITE_NOT_INDEPENDENT                   ║
║                                                                               ║
║   APPLICATION BEHAVIOR:       ✅ BLACK-BOX SECURITY CONTROLS VERIFIED         ║
║   PRODUCTION DEPLOYMENT:      ⛔ RELEASE_BLOCKED (DATABASE MIGRATION REQ)     ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

---

## 2. Comprehensive Test-Integrity Findings

We conducted a forensic inspection of `qa/test_pre_deploy_gate.py`, `generate_test_suite.py`, and the application codebase. Below are the definitive findings for the 7 specific integrity checkpoints:

### 1. Are Any PASS Results Hard-Coded?
- **Finding:** **NO.**
- **Details:** Inspection of `qa/test_pre_deploy_gate.py` confirms that every call to `record_test(..., passed, ...)` evaluates a genuine runtime expression (e.g., `st == exp`, `actual == expected`, `is_safe is False`, `(st == exp) and ((js or {}).get("error") == "feature_temporarily_unavailable")`). No assertion is hard-coded as `passed = True`.

### 2. Do Tests Reproduce Implementation Logic Instead of Independently Checking It?
- **Finding:** **YES (SIGNIFICANT DEFECT).**
- **Details:** 
  - **Phase 1 (Lockdown Environment Logic):** Evaluates `actual = sg.is_lockdown_enabled()`. Rather than querying the running server across environment states via black-box HTTP, it invokes the internal Python function in-process.
  - **Phase 4 (SSRF Guard):** Tests `SSRF-01` through `SSRF-18` invoke `sg.validate_url_ssrf_safe(target)` directly in-memory. Only `SSRF-19` tests the public HTTP endpoint (`POST /api/audit/run`).
  - **Phase 5 (Webhook Matrix):** Test `WH-04` tests missing secret handling by directly calling `sg.verify_lemonsqueezy_webhook(p1, sig1, secret="")` in-process with a parameter override, rather than testing an HTTP server instance booted without `LEMONSQUEEZY_WEBHOOK_SECRET`.

### 3. Are Security Functions Mocked During Core Tests?
- **Finding:** **NO MOCK LIBRARIES USED, BUT INTERNAL FUNCTIONS CALLED IN-PROCESS.**
- **Details:** The suite does not use `unittest.mock` or monkey-patching. However, directly invoking internal module functions (`sg.is_lockdown_enabled`, `sg.validate_url_ssrf_safe`, `sg.verify_lemonsqueezy_webhook`) bypasses the HTTP networking layer, request deserialization, header parsing, and server dispatch mechanisms.

### 4. Can Assertions Pass Without Starting the Real Local HTTP Application?
- **Finding:** **YES (31 OF 80 TESTS).**
- **Details:** 
  - All 13 Phase 1 tests (`ENV-01` to `ENV-13`) and 18 Phase 4 SSRF unit tests (`SSRF-01` to `SSRF-18`) evaluate entirely in-memory.
  - During initial harness execution when the HTTP server thread had not been started, all 31 of these tests evaluated to **`PASS`**, while the remaining 49 HTTP tests failed. This proves that 38.75% of the test suite can pass with the server offline.

### 5. Did the Generated Suite Replace or Weaken an Earlier Test Suite?
- **Finding:** **REPLACED AS PRIMARY RELEASE GATE WITHOUT REMOVING SPRINT 0 SUITE.**
- **Details:** `test_security_sprint0.py` remains in `qa/`. However, `test_pre_deploy_gate.py` was introduced as the release gate without fully adopting black-box testing principles. While `test_pre_deploy_gate.py` covers more total cases (80 vs 12), it diluted test independence by embedding in-process unit checks into what should have been an end-to-end integration gate.

### 6. Are Exceptions Swallowed or Converted into PASS?
- **Finding:** **NO.**
- **Details:** In `run_http_request()`, exceptions during HTTP transmission return `0, None, str(e)`. Since all expected statuses are legitimate positive HTTP codes (200, 401, 403, 404, 405, 503), any exception evaluates as `0 == expected` -> `False` (FAIL). No exception is converted into a PASS.

### 7. Do Tests Depend on Execution Order or Stale Local State?
- **Finding:** **YES (CRITICAL TEST DESIGN DEFECT).**
- **Details:**
  - **Sequential Coupling:**
    - `WH-05` (webhook replay) explicitly depends on `WH-01` having executed immediately prior with the exact same payload.
    - `WH-10` (subscription cancellation) explicitly depends on `WH-01` having created an active entitlement token for `sub_valid_101`.
    - `WH-16` (cancellation replay) explicitly depends on `WH-10` having executed.
  - **State Pollution / Lack of Teardown:**
    - The suite modifies `storage/active_entitlements.json` and `storage/processed_webhook_events.json` on disk during execution.
    - If `test_pre_deploy_gate.py` is executed a second time without manually wiping the storage directory, `WH-01` will fail because `evt_sub_valid_101_subscription_created` is already marked as processed, causing it to be treated as a duplicate delivery instead of creating an entitlement.

---

## 3. Review of Lemon Squeezy Subscription Lifecycle

### Defect Identified: Premature Entitlement Revocation on `subscription_cancelled`
In `omnibrain/engine/security_guard.py`:
```python
is_deactivating_event = (
    event_name in [
        "subscription_cancelled",
        "subscription_expired",
        "subscription_paused",
        "subscription_unpaid",
        "subscription_payment_failed"
    ]
    or sub_status in ["cancelled", "expired", "paused", "unpaid", "past_due"]
)

if is_deactivating_event:
    entitlements = _load_entitlements()
    revoked_count = 0
    for tok, rec in list(entitlements.items()):
        if str(rec.get("order_id", "")) == order_or_sub_id:
            rec["status"] = "inactive"
            rec["revoked_at"] = time.time()
            rec["expires_at"] = time.time()
            revoked_count += 1
```

### Forensic Analysis:
1. **The Commercial SaaS Standard:** In Lemon Squeezy and Stripe, when a user cancels a recurring subscription, they are cancelling **future auto-renewal**.
2. **Prepaid Billing Period:** The user has already paid for the current billing cycle. The webhook payload contains `attributes.ends_at` (or `attributes.renews_at`), which is typically days or weeks in the future.
3. **Current Flaw in Hotfix:** The hotfix immediately sets `rec["status"] = "inactive"` and `rec["expires_at"] = time.time()`.
4. **Impact:** A paying customer who cancels auto-renewal on day 2 of a 30-day billing period is immediately locked out and receives HTTP 401 Unauthorized for the remaining 28 paid days.
5. **Required Correction in Sprint 1:**
   - On `subscription_cancelled`: Set `rec["auto_renew"] = False` and update `rec["expires_at"]` to the UNIX timestamp of `attributes.ends_at`. Do **not** set status to `inactive` until `time.time() > ends_at` or until `subscription_expired` is received.
   - On `subscription_expired`: Immediately revoke access (`rec["status"] = "inactive"`).

*(Per user instructions, application code was not modified during this audit).*

---

## 4. Source & Test Code Immutability Verification

Before and after running the clean checkout verification suite, a complete SHA-256 hash fingerprint was generated across all 370 source, engine, web, and test files in `c:\Users\Administrator\Downloads\mastermind\omnibrain`:
- **Files Checked:** 370
- **Modified During Review:** **0**
- **Git Status:** Clean unstaged state preserved. Zero commits, zero deployments, zero merges.
