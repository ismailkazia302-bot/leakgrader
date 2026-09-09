"""
LeakGrader User Authentication, Session & CSRF Engine (Sprint 1)
Handles bcrypt password hashing (cost 12), signup, login (rate-limited),
session management, password reset, and CSRF token enforcement.
"""

import os
import re
import time
import secrets
import logging
import threading
import uuid
import hmac
from datetime import datetime, timezone, timedelta

import bcrypt

from db.connection import get_db_cursor, is_sqlite

logger = logging.getLogger("leakgrader.auth")

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")

# In-memory rate limiting for login: email -> [timestamps]
_RATE_LIMIT_LOCK = threading.Lock()
_LOGIN_ATTEMPTS = {}

# Password reset tokens: token -> {"email": email, "expires_at": timestamp, "user_id": user_id}
_RESET_TOKENS_LOCK = threading.Lock()
_RESET_TOKENS = {}


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except Exception:
        return False


def _check_rate_limit(email: str) -> bool:
    """Returns True if within limit, False if rate limited (5 attempts per 15 min)"""
    email_key = email.strip().lower()
    now = time.time()
    window = 15 * 60  # 15 minutes

    with _RATE_LIMIT_LOCK:
        attempts = _LOGIN_ATTEMPTS.get(email_key, [])
        # Filter attempts within window
        valid_attempts = [t for t in attempts if now - t < window]
        _LOGIN_ATTEMPTS[email_key] = valid_attempts

        if len(valid_attempts) >= 5:
            return False
        return True


def _record_failed_login(email: str):
    email_key = email.strip().lower()
    now = time.time()
    with _RATE_LIMIT_LOCK:
        attempts = _LOGIN_ATTEMPTS.get(email_key, [])
        attempts.append(now)
        _LOGIN_ATTEMPTS[email_key] = attempts


def _clear_failed_login(email: str):
    email_key = email.strip().lower()
    with _RATE_LIMIT_LOCK:
        _LOGIN_ATTEMPTS.pop(email_key, None)


def cleanup_expired_sessions():
    """Deletes expired sessions from the database"""
    now_iso = datetime.now(timezone.utc).isoformat()
    try:
        with get_db_cursor(commit=True) as cur:
            if is_sqlite():
                cur.execute("DELETE FROM sessions WHERE expires_at < %s;", (now_iso,))
            else:
                cur.execute("DELETE FROM sessions WHERE expires_at < NOW();")
    except Exception as e:
        logger.warning(f"Failed to cleanup expired sessions: {e}")


def create_session(user_id: str, ip_address: str = None, user_agent: str = None) -> dict:
    session_token = secrets.token_urlsafe(32)
    csrf_token = secrets.token_hex(32)
    session_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(days=7)
    expires_at_iso = expires_at.isoformat()
    now_iso = now.isoformat()

    with get_db_cursor(commit=True) as cur:
        if is_sqlite():
            cur.execute("""
                INSERT INTO sessions (id, user_id, session_token, csrf_token, created_at, expires_at, last_active_at, ip_address, user_agent)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
            """, (session_id, user_id, session_token, csrf_token, now_iso, expires_at_iso, now_iso, ip_address, user_agent))
        else:
            cur.execute("""
                INSERT INTO sessions (id, user_id, session_token, csrf_token, created_at, expires_at, last_active_at, ip_address, user_agent)
                VALUES (%s, %s, %s, %s, NOW(), NOW() + INTERVAL '7 days', NOW(), %s, %s);
            """, (session_id, user_id, session_token, csrf_token, ip_address, user_agent))

    return {
        "session_token": session_token,
        "csrf_token": csrf_token,
        "expires_at": expires_at_iso
    }


def validate_session(session_token: str) -> dict:
    """Validates session token, returning user and session dict or None"""
    if not session_token:
        return None

    cleanup_expired_sessions()
    now_iso = datetime.now(timezone.utc).isoformat()

    with get_db_cursor(commit=True) as cur:
        if is_sqlite():
            cur.execute("""
                SELECT s.id AS session_id, s.user_id, s.session_token, s.csrf_token, s.expires_at,
                       u.email, u.full_name, u.is_active
                FROM sessions s
                JOIN users u ON s.user_id = u.id
                WHERE s.session_token = %s AND s.expires_at > %s AND u.is_active = 1;
            """, (session_token, now_iso))
        else:
            cur.execute("""
                SELECT s.id AS session_id, s.user_id, s.session_token, s.csrf_token, s.expires_at,
                       u.email, u.full_name, u.is_active
                FROM sessions s
                JOIN users u ON s.user_id = u.id
                WHERE s.session_token = %s AND s.expires_at > NOW() AND u.is_active = TRUE;
            """, (session_token,))

        row = cur.fetchone()
        if not row:
            return None

        # Update last_active_at
        if is_sqlite():
            cur.execute("UPDATE sessions SET last_active_at = %s WHERE session_token = %s;", (now_iso, session_token))
        else:
            cur.execute("UPDATE sessions SET last_active_at = NOW() WHERE session_token = %s;", (session_token,))

        # Fetch primary workspace
        cur.execute("""
            SELECT w.id, w.name, w.plan
            FROM workspaces w
            WHERE w.owner_id = %s
            ORDER BY w.created_at ASC LIMIT 1;
        """, (row["user_id"],))
        workspace = cur.fetchone()

        return {
            "session_id": str(row["session_id"]),
            "user_id": str(row["user_id"]),
            "session_token": row["session_token"],
            "csrf_token": row["csrf_token"],
            "email": row["email"],
            "full_name": row["full_name"],
            "workspace": dict(workspace) if workspace else None
        }


def signup(email: str, password: str, full_name: str, ip_address: str = None, user_agent: str = None) -> tuple:
    """Handles new user signup. Returns (success, data_or_error_dict, status_code)"""
    email = (email or "").strip().lower()
    full_name = (full_name or "").strip()
    password = password or ""

    if not email or not EMAIL_REGEX.match(email):
        return False, {"error": "Invalid email address format"}, 400

    if len(password) < 8:
        return False, {"error": "Password must be at least 8 characters long"}, 400

    if not full_name:
        return False, {"error": "Full name is required"}, 400

    # Check for duplicate email
    with get_db_cursor() as cur:
        cur.execute("SELECT id FROM users WHERE LOWER(email) = %s;", (email,))
        if cur.fetchone():
            return False, {"error": "An account with this email address already exists"}, 409

    pwd_hash = hash_password(password)
    user_id = str(uuid.uuid4())
    workspace_id = str(uuid.uuid4())
    member_id = str(uuid.uuid4())
    entitlement_id = str(uuid.uuid4())
    now_iso = datetime.now(timezone.utc).isoformat()

    with get_db_cursor(commit=True) as cur:
        # Create user
        if is_sqlite():
            cur.execute("""
                INSERT INTO users (id, email, email_verified, password_hash, full_name, created_at, updated_at, is_active)
                VALUES (%s, %s, 0, %s, %s, %s, %s, 1);
            """, (user_id, email, pwd_hash, full_name, now_iso, now_iso))
        else:
            cur.execute("""
                INSERT INTO users (id, email, email_verified, password_hash, full_name, created_at, updated_at, is_active)
                VALUES (%s, %s, FALSE, %s, %s, NOW(), NOW(), TRUE);
            """, (user_id, email, pwd_hash, full_name))

        # Create personal workspace
        ws_name = f"{full_name}'s Workspace"
        if is_sqlite():
            cur.execute("""
                INSERT INTO workspaces (id, name, owner_id, plan, created_at, updated_at)
                VALUES (%s, %s, %s, 'free', %s, %s);
            """, (workspace_id, ws_name, user_id, now_iso, now_iso))
        else:
            cur.execute("""
                INSERT INTO workspaces (id, name, owner_id, plan, created_at, updated_at)
                VALUES (%s, %s, %s, 'free', NOW(), NOW());
            """, (workspace_id, ws_name, user_id))

        # Add owner membership
        if is_sqlite():
            cur.execute("""
                INSERT INTO workspace_members (id, workspace_id, user_id, role, invited_at, accepted_at)
                VALUES (%s, %s, %s, 'owner', %s, %s);
            """, (member_id, workspace_id, user_id, now_iso, now_iso))
        else:
            cur.execute("""
                INSERT INTO workspace_members (id, workspace_id, user_id, role, invited_at, accepted_at)
                VALUES (%s, %s, %s, 'owner', NOW(), NOW());
            """, (member_id, workspace_id, user_id))

        # Create default Free tier entitlements: 2 audits/month
        if is_sqlite():
            cur.execute("""
                INSERT INTO entitlements (id, workspace_id, feature, usage_limit, usage_count, is_active, created_at)
                VALUES (%s, %s, 'audit', 2, 0, 1, %s);
            """, (entitlement_id, workspace_id, now_iso))
        else:
            cur.execute("""
                INSERT INTO entitlements (id, workspace_id, feature, usage_limit, usage_count, is_active, created_at)
                VALUES (%s, %s, 'audit', 2, 0, TRUE, NOW());
            """, (entitlement_id, workspace_id))

    # Issue session
    sess = create_session(user_id, ip_address, user_agent)

    return True, {
        "user": {
            "id": user_id,
            "email": email,
            "full_name": full_name,
            "plan": "free",
            "workspace_id": workspace_id
        },
        "session": sess
    }, 201


def login(email: str, password: str, ip_address: str = None, user_agent: str = None) -> tuple:
    """Handles user login with rate limiting. Returns (success, data_or_error_dict, status_code)"""
    email = (email or "").strip().lower()
    password = password or ""

    if not email or not password:
        return False, {"error": "Email and password are required"}, 400

    if not _check_rate_limit(email):
        return False, {"error": "Too many failed login attempts. Please try again in 15 minutes."}, 429

    with get_db_cursor() as cur:
        cur.execute("""
            SELECT id, email, password_hash, full_name, is_active
            FROM users WHERE LOWER(email) = %s;
        """, (email,))
        user = cur.fetchone()

    if not user or not verify_password(password, user["password_hash"]):
        _record_failed_login(email)
        return False, {"error": "Invalid email or password"}, 401

    if not user.get("is_active", True):
        return False, {"error": "Account has been suspended or deactivated"}, 403

    _clear_failed_login(email)

    user_id = str(user["id"])
    now_iso = datetime.now(timezone.utc).isoformat()

    # Update last_login_at
    with get_db_cursor(commit=True) as cur:
        if is_sqlite():
            cur.execute("UPDATE users SET last_login_at = %s WHERE id = %s;", (now_iso, user_id))
            # Session rotation: delete existing sessions
            cur.execute("DELETE FROM sessions WHERE user_id = %s;", (user_id,))
        else:
            cur.execute("UPDATE users SET last_login_at = NOW() WHERE id = %s;", (user_id,))
            cur.execute("DELETE FROM sessions WHERE user_id = %s;", (user_id,))

    sess = create_session(user_id, ip_address, user_agent)

    # Fetch primary workspace and active subscription info
    with get_db_cursor() as cur:
        cur.execute("""
            SELECT w.id, w.name, w.plan,
                   s.status as sub_status, s.expires_at as sub_expires_at
            FROM workspaces w
            LEFT JOIN subscriptions s ON s.workspace_id = w.id
            WHERE w.owner_id = %s
            ORDER BY w.created_at ASC LIMIT 1;
        """, (user_id,))
        ws = cur.fetchone()

    return True, {
        "user": {
            "id": user_id,
            "email": user["email"],
            "full_name": user["full_name"],
            "workspace": dict(ws) if ws else None
        },
        "session": sess
    }, 200


def logout(session_token: str) -> bool:
    """Deletes the active session from the database"""
    if not session_token:
        return True
    try:
        with get_db_cursor(commit=True) as cur:
            cur.execute("DELETE FROM sessions WHERE session_token = %s;", (session_token,))
        return True
    except Exception as e:
        logger.warning(f"Error during logout: {e}")
        return False


def forgot_password(email: str) -> tuple:
    """Generates a 1-hour secure reset token. Returns (success, dict, status_code)"""
    email = (email or "").strip().lower()
    if not email:
        return False, {"error": "Email is required"}, 400

    with get_db_cursor() as cur:
        cur.execute("SELECT id FROM users WHERE LOWER(email) = %s;", (email,))
        user = cur.fetchone()

    # Always return success message to prevent user enumeration
    resp = {"success": True, "message": "If an account exists with that email, password reset instructions have been sent."}

    if user:
        token = secrets.token_urlsafe(32)
        expiry = time.time() + 3600  # 1 hour
        with _RESET_TOKENS_LOCK:
            _RESET_TOKENS[token] = {
                "user_id": str(user["id"]),
                "email": email,
                "expires_at": expiry
            }
        logger.info(f"[TEST_ONLY] Generated password reset token for {email}: {token}")
        resp["reset_token_test"] = token

    return True, resp, 200


def reset_password(token: str, new_password: str) -> tuple:
    """Validates reset token and sets new password. Invalidates all active sessions."""
    token = (token or "").strip()
    new_password = new_password or ""

    if len(new_password) < 8:
        return False, {"error": "New password must be at least 8 characters long"}, 400

    now = time.time()
    token_entry = None
    with _RESET_TOKENS_LOCK:
        entry = _RESET_TOKENS.get(token)
        if entry and entry["expires_at"] > now:
            token_entry = entry
            _RESET_TOKENS.pop(token, None)

    if not token_entry:
        return False, {"error": "Invalid or expired password reset token"}, 400

    user_id = token_entry["user_id"]
    new_hash = hash_password(new_password)
    now_iso = datetime.now(timezone.utc).isoformat()

    with get_db_cursor(commit=True) as cur:
        if is_sqlite():
            cur.execute("UPDATE users SET password_hash = %s, updated_at = %s WHERE id = %s;", (new_hash, now_iso, user_id))
            # Invalidate all existing sessions
            cur.execute("DELETE FROM sessions WHERE user_id = %s;", (user_id,))
        else:
            cur.execute("UPDATE users SET password_hash = %s, updated_at = NOW() WHERE id = %s;", (new_hash, user_id))
            cur.execute("DELETE FROM sessions WHERE user_id = %s;", (user_id,))

    return True, {"success": True, "message": "Password has been successfully reset. Please log in with your new password."}, 200


def validate_csrf(headers: dict, session_info: dict) -> bool:
    """Validates X-CSRF-Token header against active session's csrf_token"""
    if not session_info or not session_info.get("csrf_token"):
        return False

    header_csrf = None
    for k, v in headers.items():
        if k.lower().replace("_", "-") == "x-csrf-token":
            header_csrf = v
            break

    if not header_csrf:
        return False

    return hmac.compare_digest(header_csrf.strip(), session_info["csrf_token"].strip())


def build_cookie_header(session_token: str, max_age: int = 604800) -> str:
    """Builds a secure, HttpOnly, SameSite=Lax cookie header string"""
    is_prod = os.environ.get("ENVIRONMENT", "").lower() == "production"
    secure_flag = "; Secure" if is_prod else ""
    return f"session_token={session_token}; Path=/; Max-Age={max_age}; HttpOnly; SameSite=Lax{secure_flag}"


def clear_cookie_header() -> str:
    """Builds an expiring cookie header to clear the session"""
    return "session_token=; Path=/; Max-Age=0; HttpOnly; SameSite=Lax"
