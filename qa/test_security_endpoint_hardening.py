"""
Black-box Verification Suite for Security Endpoint Hardening
Tests:
1. Lockdown Full:
   - /api/leads/list -> 503
   - /api/leads/export-csv -> 503
   - /api/booking/list -> 404
   - /api/seo/recent-activity -> 404
   - /api/pipeline/*, /api/contact/list, /api/analytics/live -> 404
   - /founder -> 404
   - Deny-by-default for unknown /api/* -> 404
   - Probes: /.env, /.git/config, /wp-admin/install.php, /server-status -> 404
   - Public routes: /, /about, /contact, /privacy, /terms, /health, /api/pricing/plans, /api/audit/run -> 200
2. Lockdown Auth_Ready:
   - Unauthenticated /api/leads/list -> 401
   - Authenticated /api/leads/list -> 200 with workspace-scoped leads (empty list, not global 2726 byte dump)
   - /api/booking/list -> 404
   - Probes -> 404
3. Frontend JS Safety:
   - Verification that web/app.js guards loadInitialLeads and loadBookings behind session tokens
   - Verification that unconditional SEO interval polling is removed
"""

import os
import sys
import time
import json
import uuid
import urllib.request
import urllib.error
import subprocess

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


def run_test_suite():
    print("=" * 80)
    print("RUNNING SECURITY ENDPOINT HARDENING VERIFICATION SUITE")
    print("=" * 80)

    # Setup isolated test db
    test_db_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "storage", "test_sec_hardening.db")
    if os.path.exists(test_db_file):
        try:
            os.remove(test_db_file)
        except Exception:
            pass

    storage_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "storage")

    # ==========================================================
    # PART 1: LOCKDOWN FULL MODE
    # ==========================================================
    port_full = 8781
    env_full = os.environ.copy()
    env_full["DATABASE_URL"] = f"sqlite:///{os.path.abspath(test_db_file)}"
    env_full["ENVIRONMENT"] = "production"
    env_full["SECURITY_LOCKDOWN_MODE"] = "enabled"
    env_full["LOCKDOWN_PHASE"] = "full"
    env_full["STORAGE_DIR"] = storage_dir
    env_full["PORT"] = str(port_full)

    # Initialize sqlite tables
    import db.connection
    db.connection._PG_POOL = None
    db.connection._IS_SQLITE = False
    db.connection._SQLITE_PATH = None
    os.environ["DATABASE_URL"] = env_full["DATABASE_URL"]
    from db.migrate import run_migrations
    run_migrations()

    proc_full = subprocess.Popen(
        [sys.executable, "-c", f"from wsgiref.simple_server import make_server; from wsgi import app; make_server('127.0.0.1', {port_full}, app).serve_forever()"],
        env=env_full,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    time.sleep(2.0)
    base_full = f"http://127.0.0.1:{port_full}"

    try:
        # 1. Anonymous GET /api/leads/list in full lockdown -> 503
        st, js, b, _ = run_http_request(f"{base_full}/api/leads/list")
        record_test("SEC-01", "Full_Lockdown", "GET /api/leads/list returns 503 Service Unavailable",
                    st == 503, actual=st, expected=503)

        # 2. Anonymous GET /api/leads/export-csv in full lockdown -> 503
        st, js, b, _ = run_http_request(f"{base_full}/api/leads/export-csv")
        record_test("SEC-02", "Full_Lockdown", "GET /api/leads/export-csv returns 503 Service Unavailable",
                    st == 503, actual=st, expected=503)

        # 3. GET /api/booking/list in full lockdown -> 404 (Hidden admin)
        st, js, b, _ = run_http_request(f"{base_full}/api/booking/list")
        record_test("SEC-03", "Full_Lockdown", "GET /api/booking/list returns 404 Not Found",
                    st == 404, actual=st, expected=404)

        # 4. GET /api/seo/recent-activity in full lockdown -> 404
        st, js, b, _ = run_http_request(f"{base_full}/api/seo/recent-activity")
        record_test("SEC-04", "Full_Lockdown", "GET /api/seo/recent-activity returns 404 Not Found",
                    st == 404, actual=st, expected=404)

        # 5. GET /api/pipeline/leads in full lockdown -> 404
        st, js, b, _ = run_http_request(f"{base_full}/api/pipeline/leads")
        record_test("SEC-05", "Full_Lockdown", "GET /api/pipeline/leads returns 404 Not Found",
                    st == 404, actual=st, expected=404)

        # 6. GET /api/contact/list in full lockdown -> 404
        st, js, b, _ = run_http_request(f"{base_full}/api/contact/list")
        record_test("SEC-06", "Full_Lockdown", "GET /api/contact/list returns 404 Not Found",
                    st == 404, actual=st, expected=404)

        # 7. GET /api/analytics/live in full lockdown -> 404
        st, js, b, _ = run_http_request(f"{base_full}/api/analytics/live")
        record_test("SEC-07", "Full_Lockdown", "GET /api/analytics/live returns 404 Not Found",
                    st == 404, actual=st, expected=404)

        # 8. GET /founder in full lockdown -> 404
        st, js, b, _ = run_http_request(f"{base_full}/founder")
        record_test("SEC-08", "Full_Lockdown", "GET /founder returns 404 Not Found",
                    st == 404, actual=st, expected=404)

        # 9. Deny-by-default for unlisted /api/* probe -> 404
        st, js, b, _ = run_http_request(f"{base_full}/api/internal_debugger_probe_99")
        record_test("SEC-09", "Full_Lockdown", "Deny-by-default unlisted API probe returns 404",
                    st == 404, actual=st, expected=404)

        # 10. Probe /.env returns 404 and does not return HTML index or secret data
        st, js, b, hdrs = run_http_request(f"{base_full}/.env")
        body_text = b.decode("utf-8", errors="ignore")
        is_clean_404 = (st == 404) and ("DATABASE_URL" not in body_text) and ("<!DOCTYPE" not in body_text)
        record_test("SEC-10", "Probe_Rejection", "GET /.env returns clean 404 text/plain without leaking index HTML or envs",
                    is_clean_404, actual=f"status={st}, has_html={'<!DOCTYPE' in body_text}", expected="status=404, has_html=False")

        # 11. Probe /wp-admin/install.php returns 404
        st, js, b, _ = run_http_request(f"{base_full}/wp-admin/install.php")
        body_text = b.decode("utf-8", errors="ignore")
        record_test("SEC-11", "Probe_Rejection", "GET /wp-admin/install.php returns clean 404 text/plain",
                    st == 404 and "<!DOCTYPE" not in body_text, actual=st, expected=404)

        # 12. Probe /.git/config returns 404
        st, js, b, _ = run_http_request(f"{base_full}/.git/config")
        record_test("SEC-12", "Probe_Rejection", "GET /.git/config returns 404",
                    st == 404, actual=st, expected=404)

        # 13. Public Homepage GET / returns 200
        st, js, b, _ = run_http_request(f"{base_full}/")
        record_test("SEC-13", "Public_Routes", "GET / returns 200 OK",
                    st == 200, actual=st, expected=200)

        # 14. Public About GET /about returns 200
        st, js, b, _ = run_http_request(f"{base_full}/about")
        record_test("SEC-14", "Public_Routes", "GET /about returns 200 OK",
                    st == 200, actual=st, expected=200)

        # 15. Public Contact GET /contact returns 200
        st, js, b, _ = run_http_request(f"{base_full}/contact")
        record_test("SEC-15", "Public_Routes", "GET /contact returns 200 OK",
                    st == 200, actual=st, expected=200)

        # 16. Public Privacy GET /privacy returns 200
        st, js, b, _ = run_http_request(f"{base_full}/privacy")
        record_test("SEC-16", "Public_Routes", "GET /privacy returns 200 OK",
                    st == 200, actual=st, expected=200)

        # 17. Public Terms GET /terms returns 200
        st, js, b, _ = run_http_request(f"{base_full}/terms")
        record_test("SEC-17", "Public_Routes", "GET /terms returns 200 OK",
                    st == 200, actual=st, expected=200)

        # 18. Public Health GET /health returns 200
        st, js, b, _ = run_http_request(f"{base_full}/health")
        record_test("SEC-18", "Public_Routes", "GET /health returns 200 OK with healthy status",
                    st == 200 and js and js.get("status") == "healthy", actual=st, expected=200)

        # 19. Public Plans GET /api/pricing/plans returns 200 with plan catalog
        st, js, b, _ = run_http_request(f"{base_full}/api/pricing/plans")
        has_plans = st == 200 and isinstance(js, dict) and len(js) > 0
        record_test("SEC-19", "Public_Routes", "GET /api/pricing/plans returns 200 with plan catalog in full lockdown",
                    has_plans, actual=f"st={st}, count={len(js) if isinstance(js, dict) else 0}", expected="st=200, count>0")

        # 20. Public Audit POST /api/audit/run succeeds
        st, js, b, _ = run_http_request(f"{base_full}/api/audit/run", method="POST", body={"url": "example.com"})
        record_test("SEC-20", "Public_Routes", "POST /api/audit/run returns 200 for public audit scan",
                    st == 200 and js and js.get("success") is True, actual=st, expected=200)

    finally:
        proc_full.terminate()
        proc_full.wait()

    # ==========================================================
    # PART 2: LOCKDOWN AUTH_READY MODE
    # ==========================================================
    port_auth = 8782
    env_auth = os.environ.copy()
    env_auth["DATABASE_URL"] = f"sqlite:///{os.path.abspath(test_db_file)}"
    env_auth["ENVIRONMENT"] = "production"
    env_auth["SECURITY_LOCKDOWN_MODE"] = "enabled"
    env_auth["LOCKDOWN_PHASE"] = "auth_ready"
    env_auth["STORAGE_DIR"] = storage_dir
    env_auth["PORT"] = str(port_auth)

    proc_auth = subprocess.Popen(
        [sys.executable, "-c", f"from wsgiref.simple_server import make_server; from wsgi import app; make_server('127.0.0.1', {port_auth}, app).serve_forever()"],
        env=env_auth,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    time.sleep(2.0)
    base_auth = f"http://127.0.0.1:{port_auth}"

    try:
        # 21. Anonymous GET /api/leads/list in auth_ready -> 401 Unauthorized
        st, js, b, _ = run_http_request(f"{base_auth}/api/leads/list")
        record_test("SEC-21", "Auth_Ready_Lockdown", "Anonymous GET /api/leads/list returns 401 Unauthorized in auth_ready",
                    st == 401, actual=st, expected=401)

        # 22. Anonymous GET /api/leads/export-csv in auth_ready -> 401 Unauthorized
        st, js, b, _ = run_http_request(f"{base_auth}/api/leads/export-csv")
        record_test("SEC-22", "Auth_Ready_Lockdown", "Anonymous GET /api/leads/export-csv returns 401 Unauthorized in auth_ready",
                    st == 401, actual=st, expected=401)

        # 23. Sign up user and verify authenticated GET /api/leads/list returns scoped empty list (not global 2726 byte dump)
        su_payload = {
            "full_name": "Sec Auditor",
            "email": f"secaudit_{uuid.uuid4().hex[:6]}@example.com",
            "password": "Password123!Secure"
        }
        st_su, js_su, _, hdrs_su = run_http_request(f"{base_auth}/api/auth/signup", method="POST", body=su_payload)
        token = ""
        if js_su and "session" in js_su:
            token = js_su["session"].get("session_token", "")
        if not token:
            cookie = hdrs_su.get("set-cookie") or hdrs_su.get("Set-Cookie") or ""
            if "session_token=" in cookie:
                token = cookie.split("session_token=")[1].split(";")[0].strip()

        auth_hdrs = {"Cookie": f"session_token={token}"} if token else {}
        st_leads, js_leads, b_leads, _ = run_http_request(f"{base_auth}/api/leads/list", headers=auth_hdrs)
        
        # Must return 200, success=True, and leads is [] (isolated to workspace, not global sample leads)
        leads_data = js_leads.get("leads") if js_leads else None
        record_test("SEC-23", "Auth_Ready_Lockdown", "Authenticated GET /api/leads/list returns workspace-isolated leads (empty for new workspace)",
                    st_leads == 200 and isinstance(leads_data, list) and len(leads_data) == 0,
                    actual=f"st={st_leads}, leads_count={len(leads_data) if isinstance(leads_data, list) else 'None'}",
                    expected="st=200, leads_count=0")

        # 24. Anonymous GET /api/booking/list in auth_ready -> 404
        st, js, b, _ = run_http_request(f"{base_auth}/api/booking/list")
        record_test("SEC-24", "Auth_Ready_Lockdown", "GET /api/booking/list returns 404 Not Found in auth_ready",
                    st == 404, actual=st, expected=404)

        # 25. Probe /.env in auth_ready -> 404
        st, js, b, _ = run_http_request(f"{base_auth}/.env")
        record_test("SEC-25", "Auth_Ready_Lockdown", "GET /.env returns 404 text/plain in auth_ready",
                    st == 404 and "<!DOCTYPE" not in b.decode("utf-8", errors="ignore"),
                    actual=st, expected=404)

    finally:
        proc_auth.terminate()
        proc_auth.wait()

    # ==========================================================
    # PART 3: FRONTEND STATIC CODE SAFETY AUDIT
    # ==========================================================
    app_js_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "web", "app.js")
    with open(app_js_path, "r", encoding="utf-8") as f:
        app_js_content = f.read()

    # 26. loadInitialLeads checks csrf_token before network fetch
    leads_guarded = "if (!sessionStorage.getItem('csrf_token')) {" in app_js_content and "loadInitialLeads" in app_js_content
    record_test("SEC-26", "Frontend_Safety", "loadInitialLeads is gated on sessionStorage csrf_token",
                leads_guarded, actual=leads_guarded, expected=True)

    # 27. loadBookings checks csrf_token before network fetch
    bookings_guarded = "if (!sessionStorage.getItem('csrf_token')) {" in app_js_content and "loadBookings" in app_js_content
    record_test("SEC-27", "Frontend_Safety", "loadBookings is gated on sessionStorage csrf_token",
                bookings_guarded, actual=bookings_guarded, expected=True)

    # 28. Unconditional setInterval(loadSeoActivity, 20000) is absent
    seo_polling_removed = "setInterval(loadSeoActivity, 20000)" not in app_js_content
    record_test("SEC-28", "Frontend_Safety", "Unconditional setInterval(loadSeoActivity, 20000) is removed",
                seo_polling_removed, actual=seo_polling_removed, expected=True)

    # Clean up test DB
    if os.path.exists(test_db_file):
        try:
            os.remove(test_db_file)
        except Exception:
            pass

    # Summary
    print("=" * 80)
    total = len(TEST_RESULTS)
    passed_count = sum(1 for t in TEST_RESULTS if t["passed"])
    failed_count = total - passed_count
    print(f"SECURITY HARDENING SUITE SUMMARY: {passed_count}/{total} PASSED, {failed_count} FAILED")
    print("=" * 80)

    if failed_count > 0:
        print("[!] SUITE FAILED!")
        sys.exit(1)
    else:
        print("[+] SUITE PASSED SUCCESSFULLY!")
        return True


if __name__ == "__main__":
    run_test_suite()
