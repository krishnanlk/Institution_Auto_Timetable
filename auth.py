"""
auth.py — Session-based auth with role enforcement decorator.
Compatible with both SQLite (sqlite3.Row) and PostgreSQL (psycopg2 RealDictRow).
"""
from functools import wraps
from flask import session, redirect, url_for, request, jsonify, flash
from database import get_db


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            if request.path.startswith("/api/"):
                return jsonify({"error": "Not authenticated"}), 401
            return redirect(url_for("auth_login") + "?next=" + request.path)
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
        return {"current_user": user, "request": request}
