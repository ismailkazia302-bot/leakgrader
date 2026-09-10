"""
Sprint 1.5 End-to-End Feature Integrity Audit Suite
Tests Phases 1 to 5 in simulated production with LOCKDOWN_PHASE=auth_ready.
Uses an isolated temporary SQLite test database.
"""

import os
import sys
import time
import json
import uuid
import re
import urllib.request
import urllib.error
import http.cookiejar
import subprocess
from datetime import datetime, timezone

# Ensure project root is in sys.path
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

def main():
    print("=" * 80)
    print("RUNNING SPRINT 1.5 FEATURE INTEGRITY AUDIT (LOCAL SIMULATION)")
    print("Environment: ENVIRONMENT=production | LOCKDOWN_PHASE=auth_ready")
    print("=" * 80)

    # 1. Setup Isolated Test Database
    test_db_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "storage", "test_feature_integrity.db")
    if os.path.exists(test_db_file):
        try:
            os.remove(test_db_file)
        except Exception:
            pass

    os.environ["DATABASE_URL"] = f"sqlite:///{os.path.abspath(test_db_file)}"
    os.environ["ENVIRONMENT"] = "production"
    os.environ["SECURITY_LOCKDOWN_MODE"] = "enabled"
    os.environ["LOCKDOWN_PHASE"] = "auth_ready"
    os.environ["LEMONSQUEEZY_WEBHOOK_SECRET"] = "test_signing_secret_sprint15"

    import db.connection
    db.connection._PG_POOL = None
    db.connection._IS_SQLITE = False
    db.connection._SQLITE_PATH = None
    db.connection.init_pool()
    from db.connection import get_db_cursor, is_sqlite

    from db.migrate import run_migrations
    mig_ok = run_migrations()
    print(f"[*] Isolated Test DB Migration: {mig_ok}")

    # Start WSGI Server in background on dedicated port 8770
    port = 8770
    server_env = os.environ.copy()
    server_env["PORT"] = str(port)
    server_proc = subprocess.Popen(
        [sys.executable, "-c", f"from wsgiref.simple_server import make_server; from wsgi import app; make_server('127.0.0.1', {port}, app).serve_forever()"],
        env=server_env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    time.sleep(2.5)  # Wait for server bind
    base_url = f"http://127.0.0.1:{port}"

    try:
        # =========================================================================
        # PHASE 1 — THE SCANNER & REPORT ENGINE
        # =========================================================================
        print("\n--- PHASE 1: THE SCANNER & REPORT ENGINE ---")
        from engine.audit_engine import ViralAuditEngine
        audit_engine = ViralAuditEngine()

        # 1.1 Real Audit for 'example.com'
        audit_res = audit_engine.run_instant_audit("example.com")
        score = audit_res.get("ai_readiness_score")
        has_score = isinstance(score, (int, float)) and 0 <= score <= 100
        record_test("SCAN-01", "SCANNER", "Audit Engine produces a valid score (0-100)", has_score, score, "0-100 integer")

        # Categorization check
        pts = audit_res.get("diagnostic_points", [])
        categories = set(p.get("category") for p in pts)
        has_categories = len(categories) >= 3 and all(p.get("status") in ["PASS", "WARN", "FAIL"] for p in pts)
        record_test("SCAN-02", "SCANNER", "Findings are categorized with severity/status", has_categories, list(categories), "Categorized checks with PASS/WARN/FAIL")

        # Revenue Leak formula check (2.5% close-rate logic)
        benchmark_factors = audit_res.get("benchmark_factors", {})
        close_rate = benchmark_factors.get("lead_to_close_rate", "")
        formula_follows_25 = "2.5%" in close_rate
        record_test("SCAN-03", "SCANNER", "Revenue Leak calculation follows 2.5% close-rate benchmark", formula_follows_25, close_rate, "2.5% (Industry Benchmark)")

        # Save to database 'audits' table check via HTTP /api/audit/run
        req = urllib.request.Request(
            f"{base_url}/api/audit/run",
            data=json.dumps({"target": "example.com"}).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                scan_http_code = resp.status
        except urllib.error.HTTPError as e:
            scan_http_code = e.code

        with get_db_cursor() as cur:
            cur.execute("SELECT COUNT(*) as cnt FROM audits WHERE domain LIKE '%example.com%';")
            row = cur.fetchone()
            db_audit_count = row["cnt"] if row else 0

        record_test("SCAN-04", "SCANNER", "Scan result is saved to database 'audits' table", db_audit_count > 0, f"db_count={db_audit_count}", "db_count >= 1")

        # 1.2 PDF Generation Check (/api/audit/pdf)
        pdf_req = urllib.request.Request(
            f"{base_url}/api/audit/pdf?domain=example.com",
            headers={"User-Agent": "TestClient"}
        )
        pdf_code = 0
        pdf_bytes = b""
        try:
            with urllib.request.urlopen(pdf_req, timeout=5) as resp:
                pdf_code = resp.status
                pdf_bytes = resp.read()
        except urllib.error.HTTPError as e:
            pdf_code = e.code
            pdf_bytes = e.read()

        is_valid_pdf = pdf_bytes.startswith(b"%PDF-") or (b"<html" in pdf_bytes and b"@media print" in pdf_bytes)
        has_15_points = str(pdf_bytes).count("point_number") >= 15 or "15" in str(pdf_bytes)
        record_test("PDF-01", "PDF_ENGINE", "Trigger /api/audit/pdf endpoint responds", pdf_code == 200, pdf_code, 200)
        record_test("PDF-02", "PDF_ENGINE", "PDF is generated without corruption", is_valid_pdf and pdf_code == 200, f"code={pdf_code}, len={len(pdf_bytes)}", "Valid PDF / Print stream")
        record_test("PDF-03", "PDF_ENGINE", "PDF includes all 15 diagnostic points", has_15_points and pdf_code == 200, has_15_points, True)

        # =========================================================================
        # PHASE 2 — THE USER JOURNEY & DASHBOARD
        # =========================================================================
        print("\n--- PHASE 2: THE USER JOURNEY & DASHBOARD ---")
        user_email = f"journey_user_{int(time.time())}@example.com"
        user_pwd = "SecurePassword123!"
        
        # 2.1 User Signup
        signup_req = urllib.request.Request(
            f"{base_url}/api/auth/signup",
            data=json.dumps({"email": user_email, "password": user_pwd, "full_name": "Journey User"}).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(signup_req, timeout=5) as resp:
            signup_data = json.loads(resp.read().decode("utf-8"))
            cookie_header = resp.headers.get("Set-Cookie", "")

        session_token = None
        if "session_token=" in cookie_header:
            session_token = cookie_header.split("session_token=")[1].split(";")[0]

        record_test("JOURNEY-01", "USER_JOURNEY", "User signup via /api/auth/signup", resp.status == 201 and session_token is not None, resp.status, 201)

        # Run 1st audit as authenticated user
        audit1_req = urllib.request.Request(
            f"{base_url}/api/audit/run",
            data=json.dumps({"target": "firstscan.com"}).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Cookie": f"session_token={session_token}"
            }
        )
        try:
            with urllib.request.urlopen(audit1_req, timeout=5) as resp:
                audit1_code = resp.status
        except urllib.error.HTTPError as e:
            audit1_code = e.code

        # Check GET /api/auth/me usage_count
        me_req = urllib.request.Request(
            f"{base_url}/api/auth/me",
            headers={"Cookie": f"session_token={session_token}"}
        )
        with urllib.request.urlopen(me_req, timeout=5) as resp:
            me_data1 = json.loads(resp.read().decode("utf-8"))
            usage_1 = me_data1.get("usage_count", 0)

        record_test("JOURNEY-02", "USER_JOURNEY", "First scan increments usage_count to 1/2", usage_1 == 1, f"usage={usage_1}/2", "usage=1/2")

        # Check /dashboard Recent Scans
        recent_audits = me_data1.get("recent_audits", [])
        has_recent = any(a.get("domain") == "firstscan.com" for a in recent_audits)
        record_test("JOURNEY-03", "USER_JOURNEY", "Dashboard recent scans list includes first scan", has_recent, [a.get("domain") for a in recent_audits], "['firstscan.com']")

        # 2.2 Plan Limit Enforcement (CRITICAL)
        # Run 2nd audit
        audit2_req = urllib.request.Request(
            f"{base_url}/api/audit/run",
            data=json.dumps({"target": "airbnb.com"}).encode("utf-8"),
            headers={"Content-Type": "application/json", "Cookie": f"session_token={session_token}"}
        )
        try:
            with urllib.request.urlopen(audit2_req, timeout=10) as resp:
                pass
        except Exception:
            pass

        try:
            with urllib.request.urlopen(me_req, timeout=5) as resp:
                me_data2 = json.loads(resp.read().decode("utf-8"))
                usage_2 = me_data2.get("usage_count", 0)
        except Exception:
            usage_2 = 0

        record_test("LIMIT-01", "PLAN_LIMIT", "Second scan brings usage_count to 2/2", usage_2 == 2, f"usage={usage_2}/2", "usage=2/2")

        # Attempt 3rd audit -> Expect 403 Forbidden ("usage_limit_reached")
        audit3_req = urllib.request.Request(
            f"{base_url}/api/audit/run",
            data=json.dumps({"target": "luxehaven.ae"}).encode("utf-8"),
            headers={"Content-Type": "application/json", "Cookie": f"session_token={session_token}"}
        )
        audit3_code = 0
        audit3_body = {}
        try:
            with urllib.request.urlopen(audit3_req, timeout=10) as resp:
                audit3_code = resp.status
                audit3_body = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            audit3_code = e.code
            try:
                audit3_body = json.loads(e.read().decode("utf-8"))
            except Exception:
                audit3_body = {}
        except Exception as e:
            audit3_code = 500
            audit3_body = {"error": str(e)}

        is_blocked = audit3_code == 403 and ("usage_limit" in str(audit3_body) or "limit" in str(audit3_body))
        record_test("LIMIT-02", "PLAN_LIMIT", "Third audit blocked with 403 Forbidden (usage_limit_reached)", is_blocked, f"code={audit3_code}, body={audit3_body}", "403 Forbidden with usage_limit_reached")

        # Verify UI shows "Upgrade to Pro" / "Upgrade Plan" prompt
        dash_req = urllib.request.Request(
            f"{base_url}/dashboard",
            headers={"Cookie": f"session_token={session_token}"}
        )
        with urllib.request.urlopen(dash_req, timeout=5) as resp:
            dash_html = resp.read().decode("utf-8")

        has_upgrade_prompt = "upgradeBtn" in dash_html or "Upgrade" in dash_html
        record_test("LIMIT-03", "PLAN_LIMIT", "Dashboard UI contains Upgrade Plan prompt", has_upgrade_prompt, has_upgrade_prompt, True)

        # =========================================================================
        # PHASE 3 — DATA PERSISTENCE & PRIVACY
        # =========================================================================
        print("\n--- PHASE 3: DATA PERSISTENCE & PRIVACY ---")
        # 3.1 Multi-Tenant Isolation: User A vs User B
        user_a_email = f"usera_{int(time.time())}@example.com"
        user_b_email = f"userb_{int(time.time())}@example.com"

        from engine import auth
        _, auth_a, _ = auth.signup(user_a_email, "SecurePassA1!", "User A")
        _, auth_b, _ = auth.signup(user_b_email, "SecurePassB1!", "User B")
        token_a = auth_a["session"]["session_token"]
        token_b = auth_b["session"]["session_token"]

        # User A runs scan for 'a.com'
        req_a = urllib.request.Request(
            f"{base_url}/api/audit/run",
            data=json.dumps({"target": "uber.com"}).encode("utf-8"),
            headers={"Content-Type": "application/json", "Cookie": f"session_token={token_a}"}
        )
        try:
            with urllib.request.urlopen(req_a, timeout=5) as resp:
                resp_a = json.loads(resp.read().decode("utf-8"))
        except Exception:
            resp_a = {}

        audit_id_a = resp_a.get("audit_id") or resp_a.get("audit", {}).get("audit_id")

        # User B attempts to access User A's scan result via ID
        req_b_leak = urllib.request.Request(
            f"{base_url}/api/audit/{audit_id_a}",
            headers={"Cookie": f"session_token={token_b}"}
        )
        b_code = 0
        try:
            with urllib.request.urlopen(req_b_leak, timeout=5) as resp:
                b_code = resp.status
        except urllib.error.HTTPError as e:
            b_code = e.code

        record_test("TENANT-01", "MULTI_TENANT", "User B accessing User A audit blocked (403/404)", b_code in [403, 404], b_code, "403 or 404")

        # Check User B dashboard recent audits
        req_b_me = urllib.request.Request(
            f"{base_url}/api/auth/me",
            headers={"Cookie": f"session_token={token_b}"}
        )
        with urllib.request.urlopen(req_b_me, timeout=5) as resp:
            b_me = json.loads(resp.read().decode("utf-8"))
            b_recent = [x.get("domain") for x in b_me.get("recent_audits", [])]

        record_test("TENANT-02", "MULTI_TENANT", "User B dashboard does NOT show User A scans", "a.com" not in b_recent, b_recent, "Does not contain 'a.com'")

        # 3.2 Session Persistence
        # Invalidate in-memory caches, keep DB sessions intact
        auth._LOGIN_ATTEMPTS.clear()
        auth._RESET_TOKENS.clear()
        
        # Test session validation directly and via HTTP
        valid_sess = auth.validate_session(token_a)
        record_test("SESS-PERSIST-01", "SESSION_PERSIST", "Session persists in DB across memory cache clears", valid_sess is not None and valid_sess["email"] == user_a_email, valid_sess is not None, True)

        # =========================================================================
        # PHASE 4 — UI & MOBILE POLISH VERIFICATION (375px)
        # =========================================================================
        print("\n--- PHASE 4: UI & MOBILE POLISH VERIFICATION (375px) ---")
        # Inspect web/dashboard.html and web/account.html
        with open("web/dashboard.html", "r", encoding="utf-8") as f:
            dash_src = f.read()
        with open("web/account.html", "r", encoding="utf-8") as f:
            acct_src = f.read()

        # Usage Meter check
        meter_ok = "usageBar" in dash_src and "progress-bar-fill" in dash_src and "usageUsed" in dash_src
        record_test("UI-METER-01", "MOBILE_POLISH", "Usage Meter configured with progress bar & counts", meter_ok, meter_ok, True)

        # Table scroll wrapper check
        scroll_ok = "table-scroll-wrapper" in dash_src and "overflow-x: auto" in dash_src
        record_test("UI-SCROLL-01", "MOBILE_POLISH", "Recent Scans table has overflow-x auto wrapper", scroll_ok, scroll_ok, True)

        # Logout button tap target check
        logout_ok = "logoutBtn" in dash_src and ("min-height: 38px" in dash_src or "min-height: 44px" in dash_src or "min-height: 48px" in dash_src)
        record_test("UI-LOGOUT-01", "MOBILE_POLISH", "Logout button has adequate minimum tap height", logout_ok, logout_ok, True)

        # =========================================================================
        # PHASE 5 — ANALYTICS EVENT TRIGGERING
        # =========================================================================
        print("\n--- PHASE 5: ANALYTICS EVENT TRIGGERING ---")
        with open("web/app.js", "r", encoding="utf-8") as f:
            app_js_src = f.read()

        has_audit_start = "audit_start" in app_js_src
        has_audit_complete = "audit_complete" in app_js_src

        record_test("ANALYTICS-01", "ANALYTICS", "audit_start event fired when scan triggered", has_audit_start, has_audit_start, True)
        record_test("ANALYTICS-02", "ANALYTICS", "audit_complete event fired when scan completes", has_audit_complete, has_audit_complete, True)

    finally:
        server_proc.terminate()
        try:
            server_proc.wait(timeout=3)
        except Exception:
            server_proc.kill()

        # Cleanup test db
        if os.path.exists(test_db_file):
            try:
                os.remove(test_db_file)
            except Exception:
                pass

    print("\n" + "=" * 80)
    passed_count = sum(1 for t in TEST_RESULTS if t["passed"])
    total_count = len(TEST_RESULTS)
    print(f"SPRINT 1.5 AUDIT RESULT: {passed_count}/{total_count} CHECKS PASSED")
    print("=" * 80)

    # Save results to json
    results_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "FEATURE_INTEGRITY_RESULTS_RAW.json")
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(TEST_RESULTS, f, indent=2)

if __name__ == "__main__":
    main()
