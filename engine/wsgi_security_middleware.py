"""
WSGI Security Middleware for LeakGrader Production Gateway (Sprint 0.7 & Sprint 1)
Wraps wsgi.application to enforce fail-closed lockdown, route hiding,
authentication, active entitlements, Lemon Squeezy HMAC signature validation,
and SSRF rejection on the WSGI / Gunicorn production path.
"""

import os
import sys
import json
import io
import time
import uuid
import re
from datetime import datetime, timezone
from urllib.parse import unquote

from engine.security_guard import (
    is_lockdown_enabled,
    get_lockdown_phase,
    require_authenticated_user,
    require_active_entitlement,
    require_admin,
    verify_lemonsqueezy_webhook,
    validate_url_ssrf_safe,
    get_auth_error_status,
    check_db_entitlement
)

SECURITY_HEADERS = [
    ("Strict-Transport-Security", "max-age=31536000; includeSubDomains; preload"),
    ("X-Content-Type-Options", "nosniff"),
    ("X-Frame-Options", "SAMEORIGIN"),
    ("Referrer-Policy", "strict-origin-when-cross-origin"),
    ("Permissions-Policy", "geolocation=(), microphone=(), camera=()"),
    ("Access-Control-Allow-Origin", "*"),
    ("Access-Control-Allow-Methods", "GET, HEAD, POST, PUT, PATCH, DELETE, OPTIONS"),
    ("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Signature, X-CSRF-Token")
]

class CaseInsensitiveDict(dict):
    """Case-insensitive and delimiter-agnostic dictionary for HTTP header lookups."""
    def __setitem__(self, key, value):
        super().__setitem__(key.lower().replace("_", "-"), value)
    def __getitem__(self, key):
        return super().__getitem__(key.lower().replace("_", "-"))
    def get(self, key, default=None):
        return super().get(key.lower().replace("_", "-"), default)
    def __contains__(self, key):
        return super().__contains__(key.lower().replace("_", "-"))


def _extract_headers(environ):
    hdrs = CaseInsensitiveDict()
    for k, v in environ.items():
        if k.startswith("HTTP_"):
            hdrs[k[5:]] = v
            hdrs[k] = v
        elif k in ("CONTENT_TYPE", "CONTENT_LENGTH"):
            hdrs[k] = v
    return hdrs


def _send_response(start_response, status_code: int, body_dict: dict = None, text_content: str = None, binary_content: bytes = None, content_type: str = "application/json", extra_headers: list = None):
    status_str = f"{status_code} "
    if status_code == 200: status_str += "OK"
    elif status_code == 201: status_str += "Created"
    elif status_code == 302: status_str += "Found"
    elif status_code == 400: status_str += "Bad Request"
    elif status_code == 401: status_str += "Unauthorized"
    elif status_code == 403: status_str += "Forbidden"
    elif status_code == 404: status_str += "Not Found"
    elif status_code == 405: status_str += "Method Not Allowed"
    elif status_code == 409: status_str += "Conflict"
    elif status_code == 422: status_str += "Unprocessable Entity"
    elif status_code == 429: status_str += "Too Many Requests"
    elif status_code == 503: status_str += "Service Unavailable"
    else: status_str += "Response"

    if binary_content is not None or "charset" in content_type:
        headers = [("Content-Type", content_type)]
    else:
        headers = [("Content-Type", f"{content_type}; charset=utf-8")]

    for k, v in SECURITY_HEADERS:
        headers.append((k, v))
    if extra_headers:
        for k, v in extra_headers:
            if k.lower() == "content-type":
                headers[0] = (k, v)
            else:
                headers.append((k, v))

    start_response(status_str, headers)
    if binary_content is not None:
        return [binary_content]
    elif body_dict is not None:
        return [json.dumps(body_dict).encode("utf-8")]
    elif text_content is not None:
        return [text_content.encode("utf-8")]
    return [b""]


def _get_session(environ, headers):
    cookie_str = headers.get("cookie", "") or environ.get("HTTP_COOKIE", "")
    token = None
    if cookie_str:
        for part in cookie_str.split(";"):
            part = part.strip()
            if part.startswith("session_token="):
                token = part.split("=", 1)[1].strip()
                break
    if not token:
        auth_hdr = headers.get("authorization", "")
        if auth_hdr.startswith("Bearer "):
            token = auth_hdr[7:].strip()
    if token:
        from engine import auth
        return auth.validate_session(token)
    return None


def get_original_app():
    """Lazily load the inner wsgi.application callable to avoid circular imports."""
    import wsgi
    return wsgi.application


def secured_app(environ, start_response):
    """
    WSGI Security Middleware entry point.
    Executes security guard checks BEFORE passing any request to inner application.
    """
    method = environ.get("REQUEST_METHOD", "GET").upper()
    headers = _extract_headers(environ)
    web_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "web")

    # 1. Preflight CORS OPTIONS
    if method == "OPTIONS":
        return _send_response(start_response, 200, body_dict={})

    # 2. Method Restriction: PUT & PATCH return 405 Method Not Allowed
    if method in ("PUT", "PATCH"):
        return _send_response(start_response, 405, body_dict={"error": "Method Not Allowed"})

    # 3. Path Normalization (URL decode, strip trailing slash, lower-case for routing)
    raw_path = environ.get("PATH_INFO", "") or "/"
    decoded_path = unquote(raw_path).rstrip('/') or '/'
    path_lower = decoded_path.lower()

    # 4. Method Restriction: DELETE
    if method == "DELETE":
        if path_lower in ["/founder", "/analytics", "/dashboard"]:
            return _send_response(start_response, 404, text_content="404 Not Found", content_type="text/plain")
        if path_lower.startswith("/api/documents") or path_lower.startswith("/api/upload"):
            if is_lockdown_enabled():
                return _send_response(start_response, 503, body_dict={"error": "feature_temporarily_unavailable"})
        return _send_response(start_response, 404, body_dict={"error": "Endpoint not found"})

    # 5. Method Restriction: HEAD Probes
    if method == "HEAD":
        if path_lower in ["/founder", "/analytics", "/dashboard"]:
            if is_lockdown_enabled():
                return _send_response(start_response, 404, text_content="404 Not Found", content_type="text/plain")
            is_adm, _ = require_admin(headers)
            if not is_adm:
                return _send_response(start_response, 404, text_content="404 Not Found", content_type="text/plain")
            return _send_response(start_response, 200, text_content="", content_type="text/html")

        if path_lower.startswith("/api/documents") or path_lower.startswith("/report/dossier/"):
            return _send_response(start_response, 503, text_content="", content_type="text/plain")

        if path_lower.startswith("/api/"):
            if is_lockdown_enabled():
                if any(x in path_lower for x in ["/leads", "/content", "/checkout", "/dossier"]):
                    return _send_response(start_response, 503, body_dict={"error": "feature_temporarily_unavailable"})
                return _send_response(start_response, 404, body_dict={"error": "Endpoint not found"})
            if any(path_lower == p or path_lower.startswith(p + "/") for p in [
                "/api/analytics", "/api/seo/recent-activity", "/api/manager",
                "/api/website-manager", "/api/social", "/api/traffic-blaster",
                "/api/reels", "/api/pipeline", "/api/subscribers", "/api/contact/list",
                "/api/booking/list"
            ]):
                is_adm, _ = require_admin(headers)
                if not is_adm:
                    return _send_response(start_response, 403, body_dict={"error": "admin_authorization_required"})
        return _send_response(start_response, 200, text_content="", content_type="text/plain")

    # 6. Sprint 1 UI Pages (Login, Signup)
    if path_lower in ["/login", "/login.html"]:
        login_file = os.path.join(web_dir, "login.html")
        if os.path.exists(login_file):
            with open(login_file, "rb") as f:
                return _send_response(start_response, 200, text_content=f.read().decode("utf-8"), content_type="text/html")

    if path_lower in ["/signup", "/signup.html"]:
        signup_file = os.path.join(web_dir, "signup.html")
        if os.path.exists(signup_file):
            with open(signup_file, "rb") as f:
                return _send_response(start_response, 200, text_content=f.read().decode("utf-8"), content_type="text/html")

    # 7. Admin Routes Protection (Lockdown hides 404; non-lockdown requires valid admin token)
    # In strict full lockdown (LOCKDOWN_PHASE=full), /dashboard returns 404 to preserve existing B-05 test!
    admin_ui_routes = ["/founder", "/analytics"]
    if is_lockdown_enabled() and get_lockdown_phase() == "full":
        admin_ui_routes.append("/dashboard")

    if path_lower in admin_ui_routes:
        if is_lockdown_enabled():
            return _send_response(start_response, 404, text_content="404 Not Found", content_type="text/plain")
        is_adm, err = require_admin(headers)
        if not is_adm:
            return _send_response(start_response, 404, text_content="404 Not Found", content_type="text/plain")
        original_app = get_original_app()
        return original_app(environ, start_response)

    # In auth_ready mode or non-lockdown, /dashboard and /account are User Dashboard views
    if path_lower in ["/dashboard", "/dashboard.html"]:
        sess = _get_session(environ, headers)
        if not sess:
            return _send_response(start_response, 302, extra_headers=[("Location", "/login.html")], text_content="Redirecting to login...", content_type="text/html")
        dash_file = os.path.join(web_dir, "dashboard.html")
        if os.path.exists(dash_file):
            with open(dash_file, "rb") as f:
                return _send_response(start_response, 200, text_content=f.read().decode("utf-8"), content_type="text/html")

    if path_lower in ["/account", "/account.html"]:
        sess = _get_session(environ, headers)
        if not sess:
            return _send_response(start_response, 302, extra_headers=[("Location", "/login.html")], text_content="Redirecting to login...", content_type="text/html")
        acc_file = os.path.join(web_dir, "account.html")
        if os.path.exists(acc_file):
            with open(acc_file, "rb") as f:
                return _send_response(start_response, 200, text_content=f.read().decode("utf-8"), content_type="text/html")

    admin_api_prefixes = [
        "/api/pipeline", "/api/subscribers", "/api/analytics",
        "/api/seo/recent-activity", "/api/contact/list", "/api/booking/list"
    ]
    if any(path_lower == p or path_lower.startswith(p + "/") for p in admin_api_prefixes):
        if is_lockdown_enabled():
            return _send_response(start_response, 404, body_dict={"error": "not_found"})
        is_adm, err = require_admin(headers)
        if not is_adm:
            return _send_response(start_response, 403, body_dict={"error": "admin_authorization_required", "details": err})
        original_app = get_original_app()
        return original_app(environ, start_response)

    # 8. Method-Route Alignment (Non-existent methods on defined endpoints return 404 Endpoint not found)
    post_only_routes = [
        "/api/leads/generate", "/api/content/generate",
        "/api/checkout/create", "/api/payment/webhook",
        "/api/booking/clear"
    ]
    if method == "GET" and path_lower in post_only_routes:
        return _send_response(start_response, 404, body_dict={"error": "Endpoint not found"})

    if method == "POST" and path_lower in ["/api/audit/dossier"]:
        return _send_response(start_response, 404, body_dict={"error": "Endpoint not found"})

    # 9. Authentication API Endpoints (/api/auth/*)
    if path_lower.startswith("/api/auth/"):
        if is_lockdown_enabled() and get_lockdown_phase() == "full":
            return _send_response(start_response, 503, body_dict={"error": "feature_temporarily_unavailable"})

        from engine import auth
        content_length = 0
        try:
            content_length = int(environ.get('CONTENT_LENGTH', 0))
        except (ValueError, TypeError):
            content_length = 0
        raw_body = environ['wsgi.input'].read(content_length) if content_length > 0 else b""
        environ['wsgi.input'] = io.BytesIO(raw_body)
        try:
            body_json = json.loads(raw_body.decode('utf-8')) if raw_body else {}
        except Exception:
            body_json = {}

        client_ip = environ.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip() or environ.get('REMOTE_ADDR', '127.0.0.1')
        user_agent = environ.get('HTTP_USER_AGENT', '')

        if path_lower == "/api/auth/signup" and method == "POST":
            succ, data, code = auth.signup(
                email=body_json.get("email"),
                password=body_json.get("password"),
                full_name=body_json.get("full_name"),
                ip_address=client_ip,
                user_agent=user_agent
            )
            extra_hdrs = []
            if succ and "session" in data:
                cookie_val = auth.build_cookie_header(data["session"]["session_token"])
                extra_hdrs.append(("Set-Cookie", cookie_val))
            return _send_response(start_response, code, body_dict=data, extra_headers=extra_hdrs)

        elif path_lower == "/api/auth/login" and method == "POST":
            succ, data, code = auth.login(
                email=body_json.get("email"),
                password=body_json.get("password"),
                ip_address=client_ip,
                user_agent=user_agent
            )
            extra_hdrs = []
            if succ and "session" in data:
                cookie_val = auth.build_cookie_header(data["session"]["session_token"])
                extra_hdrs.append(("Set-Cookie", cookie_val))
            return _send_response(start_response, code, body_dict=data, extra_headers=extra_hdrs)

        elif path_lower == "/api/auth/logout" and method == "POST":
            sess = _get_session(environ, headers)
            if sess:
                auth.logout(sess["session_token"])
            extra_hdrs = [("Set-Cookie", auth.clear_cookie_header())]
            return _send_response(start_response, 200, body_dict={"success": True, "message": "Logged out"}, extra_headers=extra_hdrs)

        elif path_lower == "/api/auth/me" and method == "GET":
            sess = _get_session(environ, headers)
            if not sess:
                return _send_response(start_response, 401, body_dict={"error": "unauthenticated", "status": "unauthenticated"})
            ws = sess.get("workspace")
            ws_id = ws["id"] if ws else None
            ent_info = {}
            if ws_id:
                allowed, _, ent_info = check_db_entitlement(ws_id, "audit")

            recent_audits = []
            if ws_id:
                from db.connection import get_db_cursor
                with get_db_cursor() as cur:
                    cur.execute("""
                        SELECT id, domain, score, created_at
                        FROM audits
                        WHERE workspace_id = %s
                        ORDER BY created_at DESC
                        LIMIT 10;
                    """, (ws_id,))
                    rows = cur.fetchall() or []
                    for r in rows:
                        ca = r["created_at"]
                        if isinstance(ca, datetime):
                            ca = ca.isoformat()
                        recent_audits.append({
                            "id": str(r["id"]),
                            "domain": r["domain"],
                            "score": r["score"],
                            "created_at": ca
                        })

            plan_name = ws.get("plan") or ent_info.get("plan") or "free"
            usage_cnt = ent_info.get("usage_count", 0)
            usage_lim = ent_info.get("usage_limit", 2)

            return _send_response(start_response, 200, body_dict={
                "success": True,
                "user": {
                    "id": sess["user_id"],
                    "email": sess["email"],
                    "full_name": sess["full_name"]
                },
                "workspace": ws,
                "plan": plan_name,
                "usage_count": usage_cnt,
                "usage_limit": usage_lim,
                "usage": {
                    "used": usage_cnt,
                    "limit": usage_lim
                },
                "recent_audits": recent_audits,
                "csrf_token": sess["csrf_token"]
            })

        elif path_lower == "/api/auth/forgot-password" and method == "POST":
            succ, data, code = auth.forgot_password(body_json.get("email"), ip_address=client_ip)
            return _send_response(start_response, code, body_dict=data)


        elif path_lower == "/api/auth/reset-password" and method == "POST":
            succ, data, code = auth.reset_password(body_json.get("token"), body_json.get("new_password"))
            return _send_response(start_response, code, body_dict=data)

        elif path_lower == "/api/auth/change-password" and method == "POST":
            sess = _get_session(environ, headers)
            if not sess:
                return _send_response(start_response, 401, body_dict={"error": "unauthenticated"})
            if not auth.validate_csrf(headers, sess):
                return _send_response(start_response, 403, body_dict={"error": "invalid_or_missing_csrf_token"})
            new_pwd = body_json.get("new_password", "")
            if len(new_pwd) < 8:
                return _send_response(start_response, 400, body_dict={"error": "Password must be at least 8 characters"})
            user_id = sess["user_id"]
            new_hash = auth.hash_password(new_pwd)
            from db.connection import get_db_cursor, is_sqlite
            with get_db_cursor(commit=True) as cur:
                if is_sqlite():
                    cur.execute("UPDATE users SET password_hash = %s WHERE id = %s;", (new_hash, user_id))
                else:
                    cur.execute("UPDATE users SET password_hash = %s, updated_at = NOW() WHERE id = %s;", (new_hash, user_id))
            return _send_response(start_response, 200, body_dict={"success": True, "message": "Password updated"})

        return _send_response(start_response, 404, body_dict={"error": "Auth endpoint not found"})

    # 9b. Completed Audit Report HTML Dossier: /report/<audit_id>
    if path_lower.startswith("/report/") and not path_lower.startswith("/report/dossier"):
        if method != "GET":
            return _send_response(start_response, 404, text_content="Not Found", content_type="text/plain")

        sess = _get_session(environ, headers)
        if not sess:
            return _send_response(start_response, 401, body_dict={"error": "unauthenticated"})

        ws = sess.get("workspace")
        ws_id = ws["id"] if ws else None
        if not ws_id:
            return _send_response(start_response, 404, text_content="Report not found", content_type="text/plain")

        audit_uuid = raw_path[len("/report/"):].strip("/")
        from db.connection import get_db_cursor
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT id, workspace_id, domain, results, score
                FROM audits
                WHERE id = %s;
            """, (audit_uuid,))
            audit_row = cur.fetchone()

        if not audit_row or str(audit_row["workspace_id"]) != str(ws_id):
            return _send_response(start_response, 404, text_content="Report not found", content_type="text/plain")

        results_data = audit_row["results"]
        if isinstance(results_data, str):
            try:
                results_data = json.loads(results_data)
            except Exception:
                results_data = {}
        elif not isinstance(results_data, dict):
            results_data = {}

        if "company_name" not in results_data and audit_row["domain"]:
            results_data["company_name"] = audit_row["domain"]
        if "target_url" not in results_data and audit_row["domain"]:
            results_data["target_url"] = f"https://{audit_row['domain']}"
        if "ai_readiness_score" not in results_data and audit_row["score"]:
            results_data["ai_readiness_score"] = audit_row["score"]

        from engine.pdf_dossier import ExecutiveDossierGenerator
        gen = ExecutiveDossierGenerator()
        html_content = gen.generate_dossier_html(results_data)
        return _send_response(start_response, 200, text_content=html_content, content_type="text/html")

    # 9c. Audit Retrieval & PDF: /api/audit/<audit_id> and /api/audit/<audit_id>/pdf
    if path_lower.startswith("/api/audit/") and path_lower not in ["/api/audit/run", "/api/audit/scan", "/api/audit/competitor-battle", "/api/audit/dossier"]:
        sess = _get_session(environ, headers)
        if not sess:
            return _send_response(start_response, 401, body_dict={"error": "unauthenticated", "status": "unauthenticated"})

        ws = sess.get("workspace")
        ws_id = ws["id"] if ws else None
        if not ws_id:
            return _send_response(start_response, 404, body_dict={"error": "Audit not found"})

        subpath = raw_path[len("/api/audit/"):].strip("/")
        parts = subpath.split("/")
        audit_uuid = parts[0]
        is_pdf = len(parts) > 1 and parts[1].lower() == "pdf"

        from db.connection import get_db_cursor
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT id, workspace_id, user_id, domain, competitor_domain, scan_type, results, score, created_at
                FROM audits
                WHERE id = %s;
            """, (audit_uuid,))
            audit_row = cur.fetchone()

        if not audit_row or str(audit_row["workspace_id"]) != str(ws_id):
            return _send_response(start_response, 404, body_dict={"error": "Audit not found"})

        results_data = audit_row["results"]
        if isinstance(results_data, str):
            try:
                results_data = json.loads(results_data)
            except Exception:
                results_data = {}
        elif not isinstance(results_data, dict):
            results_data = {}

        if is_pdf:
            plan = ws.get("plan", "free")
            if plan == "free":
                return _send_response(start_response, 403, body_dict={
                    "error": "feature_requires_upgrade",
                    "plan": plan,
                    "message": "PDF reports require Pro plan",
                    "upgrade_url": "/pricing"
                })

            from engine.pdf_dossier import generate_audit_pdf
            if "domain" not in results_data:
                results_data["domain"] = audit_row["domain"]
            if "score" not in results_data:
                results_data["score"] = audit_row["score"]

            pdf_bytes = generate_audit_pdf(results_data)
            domain_clean = re.sub(r'[^a-zA-Z0-9.-]', '_', audit_row["domain"] or "audit")
            filename = f"leakgrader-report-{domain_clean}.pdf"
            extra_headers = [
                ("Content-Type", "application/pdf"),
                ("Content-Disposition", f'attachment; filename="{filename}"')
            ]
            return _send_response(start_response, 200, binary_content=pdf_bytes, content_type="application/pdf", extra_headers=extra_headers)

        # GET /api/audit/<audit_id>
        ca = audit_row["created_at"]
        if isinstance(ca, datetime):
            ca = ca.isoformat()
        audit_resp = {
            "id": str(audit_row["id"]),
            "domain": audit_row["domain"],
            "score": audit_row["score"],
            "scan_type": audit_row["scan_type"],
            "created_at": ca,
            "results": results_data
        }
        return _send_response(start_response, 200, body_dict={"success": True, "audit": audit_resp})

    # 10. Lockdown Mode Gating: All Paid/Mutating APIs return 503 Fail-Closed
    lockdown_paid_routes = [
        "/api/leads/generate", "/api/leads/clear",
        "/api/content/generate", "/api/content-crew/run",
        "/api/checkout/create", "/api/audit/dossier",
        "/api/booking/clear"
    ]
    if is_lockdown_enabled():
        if path_lower in lockdown_paid_routes or path_lower.startswith("/api/documents") or path_lower.startswith("/api/upload"):
            return _send_response(start_response, 503, body_dict={"error": "feature_temporarily_unavailable"})
        if path_lower.startswith("/report/dossier"):
            return _send_response(start_response, 503, text_content="Feature temporarily unavailable", content_type="text/plain")

    # 11. Read Request Body for Inspected Endpoints
    content_length = 0
    try:
        content_length = int(environ.get('CONTENT_LENGTH', 0))
    except (ValueError, TypeError):
        content_length = 0

    raw_body = b""
    if content_length > 0:
        raw_body = environ['wsgi.input'].read(content_length)
    # Restore wsgi.input so downstream callers can read
    environ['wsgi.input'] = io.BytesIO(raw_body)

    # 12. SSRF Protection: /api/audit/run & /api/audit/scan
    if path_lower in ["/api/audit/run", "/api/audit/scan"]:
        if method != "POST":
            return _send_response(start_response, 404, body_dict={"error": "Endpoint not found"})

        try:
            body_json = json.loads(raw_body.decode('utf-8')) if raw_body else {}
        except Exception:
            body_json = {}

        target = (
            body_json.get("target") or
            body_json.get("url_or_company") or
            body_json.get("domain") or
            body_json.get("company", "")
        )

        if target:
            is_safe, safe_target, ssrf_err = validate_url_ssrf_safe(target)
            if not is_safe:
                return _send_response(start_response, 400, body_dict={
                    "error": "prohibited_target_address",
                    "reason": ssrf_err,
                    "details": ssrf_err
                })

        # Check authentication & session
        sess = _get_session(environ, headers)
        ws_id = None
        user_id = None
        plan_name = "free"
        if sess:
            user_id = sess.get("user_id")
            ws = sess.get("workspace")
            if ws:
                ws_id = ws.get("id")
                plan_name = ws.get("plan", "free")

        # If authenticated, enforce plan limit BEFORE executing scan
        if sess and ws_id:
            allowed, reason, ent_info = check_db_entitlement(ws_id, "audit", increment_usage=False, user_id=user_id)
            if not allowed:
                return _send_response(start_response, 403, body_dict={
                    "error": "usage_limit_reached",
                    "plan": ent_info.get("plan") or plan_name,
                    "used": ent_info.get("usage_count", 2),
                    "limit": ent_info.get("usage_limit", 2),
                    "upgrade_url": "/pricing",
                    "message": "Monthly audit limit reached. Please upgrade to Pro."
                })

        from app import AUDIT_ENGINE
        ind_hint = body_json.get('industry', 'Real Estate')
        m_visitors = body_json.get('monthly_visitors')
        a_deal = body_json.get('avg_deal_value') or body_json.get('deal_value')
        audit_res = AUDIT_ENGINE.run_instant_audit(target or "Apex Global Real Estate", ind_hint, monthly_visitors=m_visitors, avg_deal_value=a_deal)

        audit_id = str(uuid.uuid4())

        # If authenticated: atomically increment usage and insert into audits table
        if sess and ws_id:
            check_db_entitlement(ws_id, "audit", increment_usage=True, user_id=user_id)

            from db.connection import get_db_cursor, is_sqlite
            now_dt = datetime.now(timezone.utc)
            now_iso = now_dt.isoformat()
            audit_score = audit_res.get("ai_readiness_score") or audit_res.get("score") or audit_res.get("total_leak_score") or 50
            try:
                audit_score = int(audit_score)
            except Exception:
                audit_score = 50
            results_json = json.dumps(audit_res)
            domain_val = target or "Apex Global Real Estate"
            competitor_val = body_json.get("competitor_domain")
            scan_type_val = body_json.get("scan_type", "single")

            with get_db_cursor(commit=True) as cur:
                if is_sqlite():
                    cur.execute("""
                        INSERT INTO audits (id, workspace_id, user_id, domain, competitor_domain, scan_type, results, score, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
                    """, (audit_id, ws_id, user_id, domain_val, competitor_val, scan_type_val, results_json, audit_score, now_iso))
                else:
                    cur.execute("""
                        INSERT INTO audits (id, workspace_id, user_id, domain, competitor_domain, scan_type, results, score, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW());
                    """, (audit_id, ws_id, user_id, domain_val, competitor_val, scan_type_val, results_json, audit_score))

            if not is_lockdown_enabled():
                try:
                    from app import AUDITS, save_audits
                    AUDITS.append(audit_res)
                    save_audits()
                except Exception:
                    pass

            resp = {"success": True, "audit_id": audit_id, "id": audit_id, "audit": audit_res}
            resp.update(audit_res)
            resp["audit_id"] = audit_id
            resp["id"] = audit_id
            return _send_response(start_response, 200, body_dict=resp)

        # Anonymous user: do not save to DB, do not increment usage
        if not is_lockdown_enabled():
            try:
                from app import AUDITS, save_audits
                AUDITS.append(audit_res)
                save_audits()
            except Exception:
                pass

        resp = {"success": True, "audit": audit_res}
        resp.update(audit_res)
        return _send_response(start_response, 200, body_dict=resp)

    # 13. Lemon Squeezy Webhook Verification: /api/payment/webhook
    if path_lower == "/api/payment/webhook":
        if method != "POST":
            return _send_response(start_response, 404, body_dict={"error": "Endpoint not found"})

        sig = headers.get("X-Signature") or headers.get("x-signature") or headers.get("HTTP_X_SIGNATURE") or ""
        is_valid, msg, code, data = verify_lemonsqueezy_webhook(raw_body, sig)
        if not is_valid:
            resp_err = {"error": msg}
            if isinstance(data, dict):
                resp_err.update(data)
            return _send_response(start_response, code, body_dict=resp_err)
        resp_ok = {"success": True, "status": "success", "message": msg}
        if isinstance(data, dict):
            resp_ok.update(data)
        return _send_response(start_response, 200, body_dict=resp_ok)

    # 14. Non-Lockdown Entitlement & Auth Enforcement for Paid Routes
    if path_lower in ["/api/leads/generate", "/api/content/generate", "/api/content-crew/run"]:
        try:
            body_json = json.loads(raw_body.decode('utf-8')) if raw_body else {}
        except Exception:
            body_json = {}

        is_auth, user_ctx, auth_err = require_authenticated_user(headers, body_json)
        if not is_auth:
            st_code = get_auth_error_status(auth_err)
            return _send_response(start_response, st_code, body_dict={"error": auth_err, "details": auth_err})

        feature = "b2b_leads" if "lead" in path_lower else "seo_content"
        has_ent, ent_err = require_active_entitlement(user_ctx, feature)
        if not has_ent:
            return _send_response(start_response, 403, body_dict={"error": "feature_not_entitled", "details": ent_err})

        original_app = get_original_app()
        return original_app(environ, start_response)

    # 15. Public Redesign Preview Handler (/preview/*)
    if path_lower.startswith("/preview/"):
        demo_name = raw_path.replace("/preview/", "").strip()
        if not demo_name.endswith(".html"):
            demo_name = f"{demo_name}.html"
        from engine.security_guard import get_storage_dir
        storage_dir = get_storage_dir()
        demo_path = os.path.join(storage_dir, "demos", demo_name)
        if os.path.exists(demo_path) and os.path.isfile(demo_path):
            with open(demo_path, "rb") as f:
                content = f.read()
            return _send_response(start_response, 200, text_content=content.decode("utf-8", errors="ignore"), content_type="text/html")
        else:
            return _send_response(start_response, 404, text_content="Demo Not Found", content_type="text/html")

    # 16. Booking Chat Mutation Containment in Lockdown Mode
    if path_lower == "/api/booking/chat" and is_lockdown_enabled():
        from app import BOOKING_AGENT
        try:
            body_json = json.loads(raw_body.decode('utf-8')) if raw_body else {}
        except Exception:
            body_json = {}
        msg = body_json.get('message', '')
        hist = body_json.get('history', [])
        ctx = body_json.get('business_context', 'LeakGrader AI Solutions')
        res = BOOKING_AGENT.chat_and_qualify(ctx, hist, msg)
        res['auto_booked'] = False
        return _send_response(start_response, 200, body_dict=res)

    # 17. Pass Allowed & Public Requests to Inner wsgi.application
    original_app = get_original_app()
    return original_app(environ, start_response)
