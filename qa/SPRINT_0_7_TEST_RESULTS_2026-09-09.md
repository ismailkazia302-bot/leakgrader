# Sprint 0.7: Test Results Matrix & Verification Evidence

**Date**: September 9, 2026  
**Branch**: `security/critical-hotfix-2026-09-07`  
**Target Suite**: `qa/test_pre_deploy_gate.py`  
**Execution Environment**: Standalone OS Subprocesses via HTTP (`http://127.0.0.1:8199`)  
**Overall Result**: **89 / 89 PASSED (100.0%)** (Verified twice consecutively)

---

## 1. Summary of Test Phases

| Phase | Category | Total Tests | Passed | Failed | Pass Rate |
|---|---|:---:|:---:|:---:|:---:|
| **Phase 0** | Offline Socket Verification | 1 | 1 | 0 | 100.0% |
| **Phase 1** | Fail-Closed Lockdown Environments | 6 | 6 | 0 | 100.0% |
| **Phase 2** | Route Matrix & Method Enforcement | 21 | 21 | 0 | 100.0% |
| **Phase 3** | Path Variant Bypass Resistance | 12 | 12 | 0 | 100.0% |
| **Phase 4** | SSRF Vector Rejection Matrix | 19 | 19 | 0 | 100.0% |
| **Phase 5** | Public Marketing UX & Static Assets | 6 | 6 | 0 | 100.0% |
| **Phase 6** | Webhook Protocol & Lemon Squeezy Lifecycle | 18 | 18 | 0 | 100.0% |
| **Phase 7** | Non-Lockdown Entitlement & Auth Security | 6 | 6 | 0 | 100.0% |
| **TOTAL** | **Full Black-Box Test Suite** | **89** | **89** | **0** | **100.0%** |

---

## 2. Phase-by-Phase Detailed Results

### Phase 0: Server Offline Verification
- `OFFLINE-01` [PASS]: Requests fail with status 0 when server is offline (Actual: 0, Expected: 0)

### Phase 1: Fail-Closed Lockdown Environment Matrix
- `ENV-01` [PASS]: `ENVIRONMENT=test`, `LOCKDOWN=enabled` -> POST /api/leads/generate -> 503
- `ENV-02` [PASS]: `ENVIRONMENT=test`, `LOCKDOWN=enabled` -> GET /founder -> 404 (Route hidden)
- `ENV-03` [PASS]: `ENVIRONMENT=production`, `LOCKDOWN=false` -> POST /api/leads/generate -> 503 (Fail-Closed)
- `ENV-04` [PASS]: `ENVIRONMENT=production`, `LOCKDOWN=false` -> GET /founder -> 404 (Route hidden)
- `ENV-05` [PASS]: `RENDER=true`, `LOCKDOWN=false` -> POST /api/leads/generate -> 503 (Fail-Closed)
- `ENV-06` [PASS]: `ENVIRONMENT=staging`, unconfigured -> POST /api/leads/generate -> 503 (Fail-Closed)

### Phase 2: Route Matrix & HTTP Method Enforcement (Lockdown Mode)
- `RT-01` [PASS]: GET /founder -> 404 (Route hidden)
- `RT-02` [PASS]: HEAD /founder -> 404 (HEAD probe hidden)
- `RT-03` [PASS]: PUT /founder -> 405 (PUT method not allowed)
- `RT-04` [PASS]: PATCH /founder -> 405 (PATCH method not allowed)
- `RT-05` [PASS]: DELETE /founder -> 404 (DELETE on founder hidden 404)
- `RT-06` [PASS]: OPTIONS /founder -> 200 (OPTIONS preflight allowed 200)
- `RT-07` [PASS]: POST /api/leads/generate -> 503 (Paid API gated 503)
- `RT-08` [PASS]: GET /api/leads/generate -> 404 (GET on paid POST returns 404)
- `RT-09` [PASS]: PUT /api/leads/generate -> 405 (PUT on paid POST returns 405)
- `RT-10` [PASS]: DELETE /api/leads/generate -> 404 (DELETE on paid POST returns 404)
- `RT-11` [PASS]: POST /api/content/generate -> 503 (Paid API gated 503)
- `RT-12` [PASS]: GET /api/content/generate -> 404 (GET on content returns 404)
- `RT-13` [PASS]: POST /api/checkout/create -> 503 (Checkout gated 503)
- `RT-14` [PASS]: GET /api/checkout/create -> 404 (GET on checkout returns 404)
- `RT-15` [PASS]: POST /api/payment/webhook -> 401 (Webhook unsigned returns 401)
- `RT-16` [PASS]: GET /api/payment/webhook -> 404 (GET on webhook returns 404)
- `RT-17` [PASS]: GET /api/audit/dossier -> 503 (Dossier API gated 503)
- `RT-18` [PASS]: POST /api/audit/dossier -> 404 (POST on dossier API returns 404)
- `RT-19` [PASS]: GET /report/dossier/apex-enterprise -> 503 (Dossier HTML report gated 503)
- `RT-20` [PASS]: POST /api/booking/clear -> 503 (Mutation API gated 503)
- `RT-21` [PASS]: GET /api/booking/clear -> 404 (GET on booking clear returns 404 Endpoint not found)

### Phase 3: Path Variant Bypass Resistance (Lockdown Mode)
- `BYP-01` [PASS]: GET /founder/ -> 404 (Trailing slash on founder hidden)
- `BYP-02` [PASS]: GET /FOUNDER -> 404 (Uppercase /FOUNDER hidden)
- `BYP-03` [PASS]: GET /FoUnDeR -> 404 (Mixed case /FoUnDeR hidden)
- `BYP-04` [PASS]: GET /%66%6f%75%6e%64%65%72 -> 404 (URL-encoded /founder hidden)
- `BYP-05` [PASS]: GET /founder?admin=true -> 404 (Query param spoofing ignored)
- `BYP-06` [PASS]: GET /founder?bypass=1 -> 404 (Bypass query param ignored)
- `BYP-07` [PASS]: POST /api/leads/generate/ -> 503 (Trailing slash on paid API gated 503)
- `BYP-08` [PASS]: POST /API/LEADS/GENERATE -> 503 (Uppercase paid API gated 503)
- `BYP-09` [PASS]: POST /api/leads/generate?free=true -> 503 (Query flag spoofing ignored)
- `BYP-10` [PASS]: POST /api/leads/generate (body `admin: true`) -> 503 (Body admin flag ignored)
- `BYP-11` [PASS]: POST /api/checkout/create/ -> 503 (Trailing slash on checkout gated 503)
- `BYP-12` [PASS]: POST /API/CHECKOUT/CREATE -> 503 (Uppercase checkout gated 503)

### Phase 4: SSRF Vector Rejection Matrix (HTTP POST /api/audit/run)
- `SSRF-01` [PASS]: Direct Loopback IPv4 (`http://127.0.0.1:8080`) -> Blocked (400)
- `SSRF-02` [PASS]: Localhost Hostname (`http://localhost/admin`) -> Blocked (400)
- `SSRF-03` [PASS]: AWS Cloud Metadata (`http://169.254.169.254/latest/meta-data/`) -> Blocked (400)
- `SSRF-04` [PASS]: Private RFC1918 Class A (`http://10.0.0.1/status`) -> Blocked (400)
- `SSRF-05` [PASS]: Private RFC1918 Class C (`http://192.168.1.1/router`) -> Blocked (400)
- `SSRF-06` [PASS]: Private RFC1918 Class B (`http://172.16.0.1/internal`) -> Blocked (400)
- `SSRF-07` [PASS]: Forbidden file:// Scheme (`file:///etc/passwd`) -> Blocked (400)
- `SSRF-08` [PASS]: Windows File Scheme (`file:///C:/Windows/win.ini`) -> Blocked (400)
- `SSRF-09` [PASS]: FTP Scheme (`ftp://127.0.0.1/data`) -> Blocked (400)
- `SSRF-10` [PASS]: Gopher Scheme (`gopher://127.0.0.1:70/`) -> Blocked (400)
- `SSRF-11` [PASS]: Dict Scheme (`dict://127.0.0.1:2628/`) -> Blocked (400)
- `SSRF-12` [PASS]: Decimal Encoded Loopback IP (`http://2130706433/`) -> Blocked (400)
- `SSRF-13` [PASS]: Hex Encoded Loopback IP (`http://0x7f000001/`) -> Blocked (400)
- `SSRF-14` [PASS]: Userinfo Credentials in Target (`http://user:pass@example.com`) -> Blocked (400)
- `SSRF-15` [PASS]: Carrier-Grade NAT IP (`http://100.64.0.1/`) -> Blocked (400)
- `SSRF-16` [PASS]: Prohibited .local Domain (`http://service.local/`) -> Blocked (400)
- `SSRF-17` [PASS]: Prohibited .internal Domain (`http://cluster.internal/`) -> Blocked (400)
- `SSRF-18` [PASS]: IPv6 Loopback Address (`http://[::1]:80/`) -> Blocked (400)
- `SSRF-19` [PASS]: Valid Company Name Accepted by Scanner (`Acme Real Estate`) -> Allowed (200)

### Phase 5: Public Marketing Pages & Static Assets
- `PUB-01` [PASS]: GET / -> 200 (Landing page loads)
- `PUB-02` [PASS]: GET /health -> 200 (Health endpoint responds)
- `PUB-03` [PASS]: GET /sitemap.xml -> 200 (SEO sitemap loads)
- `PUB-04` [PASS]: GET /robots.txt -> 200 (Robots.txt loads)
- `PUB-05` [PASS]: GET /preview/demo_183731 -> 200 (Public redesign preview loads)
- `PUB-06` [PASS]: GET /api/pricing/plans -> 200 (Public pricing plans respond)

### Phase 6: Webhook Protocol & Lemon Squeezy Lifecycle (Non-Lockdown Mode)
- `WH-01` [PASS]: Missing X-Signature header -> 401
- `WH-02` [PASS]: Corrupt HMAC-SHA256 signature -> 401
- `WH-03` [PASS]: Unsupported event type -> 422
- `LC-01` [PASS]: `subscription_created` webhook -> 200 (active token created)
- `LC-01b` [PASS]: Active subscription token accesses paid API -> 200
- `LC-02` [PASS]: `subscription_cancelled` with future `ends_at` -> 200
- `LC-03` [PASS]: Paid API allowed after cancellation before `ends_at` -> 200
- `LC-04` [PASS]: Paid API denied after cancellation when `ends_at` passed -> 401
- `LC-05` [PASS]: `subscription_expired` webhook -> 200
- `LC-05b` [PASS]: Expired token denied on paid API -> 401
- `LC-06` [PASS]: `subscription_paused` webhook -> 200
- `LC-06b` [PASS]: Paused token denied on paid API -> 401 (`token_paused`)
- `LC-07` [PASS]: `subscription_resumed` webhook -> 200
- `LC-07b` [PASS]: Resumed token allowed on paid API -> 200
- `LC-08` [PASS]: `subscription_payment_failed` webhook -> 200 (status transitions to `past_due`)
- `LC-08b` [PASS]: Past due token within grace period allowed on paid API -> 200
- `LC-09` [PASS]: Duplicate cancellation webhook re-sent -> 200 (`duplicate_ignored`)
- `LC-10` [PASS]: Cancellation without `ends_at` fails safely without error -> 200

### Phase 7: Non-Lockdown Entitlement & Auth Enforcement
- `AUTH-01` [PASS]: Missing Authorization header -> 401
- `AUTH-02` [PASS]: Malformed short token -> 401
- `AUTH-03` [PASS]: Unrecognized token string -> 401
- `AUTH-04` [PASS]: Browser spoofing without token -> 403
- `AUTH-05` [PASS]: Admin endpoint without token -> 403
- `AUTH-06` [PASS]: Admin endpoint with wrong token -> 403

---

## 3. Repeatability Verification

The entire 89-test suite was executed twice consecutively in automated subprocess mode:
1. **Run 1**: 89/89 passed (100.0%)
2. **Run 2**: 89/89 passed (100.0%)

Zero manual file cleanup, zero cache invalidation, and zero server restarts were required between runs. All test storage directories were isolated in temporary locations and cleaned up completely.
