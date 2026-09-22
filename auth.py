import secrets
import hmac
import time
from typing import Optional
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
# Institutional Role & Scope Checkers (Master Admin, Dean, HOD, Coordinator, Staff)
# ══════════════════════════════════════════════════════════════════════════════

def is_master_admin(user: Optional[dict]) -> bool:
    return bool(user and user.get("role") == "admin")

def is_dean(user: Optional[dict]) -> bool:
    return bool(user and user.get("role") == "dean")

def is_hod(user: Optional[dict], department_id: Optional[int] = None) -> bool:
    if not user or user.get("role") != "hod":
        return False
    if department_id is not None and user.get("department_id") is not None:
        return user.get("department_id") == department_id
    return True

def is_coordinator(user: Optional[dict], department_id: Optional[int] = None) -> bool:
    if not user or user.get("role") not in ("coordinator", "creator"):
        return False
    if department_id is not None and user.get("department_id") is not None:
        return user.get("department_id") == department_id
    return True

def can_view_department(user: Optional[dict], department_id: Optional[int]) -> bool:
    """Master Admin and Deans have institution-wide view; HODs/Coordinators/Staff can view their own department."""
    if not user:
        return False
    role = user.get("role")
    if role in ("admin", "dean"):
        return True
    if department_id is None or user.get("department_id") is None:
        return True
    return user.get("department_id") == department_id

def can_edit_department_resource(user: Optional[dict], department_id: Optional[int]) -> bool:
    """Master Admin can edit anything. HOD and Coordinator can only edit their own department resources."""
    if not user:
        return False
    role = user.get("role")
    if role == "admin":
        return True
    if role in ("hod", "coordinator", "creator"):
        if department_id is None or user.get("department_id") is None:
            return True
        return user.get("department_id") == department_id
    return False

def can_approve_department_timetable(user: Optional[dict], department_id: Optional[int]) -> bool:
    """Master Admin can override/approve anything. HOD can approve their own department's timetable."""
    if not user:
        return False
    role = user.get("role")
    if role == "admin":
        return True
    if role == "hod":
        if department_id is None or user.get("department_id") is None:
            return True
        return user.get("department_id") == department_id
    return False


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


def coordinator_or_above_required(f):
    """Allows Master Admin, HOD, and Timetable Coordinators. Blocks Deans (view-only) and Staff."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            if request.path.startswith("/api/"):
                return jsonify({"error": "Not authenticated"}), 401
            return redirect(url_for("auth_login"))
        role = session.get("role")
        if role not in ("admin", "hod", "coordinator", "creator"):
            if request.path.startswith("/api/"):
                return jsonify({"success": False, "error": "Permission denied. Modifying schedule requires Coordinator, HOD, or Master Admin access."}), 403
            flash("Modifying schedule requires Coordinator, HOD, or Master Admin access.", "warning")
            return redirect(request.referrer or url_for("dashboard"))
        return f(*args, **kwargs)
    return decorated


def creator_or_admin_required(f):
    """Alias to coordinator_or_above_required for full backward compatibility."""
    return coordinator_or_above_required(f)


def hod_or_admin_required(f):
    """Allows Master Admin and HOD for department authority and timetable review/approvals."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            if request.path.startswith("/api/"):
                return jsonify({"error": "Not authenticated"}), 401
            return redirect(url_for("auth_login"))
        role = session.get("role")
        if role not in ("admin", "hod"):
            if request.path.startswith("/api/"):
                return jsonify({"success": False, "error": "Approval authority restricted to HOD and Master Admin."}), 403
            flash("Approval authority restricted to HOD and Master Admin.", "warning")
            return redirect(request.referrer or url_for("dashboard"))
        return f(*args, **kwargs)
    return decorated


def dean_or_admin_required(f):
    """Allows Master Admin and Dean (institution-wide overview and monitoring)."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            if request.path.startswith("/api/"):
                return jsonify({"error": "Not authenticated"}), 401
            return redirect(url_for("auth_login"))
        role = session.get("role")
        if role not in ("admin", "dean"):
            if request.path.startswith("/api/"):
                return jsonify({"success": False, "error": "Access restricted to Dean and Master Admin."}), 403
            flash("Access restricted to Dean and Master Admin.", "warning")
            return redirect(request.referrer or url_for("dashboard"))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    """Strictly requires Master Admin role (for institution profile, college logo, department setup, coordinator assignment)."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            if request.path.startswith("/api/"):
                return jsonify({"error": "Not authenticated"}), 401
            return redirect(url_for("auth_login"))
        if session.get("role") != "admin":
            if request.path.startswith("/api/"):
                return jsonify({"success": False, "error": "Permission denied. Only Master Admin can manage institution settings, departments, and user roles."}), 403
            flash("Permission denied. Only Master Admin can manage institution settings, departments, and user roles.", "warning")
            return redirect(request.referrer or url_for("dashboard"))
        return f(*args, **kwargs)
    return decorated


def get_current_user():
    if "user_id" not in session:
        return None
    try:
        from flask import has_request_context, g
        if has_request_context() and hasattr(g, "_cached_user"):
            return g._cached_user
    except ImportError:
        pass

    with get_db() as conn:
        u = conn.execute("""
            SELECT u.*, d.name as dept_name, d.code as dept_code, d.category as dept_category,
                   i.name as inst_name, i.code as inst_code, i.logo_text, i.logo_url,
                   i.email as inst_email, i.phone as inst_phone, i.address as inst_address
            FROM users u
            JOIN institution i ON i.id=u.institution_id
            LEFT JOIN department d ON d.id=u.department_id
            WHERE u.id=?
        """, (session["user_id"],)).fetchone()
        user_dict = dict(u) if u else None

    try:
        from flask import has_request_context, g
        if has_request_context():
            g._cached_user = user_dict
    except ImportError:
        pass

    return user_dict


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
