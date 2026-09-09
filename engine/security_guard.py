"""
LeakGrader - Centralized Server-Side Security & Entitlement Engine (Sprint 0)
Handles:
1. Emergency Lockdown Mode (default enabled in production)
2. Centralized Authentication & Authorization Checks (Default DENY)
3. Lemon Squeezy Webhook HMAC-SHA256 Signature Verification & Idempotency
4. Mutex-protected Atomic Persistence
"""

import os
import hmac
import hashlib
import json
import time
import socket
import ipaddress
import threading
import tempfile
import logging
from urllib.parse import urlparse
from datetime import datetime, timezone, timedelta

logger = logging.getLogger("leakgrader.security")

# Global re-entrant lock for file persistence and webhook state
_SECURITY_LOCK = threading.RLock()

def get_storage_dir() -> str:
    """Dynamic resolution of storage directory, respecting STORAGE_DIR environment variable."""
    return os.environ.get("STORAGE_DIR") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "storage")

def get_processed_webhooks_file() -> str:
    return os.path.join(get_storage_dir(), "processed_webhook_events.json")

def get_entitlements_file() -> str:
    return os.path.join(get_storage_dir(), "active_entitlements.json")


def is_lockdown_enabled() -> bool:
    """
    Emergency Lockdown Mode setting.
    Fail-closed rules:
    - Defaults to ENABLED in all environments (including production, staging, unconfigured, or blank).
    - Can be disabled ONLY when ENVIRONMENT is explicitly 'local' or 'test' AND RENDER is not 'true'.
    - In production, staging, or when RENDER='true', ambiguous, blank, or malformed configurations remain LOCKED (True).
    - Never relies on frontend JavaScript, localStorage, query params, or body flags.
    """
    env = os.environ.get("ENVIRONMENT", "").strip().lower()
    is_render = os.environ.get("RENDER", "").strip().lower() in ["true", "1", "yes"]

    # In production, staging, Render cloud, or any environment not explicitly local/test:
    # Lockdown CANNOT be disabled under any circumstance.
    if env not in ["local", "test"] or is_render:
        return True

    # In local or test environment:
    val = os.environ.get("SECURITY_LOCKDOWN_MODE", "true").strip().lower()
    if val in ["false", "0", "disabled", "no", "off"]:
        return False
    return True


def get_auth_error_status(err_code: str) -> int:
    """
    Maps authorization/authentication failure reason to standard HTTP status codes:
    - 401 Unauthorized: missing identity, invalid token format, unrecognized token, expired token, paused token.
    - 403 Forbidden: client spoofing, unauthorized admin claim, cross-workspace access, ownership mismatch.
    """
    if err_code in [
        "authentication_required",
        "invalid_token",
        "unrecognized_token",
        "token_expired",
        "token_expired_grace_period_ended",
        "token_paused",
        "unrecognized_token_status",
        "missing_signature_header",
        "invalid_signature_digest_mismatch"
    ]:
        return 401
    return 403


def require_authenticated_user(headers: dict, body_data: dict = None) -> tuple:
    """
    Validates authenticated user identity server-side.
    Default result: DENY.
    Never accepts paid=true, admin=true, user_id, tenant_id, or workspace_id
    supplied by the client browser as proof of authorization.
    """
    # Reject client spoofing attempts
    if body_data:
        if body_data.get("admin") in [True, "true"] or body_data.get("is_admin") in [True, "true"]:
            is_adm, _ = require_admin(headers)
            if not is_adm:
                return False, None, "unauthorized_admin_claim"

    auth_header = headers.get("Authorization", "") or headers.get("authorization", "")
    if not auth_header or not auth_header.startswith("Bearer "):
        return False, None, "authentication_required"

    token = auth_header[7:].strip()
    if not token or len(token) < 16:
        return False, None, "invalid_token"

    # Verify token against active verified entitlements
    entitlements = _load_entitlements()
    user_record = entitlements.get(token)
    if not user_record:
        return False, None, "unrecognized_token"

    status = user_record.get("status")
    expires_at = user_record.get("expires_at", 0)
    current_time = time.time()

    # Lifecycle State Verification
    if status == "active":
        if expires_at and expires_at <= current_time:
            return False, None, "token_expired"
        # Access allowed (including cancelled subscriptions where auto_renew is False but expires_at > current_time)
    elif status == "past_due":
        # Configurable grace period (default 3 days)
        try:
            grace_days = float(os.environ.get("PAYMENT_GRACE_PERIOD_DAYS", "3"))
        except Exception:
            grace_days = 3.0
        past_due_since = user_record.get("past_due_since", current_time)
        if (current_time - past_due_since) > (grace_days * 86400):
            return False, None, "token_expired_grace_period_ended"
        # Access allowed during grace period
    elif status == "paused":
        return False, None, "token_paused"
    elif status in ["inactive", "revoked", "expired", "cancelled"]:
        return False, None, "token_expired"
    else:
        # missing or unknown status
        return False, None, "unrecognized_token_status"

    # Strict multi-tenant isolation: Verify workspace_id if specified in request
    if body_data and "workspace_id" in body_data:
        req_ws = str(body_data["workspace_id"]).strip()
        user_ws = str(user_record.get("workspace_id") or user_record.get("customer_ref", "")).strip()
        if req_ws and user_ws and req_ws != user_ws:
            return False, user_record, "cross_workspace_access_forbidden"

    # Verify user_id if specified
    if body_data and "user_id" in body_data:
        req_uid = str(body_data["user_id"]).strip()
        user_uid = str(user_record.get("user_id") or user_record.get("customer_ref", "")).strip()
        if req_uid and user_uid and req_uid != user_uid:
            return False, user_record, "resource_ownership_mismatch"

    return True, user_record, None


def require_active_entitlement(user_ctx: dict, feature: str) -> tuple:
    """
    Verifies that the authenticated user possesses an active entitlement for the feature.
    Default result: DENY.
    """
    if not user_ctx:
        return False, "entitlement_required"

    status = user_ctx.get("status")
    if status not in ["active", "past_due"]:
        return False, "entitlement_inactive"


    plan = user_ctx.get("plan", "")
    allowed_features = user_ctx.get("features", [])

    if plan in ["pro_saas", "agency_retainer", "enterprise"]:
        return True, None

    if feature in allowed_features:
        return True, None

    return False, "feature_not_entitled"


def require_admin(headers: dict) -> tuple:
    """
    Server-side admin authorization.
    Default result: DENY.
    Does not use hardcoded passwords or trust browser claims.
    """
    admin_secret = os.environ.get("ADMIN_TOKEN", "") or os.environ.get("ADMIN_PASSWORD", "")
    if not admin_secret:
        # In production without admin secret configured, deny unconditionally
        return False, "admin_access_unconfigured"

    auth_header = headers.get("Authorization", "") or headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
        if hmac.compare_digest(token, admin_secret):
            return True, None

    return False, "admin_authorization_required"


def require_workspace_access(user_ctx: dict, resource_workspace_id: str) -> tuple:
    """
    Validates that the authenticated user belongs to the requested workspace.
    Default result: DENY.
    """
    if not user_ctx or not resource_workspace_id:
        return False, "workspace_access_denied"

    user_ws = user_ctx.get("workspace_id")
    if not user_ws or user_ws != resource_workspace_id:
        return False, "cross_workspace_access_forbidden"

    return True, None


def require_resource_ownership(user_ctx: dict, resource_owner_id: str) -> tuple:
    """
    Validates that the authenticated user is the owner of the requested resource.
    Default result: DENY.
    """
    if not user_ctx or not resource_owner_id:
        return False, "ownership_verification_failed"

    user_id = user_ctx.get("user_id")
    if not user_id or user_id != resource_owner_id:
        return False, "resource_ownership_mismatch"

    return True, None


# ==============================================================================
# SSRF VALIDATION ENGINE (Public Scanner & Live Website Forensics)
# ==============================================================================

def validate_url_ssrf_safe(url_or_domain: str) -> tuple:
    """
    Comprehensive Server-Side Request Forgery (SSRF) Guard.
    Validates targets before any outbound HTTP/HTTPS connection is made.
    Strictly forbids:
    - Non-HTTP/HTTPS schemes (file://, ftp://, gopher://, dict://, data:, etc.)
    - Localhost, 127.0.0.0/8, 0.0.0.0, ::1
    - RFC1918 Private ranges (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16, fc00::/7)
    - Link-local and Cloud Metadata (169.254.0.0/16, 169.254.169.254, fe80::/10)
    - Multicast (224.0.0.0/4, ff00::/8)
    - Reserved/Broadcast/Unspecified addresses
    - Carrier-Grade NAT (100.64.0.0/10)
    - Numeric, octal, and hex encoded IP formats resolving to internal ranges
    - Userinfo credentials (user:pass@host)
    - Non-standard ports (allows standard 80 and 443 only)
    - Internal and mDNS hostnames (.local, .internal, .localhost, .lan, etc.)
    
    Returns: (is_safe: bool, sanitized_url: str, reason: str)
    """
    if not url_or_domain or not isinstance(url_or_domain, str):
        return False, "", "empty_target"

    target = url_or_domain.strip()
    if not target:
        return False, "", "empty_target"

    # Reject dangerous scheme prefixes
    lower_target = target.lower()
    dangerous_schemes = [
        "file:", "ftp:", "gopher:", "dict:", "ldap:", "tftp:", "ssh:",
        "data:", "javascript:", "vbscript:", "blob:", "about:", "mailto:"
    ]
    for ds in dangerous_schemes:
        if lower_target.startswith(ds):
            return False, "", f"forbidden_scheme_{ds.rstrip(':')}"

    # Check if target is a plain business name (e.g. "Test Apex", "Acme Corp")
    # A plain business name contains spaces or has no dots and no scheme, but isn't localhost or an integer/hex
    if "://" not in target and (" " in target or ("." not in target and not target.isdigit() and not lower_target.startswith("0x") and lower_target != "localhost")):
        return True, target, "company_name_safe"

    if "://" not in target:
        test_url = f"https://{target}"
    else:
        test_url = target

    try:
        parsed = urlparse(test_url)
    except Exception as e:
        return False, "", f"invalid_url_syntax: {e}"

    scheme = (parsed.scheme or "").lower()
    if scheme not in ["http", "https"]:
        return False, "", f"forbidden_scheme_{scheme}"

    # Reject embedded userinfo (e.g. admin:pass@host)
    if parsed.username or parsed.password or "@" in (parsed.netloc.split("?")[0].split("#")[0]):
        return False, "", "userinfo_not_permitted"

    hostname = parsed.hostname
    if not hostname:
        return False, "", "missing_hostname"

    hostname = hostname.strip().lower()

    # Port restriction: only standard web ports (80, 443) allowed for public scanner
    port = parsed.port
    if port is not None and port not in [80, 443]:
        return False, "", f"forbidden_port_{port}"

    # Reject internal, loopback, and local network TLDs
    forbidden_suffixes = [
        ".local", ".localhost", ".internal", ".lan", ".home", ".corp",
        ".arpa", ".invalid", ".test", ".example", ".intranet", ".onion"
    ]
    if hostname == "localhost" or any(hostname.endswith(sfx) for sfx in forbidden_suffixes):
        return False, "", "prohibited_internal_hostname"

    # Check for direct decimal, octal, or hex IP representations
    parts = hostname.split(".")
    is_numeric_like = all(p.isdigit() or p.startswith("0x") for p in parts) and len(parts) <= 4

    # Resolve hostname via DNS to verify all destination IP addresses
    try:
        addr_info = socket.getaddrinfo(
            hostname,
            port or (443 if scheme == "https" else 80),
            proto=socket.IPPROTO_TCP
        )
    except socket.gaierror as e:
        if is_numeric_like:
            return False, "", "prohibited_numeric_ip_format"
        return False, "", f"dns_resolution_failed: {e}"
    except Exception as e:
        return False, "", f"resolution_error: {e}"

    if not addr_info:
        return False, "", "no_dns_records_found"

    # Evaluate all resolved IP addresses against private / loopback / cloud metadata CIDRs
    for entry in addr_info:
        sockaddr = entry[4]
        ip_str = sockaddr[0]
        try:
            ip_obj = ipaddress.ip_address(ip_str)
        except ValueError:
            return False, "", f"invalid_resolved_ip: {ip_str}"

        # Standard IP flags
        if (
            ip_obj.is_loopback
            or ip_obj.is_private
            or ip_obj.is_link_local
            or ip_obj.is_multicast
            or ip_obj.is_reserved
            or ip_obj.is_unspecified
        ):
            return False, "", f"prohibited_destination_ip: {ip_str}"

        # Carrier-Grade NAT (100.64.0.0/10) & 0.0.0.0/8
        if isinstance(ip_obj, ipaddress.IPv4Address):
            if ip_obj in ipaddress.IPv4Network("100.64.0.0/10"):
                return False, "", f"prohibited_cgnat_ip: {ip_str}"
            if ip_obj in ipaddress.IPv4Network("0.0.0.0/8"):
                return False, "", f"prohibited_broadcast_ip: {ip_str}"
            if ip_obj in ipaddress.IPv4Network("198.18.0.0/15"):
                return False, "", f"prohibited_benchmark_ip: {ip_str}"

        # IPv4-mapped IPv6 check
        if isinstance(ip_obj, ipaddress.IPv6Address) and ip_obj.ipv4_mapped:
            mapped_v4 = ip_obj.ipv4_mapped
            if (
                mapped_v4.is_loopback
                or mapped_v4.is_private
                or mapped_v4.is_link_local
                or mapped_v4.is_multicast
                or mapped_v4.is_reserved
            ):
                return False, "", f"prohibited_mapped_ipv4: {mapped_v4}"

    return True, test_url, "safe"


# ==============================================================================
# LEMON SQUEEZY WEBHOOK VERIFICATION & IDEMPOTENCY
# ==============================================================================

def _parse_iso_timestamp(val) -> float:
    """
    Safely parses an ISO 8601 timestamp string or numeric timestamp to float epoch seconds.
    Fails safely returning 0.0 if unparseable or empty, never raises an exception.
    """
    if not val:
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        s = val.strip()
        if not s:
            return 0.0
        # Replace Zulu with UTC offset
        clean_s = s.replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(clean_s).timestamp()
        except Exception:
            pass
        for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
            try:
                dt = datetime.strptime(s.split(".")[0], fmt)
                return dt.replace(tzinfo=timezone.utc).timestamp()
            except Exception:
                pass
    return 0.0


def verify_lemonsqueezy_webhook(raw_body: bytes, signature: str, secret: str = None) -> tuple:
    """
    Verifies incoming Lemon Squeezy webhook per strict specification:
    1. Reads exact raw request body as bytes.
    2. Reads secret from LEMONSQUEEZY_WEBHOOK_SECRET.
    3. Calculates HMAC-SHA256 hex digest of exact raw body.
    4. Compares against X-Signature using hmac.compare_digest.
    5. Returns (False, "missing_secret", 503, {}) if signing secret missing.
    6. Returns (False, "missing_or_invalid_signature", 401, {}) for bad signature.
    7. Verifies event structure, store_id, product/variant, and environment.
    8. Implements idempotency / replay protection.
    9. Handles full subscription lifecycle:
       - Cancellations: retains access until ends_at expires (auto_renew=False).
       - Expirations: revokes active access (status=inactive).
       - Pauses: marks paused (status=paused).
       - Resumes: reactivates access (status=active).
       - Payment failures: marks past_due (status=past_due) with grace period.
    10. Does not log complete webhook payloads or personal data.
    """
    webhook_secret = secret if secret is not None else os.environ.get("LEMONSQUEEZY_WEBHOOK_SECRET", "")
    if not webhook_secret:
        return False, "missing_production_signing_secret", 503, {}

    if not signature or not isinstance(signature, str):
        return False, "missing_signature_header", 401, {}

    # Calculate HMAC-SHA256 hex digest of raw body bytes
    try:
        computed_sig = hmac.new(
            webhook_secret.encode("utf-8"),
            raw_body,
            hashlib.sha256
        ).hexdigest()
    except Exception as e:
        return False, f"signature_computation_error: {e}", 401, {}

    if not hmac.compare_digest(computed_sig, signature.strip()):
        return False, "invalid_signature_digest_mismatch", 401, {}

    # Parse JSON safely
    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except Exception as e:
        return False, f"malformed_json_body: {e}", 400, {}

    meta = payload.get("meta", {})
    data = payload.get("data", {})
    event_name = meta.get("event_name", "")

    # Comprehensive list of valid Lemon Squeezy event names
    valid_events = [
        "order_created",
        "subscription_created",
        "subscription_updated",
        "subscription_cancelled",
        "subscription_resumed",
        "subscription_expired",
        "subscription_paused",
        "subscription_unpaid",
        "subscription_payment_failed",
        "subscription_payment_success"
    ]
    if event_name not in valid_events:
        return False, f"unsupported_event_type: {event_name}", 422, {}

    attributes = data.get("attributes", {})

    # Check expected store_id if configured in environment
    expected_store = os.environ.get("LEMONSQUEEZY_STORE_ID", "")
    received_store = str(attributes.get("store_id", ""))
    if expected_store and received_store and expected_store != received_store:
        return False, "wrong_store_id", 400, {}

    # Check expected product_id / variant_id if configured
    expected_variants = [v.strip() for v in os.environ.get("LEMONSQUEEZY_VARIANT_IDS", "").split(",") if v.strip()]
    if expected_variants:
        received_variant = str(
            attributes.get("variant_id")
            or attributes.get("first_order_item", {}).get("variant_id")
            or ""
        )
        if received_variant and received_variant not in expected_variants:
            return False, "unknown_product_or_variant", 422, {}

    # Environment check: Test event received by live configuration
    is_test_mode = meta.get("test_mode", False)
    is_production = os.environ.get("RENDER", "").lower() == "true" or os.environ.get("ENVIRONMENT", "").lower() == "production"
    allow_test_events = os.environ.get("ALLOW_TEST_WEBHOOKS", "false").lower() in ["true", "1"]
    if is_production and is_test_mode and not allow_test_events:
        return False, "test_event_rejected_in_live_production", 400, {}

    order_or_sub_id = str(data.get("id", ""))
    sub_status = str(attributes.get("status", "")).lower()

    # Event ID for idempotency: scoped by event name and resource ID
    event_id = (
        meta.get("custom_data", {}).get("event_id")
        or f"{event_name}_{order_or_sub_id}"
    )

    # Sync to PostgreSQL database tables (Sprint 1)
    sync_webhook_to_db(event_id, event_name, raw_body, payload)

    with _SECURITY_LOCK:
        processed_events = _load_processed_webhooks()
        if event_id in processed_events:
            # Duplicate webhook delivery: Idempotency protection
            return True, "duplicate_webhook_delivery_ignored", 200, {
                "event_id": event_id,
                "status": "duplicate_ignored"
            }

        # Case A1: Subscription Cancelled (Auto-renewal stopped, keep access until ends_at)
        if event_name == "subscription_cancelled":
            ends_at_val = attributes.get("ends_at")
            parsed_ends_at = _parse_iso_timestamp(ends_at_val)
            entitlements = _load_entitlements()
            updated_count = 0
            for tok, rec in list(entitlements.items()):
                if str(rec.get("order_id", "")) == order_or_sub_id:
                    rec["auto_renew"] = False
                    rec["cancelled_at"] = time.time()
                    if parsed_ends_at > 0:
                        rec["expires_at"] = parsed_ends_at
                    # Keep status active if ends_at is in future, otherwise inactive
                    if rec.get("expires_at", 0) > time.time():
                        rec["status"] = "active"
                    elif rec.get("expires_at", 0) > 0:
                        rec["status"] = "inactive"
                    updated_count += 1
            if updated_count > 0:
                _atomic_json_dump(get_entitlements_file(), entitlements)

            processed_events[event_id] = {
                "processed_at": time.time(),
                "event_name": event_name,
                "action": "subscription_cancelled",
                "updated_count": updated_count
            }
            _atomic_json_dump(get_processed_webhooks_file(), processed_events)

            return True, "subscription_cancelled_processed", 200, {
                "event_id": event_id,
                "status": "cancelled",
                "auto_renew": False,
                "active_entitlement_created": False
            }

        # Case A2: Subscription Expired or Unpaid
        elif event_name in ["subscription_expired", "subscription_unpaid"]:
            entitlements = _load_entitlements()
            revoked_count = 0
            for tok, rec in list(entitlements.items()):
                if str(rec.get("order_id", "")) == order_or_sub_id:
                    rec["status"] = "inactive"
                    rec["revoked_at"] = time.time()
                    rec["expires_at"] = min(rec.get("expires_at", time.time()), time.time())
                    revoked_count += 1
            if revoked_count > 0:
                _atomic_json_dump(get_entitlements_file(), entitlements)

            processed_events[event_id] = {
                "processed_at": time.time(),
                "event_name": event_name,
                "action": "subscription_expired",
                "revoked_count": revoked_count
            }
            _atomic_json_dump(get_processed_webhooks_file(), processed_events)

            return True, "subscription_status_updated_inactive", 200, {
                "event_id": event_id,
                "status": "inactive",
                "active_entitlement_created": False
            }

        # Case A3: Subscription Paused
        elif event_name == "subscription_paused":
            entitlements = _load_entitlements()
            paused_count = 0
            for tok, rec in list(entitlements.items()):
                if str(rec.get("order_id", "")) == order_or_sub_id:
                    rec["status"] = "paused"
                    rec["paused_at"] = time.time()
                    paused_count += 1
            if paused_count > 0:
                _atomic_json_dump(get_entitlements_file(), entitlements)

            processed_events[event_id] = {
                "processed_at": time.time(),
                "event_name": event_name,
                "action": "subscription_paused",
                "paused_count": paused_count
            }
            _atomic_json_dump(get_processed_webhooks_file(), processed_events)

            return True, "subscription_status_updated_paused", 200, {
                "event_id": event_id,
                "status": "paused",
                "active_entitlement_created": False
            }

        # Case A4: Subscription Resumed
        elif event_name == "subscription_resumed":
            entitlements = _load_entitlements()
            resumed_count = 0
            for tok, rec in list(entitlements.items()):
                if str(rec.get("order_id", "")) == order_or_sub_id:
                    rec["status"] = "active"
                    rec["auto_renew"] = True
                    rec.pop("paused_at", None)
                    renews_at = attributes.get("renews_at") or attributes.get("ends_at")
                    parsed_renews = _parse_iso_timestamp(renews_at)
                    if parsed_renews > time.time():
                        rec["expires_at"] = parsed_renews
                    elif rec.get("expires_at", 0) <= time.time():
                        rec["expires_at"] = time.time() + (30 * 86400)
                    resumed_count += 1
            if resumed_count > 0:
                _atomic_json_dump(get_entitlements_file(), entitlements)

            processed_events[event_id] = {
                "processed_at": time.time(),
                "event_name": event_name,
                "action": "subscription_resumed",
                "resumed_count": resumed_count
            }
            _atomic_json_dump(get_processed_webhooks_file(), processed_events)

            return True, "subscription_status_updated_resumed", 200, {
                "event_id": event_id,
                "status": "active",
                "active_entitlement_created": True
            }

        # Case A5: Subscription Payment Failed (Past Due with Grace Period)
        elif event_name == "subscription_payment_failed":
            entitlements = _load_entitlements()
            failed_count = 0
            for tok, rec in list(entitlements.items()):
                if str(rec.get("order_id", "")) == order_or_sub_id:
                    rec["status"] = "past_due"
                    if "past_due_since" not in rec:
                        rec["past_due_since"] = time.time()
                    failed_count += 1
            if failed_count > 0:
                _atomic_json_dump(get_entitlements_file(), entitlements)

            processed_events[event_id] = {
                "processed_at": time.time(),
                "event_name": event_name,
                "action": "subscription_payment_failed",
                "failed_count": failed_count
            }
            _atomic_json_dump(get_processed_webhooks_file(), processed_events)

            return True, "subscription_status_updated_past_due", 200, {
                "event_id": event_id,
                "status": "past_due",
                "active_entitlement_created": False
            }

        # Case B: Active Entitlement Creation (order_created, subscription_created)
        user_email = attributes.get("user_email", "")
        customer_hash = hashlib.sha256(user_email.encode("utf-8")).hexdigest()[:16] if user_email else "anon"

        token_id = f"ent_{hashlib.sha256((order_or_sub_id + str(time.time())).encode('utf-8')).hexdigest()[:24]}"
        ends_at_val = _parse_iso_timestamp(attributes.get("ends_at"))
        default_expiry = time.time() + (30 * 86400) if "subscription" in event_name else 0

        entitlement_record = {
            "token": token_id,
            "order_id": order_or_sub_id,
            "customer_ref": customer_hash,
            "plan": "pro_saas",
            "features": ["b2b_leads", "seo_articles", "ai_closer"],
            "created_at": time.time(),
            "expires_at": ends_at_val if ends_at_val > 0 else default_expiry,
            "auto_renew": True if "subscription" in event_name else False,
            "status": "active",
            "event_name": event_name
        }

        # Record entitlement
        entitlements = _load_entitlements()
        entitlements[token_id] = entitlement_record
        _atomic_json_dump(get_entitlements_file(), entitlements)

        # Mark event processed
        processed_events[event_id] = {
            "processed_at": time.time(),
            "event_name": event_name,
            "token_created": token_id,
            "action": "entitlement_granted"
        }
        _atomic_json_dump(get_processed_webhooks_file(), processed_events)

    return True, "webhook_verified_and_processed", 200, {
        "event_id": event_id,
        "token": token_id,
        "status": "processed",
        "active_entitlement_created": True
    }


# ==============================================================================
# ATOMIC PERSISTENCE HELPERS
# ==============================================================================

def _atomic_json_dump(filepath: str, data: dict):
    """
    Writes JSON data atomically using a temporary file and atomic replace.
    Guarantees zero file truncation, zero lost updates, and crash resilience.
    """
    dir_name = os.path.dirname(filepath)
    os.makedirs(dir_name, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", dir=dir_name, delete=False, encoding="utf-8") as tf:
        json.dump(data, tf, indent=2, ensure_ascii=False)
        temp_name = tf.name
    os.replace(temp_name, filepath)


def _load_processed_webhooks() -> dict:
    fpath = get_processed_webhooks_file()
    if os.path.exists(fpath):
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def _load_entitlements() -> dict:
    fpath = get_entitlements_file()
    if os.path.exists(fpath):
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


# ==============================================================================
# SPRINT 1: POSTGRESQL SUBSCRIPTION & ENTITLEMENT LIFECYCLE
# ==============================================================================

def get_lockdown_phase() -> str:
    """
    Returns 'full' or 'auth_ready'.
    Defaults to 'full' to preserve existing security guarantees.
    """
    val = os.environ.get("LOCKDOWN_PHASE", "full").strip().lower()
    if val in ["auth_ready", "auth-ready", "auth"]:
        return "auth_ready"
    return "full"


PLAN_LIMITS = {
    "free": {
        "audit_limit": 2,
        "pdf_download": False,
        "white_label": False,
        "workspaces": 1,
        "team_members": 1
    },
    "solo": {
        "audit_limit": 25,
        "pdf_download": True,
        "white_label": False,
        "workspaces": 1,
        "team_members": 1,
        "audit_history": True
    },
    "agency": {
        "audit_limit": 100,
        "pdf_download": True,
        "white_label": True,
        "workspaces": 3,
        "team_members": 3,
        "audit_history": True
    },
    "scale": {
        "audit_limit": 400,
        "pdf_download": True,
        "white_label": True,
        "workspaces": 10,
        "team_members": 10,
        "audit_history": True,
        "scheduled_rescans": True
    }
}


def sync_webhook_to_db(event_id: str, event_name: str, payload_raw: bytes, payload_dict: dict) -> bool:
    """
    Idempotently records webhook into PostgreSQL/SQLite database tables:
    - webhook_events (idempotency via UNIQUE event_id)
    - users (find or create by customer email)
    - subscriptions (insert or update status, period, auto_renew)
    - entitlements (insert or update plan limits and usage)
    """
    try:
        from db.connection import get_db_cursor, is_sqlite
        import uuid

        payload_hash = hashlib.sha256(payload_raw).hexdigest()
        data = payload_dict.get("data", {})
        attributes = data.get("attributes", {})
        order_or_sub_id = str(data.get("id", ""))
        user_email = (
            attributes.get("user_email")
            or attributes.get("customer_email")
            or payload_dict.get("meta", {}).get("custom_data", {}).get("user_email")
            or ""
        ).strip().lower()

        raw_plan_name = (
            attributes.get("variant_name")
            or attributes.get("product_name")
            or payload_dict.get("meta", {}).get("custom_data", {}).get("plan")
            or "solo"
        ).lower()

        plan = "free"
        if "scale" in raw_plan_name:
            plan = "scale"
        elif "agency" in raw_plan_name:
            plan = "agency"
        elif "solo" in raw_plan_name:
            plan = "solo"
        else:
            plan = "solo"

        limits = PLAN_LIMITS.get(plan, PLAN_LIMITS["solo"])
        audit_limit = limits["audit_limit"]
        now_iso = datetime.now(timezone.utc).isoformat()
        next_month_iso = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()

        with get_db_cursor(commit=True) as cur:
            # 1. Idempotency Check in webhook_events
            cur.execute("SELECT id FROM webhook_events WHERE event_id = %s;", (event_id,))
            if cur.fetchone():
                return True  # Already processed in DB

            # Insert webhook_event
            we_id = str(uuid.uuid4())
            if is_sqlite():
                cur.execute("""
                    INSERT OR IGNORE INTO webhook_events (id, event_id, event_name, payload_hash, subscription_id, processed_at, status)
                    VALUES (%s, %s, %s, %s, %s, %s, 'processed');
                """, (we_id, event_id, event_name, payload_hash, order_or_sub_id, now_iso))
            else:
                cur.execute("""
                    INSERT INTO webhook_events (id, event_id, event_name, payload_hash, subscription_id, processed_at, status)
                    VALUES (%s, %s, %s, %s, %s, NOW(), 'processed')
                    ON CONFLICT (event_id) DO NOTHING;
                """, (we_id, event_id, event_name, payload_hash, order_or_sub_id))

            # If user email is present, find or create user & workspace
            if user_email:
                cur.execute("SELECT id FROM users WHERE LOWER(email) = %s;", (user_email,))
                user_row = cur.fetchone()
                if user_row:
                    user_id = str(user_row["id"])
                else:
                    user_id = str(uuid.uuid4())
                    user_name = user_email.split("@")[0].capitalize()
                    # Placeholder bcrypt hash for webhook-provisioned users
                    dummy_hash = "$2b$12$e8YkYd2U6E5a2gU.8Qx70OHj81jWqU1Y6fP0qG3V5G.qg7V0D8Zce"
                    if is_sqlite():
                        cur.execute("""
                            INSERT INTO users (id, email, password_hash, full_name, created_at, updated_at, is_active)
                            VALUES (%s, %s, %s, %s, %s, %s, 1);
                        """, (user_id, user_email, dummy_hash, user_name, now_iso, now_iso))
                    else:
                        cur.execute("""
                            INSERT INTO users (id, email, password_hash, full_name, created_at, updated_at, is_active)
                            VALUES (%s, %s, %s, %s, NOW(), NOW(), TRUE);
                        """, (user_id, user_email, dummy_hash, user_name))

                # Find or create workspace
                cur.execute("SELECT id FROM workspaces WHERE owner_id = %s LIMIT 1;", (user_id,))
                ws_row = cur.fetchone()
                if ws_row:
                    workspace_id = str(ws_row["id"])
                    # Update workspace plan
                    if is_sqlite():
                        cur.execute("UPDATE workspaces SET plan = %s, updated_at = %s WHERE id = %s;", (plan, now_iso, workspace_id))
                    else:
                        cur.execute("UPDATE workspaces SET plan = %s, updated_at = NOW() WHERE id = %s;", (plan, workspace_id))
                else:
                    workspace_id = str(uuid.uuid4())
                    ws_name = f"{user_email.split('@')[0]}'s Workspace"
                    if is_sqlite():
                        cur.execute("""
                            INSERT INTO workspaces (id, name, owner_id, plan, created_at, updated_at)
                            VALUES (%s, %s, %s, %s, %s, %s);
                        """, (workspace_id, ws_name, user_id, plan, now_iso, now_iso))
                    else:
                        cur.execute("""
                            INSERT INTO workspaces (id, name, owner_id, plan, created_at, updated_at)
                            VALUES (%s, %s, %s, %s, NOW(), NOW());
                        """, (workspace_id, ws_name, user_id, plan))

                # Handle specific subscription events in subscriptions table
                cur.execute("SELECT id FROM subscriptions WHERE workspace_id = %s OR lemon_squeezy_subscription_id = %s;", (workspace_id, order_or_sub_id))
                sub_row = cur.fetchone()

                if event_name in ["order_created", "subscription_created", "subscription_updated", "subscription_resumed"]:
                    sub_status = "active"
                    auto_renew = 1 if is_sqlite() else True
                    if sub_row:
                        sub_id = str(sub_row["id"])
                        if is_sqlite():
                            cur.execute("""
                                UPDATE subscriptions SET plan = %s, status = %s, auto_renew = %s, updated_at = %s, expires_at = %s
                                WHERE id = %s;
                            """, (plan, sub_status, auto_renew, now_iso, next_month_iso, sub_id))
                        else:
                            cur.execute("""
                                UPDATE subscriptions SET plan = %s, status = %s, auto_renew = %s, updated_at = NOW(), expires_at = NOW() + INTERVAL '30 days'
                                WHERE id = %s;
                            """, (plan, sub_status, auto_renew, sub_id))
                    else:
                        sub_id = str(uuid.uuid4())
                        if is_sqlite():
                            cur.execute("""
                                INSERT INTO subscriptions (id, workspace_id, user_id, lemon_squeezy_subscription_id, plan, status, auto_renew, expires_at, created_at, updated_at)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                            """, (sub_id, workspace_id, user_id, order_or_sub_id, plan, sub_status, auto_renew, next_month_iso, now_iso, now_iso))
                        else:
                            cur.execute("""
                                INSERT INTO subscriptions (id, workspace_id, user_id, lemon_squeezy_subscription_id, plan, status, auto_renew, expires_at, created_at, updated_at)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, NOW() + INTERVAL '30 days', NOW(), NOW());
                            """, (sub_id, workspace_id, user_id, order_or_sub_id, plan, sub_status, auto_renew))

                    # Create or update entitlements
                    cur.execute("SELECT id FROM entitlements WHERE workspace_id = %s AND feature = 'audit';", (workspace_id,))
                    ent_row = cur.fetchone()
                    if ent_row:
                        ent_id = str(ent_row["id"])
                        if is_sqlite():
                            cur.execute("""
                                UPDATE entitlements SET subscription_id = %s, usage_limit = %s, is_active = 1, usage_reset_at = %s
                                WHERE id = %s;
                            """, (sub_id, audit_limit, next_month_iso, ent_id))
                        else:
                            cur.execute("""
                                UPDATE entitlements SET subscription_id = %s, usage_limit = %s, is_active = TRUE, usage_reset_at = NOW() + INTERVAL '30 days'
                                WHERE id = %s;
                            """, (sub_id, audit_limit, ent_id))
                    else:
                        ent_id = str(uuid.uuid4())
                        if is_sqlite():
                            cur.execute("""
                                INSERT INTO entitlements (id, workspace_id, subscription_id, feature, usage_limit, usage_count, is_active, usage_reset_at, created_at)
                                VALUES (%s, %s, %s, 'audit', %s, 0, 1, %s, %s);
                            """, (ent_id, workspace_id, sub_id, audit_limit, next_month_iso, now_iso))
                        else:
                            cur.execute("""
                                INSERT INTO entitlements (id, workspace_id, subscription_id, feature, usage_limit, usage_count, is_active, usage_reset_at, created_at)
                                VALUES (%s, %s, %s, 'audit', %s, 0, TRUE, NOW() + INTERVAL '30 days', NOW());
                            """, (ent_id, workspace_id, sub_id, audit_limit))

                elif event_name == "subscription_cancelled":
                    if is_sqlite():
                        cur.execute("""
                            UPDATE subscriptions SET auto_renew = 0, cancelled_at = %s, updated_at = %s
                            WHERE workspace_id = %s OR lemon_squeezy_subscription_id = %s;
                        """, (now_iso, now_iso, workspace_id, order_or_sub_id))
                    else:
                        cur.execute("""
                            UPDATE subscriptions SET auto_renew = FALSE, cancelled_at = NOW(), updated_at = NOW()
                            WHERE workspace_id = %s OR lemon_squeezy_subscription_id = %s;
                        """, (workspace_id, order_or_sub_id))

                elif event_name in ["subscription_expired", "subscription_unpaid"]:
                    if is_sqlite():
                        cur.execute("""
                            UPDATE subscriptions SET status = 'inactive', updated_at = %s
                            WHERE workspace_id = %s OR lemon_squeezy_subscription_id = %s;
                        """, (now_iso, workspace_id, order_or_sub_id))
                        cur.execute("""
                            UPDATE entitlements SET is_active = 0
                            WHERE workspace_id = %s;
                        """, (workspace_id,))
                    else:
                        cur.execute("""
                            UPDATE subscriptions SET status = 'inactive', updated_at = NOW()
                            WHERE workspace_id = %s OR lemon_squeezy_subscription_id = %s;
                        """, (workspace_id, order_or_sub_id))
                        cur.execute("""
                            UPDATE entitlements SET is_active = FALSE
                            WHERE workspace_id = %s;
                        """, (workspace_id,))

                elif event_name == "subscription_paused":
                    if is_sqlite():
                        cur.execute("""
                            UPDATE subscriptions SET status = 'paused', updated_at = %s
                            WHERE workspace_id = %s OR lemon_squeezy_subscription_id = %s;
                        """, (now_iso, workspace_id, order_or_sub_id))
                        cur.execute("""
                            UPDATE entitlements SET is_active = 0
                            WHERE workspace_id = %s;
                        """, (workspace_id,))
                    else:
                        cur.execute("""
                            UPDATE subscriptions SET status = 'paused', updated_at = NOW()
                            WHERE workspace_id = %s OR lemon_squeezy_subscription_id = %s;
                        """, (workspace_id, order_or_sub_id))
                        cur.execute("""
                            UPDATE entitlements SET is_active = FALSE
                            WHERE workspace_id = %s;
                        """, (workspace_id,))

        return True
    except Exception as e:
        logger.warning(f"Error syncing webhook to DB: {e}")
        return False


def check_db_entitlement(workspace_id: str, feature: str = "audit", increment_usage: bool = False, user_id: str = None) -> tuple:
    """
    Checks if a workspace is entitled to use a feature:
    - Verifies is_active
    - Handles monthly reset on anniversary if current time > usage_reset_at
    - Verifies usage_count < usage_limit
    - Optionally increments usage_count and logs to usage_events
    Returns: (is_allowed: bool, reason: str, details: dict)
    """
    try:
        from db.connection import get_db_cursor, is_sqlite
        import uuid

        now_iso = datetime.now(timezone.utc).isoformat()
        next_month_iso = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()

        with get_db_cursor(commit=True) as cur:
            cur.execute("""
                SELECT id, workspace_id, subscription_id, feature, usage_limit, usage_count, usage_reset_at, is_active
                FROM entitlements
                WHERE workspace_id = %s AND feature = %s;
            """, (workspace_id, feature))
            ent = cur.fetchone()

            if not ent:
                # Default free tier entitlement if none found
                ent_id = str(uuid.uuid4())
                if is_sqlite():
                    cur.execute("""
                        INSERT INTO entitlements (id, workspace_id, feature, usage_limit, usage_count, is_active, usage_reset_at, created_at)
                        VALUES (%s, %s, %s, 2, 0, 1, %s, %s);
                    """, (ent_id, workspace_id, feature, next_month_iso, now_iso))
                else:
                    cur.execute("""
                        INSERT INTO entitlements (id, workspace_id, feature, usage_limit, usage_count, is_active, usage_reset_at, created_at)
                        VALUES (%s, %s, %s, 2, 0, TRUE, NOW() + INTERVAL '30 days', NOW());
                    """, (ent_id, workspace_id, feature))

                cur.execute("SELECT id, workspace_id, subscription_id, feature, usage_limit, usage_count, usage_reset_at, is_active FROM entitlements WHERE id = %s;", (ent_id,))
                ent = cur.fetchone()

            ent_dict = dict(ent)
            ent_id = str(ent_dict["id"])

            # Check if monthly usage reset is due
            reset_at = ent_dict.get("usage_reset_at")
            if reset_at:
                try:
                    # Parse reset_at timestamp
                    is_past = False
                    if isinstance(reset_at, datetime):
                        is_past = datetime.now(timezone.utc) > reset_at
                    elif isinstance(reset_at, str):
                        clean_reset = reset_at.replace("Z", "+00:00")
                        is_past = datetime.now(timezone.utc) > datetime.fromisoformat(clean_reset)
                    if is_past:
                        if is_sqlite():
                            cur.execute("UPDATE entitlements SET usage_count = 0, usage_reset_at = %s WHERE id = %s;", (next_month_iso, ent_id))
                        else:
                            cur.execute("UPDATE entitlements SET usage_count = 0, usage_reset_at = NOW() + INTERVAL '30 days' WHERE id = %s;", (ent_id,))
                        ent_dict["usage_count"] = 0
                except Exception:
                    pass

            # Check active flag
            if not ent_dict.get("is_active", True):
                return False, "entitlement_inactive", ent_dict

            # Check limit
            limit = ent_dict.get("usage_limit")
            count = ent_dict.get("usage_count", 0)
            if limit is not None and count >= limit:
                return False, "usage_limit_reached", ent_dict

            # Increment usage if requested
            if increment_usage:
                new_count = count + 1
                cur.execute("UPDATE entitlements SET usage_count = %s WHERE id = %s;", (new_count, ent_id))
                ent_dict["usage_count"] = new_count
                # Log usage event
                ue_id = str(uuid.uuid4())
                if is_sqlite():
                    cur.execute("""
                        INSERT INTO usage_events (id, workspace_id, user_id, feature, event_type, created_at)
                        VALUES (%s, %s, %s, %s, 'audit_run', %s);
                    """, (ue_id, workspace_id, user_id, feature, now_iso))
                else:
                    cur.execute("""
                        INSERT INTO usage_events (id, workspace_id, user_id, feature, event_type, created_at)
                        VALUES (%s, %s, %s, %s, 'audit_run', NOW());
                    """, (ue_id, workspace_id, user_id, feature))

            return True, "allowed", ent_dict
    except Exception as e:
        logger.warning(f"Error checking DB entitlement: {e}")
        return False, f"error: {e}", {}

