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
from urllib.parse import urlparse

# Global re-entrant lock for file persistence and webhook state
_SECURITY_LOCK = threading.RLock()

# File paths
_STORAGE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "storage")
_PROCESSED_WEBHOOKS_FILE = os.path.join(_STORAGE_DIR, "processed_webhook_events.json")
_ENTITLEMENTS_FILE = os.path.join(_STORAGE_DIR, "active_entitlements.json")


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
    - 401 Unauthorized: missing identity, invalid token format, unrecognized token, expired token.
    - 403 Forbidden: client spoofing, unauthorized admin claim, cross-workspace access, ownership mismatch.
    """
    if err_code in [
        "authentication_required",
        "invalid_token",
        "unrecognized_token",
        "token_expired",
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

    # Check if entitlement status is revoked or inactive
    if user_record.get("status") in ["inactive", "revoked", "cancelled", "expired"]:
        return False, None, "token_expired"

    # Check expiration
    expires_at = user_record.get("expires_at", 0)
    if expires_at and expires_at < time.time():
        return False, None, "token_expired"

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

    if user_ctx.get("status") in ["inactive", "revoked", "cancelled", "expired"]:
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
       - Cancellations, pauses, non-payments, expirations do NOT create active entitlements.
       - Revokes existing entitlements on cancellation/expiration.
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

    # Event ID for idempotency
    event_id = meta.get("custom_data", {}).get("event_id") or data.get("id") or f"{event_name}_{attributes.get('created_at', time.time())}"
    order_or_sub_id = str(data.get("id", ""))
    sub_status = str(attributes.get("status", "")).lower()

    # Subscription deactivation / cancellation detection
    is_deactivating_event = (
        event_name in [
            "subscription_cancelled",
            "subscription_expired",
            "subscription_paused",
            "subscription_unpaid",
            "subscription_payment_failed"
        ]
        or sub_status in ["cancelled", "expired", "paused", "unpaid", "past_due"]
    )

    with _SECURITY_LOCK:
        processed_events = _load_processed_webhooks()
        if event_id in processed_events:
            # Duplicate webhook delivery: Idempotency protection
            return True, "duplicate_webhook_delivery_ignored", 200, {
                "event_id": event_id,
                "status": "duplicate_ignored"
            }

        # Case A: Subscription Deactivated / Cancelled / Expired / Unpaid
        if is_deactivating_event:
            entitlements = _load_entitlements()
            revoked_count = 0
            for tok, rec in list(entitlements.items()):
                if str(rec.get("order_id", "")) == order_or_sub_id:
                    rec["status"] = "inactive"
                    rec["revoked_at"] = time.time()
                    rec["expires_at"] = time.time()
                    revoked_count += 1
            if revoked_count > 0:
                _atomic_json_dump(_ENTITLEMENTS_FILE, entitlements)

            # Record event processed (zero active entitlement created)
            processed_events[event_id] = {
                "processed_at": time.time(),
                "event_name": event_name,
                "action": "deactivated_or_ignored",
                "revoked_count": revoked_count
            }
            _atomic_json_dump(_PROCESSED_WEBHOOKS_FILE, processed_events)

            return True, "subscription_status_updated_inactive", 200, {
                "event_id": event_id,
                "status": "inactive",
                "active_entitlement_created": False
            }

        # Case B: Active Entitlement Creation (order_created, subscription_created, subscription_resumed)
        user_email = attributes.get("user_email", "")
        customer_hash = hashlib.sha256(user_email.encode("utf-8")).hexdigest()[:16] if user_email else "anon"

        token_id = f"ent_{hashlib.sha256((order_or_sub_id + str(time.time())).encode('utf-8')).hexdigest()[:24]}"

        entitlement_record = {
            "token": token_id,
            "order_id": order_or_sub_id,
            "customer_ref": customer_hash,
            "plan": "pro_saas",
            "features": ["b2b_leads", "seo_articles", "ai_closer"],
            "created_at": time.time(),
            "expires_at": time.time() + (30 * 86400) if "subscription" in event_name else 0,
            "status": "active",
            "event_name": event_name
        }

        # Record entitlement
        entitlements = _load_entitlements()
        entitlements[token_id] = entitlement_record
        _atomic_json_dump(_ENTITLEMENTS_FILE, entitlements)

        # Mark event processed
        processed_events[event_id] = {
            "processed_at": time.time(),
            "event_name": event_name,
            "token_created": token_id,
            "action": "entitlement_granted"
        }
        _atomic_json_dump(_PROCESSED_WEBHOOKS_FILE, processed_events)

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
    if os.path.exists(_PROCESSED_WEBHOOKS_FILE):
        try:
            with open(_PROCESSED_WEBHOOKS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def _load_entitlements() -> dict:
    if os.path.exists(_ENTITLEMENTS_FILE):
        try:
            with open(_ENTITLEMENTS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}
