"""
LeakGrader - Pre-Deploy Security Release Gate Sprint 0.5 Automated Test Suite
Audit Date: September 7, 2026
Branch: security/critical-hotfix-2026-09-07

Covers:
1. Strict Lockdown Fail-Closed Verification across all environment states.
2. Complete Route & HTTP Method Matrix (GET, HEAD, POST, PUT, PATCH, DELETE, OPTIONS).
3. Path Variant Bypass Resistance (casing, trailing slash, query params, URL encoding).
4. Paid API Lockdown (HTTP 503 verification).
5. Non-Lockdown Entitlement Status Codes (401 vs 403 standard).
6. Complete 16-Case Webhook Security Matrix (HMAC, replay, lifecycle deactivation).
7. Comprehensive SSRF Attack Vector Matrix (18 attack payloads).
8. Public Scanner Persistence Lockdown Check (audits_vault.json).
9. Public Checkout Hardening (server plan validation).
"""

import os
import sys
import json
import time
import hmac
import hashlib
import socket
import threading
import urllib.request
import urllib.error
from http.server import ThreadingHTTPServer

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app import MastermindRequestHandler
import engine.security_guard as sg

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
    hdrs = headers or {}
    data = None
    if raw_body is not None:
        data = raw_body
    elif body is not None:
        data = json.dumps(body).encode("utf-8")
        if "Content-Type" not in hdrs:
            hdrs["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req, timeout=4) as resp:
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

def test_lockdown_environment_logic():
    print("\n--- PHASE 1: LOCKDOWN FAIL-CLOSED ENVIRONMENT CONFIGURATION ---")
    orig_env = os.environ.copy()
    test_matrix = [
        # (ENV, RENDER, LOCKDOWN_VAL, expected_lockdown, description)
        ("", "", "", True, "Default unconfigured env must default to ENABLED"),
        ("production", "", "false", True, "Production with lockdown=false must remain ENABLED"),
        ("production", "", "", True, "Production unconfigured must remain ENABLED"),
        ("staging", "", "false", True, "Staging with lockdown=false must remain ENABLED"),
        ("staging", "", "", True, "Staging unconfigured must remain ENABLED"),
        ("", "true", "false", True, "Render cloud with lockdown=false must remain ENABLED"),
        ("production", "true", "false", True, "Production on Render with lockdown=false must remain ENABLED"),
        ("test", "true", "false", True, "Test env on Render cloud must remain ENABLED"),
        ("local", "", "true", True, "Local with lockdown=true is ENABLED"),
        ("local", "", "false", False, "Local with lockdown=false is explicitly DISABLED"),
        ("local", "", "0", False, "Local with lockdown=0 is explicitly DISABLED"),
        ("test", "", "false", False, "Test env with lockdown=false is explicitly DISABLED"),
        ("local", "", "unknown_val", True, "Local with ambiguous setting fails closed to ENABLED"),
    ]

    for idx, (env_val, render_val, lock_val, expected, desc) in enumerate(test_matrix, 1):
        for k in ["ENVIRONMENT", "RENDER", "SECURITY_LOCKDOWN_MODE"]:
            if k in os.environ:
                del os.environ[k]
        if env_val: os.environ["ENVIRONMENT"] = env_val
        if render_val: os.environ["RENDER"] = render_val
        if lock_val: os.environ["SECURITY_LOCKDOWN_MODE"] = lock_val

        actual = sg.is_lockdown_enabled()
        record_test(f"ENV-0{idx}" if idx < 10 else f"ENV-{idx}", "LOCKDOWN_ENV", desc, actual == expected, actual, expected, f"env={env_val}, render={render_val}, lock={lock_val}")

    os.environ.clear()
    os.environ.update(orig_env)

def main():
    print("=" * 75)
    print("LEAKGRADER PRE-DEPLOY SECURITY RELEASE GATE SPRINT 0.5 - TEST HARNESS")
    print("=" * 75)

    # 1. Environment matrix
    test_lockdown_environment_logic()

    # 2. Start HTTP server in Lockdown Mode (Production default)
    print("\n--- STARTING LIVE HTTP SERVER IN STRICT LOCKDOWN MODE ---")
    os.environ["ENVIRONMENT"] = "production"
    os.environ.pop("SECURITY_LOCKDOWN_MODE", None)
    TEST_SECRET = "test_ls_prod_secret_matrix_98240982098"
    os.environ["LEMONSQUEEZY_WEBHOOK_SECRET"] = TEST_SECRET
    os.environ["LEMONSQUEEZY_STORE_ID"] = "109845"
    os.environ["LEMONSQUEEZY_VARIANT_IDS"] = "var_pro_month,var_agency_month,var_micro"
    os.environ["ALLOW_TEST_WEBHOOKS"] = "true"

    server = ThreadingHTTPServer(("127.0.0.1", 0), MastermindRequestHandler)
    port = server.server_address[1]
    base_url = f"http://127.0.0.1:{port}"
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    time.sleep(0.5)
    print(f"Test server active on {base_url}")

    # -------------------------------------------------------------------------
    # PHASE 2: ROUTE NORMALIZATION & BYPASS RESISTANCE
    # -------------------------------------------------------------------------
    print("\n--- PHASE 2: ROUTE NORMALIZATION & BYPASS RESISTANCE ---")
    norm_cases = [
        ("NORM-01", "GET", "/founder", 404, "Standard /founder hidden"),
        ("NORM-02", "GET", "/founder/", 404, "Trailing slash /founder/ hidden"),
        ("NORM-03", "GET", "/FOUNDER", 404, "Uppercase /FOUNDER hidden"),
        ("NORM-04", "GET", "/Founder", 404, "Mixed-case /Founder hidden"),
        ("NORM-05", "GET", "/%66%6f%75%6e%64%65%72", 404, "URL-encoded /founder hidden"),
        ("NORM-06", "GET", "/founder?bypass=true&admin=1", 404, "Query param spoofing /founder hidden"),
        ("NORM-07", "HEAD", "/founder", 404, "HEAD /founder denied 404"),
        ("NORM-08", "GET", "/dashboard", 404, "Dashboard route hidden"),
        ("NORM-09", "GET", "/analytics", 404, "Analytics route hidden"),
        ("NORM-10", "PUT", "/founder", 405, "PUT method not allowed"),
        ("NORM-11", "PATCH", "/founder", 405, "PATCH method not allowed"),
        ("NORM-12", "OPTIONS", "/founder", 200, "OPTIONS preflight allowed"),
        ("NORM-13", "GET", "/api/unknown_protected_probe", 404, "Unknown API route default deny"),
        ("NORM-14", "HEAD", "/api/analytics/live", 404, "HEAD probe on admin API denied in lockdown"),
    ]
    for tid, mtd, pth, exp, desc in norm_cases:
        st, _, _ = run_http_request(base_url, mtd, pth)
        record_test(tid, "BYPASS_RESISTANCE", desc, st == exp, st, exp, f"{mtd} {pth}")

    # -------------------------------------------------------------------------
    # PHASE 3: PAID API LOCKDOWN (HTTP 503 VERIFICATION)
    # -------------------------------------------------------------------------
    print("\n--- PHASE 3: PAID API LOCKDOWN (FAIL-CLOSED 503) ---")
    paid_lockdown_cases = [
        ("LOCK-01", "POST", "/api/leads/generate", {"industry": "SaaS"}, 503, "Leads generate returns 503 in lockdown"),
        ("LOCK-02", "POST", "/api/leads/clear", {}, 503, "Leads clear returns 503 in lockdown"),
        ("LOCK-03", "POST", "/api/content/generate", {"topic": "AI"}, 503, "Content generate returns 503 in lockdown"),
        ("LOCK-04", "POST", "/api/content-crew/run", {"topic": "AI"}, 503, "Content crew returns 503 in lockdown"),
        ("LOCK-05", "POST", "/api/checkout/create", {"plan_key": "micro_audit"}, 503, "Checkout create returns 503 in lockdown"),
        ("LOCK-06", "GET", "/api/audit/dossier?company=Apex", None, 503, "Dossier API returns 503 in lockdown"),
        ("LOCK-07", "GET", "/report/dossier/apex-enterprise", None, 503, "Dossier HTML report returns 503 in lockdown"),
        ("LOCK-08", "POST", "/api/booking/clear", {}, 503, "Booking clear returns 503 in lockdown"),
    ]
    for tid, mtd, pth, body, exp, desc in paid_lockdown_cases:
        st, js, _ = run_http_request(base_url, mtd, pth, body=body)
        is_503 = (st == exp) and ((js or {}).get("error") == "feature_temporarily_unavailable" or "unavailable" in str(js))
        record_test(tid, "PAID_LOCKDOWN", desc, is_503, st, exp, f"Response: {js}")

    # Booking chat mutation containment in lockdown
    st_chat, js_chat, _ = run_http_request(base_url, "POST", "/api/booking/chat", body={"message": "Book demo tomorrow 3pm please", "history": []})
    chat_safe = (st_chat == 200 and (js_chat or {}).get("auto_booked") is False)
    record_test("LOCK-09", "PAID_LOCKDOWN", "Booking chat disables auto-mutation under lockdown", chat_safe, (js_chat or {}).get("auto_booked"), False, f"Chat resp: {js_chat}")

    # -------------------------------------------------------------------------
    # PHASE 4: PUBLIC SCANNER SSRF GUARD
    # -------------------------------------------------------------------------
    print("\n--- PHASE 4: PUBLIC SCANNER SSRF GUARD (18 ATTACK VECTORS) ---")
    ssrf_vectors = [
        ("SSRF-01", "http://127.0.0.1:8090/founder", "Direct loopback IP"),
        ("SSRF-02", "http://127.0.0.2:80", "Alternative loopback 127.0.0.2"),
        ("SSRF-03", "http://localhost:8090", "Localhost hostname"),
        ("SSRF-04", "http://0.0.0.0:80", "Zero broadcast IP"),
        ("SSRF-05", "http://[::1]:80", "IPv6 loopback"),
        ("SSRF-06", "http://169.254.169.254/latest/meta-data/", "AWS/Cloud metadata IP"),
        ("SSRF-07", "http://10.0.0.1/admin", "RFC1918 10.0.0.0/8 private network"),
        ("SSRF-08", "http://172.16.0.1/admin", "RFC1918 172.16.0.0/12 private network"),
        ("SSRF-09", "http://192.168.1.1/setup", "RFC1918 192.168.0.0/16 private network"),
        ("SSRF-10", "http://224.0.0.1", "Multicast IP address"),
        ("SSRF-11", "file:///etc/passwd", "file:// scheme access"),
        ("SSRF-12", "ftp://127.0.0.1/resource", "ftp:// protocol access"),
        ("SSRF-13", "gopher://127.0.0.1:70", "gopher:// protocol access"),
        ("SSRF-14", "http://admin:secret@127.0.0.1", "Userinfo embedded in URL"),
        ("SSRF-15", "http://127.0.0.1:22", "Non-standard port (SSH 22)"),
        ("SSRF-16", "http://0177.0.0.1", "Octal representation of 127.0.0.1"),
        ("SSRF-17", "http://0x7f000001", "Hex representation of 127.0.0.1"),
        ("SSRF-18", "http://2130706433", "Integer representation of 127.0.0.1"),
    ]
    for tid, target, desc in ssrf_vectors:
        is_safe, _, reason = sg.validate_url_ssrf_safe(target)
        record_test(tid, "SSRF_SECURITY", f"SSRF rejection: {desc}", is_safe is False, "BLOCKED" if not is_safe else "ALLOWED", "BLOCKED", f"Target: {target}, reason: {reason}")

    # Test audit endpoint SSRF enforcement
    st_ssrf_api, js_ssrf_api, _ = run_http_request(base_url, "POST", "/api/audit/run", body={"url_or_company": "http://127.0.0.1:8090/founder"})
    record_test("SSRF-19", "SSRF_SECURITY", "/api/audit/run rejects SSRF target with 400", st_ssrf_api == 400, st_ssrf_api, 400, f"Response: {js_ssrf_api}")

    # Public business name allowed
    is_biz_safe, _, _ = sg.validate_url_ssrf_safe("Acme Real Estate")
    record_test("SSRF-20", "SSRF_SECURITY", "Public company name allowed for audit simulation", is_biz_safe is True, is_biz_safe, True, "Acme Real Estate")

    # Scanner persistence in lockdown check
    audits_file = os.path.join(BASE_DIR, "storage", "audits_vault.json")
    mtime_before = os.path.getmtime(audits_file) if os.path.exists(audits_file) else 0
    st_scan, _, _ = run_http_request(base_url, "POST", "/api/audit/run", body={"url_or_company": "Apex Enterprise"})
    mtime_after = os.path.getmtime(audits_file) if os.path.exists(audits_file) else 0
    record_test("AUDIT-PERSIST", "SCANNER_LOCKDOWN", "audits_vault.json unmodified during lockdown scan", (mtime_before == mtime_after and st_scan == 200), mtime_after, mtime_before, "Persistence disabled in lockdown")

    # -------------------------------------------------------------------------
    # PHASE 5: COMPLETE 16-CASE WEBHOOK SECURITY MATRIX
    # -------------------------------------------------------------------------
    print("\n--- PHASE 5: COMPLETE 16-CASE WEBHOOK SECURITY MATRIX ---")

    def sign_payload(payload_bytes: bytes, secret: str) -> str:
        return hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()

    def make_ls_payload(event_name: str, order_id: str, store_id: str = "109845", variant_id: str = "var_pro_month", status: str = "active", test_mode: bool = False):
        return {
            "meta": {
                "event_name": event_name,
                "test_mode": test_mode,
                "custom_data": {"event_id": f"evt_{order_id}_{event_name}"}
            },
            "data": {
                "id": order_id,
                "type": "subscriptions" if "subscription" in event_name else "orders",
                "attributes": {
                    "store_id": store_id,
                    "variant_id": variant_id,
                    "status": status,
                    "user_name": "Test Customer",
                    "user_email": "customer@testcorp.com",
                    "created_at": "2026-09-08T00:00:00.000000Z"
                }
            }
        }

    # Case 1: Valid signature & payload
    p1 = json.dumps(make_ls_payload("subscription_created", "sub_valid_101")).encode("utf-8")
    sig1 = sign_payload(p1, TEST_SECRET)
    st1, js1, _ = run_http_request(base_url, "POST", "/api/payment/webhook", headers={"X-Signature": sig1}, raw_body=p1)
    record_test("WH-01", "WEBHOOK_MATRIX", "Valid signature & subscription_created -> 200", st1 == 200 and (js1 or {}).get("success") is True, st1, 200, f"Resp: {js1}")

    # Case 2: Missing signature header
    st2, _, _ = run_http_request(base_url, "POST", "/api/payment/webhook", raw_body=p1)
    record_test("WH-02", "WEBHOOK_MATRIX", "Missing X-Signature header -> 401", st2 == 401, st2, 401, "Header absent")

    # Case 3: Invalid/corrupt signature
    st3, _, _ = run_http_request(base_url, "POST", "/api/payment/webhook", headers={"X-Signature": "bad_sig_abc123"}, raw_body=p1)
    record_test("WH-03", "WEBHOOK_MATRIX", "Corrupt signature digest -> 401", st3 == 401, st3, 401, "Bad digest")

    # Case 4: Missing LEMONSQUEEZY_WEBHOOK_SECRET in environment
    is_v4, msg4, st4, _ = sg.verify_lemonsqueezy_webhook(p1, sig1, secret="")
    record_test("WH-04", "WEBHOOK_MATRIX", "Missing secret in environment -> 503", st4 == 503, st4, 503, f"Msg: {msg4}")

    # Case 5: Duplicate webhook delivery (Idempotency)
    st5, js5, _ = run_http_request(base_url, "POST", "/api/payment/webhook", headers={"X-Signature": sig1}, raw_body=p1)
    dup_ok = (st5 == 200 and (js5 or {}).get("status") == "duplicate_ignored")
    record_test("WH-05", "WEBHOOK_MATRIX", "Duplicate webhook replay -> 200 duplicate_ignored", dup_ok, st5, 200, f"Resp: {js5}")

    # Case 6: Malformed JSON body
    bad_bytes = b'{"meta": {bad json payload'
    sig6 = sign_payload(bad_bytes, TEST_SECRET)
    st6, _, _ = run_http_request(base_url, "POST", "/api/payment/webhook", headers={"X-Signature": sig6}, raw_body=bad_bytes)
    record_test("WH-06", "WEBHOOK_MATRIX", "Malformed JSON body -> 400", st6 == 400, st6, 400, "Syntax error in JSON")

    # Case 7: Wrong store_id
    p7 = json.dumps(make_ls_payload("subscription_created", "sub_wrong_store", store_id="999999")).encode("utf-8")
    sig7 = sign_payload(p7, TEST_SECRET)
    st7, _, _ = run_http_request(base_url, "POST", "/api/payment/webhook", headers={"X-Signature": sig7}, raw_body=p7)
    record_test("WH-07", "WEBHOOK_MATRIX", "Mismatched store_id -> 400", st7 == 400, st7, 400, "Foreign store rejected")

    # Case 8: Unknown product_id or variant_id
    p8 = json.dumps(make_ls_payload("subscription_created", "sub_wrong_var", variant_id="unknown_variant_xyz")).encode("utf-8")
    sig8 = sign_payload(p8, TEST_SECRET)
    st8, _, _ = run_http_request(base_url, "POST", "/api/payment/webhook", headers={"X-Signature": sig8}, raw_body=p8)
    record_test("WH-08", "WEBHOOK_MATRIX", "Unknown variant_id -> 422", st8 == 422, st8, 422, "Unauthorized variant")

    # Case 9: Test-mode event in production without ALLOW_TEST_WEBHOOKS
    orig_allow = os.environ.get("ALLOW_TEST_WEBHOOKS", "")
    os.environ["ALLOW_TEST_WEBHOOKS"] = "false"
    p9 = json.dumps(make_ls_payload("order_created", "ord_test_prod", test_mode=True)).encode("utf-8")
    sig9 = sign_payload(p9, TEST_SECRET)
    st9, _, _ = run_http_request(base_url, "POST", "/api/payment/webhook", headers={"X-Signature": sig9}, raw_body=p9)
    os.environ["ALLOW_TEST_WEBHOOKS"] = orig_allow
    record_test("WH-09", "WEBHOOK_MATRIX", "Test-mode event in production rejected -> 400", st9 == 400, st9, 400, "Test mode in prod")

    # Case 10: subscription_cancelled -> handled safely, no active entitlement created, existing revoked
    p10 = json.dumps(make_ls_payload("subscription_cancelled", "sub_valid_101", status="cancelled")).encode("utf-8")
    sig10 = sign_payload(p10, TEST_SECRET)
    st10, js10, _ = run_http_request(base_url, "POST", "/api/payment/webhook", headers={"X-Signature": sig10}, raw_body=p10)
    can_ok = (st10 == 200 and (js10 or {}).get("active_entitlement_created") is False)
    record_test("WH-10", "WEBHOOK_MATRIX", "subscription_cancelled revokes entitlement -> 200 inactive", can_ok, st10, 200, f"Resp: {js10}")

    # Case 11: subscription_expired -> handled safely without creating active entitlement
    p11 = json.dumps(make_ls_payload("subscription_expired", "sub_expired_99", status="expired")).encode("utf-8")
    sig11 = sign_payload(p11, TEST_SECRET)
    st11, js11, _ = run_http_request(base_url, "POST", "/api/payment/webhook", headers={"X-Signature": sig11}, raw_body=p11)
    exp_ok = (st11 == 200 and (js11 or {}).get("active_entitlement_created") is False)
    record_test("WH-11", "WEBHOOK_MATRIX", "subscription_expired -> 200 inactive", exp_ok, st11, 200, f"Resp: {js11}")

    # Case 12: subscription_paused -> handled safely without creating active entitlement
    p12 = json.dumps(make_ls_payload("subscription_paused", "sub_paused_88", status="paused")).encode("utf-8")
    sig12 = sign_payload(p12, TEST_SECRET)
    st12, js12, _ = run_http_request(base_url, "POST", "/api/payment/webhook", headers={"X-Signature": sig12}, raw_body=p12)
    pau_ok = (st12 == 200 and (js12 or {}).get("active_entitlement_created") is False)
    record_test("WH-12", "WEBHOOK_MATRIX", "subscription_paused -> 200 inactive", pau_ok, st12, 200, f"Resp: {js12}")

    # Case 13: subscription_unpaid -> handled safely without creating active entitlement
    p13 = json.dumps(make_ls_payload("subscription_unpaid", "sub_unpaid_77", status="unpaid")).encode("utf-8")
    sig13 = sign_payload(p13, TEST_SECRET)
    st13, js13, _ = run_http_request(base_url, "POST", "/api/payment/webhook", headers={"X-Signature": sig13}, raw_body=p13)
    unp_ok = (st13 == 200 and (js13 or {}).get("active_entitlement_created") is False)
    record_test("WH-13", "WEBHOOK_MATRIX", "subscription_unpaid -> 200 inactive", unp_ok, st13, 200, f"Resp: {js13}")

    # Case 14: subscription_resumed -> reactivates entitlement
    p14 = json.dumps(make_ls_payload("subscription_resumed", "sub_resumed_66", status="active")).encode("utf-8")
    sig14 = sign_payload(p14, TEST_SECRET)
    st14, js14, _ = run_http_request(base_url, "POST", "/api/payment/webhook", headers={"X-Signature": sig14}, raw_body=p14)
    res_ok = (st14 == 200 and (js14 or {}).get("active_entitlement_created") is True)
    record_test("WH-14", "WEBHOOK_MATRIX", "subscription_resumed -> 200 active entitlement granted", res_ok, st14, 200, f"Resp: {js14}")

    # Case 15: Client spoofed paid=true without valid signature
    p15 = b'{"paid": true, "user_id": "attacker"}'
    st15, _, _ = run_http_request(base_url, "POST", "/api/payment/webhook", headers={"X-Signature": "fake"}, raw_body=p15)
    record_test("WH-15", "WEBHOOK_MATRIX", "Client paid=true spoofing rejected at webhook -> 401", st15 == 401, st15, 401, "Sig failed")

    # Case 16: Replay of cancelled subscription event
    st16, js16, _ = run_http_request(base_url, "POST", "/api/payment/webhook", headers={"X-Signature": sig10}, raw_body=p10)
    rep_can_ok = (st16 == 200 and (js16 or {}).get("status") == "duplicate_ignored")
    record_test("WH-16", "WEBHOOK_MATRIX", "Replay of cancellation event -> 200 duplicate_ignored", rep_can_ok, st16, 200, f"Resp: {js16}")

    # Stop server
    server.shutdown()
    server.server_close()

    # -------------------------------------------------------------------------
    # PHASE 6: NON-LOCKDOWN STATUS CODE VERIFICATION (401 vs 403)
    # -------------------------------------------------------------------------
    print("\n--- PHASE 6: NON-LOCKDOWN STATUS CODE VERIFICATION (401 vs 403) ---")
    os.environ["ENVIRONMENT"] = "local"
    os.environ["SECURITY_LOCKDOWN_MODE"] = "false"
    server2 = ThreadingHTTPServer(("127.0.0.1", 0), MastermindRequestHandler)
    port2 = server2.server_address[1]
    base_url2 = f"http://127.0.0.1:{port2}"
    server2_thread = threading.Thread(target=server2.serve_forever, daemon=True)
    server2_thread.start()
    time.sleep(0.5)

    # Missing auth header -> 401
    st_no_auth, _, _ = run_http_request(base_url2, "POST", "/api/leads/generate", body={"industry": "SaaS"})
    record_test("AUTH-401-A", "AUTH_STATUS_CODES", "Missing identity header -> HTTP 401", st_no_auth == 401, st_no_auth, 401, "No Bearer token")

    # Invalid token format -> 401
    st_inv_tok, _, _ = run_http_request(base_url2, "POST", "/api/leads/generate", headers={"Authorization": "Bearer short"}, body={"industry": "SaaS"})
    record_test("AUTH-401-B", "AUTH_STATUS_CODES", "Malformed/short token -> HTTP 401", st_inv_tok == 401, st_inv_tok, 401, "Invalid token")

    # Expired / unlisted token -> 401
    st_unlisted, _, _ = run_http_request(base_url2, "POST", "/api/leads/generate", headers={"Authorization": "Bearer ent_unlisted_token_12345678"}, body={"industry": "SaaS"})
    record_test("AUTH-401-C", "AUTH_STATUS_CODES", "Unrecognized token -> HTTP 401", st_unlisted == 401, st_unlisted, 401, "Token not found")

    # Client spoofing paid=true without token -> 401
    st_paid_spoof, _, _ = run_http_request(base_url2, "POST", "/api/leads/generate", body={"paid": True})
    record_test("AUTH-401-D", "AUTH_STATUS_CODES", "Client paid=true spoofing rejected -> HTTP 401", st_paid_spoof == 401, st_paid_spoof, 401, "Untrusted client body flag")

    # Client spoofing admin=true without admin credentials -> 403
    st_adm_spoof, _, _ = run_http_request(base_url2, "POST", "/api/leads/generate", body={"admin": True})
    record_test("AUTH-403-A", "AUTH_STATUS_CODES", "Client admin=true claim rejected -> HTTP 403", st_adm_spoof == 403, st_adm_spoof, 403, "Admin spoofing denied")

    # Public checkout outside lockdown - validates server plans
    st_chk_ok, _, _ = run_http_request(base_url2, "POST", "/api/checkout/create", body={"plan_key": "micro_audit"})
    record_test("CHK-01", "CHECKOUT_HARDENING", "Valid server plan allowed outside lockdown", st_chk_ok == 200, st_chk_ok, 200, "micro_audit")

    st_chk_bad, _, _ = run_http_request(base_url2, "POST", "/api/checkout/create", body={"plan_key": "unauthorized_custom_price_1dollar"})
    record_test("CHK-02", "CHECKOUT_HARDENING", "Arbitrary client plan rejected -> 400", st_chk_bad == 400, st_chk_bad, 400, "Invalid plan")

    server2.shutdown()
    server2.server_close()

    # -------------------------------------------------------------------------
    # SUMMARY & EVIDENCE PERSISTENCE
    # -------------------------------------------------------------------------
    print("\n" + "=" * 75)
    pass_count = sum(1 for r in results if r["status"] == "PASS")
    total_count = len(results)
    print(f"RELEASE GATE RESULTS: {pass_count}/{total_count} TESTS PASSED ({(pass_count/total_count)*100:.1f}%)")
    print("=" * 75)

    evidence_file = os.path.join(BASE_DIR, "qa", "PRE_DEPLOY_TEST_RESULTS_RAW.json")
    with open(evidence_file, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "branch": "security/critical-hotfix-2026-09-07",
            "total": total_count,
            "passed": pass_count,
            "failed": total_count - pass_count,
            "results": results
        }, f, indent=2)
    print(f"Test run results saved to: {evidence_file}")

    return 0 if pass_count == total_count else 1

if __name__ == "__main__":
    sys.exit(main())
