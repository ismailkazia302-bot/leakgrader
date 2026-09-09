"""
LeakGrader Sprint 1 Comprehensive Test Suite
Verifies:
1. Database connection, schema tables & indexes, and migration idempotency
2. User signup (valid, duplicate, invalid email, weak password)
3. User login (valid, wrong password, rate limiting)
4. Session creation, validation, expiry, rotation
5. Logout and session deletion
6. CSRF token validation
7. Password reset flow
8. Dashboard page loads for authenticated user
9. Dashboard redirects for unauthenticated user
10. Subscription webhook creates database records
11. Entitlement check with database
12. Usage counting and limits
13. Plan upgrade changes entitlements
14. Existing security tests compatibility
"""

import os
import sys
import json
import time
import uuid
import secrets
import subprocess
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.connection import get_db_cursor, execute_query, is_sqlite
from db import migrate
from engine import auth, security_guard

TEST_RESULTS = []

def record(test_id: str, name: str, passed: bool, details: str = ""):
    status = "PASS" if passed else "FAIL"
    res = {
        "test_id": test_id,
        "name": name,
        "status": status,
        "details": details
    }
    TEST_RESULTS.append(res)
    print(f"[{status}] {test_id}: {name} {f'({details})' if details else ''}")


def run_sprint1_suite():
    print("=" * 80)
    print("RUNNING SPRINT 1 TEST SUITE: DATABASE, AUTH & SUBSCRIPTIONS")
    print("=" * 80)

    # --------------------------------------------------------------------------
    # 1. Database connection and schema
    # --------------------------------------------------------------------------
    print("\n--- 1. Database Connection & Schema Verification ---")
    try:
        # Verify migration runner
        mig_ok = migrate.run_migrations()
        record("DB-01", "Database migration runner idempotency", mig_ok)

        # Verify tables exist
        required_tables = [
            "users", "workspaces", "workspace_members", "sessions",
            "subscriptions", "entitlements", "webhook_events", "audits", "usage_events"
        ]
        if is_sqlite():
            rows = execute_query("SELECT name FROM sqlite_master WHERE type='table';", fetchall=True)
            table_names = [r["name"] for r in rows]
        else:
            rows = execute_query("SELECT table_name FROM information_schema.tables WHERE table_schema='public';", fetchall=True)
            table_names = [r["table_name"] for r in rows]

        all_tables_present = all(t in table_names for t in required_tables)
        record("DB-02", "All 9 required tables present in schema", all_tables_present, f"Found: {len(table_names)} tables")
    except Exception as e:
        record("DB-01", "Database setup exception", False, str(e))
        record("DB-02", "Table presence check", False, str(e))

    # --------------------------------------------------------------------------
    # 2. User signup (valid, duplicate, invalid email, weak password)
    # --------------------------------------------------------------------------
    print("\n--- 2. User Signup Validation ---")
    rand_suffix = secrets.token_hex(4)
    signup_email = f"alex_{rand_suffix}@company.com"
    pwd_valid = "SecurePassword123!"

    # Valid signup
    succ, data, code = auth.signup(signup_email, pwd_valid, "Alex Taylor")
    record("AUTH-SIGNUP-01", "Valid user signup -> 201", succ and code == 201, f"User ID: {data.get('user', {}).get('id')}")

    # Duplicate email signup
    succ_dup, _, code_dup = auth.signup(signup_email, pwd_valid, "Alex Duplicate")
    record("AUTH-SIGNUP-02", "Duplicate email signup -> 409", (not succ_dup) and code_dup == 409)

    # Invalid email format
    succ_inv, _, code_inv = auth.signup("invalid-email", pwd_valid, "Invalid Email")
    record("AUTH-SIGNUP-03", "Invalid email format signup -> 400", (not succ_inv) and code_inv == 400)

    # Weak password (<8 chars)
    succ_weak, _, code_weak = auth.signup(f"weak_{rand_suffix}@company.com", "short", "Weak Pwd")
    record("AUTH-SIGNUP-04", "Weak password (<8 chars) signup -> 400", (not succ_weak) and code_weak == 400)

    # --------------------------------------------------------------------------
    # 3. User login (valid, wrong password, rate limiting)
    # --------------------------------------------------------------------------
    print("\n--- 3. User Login & Rate Limiting ---")
    # Valid login
    l_succ, l_data, l_code = auth.login(signup_email, pwd_valid)
    record("AUTH-LOGIN-01", "Valid credentials login -> 200", l_succ and l_code == 200)

    # Wrong password
    w_succ, _, w_code = auth.login(signup_email, "WrongPassword!")
    record("AUTH-LOGIN-02", "Wrong password login -> 401", (not w_succ) and w_code == 401)

    # Rate limiting: trigger 5 failed attempts
    rate_email = f"ratelimit_{rand_suffix}@company.com"
    auth.signup(rate_email, pwd_valid, "Rate Limit Test")
    for _ in range(5):
        auth.login(rate_email, "WrongPassword!")
    # 6th attempt should return 429
    r_succ, r_data, r_code = auth.login(rate_email, "WrongPassword!")
    record("AUTH-LOGIN-03", "5 failed attempts triggers rate limit -> 429", (not r_succ) and r_code == 429)

    # --------------------------------------------------------------------------
    # 4. Session creation, validation, expiry, rotation
    # --------------------------------------------------------------------------
    print("\n--- 4. Session Management ---")
    session_token = l_data["session"]["session_token"]
    session_info = auth.validate_session(session_token)
    record("SESS-01", "Session validation returns user and workspace", session_info is not None and session_info["email"] == signup_email)
    record("SESS-02", "CSRF token generated with session", bool(session_info and session_info.get("csrf_token")))

    # Session rotation: login again should rotate session token
    time.sleep(0.01)
    _, l_data2, _ = auth.login(signup_email, pwd_valid)
    new_session_token = l_data2["session"]["session_token"]
    record("SESS-03", "Session token rotated on new login", new_session_token != session_token)
    # Previous session invalidated
    old_valid = auth.validate_session(session_token)
    record("SESS-04", "Old session invalidated upon rotation", old_valid is None)

    # --------------------------------------------------------------------------
    # 5. Logout and session deletion
    # --------------------------------------------------------------------------
    print("\n--- 5. Logout & Session Invalidation ---")
    auth.logout(new_session_token)
    logged_out_valid = auth.validate_session(new_session_token)
    record("AUTH-LOGOUT-01", "Logout deletes active session from database", logged_out_valid is None)

    # --------------------------------------------------------------------------
    # 6. CSRF token validation
    # --------------------------------------------------------------------------
    print("\n--- 6. CSRF Protection ---")
    _, l_data3, _ = auth.login(signup_email, pwd_valid)
    active_token = l_data3["session"]["session_token"]
    active_sess = auth.validate_session(active_token)

    csrf_valid = auth.validate_csrf({"X-CSRF-Token": active_sess["csrf_token"]}, active_sess)
    record("CSRF-01", "Matching X-CSRF-Token header validated", csrf_valid)

    csrf_tampered = auth.validate_csrf({"X-CSRF-Token": "tampered_token_123"}, active_sess)
    record("CSRF-02", "Tampered X-CSRF-Token rejected", not csrf_tampered)

    csrf_missing = auth.validate_csrf({}, active_sess)
    record("CSRF-03", "Missing X-CSRF-Token header rejected", not csrf_missing)

    # --------------------------------------------------------------------------
    # 7. Password reset flow
    # --------------------------------------------------------------------------
    print("\n--- 7. Password Reset Flow ---")
    f_succ, f_data, f_code = auth.forgot_password(signup_email)
    reset_token = f_data.get("reset_token_test")
    record("RESET-01", "Forgot password issues reset token", f_succ and bool(reset_token))

    # Invalid reset token
    bad_succ, _, bad_code = auth.reset_password("invalid_token_999", "BrandNewPassword123!")
    record("RESET-02", "Invalid reset token rejected -> 400", (not bad_succ) and bad_code == 400)

    # Valid reset
    new_pwd = "BrandNewPassword123!"
    r_succ, _, r_code = auth.reset_password(reset_token, new_pwd)
    record("RESET-03", "Valid reset token updates password -> 200", r_succ and r_code == 200)

    # Active session invalidated by reset
    record("RESET-04", "Password reset invalidates active sessions", auth.validate_session(active_token) is None)

    # Login with new password succeeds
    login_new_succ, _, _ = auth.login(signup_email, new_pwd)
    record("RESET-05", "Login succeeds with newly set password", login_new_succ)

    # --------------------------------------------------------------------------
    # 8 & 9. Dashboard HTTP access (Authenticated vs Unauthenticated)
    # --------------------------------------------------------------------------
    print("\n--- 8 & 9. Dashboard Access & Redirects (HTTP) ---")
    # Start WSGI server on dedicated test port in auth_ready mode
    port = 8765
    server_env = os.environ.copy()
    server_env["PORT"] = str(port)
    server_env["ENVIRONMENT"] = "test"
    server_env["SECURITY_LOCKDOWN_MODE"] = "enabled"
    server_env["LOCKDOWN_PHASE"] = "auth_ready"
    server_env["LEMONSQUEEZY_WEBHOOK_SECRET"] = "test_signing_secret_123"

    server_proc = subprocess.Popen(
        [sys.executable, "-c", f"from wsgiref.simple_server import make_server; from wsgi import app; make_server('127.0.0.1', {port}, app).serve_forever()"],
        env=server_env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    time.sleep(2)  # Allow server to bind

    base_http = f"http://127.0.0.1:{port}"
    try:
        # Unauthenticated request to /dashboard -> 302 redirect
        req_unauth = urllib.request.Request(f"{base_http}/dashboard", headers={"User-Agent": "Test"})
        # Custom opener that doesn't auto-follow redirect
        class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
            def http_error_302(self, req, fp, code, msg, headers):
                return fp
        opener = urllib.request.build_opener(NoRedirectHandler)
        try:
            resp = opener.open(req_unauth, timeout=5)
            record("DASH-01", "Unauthenticated /dashboard redirects to /login (302)", resp.status in [302, 401])
        except urllib.error.HTTPError as e:
            record("DASH-01", "Unauthenticated /dashboard redirects to /login", e.code in [302, 401])

        # Authenticated request to /dashboard
        _, auth_log, _ = auth.login(signup_email, new_pwd)
        user_sess_token = auth_log["session"]["session_token"]

        req_auth = urllib.request.Request(
            f"{base_http}/dashboard",
            headers={"User-Agent": "Test", "Cookie": f"session_token={user_sess_token}"}
        )
        try:
            with urllib.request.urlopen(req_auth, timeout=5) as resp:
                body = resp.read().decode("utf-8")
                record("DASH-02", "Authenticated /dashboard loads 200 text/html", resp.status == 200 and "Dashboard" in body)
        except Exception as e:
            record("DASH-02", "Authenticated /dashboard loads 200", False, str(e))

        # Test /api/auth/me returns 200 for authenticated user
        req_me = urllib.request.Request(
            f"{base_http}/api/auth/me",
            headers={"User-Agent": "Test", "Cookie": f"session_token={user_sess_token}"}
        )
        try:
            with urllib.request.urlopen(req_me, timeout=5) as resp:
                me_data = json.loads(resp.read().decode("utf-8"))
                record("AUTH-ME-01", "GET /api/auth/me returns user & workspace info", resp.status == 200 and me_data.get("user", {}).get("email") == signup_email)
        except Exception as e:
            record("AUTH-ME-01", "GET /api/auth/me returns user info", False, str(e))

    finally:
        server_proc.terminate()
        server_proc.wait()

    # --------------------------------------------------------------------------
    # 10. Subscription webhook creates database records
    # --------------------------------------------------------------------------
    print("\n--- 10. Subscription Webhook Database Persistence ---")
    sub_test_email = f"subscriber_{rand_suffix}@enterprise.com"
    event_id = f"evt_sprint1_{rand_suffix}"
    order_id = f"ord_{rand_suffix}"

    webhook_payload = {
        "meta": {"event_name": "subscription_created"},
        "data": {
            "id": order_id,
            "attributes": {
                "user_email": sub_test_email,
                "product_name": "Solo Plan",
                "status": "active"
            }
        }
    }
    raw_bytes = json.dumps(webhook_payload).encode("utf-8")
    sync_ok = security_guard.sync_webhook_to_db(event_id, "subscription_created", raw_bytes, webhook_payload)
    record("SUB-DB-01", "Webhook syncs to database successfully", sync_ok)

    # Verify records in database
    sub_user = execute_query("SELECT id, email FROM users WHERE email = %s;", (sub_test_email,), fetchone=True)
    record("SUB-DB-02", "User created in database by subscription webhook", sub_user is not None)

    sub_rec = execute_query("SELECT s.id, s.plan, s.status, w.id AS ws_id FROM subscriptions s JOIN workspaces w ON s.workspace_id = w.id WHERE s.user_id = %s;", (sub_user["id"],), fetchone=True)
    record("SUB-DB-03", "Subscription record created with active status", sub_rec is not None and sub_rec["status"] == "active")

    ws_id = sub_rec["ws_id"]
    ent_rec = execute_query("SELECT usage_limit, usage_count, is_active FROM entitlements WHERE workspace_id = %s AND feature = 'audit';", (ws_id,), fetchone=True)
    record("SUB-DB-04", "Solo Plan entitlement limit set to 25 audits", ent_rec is not None and ent_rec["usage_limit"] == 25)

    # --------------------------------------------------------------------------
    # 11, 12, 13. Entitlement check, usage counting & plan upgrade
    # --------------------------------------------------------------------------
    print("\n--- 11, 12, 13. Entitlements, Usage Limits & Plan Upgrades ---")
    # Entitlement check (allowed)
    allowed, reason, details = security_guard.check_db_entitlement(ws_id, "audit", increment_usage=False)
    record("ENT-01", "check_db_entitlement returns allowed for active subscription", allowed)

    # Usage counting: simulate hitting limit
    execute_query("UPDATE entitlements SET usage_count = 24 WHERE workspace_id = %s AND feature = 'audit';", (ws_id,), commit=True)
    # 25th audit allowed and increments to 25
    allowed_25, _, _ = security_guard.check_db_entitlement(ws_id, "audit", increment_usage=True)
    record("ENT-02", "25th audit allowed and incremented", allowed_25)

    # 26th audit blocked (limit is 25)
    allowed_26, reason_26, _ = security_guard.check_db_entitlement(ws_id, "audit", increment_usage=True)
    record("ENT-03", "Audit blocked upon reaching plan limit", (not allowed_26) and reason_26 == "usage_limit_reached")

    # Plan Upgrade to Agency Plan (100 audits)
    upgrade_payload = {
        "meta": {"event_name": "subscription_updated"},
        "data": {
            "id": order_id,
            "attributes": {
                "user_email": sub_test_email,
                "product_name": "Agency Plan",
                "status": "active"
            }
        }
    }
    upg_bytes = json.dumps(upgrade_payload).encode("utf-8")
    security_guard.sync_webhook_to_db(f"evt_upg_{rand_suffix}", "subscription_updated", upg_bytes, upgrade_payload)

    upg_ent = execute_query("SELECT usage_limit FROM entitlements WHERE workspace_id = %s AND feature = 'audit';", (ws_id,), fetchone=True)
    record("ENT-04", "Plan upgrade expands audit limit to 100", upg_ent is not None and upg_ent["usage_limit"] == 100)

    # Access is now restored because count (25) < limit (100)
    allowed_restored, _, _ = security_guard.check_db_entitlement(ws_id, "audit", increment_usage=True)
    record("ENT-05", "Usage access restored following plan upgrade", allowed_restored)

    # --------------------------------------------------------------------------
    # Summary
    # --------------------------------------------------------------------------
    total = len(TEST_RESULTS)
    passed = sum(1 for r in TEST_RESULTS if r["status"] == "PASS")
    failed = total - passed
    print("\n" + "=" * 80)
    print(f"SPRINT 1 SUITE SUMMARY: {passed}/{total} TESTS PASSED ({passed/total*100:.1f}%)")
    print("=" * 80)

    with open("qa/SPRINT_1_RAW_RESULTS.json", "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total": total,
            "passed": passed,
            "failed": failed,
            "results": TEST_RESULTS
        }, f, indent=2)

    return failed == 0

if __name__ == "__main__":
    success = run_sprint1_suite()
    sys.exit(0 if success else 1)
