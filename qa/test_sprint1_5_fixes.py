"""
Comprehensive Black-Box Verification Suite for Sprint 1.5 Feature Fixes
Tests all 7 feature areas across 25 black-box HTTP tests:
1. Scanner & Database Connection (5 tests)
2. Plan Limit Enforcement (5 tests)
3. Multi-Tenant Isolation (4 tests)
4. PDF & Report Endpoints (4 tests)
5. Recent Audits & Dashboard API (3 tests)
6. Analytics Events Verification (2 tests)
7. Regression Checks (2 tests)
"""

import os
import sys
import time
import json
import uuid
import re
import urllib.request
import urllib.error
import subprocess
from datetime import datetime, timezone

# Ensure project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

TEST_RESULTS = []

def record_test(test_id, category, description, passed, actual="", expected="", details=""):
    status_str = "[PASS]" if passed else "[FAIL]"
    print(f"{status_str} {test_id} [{category}]: {description} (Actual: {actual} vs Expected: {expected})")
    TEST_RESULTS.append({
        "id": test_id,
        "category": category,
        "description": description,
        "passed": passed,
        "actual": str(actual),
        "expected": str(expected),
        "details": str(details)
    })


def run_http_request(url, method="GET", body=None, headers=None):
    hdrs = headers.copy() if headers else {}
    data = None
    if body is not None:
        if isinstance(body, (dict, list)):
            data = json.dumps(body).encode("utf-8")
            if "Content-Type" not in hdrs and "content-type" not in hdrs:
                hdrs["Content-Type"] = "application/json"
        elif isinstance(body, str):
            data = body.encode("utf-8")
        elif isinstance(body, bytes):
            data = body

    req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            resp_body = resp.read()
            resp_hdrs = dict(resp.info())
            json_data = None
            try:
                json_data = json.loads(resp_body.decode("utf-8"))
            except Exception:
                pass
            return resp.status, json_data, resp_body, resp_hdrs
    except urllib.error.HTTPError as e:
        err_body = e.read()
        err_hdrs = dict(e.info())
        err_json = None
        try:
            err_json = json.loads(err_body.decode("utf-8"))
        except Exception:
            pass
        return e.code, err_json, err_body, err_hdrs


def main():
    print("=" * 80)
    print("RUNNING SPRINT 1.5 FIXES BLACK-BOX VERIFICATION SUITE (25 TESTS)")
    print("=" * 80)

    test_db_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "storage", "test_sprint1_5_runner.db")
    if os.path.exists(test_db_file):
        try:
            os.remove(test_db_file)
        except Exception:
            pass

    os.environ["DATABASE_URL"] = f"sqlite:///{os.path.abspath(test_db_file)}"
    os.environ["ENVIRONMENT"] = "production"
    os.environ["SECURITY_LOCKDOWN_MODE"] = "enabled"
    os.environ["LOCKDOWN_PHASE"] = "auth_ready"
    os.environ["STORAGE_DIR"] = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "storage")

    import db.connection
    db.connection._PG_POOL = None
    db.connection._IS_SQLITE = False
    db.connection._SQLITE_PATH = None
    db.connection.init_pool()
    from db.connection import get_db_cursor, is_sqlite
    from db.migrate import run_migrations

    mig_ok = run_migrations()
    print(f"[*] Database initialized & migrated: {mig_ok}")

    port = 8778
    server_env = os.environ.copy()
    server_env["PORT"] = str(port)
    server_proc = subprocess.Popen(
        [sys.executable, "-c", f"from wsgiref.simple_server import make_server; from wsgi import app; make_server('127.0.0.1', {port}, app).serve_forever()"],
        env=server_env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    time.sleep(2.5)
    base_url = f"http://127.0.0.1:{port}"

    try:
        # Create Test User A (Free tier, 2 audits/month)
        email_a = f"test_a_{int(time.time())}@example.com"
        pwd_a = "SecurePassword123!"
        st_signup, js_signup, _, hdrs_signup = run_http_request(
            f"{base_url}/api/auth/signup",
            method="POST",
            body={"email": email_a, "password": pwd_a, "full_name": "Test User A"}
        )
        token_a = ""
        cookie_header = hdrs_signup.get("Set-Cookie") or hdrs_signup.get("set-cookie") or ""
        if "session_token=" in cookie_header:
            token_a = cookie_header.split("session_token=")[1].split(";")[0].strip()
        user_a_id = js_signup.get("user", {}).get("id")

        # Create Test User B (Free tier for multi-tenant isolation testing)
        email_b = f"test_b_{int(time.time())}@example.com"
        pwd_b = "SecurePassword123!"
        st_signup_b, js_signup_b, _, hdrs_signup_b = run_http_request(
            f"{base_url}/api/auth/signup",
            method="POST",
            body={"email": email_b, "password": pwd_b, "full_name": "Test User B"}
        )
        token_b = ""
        cookie_header_b = hdrs_signup_b.get("Set-Cookie") or hdrs_signup_b.get("set-cookie") or ""
        if "session_token=" in cookie_header_b:
            token_b = cookie_header_b.split("session_token=")[1].split(";")[0].strip()
        user_b_id = js_signup_b.get("user", {}).get("id")

        print(f"[*] Test User A created: {email_a} (Token: {token_a[:10]}...)")
        print(f"[*] Test User B created: {email_b} (Token: {token_b[:10]}...)")

        # =====================================================================
        # GROUP 1: SCANNER & DATABASE CONNECTION (5 Tests)
        # =====================================================================
        print("\n--- GROUP 1: SCANNER & DATABASE CONNECTION ---")

        # 1. FIX-DB-01: Authenticated scan persists to 'audits' table
        st_scan1, js_scan1, _, _ = run_http_request(
            f"{base_url}/api/audit/run",
            method="POST",
            body={"target": "example.com"},
            headers={"Cookie": f"session_token={token_a}"}
        )
        with get_db_cursor() as cur:
            cur.execute("SELECT COUNT(*) as cnt FROM audits WHERE domain LIKE '%example.com%';")
            cnt_row = cur.fetchone()
            db_persisted = cnt_row and cnt_row["cnt"] >= 1
        record_test("FIX-DB-01", "SCAN_DB", "Authenticated scan persists to audits database table", db_persisted, db_persisted, True)

        # 2. FIX-DB-02: 'audits' row contains full results JSONB
        audit_row = None
        has_results = False
        with get_db_cursor() as cur:
            cur.execute("SELECT id, domain, results, score FROM audits WHERE domain LIKE '%example.com%' ORDER BY created_at DESC LIMIT 1;")
            audit_row = cur.fetchone()
            if audit_row and audit_row["results"]:
                res_obj = json.loads(audit_row["results"]) if isinstance(audit_row["results"], str) else audit_row["results"]
                has_results = isinstance(res_obj, dict) and "diagnostic_points" in res_obj and len(res_obj["diagnostic_points"]) == 15
        record_test("FIX-DB-02", "SCAN_DB", "Audits row stores full 15-point diagnostic results JSON", has_results, has_results, True)

        # 3. FIX-DB-03: API response includes audit_id
        audit_id_a1 = js_scan1.get("audit_id") or js_scan1.get("id")
        has_audit_id = bool(audit_id_a1 and len(str(audit_id_a1)) >= 10)
        record_test("FIX-DB-03", "SCAN_DB", "API response returns audit_id UUID for saved scan", has_audit_id, audit_id_a1, "Valid UUID string")

        # 4. FIX-DB-04: Anonymous scan does NOT write to 'audits' table
        with get_db_cursor() as cur:
            cur.execute("SELECT COUNT(*) as cnt FROM audits;")
            before_anon = cur.fetchone()["cnt"]

        st_anon, js_anon, _, _ = run_http_request(
            f"{base_url}/api/audit/run",
            method="POST",
            body={"target": "Apex Dental Clinic"}
        )
        with get_db_cursor() as cur:
            cur.execute("SELECT COUNT(*) as cnt FROM audits;")
            after_anon = cur.fetchone()["cnt"]
        anon_did_not_write = (st_anon == 200) and (before_anon == after_anon)
        record_test("FIX-DB-04", "SCAN_DB", "Anonymous scan succeeds without persisting to audits table", anon_did_not_write, f"Delta: {after_anon - before_anon}", "0 delta")

        # 5. FIX-DB-05: GET /api/audit/<audit_id> returns saved audit for owner
        st_get_aud, js_get_aud, _, _ = run_http_request(
            f"{base_url}/api/audit/{audit_id_a1}",
            method="GET",
            headers={"Cookie": f"session_token={token_a}"}
        )
        aud_matches = st_get_aud == 200 and js_get_aud and js_get_aud.get("audit", {}).get("domain") == "example.com"
        record_test("FIX-DB-05", "SCAN_DB", "GET /api/audit/<audit_id> returns saved audit to owner", aud_matches, st_get_aud, 200)

        # =====================================================================
        # GROUP 2: PLAN LIMIT ENFORCEMENT (5 Tests)
        # =====================================================================
        print("\n--- GROUP 2: PLAN LIMIT ENFORCEMENT ---")

        # 6. FIX-LIM-01: Free user can run audit 1 of 2 (usage_count becomes 1)
        st_me1, js_me1, _, _ = run_http_request(
            f"{base_url}/api/auth/me",
            method="GET",
            headers={"Cookie": f"session_token={token_a}"}
        )
        used_after_1 = js_me1.get("usage", {}).get("used")
        if used_after_1 is None:
            used_after_1 = js_me1.get("usage_count")
        record_test("FIX-LIM-01", "PLAN_LIMITS", "Audit 1 of 2 consumed and recorded in usage count", used_after_1 == 1, used_after_1, 1)

        # 7. FIX-LIM-02: Free user can run audit 2 of 2 (usage_count becomes 2)
        st_scan2, js_scan2, _, _ = run_http_request(
            f"{base_url}/api/audit/run",
            method="POST",
            body={"target": "example.org"},
            headers={"Cookie": f"session_token={token_a}"}
        )
        audit_id_a2 = js_scan2.get("audit_id") or js_scan2.get("id")
        st_me2, js_me2, _, _ = run_http_request(
            f"{base_url}/api/auth/me",
            method="GET",
            headers={"Cookie": f"session_token={token_a}"}
        )
        used_after_2 = js_me2.get("usage", {}).get("used")
        if used_after_2 is None:
            used_after_2 = js_me2.get("usage_count")
        record_test("FIX-LIM-02", "PLAN_LIMITS", "Audit 2 of 2 succeeds and updates usage count to 2", st_scan2 == 200 and used_after_2 == 2, used_after_2, 2)

        # 8. FIX-LIM-03: Free user 3rd audit attempt blocked with HTTP 403
        st_scan3, js_scan3, _, _ = run_http_request(
            f"{base_url}/api/audit/run",
            method="POST",
            body={"target": "example.net"},
            headers={"Cookie": f"session_token={token_a}"}
        )
        record_test("FIX-LIM-03", "PLAN_LIMITS", "3rd audit attempt on Free plan is blocked with HTTP 403 Forbidden", st_scan3 == 403, st_scan3, 403)

        # 9. FIX-LIM-04: 403 response includes usage_limit_reached error and upgrade info
        has_limit_err = bool(js_scan3 and js_scan3.get("error") == "usage_limit_reached" and "upgrade_url" in js_scan3)
        record_test("FIX-LIM-04", "PLAN_LIMITS", "403 response returns usage_limit_reached and upgrade details", has_limit_err, js_scan3.get("error"), "usage_limit_reached")

        # 10. FIX-LIM-05: Blocked audit does NOT increment usage or call scanner
        st_me3, js_me3, _, _ = run_http_request(
            f"{base_url}/api/auth/me",
            method="GET",
            headers={"Cookie": f"session_token={token_a}"}
        )
        used_after_blocked = js_me3.get("usage", {}).get("used")
        with get_db_cursor() as cur:
            cur.execute("SELECT COUNT(*) as cnt FROM audits WHERE domain LIKE '%example.net%';")
            blocked_in_db = cur.fetchone()["cnt"]
        blocked_not_counted = (used_after_blocked == 2) and (blocked_in_db == 0)
        record_test("FIX-LIM-05", "PLAN_LIMITS", "Blocked audit does not mutate usage count or write to database", blocked_not_counted, f"Used: {used_after_blocked}, In DB: {blocked_in_db}", "Used: 2, In DB: 0")

        # =====================================================================
        # GROUP 3: MULTI-TENANT ISOLATION (4 Tests)
        # =====================================================================
        print("\n--- GROUP 3: MULTI-TENANT ISOLATION ---")

        # 11. FIX-TEN-01: User B cannot access User A's audit via GET /api/audit/<audit_id> (404)
        st_cross_aud, _, _, _ = run_http_request(
            f"{base_url}/api/audit/{audit_id_a1}",
            method="GET",
            headers={"Cookie": f"session_token={token_b}"}
        )
        record_test("FIX-TEN-01", "MULTI_TENANT", "User B is denied access to User A's audit (HTTP 404 masked)", st_cross_aud == 404, st_cross_aud, 404)

        # 12. FIX-TEN-02: User B cannot download User A's PDF report (404)
        st_cross_pdf, _, _, _ = run_http_request(
            f"{base_url}/api/audit/{audit_id_a1}/pdf",
            method="GET",
            headers={"Cookie": f"session_token={token_b}"}
        )
        record_test("FIX-TEN-02", "MULTI_TENANT", "User B is denied download of User A's PDF (HTTP 404 masked)", st_cross_pdf == 404, st_cross_pdf, 404)

        # 13. FIX-TEN-03: User B cannot view User A's HTML report at /report/<audit_id> (404)
        st_cross_rep, _, _, _ = run_http_request(
            f"{base_url}/report/{audit_id_a1}",
            method="GET",
            headers={"Cookie": f"session_token={token_b}"}
        )
        record_test("FIX-TEN-03", "MULTI_TENANT", "User B cannot view User A's HTML report at /report/<audit_id> (404)", st_cross_rep == 404, st_cross_rep, 404)

        # 14. FIX-TEN-04: Unauthenticated request to /api/audit/<audit_id> returns 401
        st_unauth_aud, _, _, _ = run_http_request(
            f"{base_url}/api/audit/{audit_id_a1}",
            method="GET"
        )
        record_test("FIX-TEN-04", "MULTI_TENANT", "Unauthenticated request to /api/audit/<audit_id> returns 401", st_unauth_aud == 401, st_unauth_aud, 401)

        # =====================================================================
        # GROUP 4: PDF & REPORT ENDPOINTS (4 Tests)
        # =====================================================================
        print("\n--- GROUP 4: PDF & REPORT ENDPOINTS ---")

        # 15. FIX-PDF-01: Free user requesting PDF returns 403 (feature_requires_upgrade)
        st_pdf_free, js_pdf_free, _, _ = run_http_request(
            f"{base_url}/api/audit/{audit_id_a1}/pdf",
            method="GET",
            headers={"Cookie": f"session_token={token_a}"}
        )
        free_blocked = st_pdf_free == 403 and js_pdf_free and js_pdf_free.get("error") == "feature_requires_upgrade"
        record_test("FIX-PDF-01", "PDF_REPORT", "Free user PDF download returns HTTP 403 feature_requires_upgrade", free_blocked, st_pdf_free, 403)

        # Upgrade User A workspace to Pro plan in DB for testing Pro PDF download
        with get_db_cursor(commit=True) as cur:
            cur.execute("""
                UPDATE workspaces SET plan = 'pro'
                WHERE owner_id = %s;
            """, (user_a_id,))

        # 16. FIX-PDF-02: Paid user (pro) requesting PDF returns 200 + valid PDF binary (%PDF-1.4)
        st_pdf_pro, _, bin_pdf_pro, hdrs_pdf_pro = run_http_request(
            f"{base_url}/api/audit/{audit_id_a1}/pdf",
            method="GET",
            headers={"Cookie": f"session_token={token_a}"}
        )
        is_valid_pdf = st_pdf_pro == 200 and bin_pdf_pro.startswith(b"%PDF-1.4") and b"%%EOF" in bin_pdf_pro
        record_test("FIX-PDF-02", "PDF_REPORT", "Paid Pro user downloads valid self-contained PDF 1.4 binary", is_valid_pdf, f"Status: {st_pdf_pro}, Len: {len(bin_pdf_pro)}", "200 + %PDF-1.4 header")

        # 17. FIX-PDF-03: PDF response headers include application/pdf and Content-Disposition
        ct_pdf = hdrs_pdf_pro.get("Content-Type") or hdrs_pdf_pro.get("content-type") or ""
        cd_pdf = hdrs_pdf_pro.get("Content-Disposition") or hdrs_pdf_pro.get("content-disposition") or ""
        valid_pdf_hdrs = "application/pdf" in ct_pdf and "attachment" in cd_pdf and "leakgrader-report" in cd_pdf
        record_test("FIX-PDF-03", "PDF_REPORT", "PDF response headers include application/pdf and Content-Disposition", valid_pdf_hdrs, f"CT: {ct_pdf}, CD: {cd_pdf[:30]}", "application/pdf + attachment")

        # 18. FIX-REP-01: GET /report/<audit_id> returns 200 + valid HTML dossier for owner
        st_rep_html, _, bin_rep_html, hdrs_rep_html = run_http_request(
            f"{base_url}/report/{audit_id_a1}",
            method="GET",
            headers={"Cookie": f"session_token={token_a}"}
        )
        html_str = bin_rep_html.decode("utf-8", errors="ignore") if bin_rep_html else ""
        valid_rep_html = st_rep_html == 200 and "<!DOCTYPE html>" in html_str and "example.com" in html_str and "15-Point" in html_str
        record_test("FIX-REP-01", "PDF_REPORT", "GET /report/<audit_id> renders printable HTML dossier for owner", valid_rep_html, st_rep_html, 200)

        # =====================================================================
        # GROUP 5: RECENT AUDITS & DASHBOARD API (3 Tests)
        # =====================================================================
        print("\n--- GROUP 5: RECENT AUDITS & DASHBOARD API ---")

        # 19. FIX-DASH-01: GET /api/auth/me includes recent_audits array
        st_me_auds, js_me_auds, _, _ = run_http_request(
            f"{base_url}/api/auth/me",
            method="GET",
            headers={"Cookie": f"session_token={token_a}"}
        )
        rec_auds = js_me_auds.get("recent_audits", [])
        has_recent = st_me_auds == 200 and isinstance(rec_auds, list) and len(rec_auds) >= 2
        record_test("FIX-DASH-01", "DASHBOARD_API", "GET /api/auth/me returns recent_audits array with stored scans", has_recent, len(rec_auds), ">= 2 audits")

        # 20. FIX-DASH-02: recent_audits contains correct fields (id, domain, score, created_at)
        first_aud = rec_auds[0] if rec_auds else {}
        req_fields = all(k in first_aud for k in ["id", "domain", "score", "created_at"])
        record_test("FIX-DASH-02", "DASHBOARD_API", "Recent audits list contains id, domain, score, and created_at fields", req_fields, list(first_aud.keys()), "id, domain, score, created_at")

        # 21. FIX-DASH-03: GET /api/auth/me includes plan and usage: { used, limit }
        has_plan_and_usage = (
            "plan" in js_me_auds and
            "usage" in js_me_auds and
            "used" in js_me_auds["usage"] and
            "limit" in js_me_auds["usage"]
        )
        record_test("FIX-DASH-03", "DASHBOARD_API", "GET /api/auth/me includes plan and structured usage object", has_plan_and_usage, js_me_auds.get("usage"), "{'used': N, 'limit': N}")

        # =====================================================================
        # GROUP 6: ANALYTICS EVENTS VERIFICATION (2 Tests)
        # =====================================================================
        print("\n--- GROUP 6: ANALYTICS EVENTS & DASHBOARD UI ---")

        # 22. FIX-GA-01: web/app.js contains guarded gtag events
        app_js_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "web", "app.js")
        with open(app_js_path, "r", encoding="utf-8") as f:
            app_js_content = f.read()

        ga_events = ["audit_start", "audit_complete", "sign_up_click", "plan_limit_reached", "upgrade_click"]
        all_events_wired = all(ev in app_js_content for ev in ga_events) and "gtag(" in app_js_content
        record_test("FIX-GA-01", "ANALYTICS", "web/app.js contains all 5 guarded gtag event tracking triggers", all_events_wired, all_events_wired, True)

        # 23. FIX-GA-02: web/dashboard.html contains real audit table rendering with /report/ and /pdf actions
        dash_html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "web", "dashboard.html")
        with open(dash_html_path, "r", encoding="utf-8") as f:
            dash_html_content = f.read()

        dash_features = (
            "/report/" in dash_html_content and
            "/api/audit/" in dash_html_content and
            "limitBanner" in dash_html_content and
            "dashScanForm" in dash_html_content
        )
        record_test("FIX-GA-02", "DASHBOARD_UI", "web/dashboard.html wires real audits, limit banner, quick scan, and report/pdf actions", dash_features, dash_features, True)

        # =====================================================================
        # GROUP 7: REGRESSION CHECKS (2 Tests)
        # =====================================================================
        print("\n--- GROUP 7: REGRESSION CHECKS ---")

        # 24. FIX-REG-01: SSRF protection on /api/audit/run still rejects 127.0.0.1 (400)
        st_ssrf, _, _, _ = run_http_request(
            f"{base_url}/api/audit/run",
            method="POST",
            body={"target": "http://127.0.0.1:8080/internal"}
        )
        record_test("FIX-REG-01", "REGRESSION", "SSRF protection on /api/audit/run rejects loopback with HTTP 400", st_ssrf == 400, st_ssrf, 400)

        # 25. FIX-REG-02: Admin routes still return 404 in lockdown mode
        st_admin, _, _, _ = run_http_request(
            f"{base_url}/founder",
            method="GET"
        )
        record_test("FIX-REG-02", "REGRESSION", "Administrative route /founder remains masked with HTTP 404 Not Found", st_admin == 404, st_admin, 404)

    finally:
        server_proc.terminate()
        try:
            server_proc.wait(timeout=3)
        except Exception:
            server_proc.kill()
        if os.path.exists(test_db_file):
            try:
                os.remove(test_db_file)
            except Exception:
                pass

    print("\n" + "=" * 80)
    passed_count = sum(1 for t in TEST_RESULTS if t["passed"])
    total_count = len(TEST_RESULTS)
    pass_pct = (passed_count / total_count) * 100.0 if total_count > 0 else 0.0
    print(f"SPRINT 1.5 FIXES SUITE SUMMARY: {passed_count}/{total_count} TESTS PASSED ({pass_pct:.1f}%)")
    print("=" * 80)

    # Save raw test results
    results_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "SPRINT_1_5_TEST_RESULTS_RAW.json")
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total": total_count,
            "passed": passed_count,
            "failed": total_count - passed_count,
            "pass_rate": pass_pct,
            "tests": TEST_RESULTS
        }, f, indent=2)
    print(f"Results written to {results_path}")

    if passed_count != total_count:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
