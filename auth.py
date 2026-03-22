"""
auth.py — Session-based auth with role enforcement decorator.
"""
from functools import wraps
from flask import session, redirect, url_for, request, jsonify
from database import get_db

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            # API vs page request
            if request.path.startswith('/api/'):
                return jsonify({'error': 'Not authenticated'}), 401
            return redirect(url_for('auth_login') + '?next=' + request.path)
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    """Blocks viewers from mutating data. Returns 403 for API, flash+redirect for pages."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            if request.path.startswith('/api/'):
                return jsonify({'error': 'Not authenticated'}), 401
            return redirect(url_for('auth_login'))
        if session.get('role') != 'admin':
            if request.path.startswith('/api/'):
                return jsonify({'success': False, 'error': 'Permission denied. Viewer accounts cannot modify data.'}), 403
            from flask import flash
            flash('You have viewer access only. Contact your admin to make changes.', 'warning')
            return redirect(request.referrer or url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated

def get_current_user():
    if 'user_id' not in session:
        return None
    with get_db() as conn:
        u = conn.execute(
            "SELECT u.*, i.name as inst_name, i.code as inst_code, i.logo_text "
            "FROM users u JOIN institution i ON i.id=u.institution_id WHERE u.id=?",
            (session['user_id'],)
        ).fetchone()
        return dict(u) if u else None

def inject_user(app):
    @app.context_processor
    def ctx():
        user = get_current_user()
        return {'current_user': user, 'request': request}
