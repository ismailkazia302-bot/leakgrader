"""
LeakGrader - Pre-Deploy Security Release Gate Sprint 0.7 Automated Test Suite
Independent Black-Box HTTP Verification Suite (Zero Application Imports)

Covers:
1. Server Offline Verification (Tests fail if server is offline).
2. Fail-Closed Lockdown Configuration Matrix (Real HTTP responses across subprocesses).
3. Complete Route & HTTP Method Matrix (GET, HEAD, POST, PUT, PATCH, DELETE, OPTIONS).
4. Path Variant Bypass Resistance (casing, trailing slash, query params, URL encoding).
5. Comprehensive SSRF Vector Rejection Matrix (18 attack payloads over HTTP).
6. Webhook Security & Idempotency Matrix (HMAC-SHA256, replay protection).
7. Full Lemon Squeezy Subscription Lifecycle Matrix (10 black-box lifecycle tests).
8. Non-Lockdown Entitlement Authorization Matrix (401 vs 403 standard).
9. Public Marketing & Static Asset Availability.
"""

import os
import sys

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import json
import time
import hmac
import hashlib
import shutil
import tempfile
import subprocess
import urllib.request
import urllib.error

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEST_PORT = 8199
BASE_URL = f"http://127.0.0.1:{TEST_PORT}"
TEST_SECRET = "sec_test_sprint07_hmac_998127361827"

results = []

def record_test(test_id: str, category: str, title: str, passed: bool, status_code, expected_code, details: str):
    res = {
        "test_id": test_id,
        "category": category,
        "title": title,
        "status": "PASS" if passed else "FAIL",
        "actual": status_code,
        "expected": expected_code,
        "details": details
    }
    results.append(res)
    mark = "PASS" if passed else "FAIL"
    print(f"[{mark}] {test_id} [{category}]: {title} (Actual: {status_code} vs Expected: {expected_code})")
    if not passed:
        print(f"       Details: {details}")

def run_http_request(base_url: str, method: str, path: str, headers: dict = None, body: dict = None, raw_body: bytes = None):
    url = f"{base_url}{path}"
    hdrs = dict(headers) if headers else {}
    data = None
    if raw_body is not None:
        data = raw_body
    elif body is not None:
        data = json.dumps(body).encode("utf-8")
        if "Content-Type" not in hdrs:
            hdrs["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            resp_body = resp.read().decode("utf-8", errors="ignore")
            try:
                parsed_json = json.loads(resp_body)
            except Exception:
                parsed_json = None
            return resp.status, parsed_json, resp_body
    except urllib.error.HTTPError as e:
        resp_body = e.read().decode("utf-8", errors="ignore")
        try:
            parsed_json = json.loads(resp_body)
        except Exception:
            parsed_json = None
        return e.code, parsed_json, resp_body
    except Exception as e:
        return 0, None, str(e)


class TestServerSubprocess:
    """Manages an isolated application server running as a separate OS subprocess."""
    def __init__(self, port: int = TEST_PORT, env_overrides: dict = None):
        self.port = port
        self.base_url = f"http://127.0.0.1:{port}"
        self.storage_dir = tempfile.mkdtemp(prefix="lg_test_storage_")
        self.env = os.environ.copy()
        self.env["PORT"] = str(self.port)
        self.env["STORAGE_DIR"] = self.storage_dir
        self.env["ALLOW_TEST_WEBHOOKS"] = "true"
        self.env["LEMONSQUEEZY_WEBHOOK_SECRET"] = TEST_SECRET
        if env_overrides:
            self.env.update(env_overrides)
        self.process = None

    def start(self):
        # Initialize empty storage structures in temporary directory
        for fname in ["active_entitlements.json", "processed_webhook_events.json", "audits_vault.json", "leads_vault.json"]:
            fpath = os.path.join(self.storage_dir, fname)
            with open(fpath, "w", encoding="utf-8") as f:
                f.write("{}")

        # Copy existing demo assets into temporary storage so preview routes resolve
        demos_src = os.path.join(BASE_DIR, "storage", "demos")
        if os.path.exists(demos_src):
            try:
                shutil.copytree(demos_src, os.path.join(self.storage_dir, "demos"), dirs_exist_ok=True)
            except Exception:
                pass

        # Production WSGI server command (Gunicorn if available, fallback to wsgiref make_server)
        if shutil.which("gunicorn"):
            cmd = ["gunicorn", "wsgi:app", "--bind", f"0.0.0.0:{self.port}", "--workers", "1", "--timeout", "30"]
        else:
            server_code = f"from wsgi import app; from wsgiref.simple_server import make_server; make_server('', {self.port}, app).serve_forever()"
            cmd = [sys.executable, "-c", server_code]

        self.process = subprocess.Popen(
            cmd,
            cwd=BASE_DIR,
            env=self.env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        # Wait up to 10 seconds for server to respond on /health
        start_time = time.time()
        while time.time() - start_time < 10:
            st, _, _ = run_http_request(self.base_url, "GET", "/health")
            if st == 200:
                return True
            time.sleep(0.15)
        return False

    def stop(self):
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=3)
            except Exception:
                try:
                    self.process.kill()
                except Exception:
                    pass
            self.process = None

        if os.path.exists(self.storage_dir):
            try:
                shutil.rmtree(self.storage_dir, ignore_errors=True)
            except Exception:
                pass


def compute_signature(payload_bytes: bytes, secret: str = TEST_SECRET) -> str:
    return hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()


def test_offline_verification():
    print("\n--- PHASE 0: SERVER OFFLINE VERIFICATION ---")
    st, _, err = run_http_request(BASE_URL, "GET", "/health")
    passed = (st == 0)
    record_test(
        "OFFLINE-01",
        "OFFLINE_CHECK",
        "Requests fail with status 0 when server is offline",
        passed,
        st,
        0,
        f"Server not running as expected (details: {err})"
    )


def test_lockdown_environments():
    print("\n--- PHASE 1: FAIL-CLOSED LOCKDOWN ENVIRONMENT CONFIGURATION VIA SUBPROCESSES ---")
    
    # 1. Test Environment with Lockdown Enabled
    srv1 = TestServerSubprocess(TEST_PORT, {
        "ENVIRONMENT": "test",
        "SECURITY_LOCKDOWN_MODE": "enabled"
    })
    srv1.start()
    try:
        st, js, _ = run_http_request(srv1.base_url, "POST", "/api/leads/generate", body={"query": "test"})
        record_test("ENV-01", "LOCKDOWN_HTTP", "ENVIRONMENT=test, LOCKDOWN=enabled -> 503", st == 503, st, 503, str(js))

        st, _, _ = run_http_request(srv1.base_url, "GET", "/founder")
        record_test("ENV-02", "LOCKDOWN_HTTP", "ENVIRONMENT=test, LOCKDOWN=enabled -> /founder hidden (404)", st == 404, st, 404, "")
    finally:
        srv1.stop()

    # 2. Production Environment with lockdown=false (Fail-closed must enforce lockdown)
    srv2 = TestServerSubprocess(TEST_PORT, {
        "ENVIRONMENT": "production",
        "SECURITY_LOCKDOWN_MODE": "false"
    })
    srv2.start()
    try:
        st, js, _ = run_http_request(srv2.base_url, "POST", "/api/leads/generate", body={"query": "test"})
        record_test("ENV-03", "LOCKDOWN_HTTP", "ENVIRONMENT=production, LOCKDOWN=false -> 503 (Fail-Closed)", st == 503, st, 503, str(js))

        st, _, _ = run_http_request(srv2.base_url, "GET", "/founder")
        record_test("ENV-04", "LOCKDOWN_HTTP", "ENVIRONMENT=production, LOCKDOWN=false -> /founder hidden (404)", st == 404, st, 404, "")
    finally:
        srv2.stop()

    # 3. Render Cloud Environment with lockdown=false (Fail-closed must enforce lockdown)
    srv3 = TestServerSubprocess(TEST_PORT, {
        "ENVIRONMENT": "",
        "RENDER": "true",
        "SECURITY_LOCKDOWN_MODE": "false"
    })
    srv3.start()
    try:
        st, js, _ = run_http_request(srv3.base_url, "POST", "/api/leads/generate", body={"query": "test"})
        record_test("ENV-05", "LOCKDOWN_HTTP", "RENDER=true, LOCKDOWN=false -> 503 (Fail-Closed)", st == 503, st, 503, str(js))
    finally:
        srv3.stop()

    # 4. Staging Unconfigured Environment (Fail-closed must enforce lockdown)
    srv4 = TestServerSubprocess(TEST_PORT, {
        "ENVIRONMENT": "staging",
        "SECURITY_LOCKDOWN_MODE": ""
    })
    srv4.start()
    try:
        st, js, _ = run_http_request(srv4.base_url, "POST", "/api/leads/generate", body={"query": "test"})
        record_test("ENV-06", "LOCKDOWN_HTTP", "ENVIRONMENT=staging, unconfigured -> 503 (Fail-Closed)", st == 503, st, 503, str(js))
    finally:
        srv4.stop()


def run_lockdown_test_suite(server: TestServerSubprocess):
    base_url = server.base_url

    print("\n--- PHASE 2: ROUTE MATRIX & HTTP METHOD ENFORCEMENT (LOCKDOWN MODE) ---")
    routes_and_methods = [
        ("RT-01", "GET", "/founder", 404, "Route hidden"),
        ("RT-02", "HEAD", "/founder", 404, "HEAD probe hidden"),
        ("RT-03", "PUT", "/founder", 405, "PUT method not allowed"),
        ("RT-04", "PATCH", "/founder", 405, "PATCH method not allowed"),
        ("RT-05", "DELETE", "/founder", 404, "DELETE on founder hidden 404"),
        ("RT-06", "OPTIONS", "/founder", 200, "OPTIONS preflight allowed 200"),
        ("RT-07", "POST", "/api/leads/generate", 503, "Paid API gated 503"),
        ("RT-08", "GET", "/api/leads/generate", 404, "GET on paid POST returns 404"),
        ("RT-09", "PUT", "/api/leads/generate", 405, "PUT on paid POST returns 405"),
        ("RT-10", "DELETE", "/api/leads/generate", 404, "DELETE on paid POST returns 404"),
        ("RT-11", "POST", "/api/content/generate", 503, "Paid API gated 503"),
        ("RT-12", "GET", "/api/content/generate", 404, "GET on content returns 404"),
        ("RT-13", "POST", "/api/checkout/create", 503, "Checkout gated 503"),
        ("RT-14", "GET", "/api/checkout/create", 404, "GET on checkout returns 404"),
        ("RT-15", "POST", "/api/payment/webhook", 401, "Webhook unsigned returns 401"),
        ("RT-16", "GET", "/api/payment/webhook", 404, "GET on webhook returns 404"),
        ("RT-17", "GET", "/api/audit/dossier", 503, "Dossier API gated 503"),
        ("RT-18", "POST", "/api/audit/dossier", 404, "POST on dossier API returns 404"),
        ("RT-19", "GET", "/report/dossier/apex-enterprise", 503, "Dossier HTML report gated 503"),
        ("RT-20", "POST", "/api/booking/clear", 503, "Mutation API gated 503"),
        ("RT-21", "GET", "/api/booking/clear", 404, "GET on booking clear returns 404 Endpoint not found"),
    ]
    for tid, mth, path, exp, desc in routes_and_methods:
        st, _, _ = run_http_request(base_url, mth, path)
        record_test(tid, "ROUTE_METHOD", f"{mth} {path} -> {exp} ({desc})", st == exp, st, exp, "")

    print("\n--- PHASE 3: PATH VARIANT BYPASS RESISTANCE (LOCKDOWN MODE) ---")
    bypass_tests = [
        ("BYP-01", "GET", "/founder/", 404, "Trailing slash on founder hidden"),
        ("BYP-02", "GET", "/FOUNDER", 404, "Uppercase /FOUNDER hidden"),
        ("BYP-03", "GET", "/FoUnDeR", 404, "Mixed case /FoUnDeR hidden"),
        ("BYP-04", "GET", "/%66%6f%75%6e%64%65%72", 404, "URL-encoded /founder hidden"),
        ("BYP-05", "GET", "/founder?admin=true", 404, "Query param spoofing ignored"),
        ("BYP-06", "GET", "/founder?bypass=1", 404, "Bypass query param ignored"),
        ("BYP-07", "POST", "/api/leads/generate/", 503, "Trailing slash on paid API gated 503"),
        ("BYP-08", "POST", "/API/LEADS/GENERATE", 503, "Uppercase paid API gated 503"),
        ("BYP-09", "POST", "/api/leads/generate?free=true", 503, "Query flag spoofing ignored"),
        ("BYP-10", "POST", "/api/leads/generate", 503, "Body admin flag ignored (still 503)"),
        ("BYP-11", "POST", "/api/checkout/create/", 503, "Trailing slash on checkout gated 503"),
        ("BYP-12", "POST", "/API/CHECKOUT/CREATE", 503, "Uppercase checkout gated 503"),
    ]
    for tid, mth, path, exp, desc in bypass_tests:
        body = {"admin": True} if tid == "BYP-10" else None
        st, _, _ = run_http_request(base_url, mth, path, body=body)
        record_test(tid, "BYPASS_RESISTANCE", f"{mth} {path} -> {exp} ({desc})", st == exp, st, exp, "")

    print("\n--- PHASE 4: COMPREHENSIVE SSRF VECTOR REJECTION MATRIX (HTTP POST /api/audit/run) ---")
    ssrf_vectors = [
        ("SSRF-01", "http://127.0.0.1:8090/founder", "Direct Loopback IPv4"),
        ("SSRF-02", "http://localhost:8090/", "Localhost Hostname"),
        ("SSRF-03", "http://169.254.169.254/latest/meta-data/", "AWS Cloud Metadata"),
        ("SSRF-04", "http://10.0.0.1/admin", "Private RFC1918 Class A"),
        ("SSRF-05", "http://192.168.1.1/setup", "Private RFC1918 Class C"),
        ("SSRF-06", "http://172.16.0.1/status", "Private RFC1918 Class B"),
        ("SSRF-07", "file:///etc/passwd", "Forbidden file:// Scheme"),
        ("SSRF-08", "file:///C:/Windows/win.ini", "Windows File Scheme"),
        ("SSRF-09", "ftp://anonymous@internal.corp", "FTP Scheme"),
        ("SSRF-10", "gopher://127.0.0.1:6379/", "Gopher Scheme"),
        ("SSRF-11", "dict://127.0.0.1:11211/", "Dict Scheme"),
        ("SSRF-12", "http://2130706433/", "Decimal Encoded Loopback IP"),
        ("SSRF-13", "http://0x7f000001/", "Hex Encoded Loopback IP"),
        ("SSRF-14", "http://admin:secret@127.0.0.1/", "Userinfo Credentials in Target"),
        ("SSRF-15", "http://100.64.0.1/", "Carrier-Grade NAT IP"),
        ("SSRF-16", "http://intranet.local/", "Prohibited .local Domain"),
        ("SSRF-17", "http://portal.internal/", "Prohibited .internal Domain"),
        ("SSRF-18", "http://[::1]:8090/", "IPv6 Loopback Address"),
    ]
    for tid, target, desc in ssrf_vectors:
        st, js, _ = run_http_request(base_url, "POST", "/api/audit/run", body={"target": target, "url_or_company": target})
        passed = (st == 400) and ((js or {}).get("error") in ["prohibited_target_address", "invalid_target_domain"])
        record_test(tid, "SSRF_HTTP", f"SSRF Blocked: {desc}", passed, st, 400, str(js))

    # Public business name accepted by scanner
    st, js, _ = run_http_request(base_url, "POST", "/api/audit/run", body={"target": "Apex Dental Clinic", "url_or_company": "Apex Dental Clinic"})
    passed = (st == 200) and "audit" in (js or {})
    record_test("SSRF-19", "SSRF_HTTP", "Valid Company Name Accepted by Scanner", passed, st, 200, "")

    print("\n--- PHASE 5: PUBLIC MARKETING PAGES & STATIC ASSETS ---")
    public_endpoints = [
        ("PUB-01", "GET", "/", 200, "Landing page loads"),
        ("PUB-02", "GET", "/health", 200, "Health endpoint responds"),
        ("PUB-03", "GET", "/sitemap.xml", 200, "SEO sitemap loads"),
        ("PUB-04", "GET", "/robots.txt", 200, "Robots.txt loads"),
        ("PUB-05", "GET", "/preview/demo_183731", 200, "Public redesign preview loads"),
        ("PUB-06", "GET", "/api/pricing/plans", 200, "Public pricing plans respond"),
    ]
    for tid, mth, path, exp, desc in public_endpoints:
        st, _, _ = run_http_request(base_url, mth, path)
        record_test(tid, "PUBLIC_UX", f"{mth} {path} -> {exp} ({desc})", st == exp, st, exp, "")

    print("\n--- PHASE 8: WSGI SECURITY MIDDLEWARE TARGET VERIFICATION ---")
    # MW-01: Verify /founder returns 404 through WSGI path
    st_mw01, _, _ = run_http_request(base_url, "GET", "/founder")
    record_test("MW-01", "WSGI_MIDDLEWARE", "Verify /founder returns 404 through WSGI path", st_mw01 == 404, st_mw01, 404, "")

    # MW-02: Verify /api/leads/generate returns 503 through WSGI path
    st_mw02, js_mw02, _ = run_http_request(base_url, "POST", "/api/leads/generate", body={"industry": "SaaS"})
    record_test("MW-02", "WSGI_MIDDLEWARE", "Verify /api/leads/generate returns 503 through WSGI path", st_mw02 == 503, st_mw02, 503, str(js_mw02))

    # MW-03: Verify /api/audit/run rejects SSRF through WSGI path
    st_mw03, js_mw03, _ = run_http_request(base_url, "POST", "/api/audit/run", body={"target": "http://127.0.0.1:8090/founder"})
    record_test("MW-03", "WSGI_MIDDLEWARE", "Verify /api/audit/run rejects SSRF through WSGI path", st_mw03 == 400, st_mw03, 400, str(js_mw03))

    # MW-04: Verify /api/documents/clear returns 503 through WSGI path
    st_mw04, js_mw04, _ = run_http_request(base_url, "POST", "/api/documents/clear", body={})
    record_test("MW-04", "WSGI_MIDDLEWARE", "Verify /api/documents/clear returns 503 through WSGI path", st_mw04 == 503, st_mw04, 503, str(js_mw04))

    # MW-05: Verify public pages return 200 through WSGI path
    st_mw05, _, _ = run_http_request(base_url, "GET", "/")
    record_test("MW-05", "WSGI_MIDDLEWARE", "Verify public pages return 200 through WSGI path", st_mw05 == 200, st_mw05, 200, "")


def run_lifecycle_and_webhook_suite(server: TestServerSubprocess):
    base_url = server.base_url

    print("\n--- PHASE 6: WEBHOOK PROTOCOL & LEMON SQUEEZY LIFECYCLE (NON-LOCKDOWN) ---")

    # 1. Missing Signature
    raw_dummy = json.dumps({"test": 1}).encode("utf-8")
    st, js, _ = run_http_request(base_url, "POST", "/api/payment/webhook", raw_body=raw_dummy)
    record_test("WH-01", "WEBHOOK_HTTP", "Missing X-Signature -> 401", st == 401, st, 401, str(js))

    # 2. Corrupt Signature
    hdrs_bad = {"X-Signature": "bad_digest_0000000000000000000000000000000000000000000000000000000000000000"}
    st, js, _ = run_http_request(base_url, "POST", "/api/payment/webhook", headers=hdrs_bad, raw_body=raw_dummy)
    record_test("WH-02", "WEBHOOK_HTTP", "Corrupt Signature -> 401", st == 401, st, 401, str(js))

    # 3. Unsupported event
    unsupp_payload = json.dumps({
        "meta": {"event_name": "unsupported_event", "test_mode": True},
        "data": {"id": "ord_unsupp", "attributes": {}}
    }).encode("utf-8")
    sig_unsupp = compute_signature(unsupp_payload)
    st, js, _ = run_http_request(base_url, "POST", "/api/payment/webhook", headers={"X-Signature": sig_unsupp}, raw_body=unsupp_payload)
    record_test("WH-03", "WEBHOOK_HTTP", "Unsupported Event -> 422", st == 422, st, 422, str(js))

    # Task 4 Test 1: Valid subscription_created webhook -> entitlement active
    sub_id_1 = f"sub_active_{int(time.time()*1000)}"
    payload_created = json.dumps({
        "meta": {"event_name": "subscription_created", "test_mode": True},
        "data": {
            "id": sub_id_1,
            "attributes": {
                "user_email": "client1@example.com",
                "status": "active",
                "ends_at": None
            }
        }
    }).encode("utf-8")
    sig1 = compute_signature(payload_created)
    st, js, _ = run_http_request(base_url, "POST", "/api/payment/webhook", headers={"X-Signature": sig1}, raw_body=payload_created)
    tok1 = (js or {}).get("token", "")
    passed = (st == 200) and (js or {}).get("active_entitlement_created") is True and bool(tok1)
    record_test("LC-01", "LIFECYCLE", "subscription_created creates active token", passed, st, 200, str(js))

    # Verify token can access paid API (non-lockdown)
    st_paid, js_paid, _ = run_http_request(
        base_url, "POST", "/api/leads/generate",
        headers={"Authorization": f"Bearer {tok1}"},
        body={"query": "dentists"}
    )
    record_test("LC-01b", "LIFECYCLE", "Active subscription token accesses paid API -> 200", st_paid == 200, st_paid, 200, str(js_paid))

    # Task 4 Test 2: subscription_cancelled with ends_at 30 days away -> remains active, auto_renew=False
    future_ends_at = "2026-10-30T12:00:00.000000Z"
    payload_cancel_future = json.dumps({
        "meta": {"event_name": "subscription_cancelled", "test_mode": True},
        "data": {
            "id": sub_id_1,
            "attributes": {
                "user_email": "client1@example.com",
                "status": "cancelled",
                "ends_at": future_ends_at
            }
        }
    }).encode("utf-8")
    sig2 = compute_signature(payload_cancel_future)
    st, js, _ = run_http_request(base_url, "POST", "/api/payment/webhook", headers={"X-Signature": sig2}, raw_body=payload_cancel_future)
    passed = (st == 200) and (js or {}).get("auto_renew") is False
    record_test("LC-02", "LIFECYCLE", "subscription_cancelled with future ends_at processed", passed, st, 200, str(js))

    # Task 4 Test 3: Paid API request after cancellation but before ends_at -> ACCESS ALLOWED (200)
    st_paid, js_paid, _ = run_http_request(
        base_url, "POST", "/api/leads/generate",
        headers={"Authorization": f"Bearer {tok1}"},
        body={"query": "dentists"}
    )
    record_test("LC-03", "LIFECYCLE", "Paid API allowed after cancellation before ends_at -> 200", st_paid == 200, st_paid, 200, str(js_paid))

    # Task 4 Test 4: Paid API request after cancellation and after ends_at -> ACCESS DENIED (401)
    # Create a subscription with ends_at 1.5 seconds in the future
    sub_id_short = f"sub_short_{int(time.time()*1000)}"
    payload_created_short = json.dumps({
        "meta": {"event_name": "subscription_created", "test_mode": True},
        "data": {
            "id": sub_id_short,
            "attributes": {
                "user_email": "short@example.com",
                "status": "active"
            }
        }
    }).encode("utf-8")
    sig_cs = compute_signature(payload_created_short)
    _, js_cs, _ = run_http_request(base_url, "POST", "/api/payment/webhook", headers={"X-Signature": sig_cs}, raw_body=payload_created_short)
    tok_short = (js_cs or {}).get("token", "")

    # Cancel with ends_at 1 second in the future
    near_future = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() + 1))
    payload_cancel_short = json.dumps({
        "meta": {"event_name": "subscription_cancelled", "test_mode": True},
        "data": {
            "id": sub_id_short,
            "attributes": {
                "status": "cancelled",
                "ends_at": near_future
            }
        }
    }).encode("utf-8")
    sig_short = compute_signature(payload_cancel_short)
    run_http_request(base_url, "POST", "/api/payment/webhook", headers={"X-Signature": sig_short}, raw_body=payload_cancel_short)
    # Wait for ends_at to pass
    time.sleep(2.5)
    st_exp, js_exp, _ = run_http_request(
        base_url, "POST", "/api/leads/generate",
        headers={"Authorization": f"Bearer {tok_short}"},
        body={"query": "dentists"}
    )
    passed = (st_exp == 401) and (js_exp or {}).get("error") == "token_expired"
    record_test("LC-04", "LIFECYCLE", "Paid API denied after cancellation when ends_at passed -> 401", passed, st_exp, 401, str(js_exp))

    # Task 4 Test 5: subscription_expired webhook -> entitlement inactive
    sub_id_exp = f"sub_exp_{int(time.time()*1000)}"
    # Setup active subscription
    p_exp_init = json.dumps({
        "meta": {"event_name": "subscription_created", "test_mode": True},
        "data": {"id": sub_id_exp, "attributes": {"user_email": "exp@example.com", "status": "active"}}
    }).encode("utf-8")
    _, js_init, _ = run_http_request(base_url, "POST", "/api/payment/webhook", headers={"X-Signature": compute_signature(p_exp_init)}, raw_body=p_exp_init)
    tok_exp = (js_init or {}).get("token", "")

    # Expire it
    p_exp = json.dumps({
        "meta": {"event_name": "subscription_expired", "test_mode": True},
        "data": {"id": sub_id_exp, "attributes": {"status": "expired"}}
    }).encode("utf-8")
    st, js, _ = run_http_request(base_url, "POST", "/api/payment/webhook", headers={"X-Signature": compute_signature(p_exp)}, raw_body=p_exp)
    record_test("LC-05", "LIFECYCLE", "subscription_expired webhook processed -> 200", st == 200, st, 200, str(js))

    st_exp2, js_exp2, _ = run_http_request(
        base_url, "POST", "/api/leads/generate",
        headers={"Authorization": f"Bearer {tok_exp}"},
        body={"query": "dentists"}
    )
    record_test("LC-05b", "LIFECYCLE", "Expired token denied on paid API -> 401", st_exp2 == 401, st_exp2, 401, str(js_exp2))

    # Task 4 Test 6: subscription_paused webhook -> entitlement paused, access denied (401)
    sub_id_pause = f"sub_pause_{int(time.time()*1000)}"
    p_pause_init = json.dumps({
        "meta": {"event_name": "subscription_created", "test_mode": True},
        "data": {"id": sub_id_pause, "attributes": {"user_email": "pause@example.com", "status": "active"}}
    }).encode("utf-8")
    _, js_pinit, _ = run_http_request(base_url, "POST", "/api/payment/webhook", headers={"X-Signature": compute_signature(p_pause_init)}, raw_body=p_pause_init)
    tok_pause = (js_pinit or {}).get("token", "")

    p_paused = json.dumps({
        "meta": {"event_name": "subscription_paused", "test_mode": True},
        "data": {"id": sub_id_pause, "attributes": {"status": "paused"}}
    }).encode("utf-8")
    st, js, _ = run_http_request(base_url, "POST", "/api/payment/webhook", headers={"X-Signature": compute_signature(p_paused)}, raw_body=p_paused)
    record_test("LC-06", "LIFECYCLE", "subscription_paused webhook processed -> 200", st == 200, st, 200, str(js))

    st_pcheck, js_pcheck, _ = run_http_request(
        base_url, "POST", "/api/leads/generate",
        headers={"Authorization": f"Bearer {tok_pause}"},
        body={"query": "dentists"}
    )
    passed = (st_pcheck == 401) and (js_pcheck or {}).get("error") == "token_paused"
    record_test("LC-06b", "LIFECYCLE", "Paused token denied on paid API -> 401 (token_paused)", passed, st_pcheck, 401, str(js_pcheck))

    # Task 4 Test 7: subscription_resumed webhook -> entitlement active again (200)
    p_resume = json.dumps({
        "meta": {"event_name": "subscription_resumed", "test_mode": True},
        "data": {"id": sub_id_pause, "attributes": {"status": "active"}}
    }).encode("utf-8")
    st, js, _ = run_http_request(base_url, "POST", "/api/payment/webhook", headers={"X-Signature": compute_signature(p_resume)}, raw_body=p_resume)
    record_test("LC-07", "LIFECYCLE", "subscription_resumed webhook processed -> 200", st == 200, st, 200, str(js))

    st_rcheck, js_rcheck, _ = run_http_request(
        base_url, "POST", "/api/leads/generate",
        headers={"Authorization": f"Bearer {tok_pause}"},
        body={"query": "dentists"}
    )
    record_test("LC-07b", "LIFECYCLE", "Resumed token allowed on paid API -> 200", st_rcheck == 200, st_rcheck, 200, str(js_rcheck))

    # Task 4 Test 8: subscription_payment_failed webhook -> past_due (allowed during grace period)
    sub_id_fail = f"sub_fail_{int(time.time()*1000)}"
    p_fail_init = json.dumps({
        "meta": {"event_name": "subscription_created", "test_mode": True},
        "data": {"id": sub_id_fail, "attributes": {"user_email": "fail@example.com", "status": "active"}}
    }).encode("utf-8")
    _, js_finit, _ = run_http_request(base_url, "POST", "/api/payment/webhook", headers={"X-Signature": compute_signature(p_fail_init)}, raw_body=p_fail_init)
    tok_fail = (js_finit or {}).get("token", "")

    p_failed = json.dumps({
        "meta": {"event_name": "subscription_payment_failed", "test_mode": True},
        "data": {"id": sub_id_fail, "attributes": {"status": "past_due"}}
    }).encode("utf-8")
    st, js, _ = run_http_request(base_url, "POST", "/api/payment/webhook", headers={"X-Signature": compute_signature(p_failed)}, raw_body=p_failed)
    record_test("LC-08", "LIFECYCLE", "subscription_payment_failed webhook processed -> 200", st == 200, st, 200, str(js))

    st_fcheck, js_fcheck, _ = run_http_request(
        base_url, "POST", "/api/leads/generate",
        headers={"Authorization": f"Bearer {tok_fail}"},
        body={"query": "dentists"}
    )
    record_test("LC-08b", "LIFECYCLE", "Past due token within grace period allowed -> 200", st_fcheck == 200, st_fcheck, 200, str(js_fcheck))

    # Task 4 Test 9: Duplicate cancellation webhook -> duplicate_ignored
    st_dup, js_dup, _ = run_http_request(base_url, "POST", "/api/payment/webhook", headers={"X-Signature": sig2}, raw_body=payload_cancel_future)
    passed = (st_dup == 200) and (js_dup or {}).get("status") == "duplicate_ignored"
    record_test("LC-09", "LIFECYCLE", "Duplicate cancellation webhook ignored -> 200 duplicate_ignored", passed, st_dup, 200, str(js_dup))

    # Task 4 Test 10: Cancellation webhook without ends_at -> fails safely without crash
    sub_id_noend = f"sub_noend_{int(time.time()*1000)}"
    p_noend_init = json.dumps({
        "meta": {"event_name": "subscription_created", "test_mode": True},
        "data": {"id": sub_id_noend, "attributes": {"user_email": "noend@example.com", "status": "active"}}
    }).encode("utf-8")
    run_http_request(base_url, "POST", "/api/payment/webhook", headers={"X-Signature": compute_signature(p_noend_init)}, raw_body=p_noend_init)

    p_noend_cancel = json.dumps({
        "meta": {"event_name": "subscription_cancelled", "test_mode": True},
        "data": {"id": sub_id_noend, "attributes": {"status": "cancelled", "ends_at": None}}
    }).encode("utf-8")
    st, js, _ = run_http_request(base_url, "POST", "/api/payment/webhook", headers={"X-Signature": compute_signature(p_noend_cancel)}, raw_body=p_noend_cancel)
    passed = (st == 200) and (js or {}).get("status") == "cancelled"
    record_test("LC-10", "LIFECYCLE", "Cancellation without ends_at fails safely -> 200", passed, st, 200, str(js))

    print("\n--- PHASE 7: NON-LOCKDOWN ENTITLEMENT & AUTH ENFORCEMENT ---")
    auth_tests = [
        ("AUTH-01", "POST", "/api/leads/generate", None, None, 401, "Missing Authorization header -> 401"),
        ("AUTH-02", "POST", "/api/leads/generate", {"Authorization": "Bearer short"}, None, 401, "Malformed short token -> 401"),
        ("AUTH-03", "POST", "/api/leads/generate", {"Authorization": "Bearer ent_00000000000000000000"}, None, 401, "Unrecognized token -> 401"),
        ("AUTH-04", "POST", "/api/leads/generate", None, {"admin": True}, 403, "Browser spoofing without token -> 403"),
        ("AUTH-05", "GET", "/api/subscribers/list", None, None, 403, "Admin endpoint without token -> 403"),
        ("AUTH-06", "GET", "/api/subscribers/list", {"Authorization": "Bearer wrong_secret_key_123"}, None, 403, "Admin endpoint with wrong token -> 403"),
    ]
    for tid, mth, path, hdrs, bdy, exp, desc in auth_tests:
        st, js, _ = run_http_request(base_url, mth, path, headers=hdrs, body=bdy)
        record_test(tid, "AUTH_SECURITY", f"{desc} (Actual: {st})", st == exp, st, exp, str(js))


def main():
    print("=" * 80)
    print("LEAKGRADER PRE-DEPLOY SECURITY RELEASE GATE SPRINT 0.7")
    print("Pure Black-Box HTTP Test Suite (Zero Application Imports)")
    print(f"Target Port: {TEST_PORT}")
    print("=" * 80)

    # 1. Verify offline failure
    test_offline_verification()

    # 2. Verify lockdown environment configurations across subprocesses
    test_lockdown_environments()

    # 3. Main Lockdown Mode Server Subprocess
    print("\n--- STARTING PRIMARY LOCKDOWN SERVER SUBPROCESS ---")
    main_server = TestServerSubprocess(TEST_PORT, {
        "ENVIRONMENT": "test",
        "SECURITY_LOCKDOWN_MODE": "enabled"
    })
    if not main_server.start():
        print("ERROR: Failed to launch primary test server subprocess.")
        return 1

    try:
        run_lockdown_test_suite(main_server)
    finally:
        main_server.stop()

    # 4. Lifecycle & Non-Lockdown Server Subprocess
    print("\n--- STARTING LIFECYCLE & NON-LOCKDOWN SERVER SUBPROCESS ---")
    lifecycle_server = TestServerSubprocess(TEST_PORT, {
        "ENVIRONMENT": "test",
        "SECURITY_LOCKDOWN_MODE": "disabled",
        "PAYMENT_GRACE_PERIOD_DAYS": "3"
    })
    if not lifecycle_server.start():
        print("ERROR: Failed to launch lifecycle test server subprocess.")
        return 1

    try:
        run_lifecycle_and_webhook_suite(lifecycle_server)
    finally:
        lifecycle_server.stop()

    # Summary
    total_count = len(results)
    pass_count = sum(1 for r in results if r["status"] == "PASS")
    fail_count = total_count - pass_count

    print("\n" + "=" * 80)
    print(f"SPRINT 0.7 GATE RESULTS: {pass_count}/{total_count} TESTS PASSED ({(pass_count/total_count)*100:.1f}%)")
    print("=" * 80)

    evidence_file = os.path.join(BASE_DIR, "qa", "PRE_DEPLOY_TEST_RESULTS_RAW.json")
    with open(evidence_file, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "branch": "security/critical-hotfix-2026-09-07",
            "total": total_count,
            "passed": pass_count,
            "failed": fail_count,
            "results": results
        }, f, indent=2)
    print(f"Test results saved to: {evidence_file}")

    return 0 if pass_count == total_count else 1

if __name__ == "__main__":
    sys.exit(main())
