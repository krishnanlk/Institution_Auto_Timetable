import secrets
import hmac
import time
from urllib.parse import urlparse, urljoin
from collections import defaultdict
from functools import wraps
from flask import session, redirect, url_for, request, jsonify, flash
from database import get_db


# ══════════════════════════════════════════════════════════════════════════════
# CSRF Defense (OWASP A07 & A05)
# ══════════════════════════════════════════════════════════════════════════════

def get_or_create_csrf_token() -> str:
    """Retrieves or initializes a cryptographically strong session CSRF token."""
    if "_csrf_token" not in session:
        session["_csrf_token"] = secrets.token_hex(32)
    return session["_csrf_token"]


def validate_csrf_token(token: str) -> bool:
    """Validates form token against session CSRF token using constant-time check."""
    session_token = session.get("_csrf_token")
    if not session_token or not token:
        return False
    return hmac.compare_digest(session_token, token)


# ══════════════════════════════════════════════════════════════════════════════
# Open Redirect Protection (OWASP A01)
# ══════════════════════════════════════════════════════════════════════════════

def is_safe_url(target: str) -> bool:
    """Ensures redirect URL is strictly internal and does not navigate off-site."""
    if not target or not isinstance(target, str):
        return False
    # Disallow protocol-relative URLs like '//evil.com'
    if target.startswith("//") or target.startswith("\\\\"):
        return False
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ("http", "https") and ref_url.netloc == test_url.netloc


# ══════════════════════════════════════════════════════════════════════════════
# Brute-Force & Credential Stuffing Defense (OWASP A04 & A07)
# ══════════════════════════════════════════════════════════════════════════════

class AuthRateLimiter:
    """
    In-memory rate limiter & lockout manager.
    Tracks failed attempts per IP and per (institution, username) account.
    """
    def __init__(self, max_attempts: int = 5, window_seconds: int = 300, lockout_seconds: int = 60):
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self.lockout_seconds = lockout_seconds
        self.failed_attempts = defaultdict(list)
        self.lockouts = {}

    def _clean(self, key: str, now: float):
        self.failed_attempts[key] = [t for t in self.failed_attempts[key] if now - t < self.window_seconds]

    def is_locked(self, key: str) -> tuple[bool, int]:
        now = time.time()
        if key in self.lockouts:
            remaining = int(self.lockouts[key] - now)
            if remaining > 0:
                return True, remaining
            else:
                del self.lockouts[key]
        return False, 0

    def record_failure(self, key: str) -> tuple[bool, int]:
        now = time.time()
        self._clean(key, now)
        self.failed_attempts[key].append(now)
        if len(self.failed_attempts[key]) >= self.max_attempts:
            lockout_until = now + self.lockout_seconds
            self.lockouts[key] = lockout_until
            return True, self.lockout_seconds
        return False, 0

    def reset(self, key: str):
        self.failed_attempts.pop(key, None)
        self.lockouts.pop(key, None)


auth_limiter = AuthRateLimiter(max_attempts=5, window_seconds=300, lockout_seconds=60)


def validate_password_strength(password: str) -> tuple[bool, str]:
    """Enforces minimum 8 chars, requiring at least one letter and one number/symbol."""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not any(c.isalpha() for c in password):
        return False, "Password must include at least one letter."
    if not any(c.isdigit() or not c.isalnum() for c in password):
        return False, "Password must include at least one number or special symbol."
    return True, ""


# ══════════════════════════════════════════════════════════════════════════════
# Access Control Decorators
# ══════════════════════════════════════════════════════════════════════════════

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            if request.path.startswith("/api/"):
                return jsonify({"error": "Not authenticated"}), 401
            target = request.path
            return redirect(url_for("auth_login") + ("?next=" + target if is_safe_url(target) else ""))
        return f(*args, **kwargs)
    return decorated


def creator_or_admin_required(f):
    """Allows admin and creator to modify academic and scheduling data (staff, subjects, classes, rooms, timetables, time config, slots). Blocks viewers."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            if request.path.startswith("/api/"):
                return jsonify({"error": "Not authenticated"}), 401
            return redirect(url_for("auth_login"))
        if session.get("role") not in ("admin", "creator"):
            if request.path.startswith("/api/"):
                return jsonify({"success": False, "error": "Permission denied. Viewer accounts cannot modify data."}), 403
            flash("You have viewer access only. Contact your administrator to make changes.", "warning")
            return redirect(request.referrer or url_for("dashboard"))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    """Strictly requires master admin role (for institution profile, college logo, and user management)."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            if request.path.startswith("/api/"):
                return jsonify({"error": "Not authenticated"}), 401
            return redirect(url_for("auth_login"))
        if session.get("role") != "admin":
            if request.path.startswith("/api/"):
                return jsonify({"success": False, "error": "Permission denied. Only Master Admin can manage institution profile, logo, and users."}), 403
            flash("Permission denied. Only Master Admin can manage institution profile, logo, and users.", "warning")
            return redirect(request.referrer or url_for("dashboard"))
        return f(*args, **kwargs)
    return decorated


def get_current_user():
    if "user_id" not in session:
        return None
    with get_db() as conn:
        u = conn.execute(
            "SELECT u.*, i.name as inst_name, i.code as inst_code, i.logo_text, i.logo_url, "
            "i.email as inst_email, i.phone as inst_phone, i.address as inst_address "
            "FROM users u JOIN institution i ON i.id=u.institution_id WHERE u.id=?",
            (session["user_id"],)
        ).fetchone()
        return dict(u) if u else None


def inject_user(app):
    @app.context_processor
    def ctx():
        user = get_current_user()
        show_tour = session.pop("show_tour", False)
        return {
            "current_user": user,
            "request": request,
            "csrf_token": get_or_create_csrf_token(),
            "show_tour": show_tour
        }
