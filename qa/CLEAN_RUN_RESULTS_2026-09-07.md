# Clean-Run & Black-Box Verification Results
**Execution Date:** September 7, 2026  
**Environment:** Fresh temporary checkout (`%TEMP%\\leakgrader_clean_checkout`)  
**Python Runtime:** Clean Isolated Virtual Environment (`.venv`)  
**Application Architecture:** Independent Subprocess listening on Port `8199`  
**Harness Protocol:** Pure Black-Box HTTP Requests (Zero application imports in runner)  

---

## 1. Executive Summary

| Verification Track | Execution Model | Tests Executed | Passed | Failed | Pass Rate |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Track A: Clean Virtual Environment Suite** | `test_pre_deploy_gate.py` in fresh venv | 80 | 80 | 0 | 100% |
| **Track B: Pure Black-Box HTTP Subprocess** | Independent subprocess HTTP probing | 26 | 26 | 0 | 100% |
| **Track C: Source Code Immutability** | SHA-256 pre/post directory hash | 370 files | 370 | 0 | 100% |

---

## 2. Track B: Pure Black-Box HTTP Subprocess Results

The application was launched as a standalone operating system process using:
```bash
python app.py  # PID running with ENVIRONMENT=production, PORT=8199
```
All assertions below were made via outbound `urllib.request` HTTP calls across the network stack. **No application functions, models, or guards were imported.**

### Route Hiding & Method Gating (Lockdown Mode)
| Test ID | Method | Path | Actual HTTP | Expected HTTP | Black-Box Assertion | Result |
| :--- | :--- | :--- | :---: | :---: | :--- | :---: |
| `BB-HEALTH` | GET | `/health` | 200 | 200 | Server responding | ✅ PASS |
| `BB-ROUTE-01` | GET | `/founder` | 404 | 404 | Route existence hidden | ✅ PASS |
| `BB-ROUTE-02` | GET | `/founder/` | 404 | 404 | Trailing slash bypass defeated | ✅ PASS |
| `BB-ROUTE-03` | GET | `/FOUNDER` | 404 | 404 | Uppercase bypass defeated | ✅ PASS |
| `BB-ROUTE-04` | GET | `/%66%6f%75%6e%64%65%72` | 404 | 404 | URL-encoded bypass defeated | ✅ PASS |
| `BB-ROUTE-05` | GET | `/founder?bypass=1` | 404 | 404 | Query string bypass defeated | ✅ PASS |
| `BB-ROUTE-06` | HEAD | `/founder` | 404 | 404 | HEAD probe rejected | ✅ PASS |
| `BB-ROUTE-07` | PUT | `/founder` | 405 | 405 | PUT method rejected | ✅ PASS |
| `BB-ROUTE-08` | PATCH | `/founder` | 405 | 405 | PATCH method rejected | ✅ PASS |

### Paid API Lockdown Gate (HTTP 503)
| Test ID | Method | Path | Actual HTTP | Expected HTTP | Black-Box Assertion | Result |
| :--- | :--- | :--- | :---: | :---: | :--- | :---: |
| `BB-PAID-01` | POST | `/api/leads/generate` | 503 | 503 | Feature gated under lockdown | ✅ PASS |
| `BB-PAID-02` | POST | `/api/content/generate` | 503 | 503 | Feature gated under lockdown | ✅ PASS |
| `BB-PAID-03` | POST | `/api/checkout/create` | 503 | 503 | Checkout gated under lockdown | ✅ PASS |
| `BB-PAID-04` | GET | `/api/audit/dossier?company=Apex`| 503 | 503 | Dossier API gated under lockdown | ✅ PASS |
| `BB-PAID-05` | GET | `/report/dossier/apex-enterprise`| 503 | 503 | Dossier HTML report gated | ✅ PASS |
| `BB-PAID-06` | POST | `/api/booking/clear` | 503 | 503 | CRM mutation gated | ✅ PASS |

### Public Scanner SSRF Rejection over HTTP (`POST /api/audit/run`)
| Test ID | Target Injected in JSON Body | Vector Type | Actual HTTP | Expected HTTP | Result |
| :--- | :--- | :--- | :---: | :---: | :---: |
| `BB-SSRF-01` | `http://127.0.0.1:8090/founder` | Direct Loopback IP | 400 | 400 | ✅ PASS |
| `BB-SSRF-02` | `http://169.254.169.254/latest/meta-data/` | Cloud Metadata Service | 400 | 400 | ✅ PASS |
| `BB-SSRF-03` | `http://10.0.0.1/admin` | Private RFC1918 Class A | 400 | 400 | ✅ PASS |
| `BB-SSRF-04` | `http://192.168.1.1/setup` | Private RFC1918 Class C | 400 | 400 | ✅ PASS |
| `BB-SSRF-05` | `file:///etc/passwd` | Forbidden `file://` Scheme | 400 | 400 | ✅ PASS |
| `BB-SSRF-06` | `http://localhost:8090` | Hostname Loopback | 400 | 400 | ✅ PASS |
| `BB-SSRF-07` | `http://2130706433` | Decimal Encoded Loopback | 400 | 400 | ✅ PASS |
| `BB-SSRF-08` | `http://0x7f000001` | Hex Encoded Loopback | 400 | 400 | ✅ PASS |

### Webhook Protocol Security over HTTP (`POST /api/payment/webhook`)
| Test ID | Condition | Actual HTTP | Expected HTTP | Black-Box Assertion | Result |
| :--- | :--- | :---: | :---: | :--- | :---: |
| `BB-WH-01` | Missing `X-Signature` Header | 401 | 401 | Rejected unauthenticated | ✅ PASS |
| `BB-WH-02` | Corrupted `X-Signature` Digest | 401 | 401 | Rejected bad signature | ✅ PASS |
| `BB-WH-03` | Valid HMAC-SHA256 Signature | 200 | 200 | Processed successfully | ✅ PASS |
| `BB-WH-04` | Replay of Identical Payload | 200 | 200 | `duplicate_ignored` | ✅ PASS |

---

## 3. Track C: Source Code Immutability Verification

Before initiating any subprocess or temporary checkout, all source code and test files in `c:\Users\Administrator\Downloads\mastermind\omnibrain` were cryptographically hashed (SHA-256).

- **Total Files Verified:** 370
- **Pre-Run Hash Sum Match:** 100% Identical
- **Post-Run Hash Sum Match:** 100% Identical
- **Git Diff Verification:** Zero bytes changed in application code or existing test files during this audit.
