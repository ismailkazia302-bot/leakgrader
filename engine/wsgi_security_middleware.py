"""
WSGI Security Middleware for LeakGrader Production Gateway (Sprint 0.7+)
Wraps wsgi.application to enforce fail-closed lockdown, route hiding,
authentication, active entitlements, Lemon Squeezy HMAC signature validation,
and SSRF rejection on the WSGI / Gunicorn production path.
"""

import os
import sys
import json
import io
import time
from urllib.parse import unquote

from engine.security_guard import (
    is_lockdown_enabled,
    require_authenticated_user,
    require_active_entitlement,
    require_admin,
    verify_lemonsqueezy_webhook,
    validate_url_ssrf_safe,
    get_auth_error_status
)

SECURITY_HEADERS = [
    ("Strict-Transport-Security", "max-age=31536000; includeSubDomains; preload"),
    ("X-Content-Type-Options", "nosniff"),
    ("X-Frame-Options", "SAMEORIGIN"),
    ("Referrer-Policy", "strict-origin-when-cross-origin"),
    ("Permissions-Policy", "geolocation=(), microphone=(), camera=()"),
    ("Access-Control-Allow-Origin", "*"),
    ("Access-Control-Allow-Methods", "GET, HEAD, POST, PUT, PATCH, DELETE, OPTIONS"),
    ("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Signature")
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


def _send_response(start_response, status_code: int, body_dict: dict = None, text_content: str = None, content_type: str = "application/json"):
    status_str = f"{status_code} "
    if status_code == 200: status_str += "OK"
    elif status_code == 400: status_str += "Bad Request"
    elif status_code == 401: status_str += "Unauthorized"
    elif status_code == 403: status_str += "Forbidden"
    elif status_code == 404: status_str += "Not Found"
    elif status_code == 405: status_str += "Method Not Allowed"
    elif status_code == 422: status_str += "Unprocessable Entity"
    elif status_code == 503: status_str += "Service Unavailable"
    else: status_str += "Response"

    headers = [("Content-Type", f"{content_type}; charset=utf-8")]
    for k, v in SECURITY_HEADERS:
        headers.append((k, v))

    start_response(status_str, headers)
    if body_dict is not None:
        return [json.dumps(body_dict).encode("utf-8")]
    elif text_content is not None:
        return [text_content.encode("utf-8")]
    return [b""]


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

    # 6. Admin Routes Protection (Lockdown hides 404; non-lockdown requires valid admin token)
    admin_ui_routes = ["/founder", "/analytics", "/dashboard"]
    admin_api_prefixes = [
        "/api/pipeline", "/api/subscribers", "/api/analytics",
        "/api/seo/recent-activity", "/api/contact/list", "/api/booking/list"
    ]

    if path_lower in admin_ui_routes:
        if is_lockdown_enabled():
            return _send_response(start_response, 404, text_content="404 Not Found", content_type="text/plain")
        is_adm, err = require_admin(headers)
        if not is_adm:
            return _send_response(start_response, 404, text_content="404 Not Found", content_type="text/plain")
        original_app = get_original_app()
        return original_app(environ, start_response)

    if any(path_lower == p or path_lower.startswith(p + "/") for p in admin_api_prefixes):
        if is_lockdown_enabled():
            return _send_response(start_response, 404, body_dict={"error": "not_found"})
        is_adm, err = require_admin(headers)
        if not is_adm:
            return _send_response(start_response, 403, body_dict={"error": "admin_authorization_required", "details": err})
        original_app = get_original_app()
        return original_app(environ, start_response)

    # 7. Method-Route Alignment (Non-existent methods on defined endpoints return 404 Endpoint not found)
    post_only_routes = [
        "/api/leads/generate", "/api/content/generate",
        "/api/checkout/create", "/api/payment/webhook",
        "/api/booking/clear"
    ]
    if method == "GET" and path_lower in post_only_routes:
        return _send_response(start_response, 404, body_dict={"error": "Endpoint not found"})

    if method == "POST" and path_lower in ["/api/audit/dossier"]:
        return _send_response(start_response, 404, body_dict={"error": "Endpoint not found"})

    # 8. Lockdown Mode Gating: All Paid/Mutating APIs return 503 Fail-Closed
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

    # 9. Read Request Body for Inspected Endpoints
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

    # 10. SSRF Protection: /api/audit/run & /api/audit/scan
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
                    "details": ssrf_err
                })

        # Under lockdown mode, execute audit without file persistence
        if is_lockdown_enabled():
            from app import AUDIT_ENGINE
            ind_hint = body_json.get('industry', 'Real Estate')
            m_visitors = body_json.get('monthly_visitors')
            a_deal = body_json.get('avg_deal_value') or body_json.get('deal_value')
            audit_res = AUDIT_ENGINE.run_instant_audit(target or "Apex Global Real Estate", ind_hint, monthly_visitors=m_visitors, avg_deal_value=a_deal)
            resp = {"success": True, "audit": audit_res}
            resp.update(audit_res)
            return _send_response(start_response, 200, body_dict=resp)

        original_app = get_original_app()
        return original_app(environ, start_response)

    # 11. Lemon Squeezy Webhook Verification: /api/payment/webhook
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
        resp_ok = {"success": True, "message": msg}
        if isinstance(data, dict):
            resp_ok.update(data)
        return _send_response(start_response, 200, body_dict=resp_ok)

    # 12. Non-Lockdown Entitlement & Auth Enforcement for Paid Routes
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

    # 13. Public Redesign Preview Handler (/preview/*)
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

    # 14. Booking Chat Mutation Containment in Lockdown Mode
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

    # 15. Pass Allowed & Public Requests to Inner wsgi.application
    original_app = get_original_app()
    return original_app(environ, start_response)
