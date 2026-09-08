# Pre-Deploy Security Release Gate Test Execution Results
**Execution Date:** September 7, 2026  
**Harness:** `omnibrain/qa/test_pre_deploy_gate.py`  
**Total Tests Executed:** 80  
**Passed:** 80 (100.0%)  
**Failed:** 0 (0.0%)  
**Verdict:** All Release Gate automated assertions PASSED.

---

## Test Execution Summary by Category

| Test Phase / Category | Test IDs | Total | Passed | Failed | Pass Rate |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Phase 1: Lockdown Environment Matrix** | `ENV-01` to `ENV-13` | 13 | 13 | 0 | 100% |
| **Phase 2: Route Normalization & Bypass Resistance** | `NORM-01` to `NORM-14` | 14 | 14 | 0 | 100% |
| **Phase 3: Paid API Lockdown (HTTP 503)** | `LOCK-01` to `LOCK-09` | 9 | 9 | 0 | 100% |
| **Phase 4: Public Scanner SSRF Security** | `SSRF-01` to `SSRF-20`, `AUDIT-PERSIST` | 21 | 21 | 0 | 100% |
| **Phase 5: Lemon Squeezy 16-Case Webhook Matrix** | `WH-01` to `WH-16` | 16 | 16 | 0 | 100% |
| **Phase 6: Auth & Entitlement Status Codes** | `AUTH-401-*`, `AUTH-403-*`, `CHK-*` | 7 | 7 | 0 | 100% |
| **TOTALS** | | **80** | **80** | **0** | **100.0%** |

---

## Complete Test Ledger

### Phase 1: Lockdown Fail-Closed Environment Configuration
| Test ID | Environment State | Lockdown Flag | Expected Status | Actual Status | Result |
| :--- | :--- | :--- | :---: | :---: | :---: |
| `ENV-01` | Default (unconfigured) | Default | True (Locked) | True (Locked) | ✅ PASS |
| `ENV-02` | `ENVIRONMENT=production` | `SECURITY_LOCKDOWN_MODE=false` | True (Locked) | True (Locked) | ✅ PASS |
| `ENV-03` | `ENVIRONMENT=production` | Unconfigured | True (Locked) | True (Locked) | ✅ PASS |
| `ENV-04` | `ENVIRONMENT=staging` | `SECURITY_LOCKDOWN_MODE=false` | True (Locked) | True (Locked) | ✅ PASS |
| `ENV-05` | `ENVIRONMENT=staging` | Unconfigured | True (Locked) | True (Locked) | ✅ PASS |
| `ENV-06` | Render Cloud (`RENDER=true`) | `SECURITY_LOCKDOWN_MODE=false` | True (Locked) | True (Locked) | ✅ PASS |
| `ENV-07` | Render Cloud + Production | `SECURITY_LOCKDOWN_MODE=false` | True (Locked) | True (Locked) | ✅ PASS |
| `ENV-08` | Render Cloud + Test | `SECURITY_LOCKDOWN_MODE=false` | True (Locked) | True (Locked) | ✅ PASS |
| `ENV-09` | Local Development | `SECURITY_LOCKDOWN_MODE=true` | True (Locked) | True (Locked) | ✅ PASS |
| `ENV-10` | Local Development | `SECURITY_LOCKDOWN_MODE=false` | False (Unlocked) | False (Unlocked) | ✅ PASS |
| `ENV-11` | Local Development | `SECURITY_LOCKDOWN_MODE=0` | False (Unlocked) | False (Unlocked) | ✅ PASS |
| `ENV-12` | Automated Test (`ENVIRONMENT=test`) | `SECURITY_LOCKDOWN_MODE=false` | False (Unlocked) | False (Unlocked) | ✅ PASS |
| `ENV-13` | Local Development | Ambiguous value (`"unknown"`) | True (Locked) | True (Locked) | ✅ PASS |

### Phase 2: Route Normalization & Bypass Resistance
| Test ID | Method | Path Probe | Expected HTTP | Actual HTTP | Result |
| :--- | :--- | :--- | :---: | :---: | :---: |
| `NORM-01` | GET | `/founder` | 404 | 404 | ✅ PASS |
| `NORM-02` | GET | `/founder/` | 404 | 404 | ✅ PASS |
| `NORM-03` | GET | `/FOUNDER` | 404 | 404 | ✅ PASS |
| `NORM-04` | GET | `/Founder` | 404 | 404 | ✅ PASS |
| `NORM-05` | GET | `/%66%6f%75%6e%64%65%72` | 404 | 404 | ✅ PASS |
| `NORM-06` | GET | `/founder?bypass=true&admin=1` | 404 | 404 | ✅ PASS |
| `NORM-07` | HEAD | `/founder` | 404 | 404 | ✅ PASS |
| `NORM-08` | GET | `/dashboard` | 404 | 404 | ✅ PASS |
| `NORM-09` | GET | `/analytics` | 404 | 404 | ✅ PASS |
| `NORM-10` | PUT | `/founder` | 405 | 405 | ✅ PASS |
| `NORM-11` | PATCH | `/founder` | 405 | 405 | ✅ PASS |
| `NORM-12` | OPTIONS | `/founder` | 200 | 200 | ✅ PASS |
| `NORM-13` | GET | `/api/unknown_protected_probe` | 404 | 404 | ✅ PASS |
| `NORM-14` | HEAD | `/api/analytics/live` | 404 | 404 | ✅ PASS |

### Phase 3: Paid API Lockdown (HTTP 503 Verification)
| Test ID | Method | Target Endpoint | Expected HTTP | Actual HTTP | Payload Error Text | Result |
| :--- | :--- | :--- | :---: | :---: | :--- | :---: |
| `LOCK-01` | POST | `/api/leads/generate` | 503 | 503 | `feature_temporarily_unavailable` | ✅ PASS |
| `LOCK-02` | POST | `/api/leads/clear` | 503 | 503 | `feature_temporarily_unavailable` | ✅ PASS |
| `LOCK-03` | POST | `/api/content/generate` | 503 | 503 | `feature_temporarily_unavailable` | ✅ PASS |
| `LOCK-04` | POST | `/api/content-crew/run` | 503 | 503 | `feature_temporarily_unavailable` | ✅ PASS |
| `LOCK-05` | POST | `/api/checkout/create` | 503 | 503 | `feature_temporarily_unavailable` | ✅ PASS |
| `LOCK-06` | GET | `/api/audit/dossier?company=Apex` | 503 | 503 | `feature_temporarily_unavailable` | ✅ PASS |
| `LOCK-07` | GET | `/report/dossier/apex-enterprise` | 503 | 503 | `feature_temporarily_unavailable` | ✅ PASS |
| `LOCK-08` | POST | `/api/booking/clear` | 503 | 503 | `feature_temporarily_unavailable` | ✅ PASS |
| `LOCK-09` | POST | `/api/booking/chat` | 200 | 200 | `auto_booked=False` (disabled) | ✅ PASS |

### Phase 4: Public Scanner SSRF Security Matrix
| Test ID | Attack Vector / Payload | Vector Classification | Expected Action | Actual Action | Result |
| :--- | :--- | :--- | :---: | :---: | :---: |
| `SSRF-01` | `http://127.0.0.1:8090/founder` | IPv4 Loopback | BLOCKED | BLOCKED | ✅ PASS |
| `SSRF-02` | `http://127.0.0.2:80` | Alternative Loopback | BLOCKED | BLOCKED | ✅ PASS |
| `SSRF-03` | `http://localhost:8090` | Internal Hostname | BLOCKED | BLOCKED | ✅ PASS |
| `SSRF-04` | `http://0.0.0.0:80` | Broadcast / Unspecified | BLOCKED | BLOCKED | ✅ PASS |
| `SSRF-05` | `http://[::1]:80` | IPv6 Loopback | BLOCKED | BLOCKED | ✅ PASS |
| `SSRF-06` | `http://169.254.169.254/latest/meta-data/` | AWS/Cloud Metadata | BLOCKED | BLOCKED | ✅ PASS |
| `SSRF-07` | `http://10.0.0.1/admin` | RFC1918 Class A Private | BLOCKED | BLOCKED | ✅ PASS |
| `SSRF-08` | `http://172.16.0.1/admin` | RFC1918 Class B Private | BLOCKED | BLOCKED | ✅ PASS |
| `SSRF-09` | `http://192.168.1.1/setup` | RFC1918 Class C Private | BLOCKED | BLOCKED | ✅ PASS |
| `SSRF-10` | `http://224.0.0.1` | Multicast Address | BLOCKED | BLOCKED | ✅ PASS |
| `SSRF-11` | `file:///etc/passwd` | Forbidden `file://` Scheme | BLOCKED | BLOCKED | ✅ PASS |
| `SSRF-12` | `ftp://127.0.0.1/resource` | Forbidden `ftp://` Scheme | BLOCKED | BLOCKED | ✅ PASS |
| `SSRF-13` | `gopher://127.0.0.1:70` | Forbidden `gopher://` Scheme | BLOCKED | BLOCKED | ✅ PASS |
| `SSRF-14` | `http://admin:secret@127.0.0.1` | Userinfo Credentials in URL | BLOCKED | BLOCKED | ✅ PASS |
| `SSRF-15` | `http://127.0.0.1:22` | Forbidden Non-Standard Port | BLOCKED | BLOCKED | ✅ PASS |
| `SSRF-16` | `http://0177.0.0.1` | Octal IP Address | BLOCKED | BLOCKED | ✅ PASS |
| `SSRF-17` | `http://0x7f000001` | Hex IP Address | BLOCKED | BLOCKED | ✅ PASS |
| `SSRF-18` | `http://2130706433` | Decimal Integer IP | BLOCKED | BLOCKED | ✅ PASS |
| `SSRF-19` | `POST /api/audit/run` (`127.0.0.1`) | Audit API Endpoint SSRF Check | 400 Bad Request | 400 Bad Request | ✅ PASS |
| `SSRF-20` | `Acme Real Estate` | Legitimate Company Name | ALLOWED | ALLOWED | ✅ PASS |
| `AUDIT-PERSIST`| `POST /api/audit/run` in lockdown | Vault Disk Modification | Zero Byte/mtime Change | Unmodified | ✅ PASS |

### Phase 5: Lemon Squeezy Webhook Security Matrix
| Test ID | Test Scenario | Expected HTTP | Actual HTTP | Entitlement Action | Result |
| :--- | :--- | :---: | :---: | :--- | :---: |
| `WH-01` | Valid HMAC signature & `subscription_created` | 200 | 200 | Token granted | ✅ PASS |
| `WH-02` | Missing `X-Signature` header | 401 | 401 | None | ✅ PASS |
| `WH-03` | Corrupt HMAC digest signature | 401 | 401 | None | ✅ PASS |
| `WH-04` | Missing `LEMONSQUEEZY_WEBHOOK_SECRET` | 503 | 503 | None | ✅ PASS |
| `WH-05` | Duplicate webhook replay (Idempotency) | 200 | 200 | `duplicate_ignored` | ✅ PASS |
| `WH-06` | Malformed JSON body | 400 | 400 | None | ✅ PASS |
| `WH-07` | Mismatched `store_id` | 400 | 400 | None | ✅ PASS |
| `WH-08` | Unknown/unauthorized `variant_id` | 422 | 422 | None | ✅ PASS |
| `WH-09` | Test-mode event in production without override | 400 | 400 | None | ✅ PASS |
| `WH-10` | `subscription_cancelled` event | 200 | 200 | Entitlement revoked | ✅ PASS |
| `WH-11` | `subscription_expired` event | 200 | 200 | Status set to `inactive` | ✅ PASS |
| `WH-12` | `subscription_paused` event | 200 | 200 | Status set to `inactive` | ✅ PASS |
| `WH-13` | `subscription_unpaid` event | 200 | 200 | Status set to `inactive` | ✅ PASS |
| `WH-14` | `subscription_resumed` event | 200 | 200 | Entitlement re-granted | ✅ PASS |
| `WH-15` | Client body spoofing `paid=true` at webhook | 401 | 401 | None (HMAC failure) | ✅ PASS |
| `WH-16` | Replay of cancellation event | 200 | 200 | `duplicate_ignored` | ✅ PASS |

### Phase 6: Auth & Entitlement Status Codes (Non-Lockdown)
| Test ID | Condition | Expected HTTP | Actual HTTP | Rationale | Result |
| :--- | :--- | :---: | :---: | :--- | :---: |
| `AUTH-401-A` | Missing Authorization Bearer header | 401 | 401 | Unauthenticated | ✅ PASS |
| `AUTH-401-B` | Malformed/short bearer token | 401 | 401 | Invalid token | ✅ PASS |
| `AUTH-401-C` | Unrecognized token | 401 | 401 | Unrecognized identity | ✅ PASS |
| `AUTH-401-D` | Body flag `paid=true` without bearer token | 401 | 401 | Unauthenticated spoof | ✅ PASS |
| `AUTH-403-A` | Body flag `admin=true` without admin token | 403 | 403 | Forbidden admin claim | ✅ PASS |
| `CHK-01` | Checkout create with valid server plan | 200 | 200 | Standard checkout session | ✅ PASS |
| `CHK-02` | Checkout create with arbitrary client plan | 400 | 400 | Plan tampering rejected | ✅ PASS |\n