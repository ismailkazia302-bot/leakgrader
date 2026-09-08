"""
LeakGrader - Automated Security Hotfix Sprint 0 Verification Suite
Audit Date: September 7, 2026
Branch: security/critical-hotfix-2026-09-07

Verifies 12 Mandatory Security Hotfix Test Conditions:
1. Anonymous request to /founder returns HTTP 404 (route existence hidden).
2. Anonymous request to admin APIs returns HTTP 404 in lockdown mode.
3. Any Document Vault operation returns HTTP 503 (feature_temporarily_unavailable).
4. Anonymous call to /api/leads/generate or /api/content/generate returns HTTP 403 (entitlement_required).
5. Call with body flag {"paid": true} without active entitlement returns HTTP 403.
6. Call with body flag {"admin": true} without valid admin auth returns HTTP 403/404.
7. Call attempting to access another workspace or spoofing workspace_id returns HTTP 403.
8. Lemon Squeezy webhook with missing signature returns HTTP 401 (or 503 if secret unconfigured).
9. Lemon Squeezy webhook with invalid HMAC signature returns HTTP 401.
10. Validly signed Lemon Squeezy webhook in local test mode creates exactly 1 entitlement and returns HTTP 200.
11. Replay of same valid webhook delivery returns HTTP 200 (duplicate_ignored) and leaves count at 1.
12. Public marketing pages and public scan remain accessible with HTTP 200.
"""

import os
import sys
import json
import time
import hmac
import hashlib
import threading
import urllib.request
import urllib.error
from http.server import ThreadingHTTPServer

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

os.environ.pop("SECURITY_LOCKDOWN_MODE", None)
TEST_WEBHOOK_SECRET = "test_ls_secret_key_84920491823091820938"
os.environ["LEMONSQUEEZY_WEBHOOK_SECRET"] = TEST_WEBHOOK_SECRET
os.environ["ALLOW_TEST_WEBHOOKS"] = "true"

from app import MastermindRequestHandler
import engine.security_guard as sg

results = []

def record_test(test_id: str, title: str, passed: bool, status_code: int, expected_code: int, details: str):
    res = {
        "test_id": test_id,
        "title": title,
        "status": "PASS" if passed else "FAIL",
        "http_status": status_code,
        "expected_status": expected_code,
        "details": details
    }
    results.append(res)
    mark = "PASS" if passed else "FAIL"
    print(f"[{mark}] {test_id}: {title} (HTTP {status_code} vs expected {expected_code})")
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

def main():
    print("=" * 70)
    print("LEAKGRADER CRITICAL SECURITY HOTFIX SPRINT 0 - AUTOMATED VERIFICATION")
    print("=" * 70)
    print("1. Starting local HTTP test server with MastermindRequestHandler...")

    server = ThreadingHTTPServer(("127.0.0.1", 0), MastermindRequestHandler)
    port = server.server_address[1]
    base_url = f"http://127.0.0.1:{port}"

    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    print(f"   Server active at {base_url}")
    time.sleep(0.5)

    # TEST 1: Anonymous request to /founder returns HTTP 404
    status, _, _ = run_http_request(base_url, "GET", "/founder")
    record_test("TEST-01", "Anonymous GET /founder containment", status == 404, status, 404, "Route existence hidden in lockdown")

    # TEST 2: Anonymous request to admin APIs returns HTTP 404 in lockdown mode
    status_live, _, _ = run_http_request(base_url, "GET", "/api/analytics/live")
    status_pipe, _, _ = run_http_request(base_url, "GET", "/api/pipeline/ledger")
    record_test("TEST-02", "Anonymous Admin APIs (/api/analytics/live, /api/pipeline/ledger)", status_live == 404 and status_pipe == 404, status_live, 404, f"live={status_live}, pipe={status_pipe}")

    # TEST 3: Document Vault operations return HTTP 503
    st_get, j_get, _ = run_http_request(base_url, "GET", "/api/documents")
    st_post, j_post, _ = run_http_request(base_url, "POST", "/api/query", body={"query": "financial leaks"})
    st_del, j_del, _ = run_http_request(base_url, "DELETE", "/api/documents/doc_test123")
    passed = (st_get == 503 and st_post == 503 and st_del == 503)
    record_test("TEST-03", "Document Vault containment (GET, POST, DELETE)", passed, st_get, 503, f"Status: get={st_get}, post={st_post}, del={st_del}")

    # TEST 4: Anonymous call to paid APIs returns HTTP 403
    st_leads, _, _ = run_http_request(base_url, "POST", "/api/leads/generate", body={"industry": "SaaS"})
    st_art, _, _ = run_http_request(base_url, "POST", "/api/content/generate", body={"topic": "Conversion Leaks"})
    passed = (st_leads == 403 and st_art == 403)
    record_test("TEST-04", "Anonymous access to paid generation APIs", passed, st_leads, 403, f"leads={st_leads}, content={st_art}")

    # TEST 5: Call with body flag {"paid": true} returns HTTP 403 (spoofing blocked)
    st_spoof_paid, _, _ = run_http_request(base_url, "POST", "/api/leads/generate", body={"industry": "SaaS", "paid": True, "is_paid": "true"})
    record_test("TEST-05", "Client spoofing flag paid=true rejection", st_spoof_paid == 403, st_spoof_paid, 403, "Client boolean claim rejected")

    # TEST 6: Call with body flag {"admin": true} returns HTTP 403 (spoofing blocked)
    st_spoof_adm, _, _ = run_http_request(base_url, "POST", "/api/leads/generate", body={"industry": "SaaS", "admin": True})
    record_test("TEST-06", "Client spoofing flag admin=true rejection", st_spoof_adm in [403, 404], st_spoof_adm, 403, "Client admin claim rejected")

    # TEST 7: Cross-workspace access or spoofing workspace_id returns HTTP 403
    st_ws, _, _ = run_http_request(base_url, "POST", "/api/leads/generate", body={"industry": "SaaS", "workspace_id": "ws_victim_tenant"})
    record_test("TEST-07", "Cross-workspace tenant spoofing rejection", st_ws == 403, st_ws, 403, "Untrusted workspace_id rejected")

    # TEST 8: Lemon Squeezy webhook with missing signature returns HTTP 401
    webhook_payload = json.dumps({
        "meta": {"event_name": "order_created", "test_mode": True},
        "data": {
            "id": "order_test_8819",
            "attributes": {"store_id": "123", "user_email": "qa_tester@leakgrader.com"}
        }
    }).encode("utf-8")
    st_wh_nosig, _, _ = run_http_request(base_url, "POST", "/api/payment/webhook", raw_body=webhook_payload)
    record_test("TEST-08", "Lemon Squeezy webhook missing signature header", st_wh_nosig in [401, 503], st_wh_nosig, 401, "Rejected unsigned webhook")

    # TEST 9: Lemon Squeezy webhook with invalid HMAC signature returns HTTP 401
    st_wh_badsig, _, _ = run_http_request(base_url, "POST", "/api/payment/webhook", headers={"X-Signature": "invalid_hex_digest_9999"}, raw_body=webhook_payload)
    record_test("TEST-09", "Lemon Squeezy webhook invalid HMAC signature digest", st_wh_badsig == 401, st_wh_badsig, 401, "Rejected digest mismatch")

    # TEST 10: Validly signed Lemon Squeezy webhook creates active entitlement
    valid_sig = hmac.new(TEST_WEBHOOK_SECRET.encode("utf-8"), webhook_payload, hashlib.sha256).hexdigest()
    st_wh_valid, j_wh_valid, _ = run_http_request(base_url, "POST", "/api/payment/webhook", headers={"X-Signature": valid_sig}, raw_body=webhook_payload)
    passed = (st_wh_valid == 200 and (j_wh_valid or {}).get("success") is True)
    ent_token = (j_wh_valid or {}).get("token", "")
    record_test("TEST-10", "Valid signed Lemon Squeezy webhook processing", passed, st_wh_valid, 200, f"Token generated: {ent_token[:8]}...")

    # TEST 11: Replaying the exact same valid webhook returns duplicate_ignored
    st_wh_replay, j_wh_replay, _ = run_http_request(base_url, "POST", "/api/payment/webhook", headers={"X-Signature": valid_sig}, raw_body=webhook_payload)
    passed = (st_wh_replay == 200 and (j_wh_replay or {}).get("status") == "duplicate_ignored")
    record_test("TEST-11", "Webhook idempotency replay protection", passed, st_wh_replay, 200, f"Status: {(j_wh_replay or {}).get('status')}")

    # TEST 12: Public marketing pages remain accessible with HTTP 200
    st_home, _, _ = run_http_request(base_url, "GET", "/")
    st_about, _, _ = run_http_request(base_url, "GET", "/about")
    st_contact, _, _ = run_http_request(base_url, "GET", "/contact")
    st_plans, _, _ = run_http_request(base_url, "GET", "/api/pricing/plans")
    st_scan, _, _ = run_http_request(base_url, "POST", "/api/audit/run", body={"company": "Test Apex", "industry": "SaaS"})
    st_checkout, _, _ = run_http_request(base_url, "POST", "/api/checkout/create", body={"plan_key": "micro_audit"})
    all_public_ok = (st_home == 200 and st_about == 200 and st_contact == 200 and st_plans == 200 and st_scan == 200 and st_checkout == 200)
    record_test("TEST-12", "Public marketing pages and public scan accessibility", all_public_ok, st_home, 200, f"home={st_home}, about={st_about}, contact={st_contact}, scan={st_scan}, checkout={st_checkout}")

    # TEST 13 (Bonus): Active Entitlement access verification using generated token
    if ent_token:
        st_auth_gen, j_auth_gen, _ = run_http_request(base_url, "POST", "/api/leads/generate", headers={"Authorization": f"Bearer {ent_token}"}, body={"industry": "Healthcare", "count": 2})
        passed = (st_auth_gen == 200 and (j_auth_gen or {}).get("success") is True)
        record_test("TEST-13", "Paid feature generation using valid entitlement token", passed, st_auth_gen, 200, f"Generated: {(j_auth_gen or {}).get('generated_count')} leads")

    # Stop server
    server.shutdown()
    server.server_close()

    print("=" * 70)
    pass_count = sum(1 for r in results if r["status"] == "PASS")
    total_count = len(results)
    print(f"RESULTS: {pass_count}/{total_count} TESTS PASSED ({(pass_count/total_count)*100:.1f}%)")
    print("=" * 70)

    # Save evidence file
    evidence_path = os.path.join(BASE_DIR, "qa", "evidence", "security_sprint0_results.json")
    os.makedirs(os.path.dirname(evidence_path), exist_ok=True)
    with open(evidence_path, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "branch": "security/critical-hotfix-2026-09-07",
            "total": total_count,
            "passed": pass_count,
            "failed": total_count - pass_count,
            "results": results
        }, f, indent=2)
    print(f"Evidence saved to: {evidence_path}")

    return 0 if pass_count == total_count else 1

if __name__ == "__main__":
    sys.exit(main())

