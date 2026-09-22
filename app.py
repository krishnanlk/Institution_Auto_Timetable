"""
SchedHub v3 — Automated Institutional Timetable & Faculty Allocation Portal
Supports SQLite (dev) and Supabase/PostgreSQL (production) via DATABASE_URL env var.
Run: python app.py
"""
import os, json, csv, io, time
from datetime import timedelta
from werkzeug.utils import secure_filename
from flask import (Flask, render_template, request, jsonify, redirect,
                   url_for, session, flash, make_response, Response,
                   stream_with_context)
from database import (get_db, init_db, seed_demo_institution, seed_realtime_model,
                      check_password, hash_password, is_legacy_hash, generate_abbreviation,
                      close_request_db, log_activity, get_recent_activities)
from scheduler import (
    generate_timetable, generate_timetable_iter,
    get_class_timetable, get_staff_timetable,
    get_recommendations, compute_analytics, validate_before_generate,
    get_working_days, get_period_count, get_period_slots,
    edit_slot, move_slot, swap_slots, check_move_valid,
    delete_timetable, get_conflict_list, get_slot_staff_options,
    get_class_printable_data, submit_timetable, approve_timetable,
    reject_timetable, publish_timetable,
)
from auth import (login_required, admin_required, creator_or_admin_required,
                  coordinator_or_above_required, hod_or_admin_required,
                  dean_or_admin_required, inject_user,
                  get_current_user, validate_csrf_token, is_safe_url, auth_limiter,
                  validate_password_strength)
from realtime import realtime_hub, cell_lock_manager
from config import FLASK_SECRET_KEY, DB_BACKEND
import syllabus_parser

app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY

# ── OWASP A05: Security Hardened Session Cookie Configuration ──────────────────
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = False  # Set to True over HTTPS in production
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=12)

# ── OWASP A05: HTTP Security Headers (Clickjacking, MIME Sniffing, XSS, CSP) ───
@app.after_request
def add_security_headers(response):
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com https://fonts.googleapis.com; "
        "font-src 'self' https://cdnjs.cloudflare.com https://fonts.gstatic.com data:; "
        "img-src 'self' data: blob: *; "
        "connect-src 'self';"
    )
    return response

# Handle upload directory safely in both local and Vercel serverless environments
if os.environ.get("VERCEL"):
    UPLOAD_FOLDER = os.path.join('/tmp', 'uploads', 'logos')
else:
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads', 'logos')

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'svg', 'webp'}
try:
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
except Exception:
    pass

# Safe auto-init for serverless (Vercel) where __name__ != '__main__'
if os.environ.get("VERCEL"):
    try:
        init_db()
        seed_demo_institution()
    except Exception as _e:
        print(f"[INIT] Serverless startup check: {_e}")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

inject_user(app)

@app.teardown_appcontext
def shutdown_session(exception=None):
    close_request_db(exception)

def inst_id():
    return session.get("institution_id")

# ── Vercel Serverless Path Dispatcher Middleware ─────────────────────────────
class VercelPathFixMiddleware:
    """Ensures paths passed via vercel.json (?__path=...) map to correct Flask routes."""
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        query_string = environ.get('QUERY_STRING', '')
        if '__path=' in query_string:
            from urllib.parse import parse_qs, urlencode
            qs = parse_qs(query_string, keep_blank_values=True)
            if '__path' in qs:
                path_val = qs.pop('__path')[0]
                environ['PATH_INFO'] = '/' + path_val.lstrip('/')
                environ['QUERY_STRING'] = urlencode(qs, doseq=True)
        return self.wsgi_app(environ, start_response)

app.wsgi_app = VercelPathFixMiddleware(app.wsgi_app)

@app.route("/api/debug-db")
@admin_required
def api_debug_db():
    info = {
        "backend": DB_BACKEND,
        "has_database_url": bool(os.environ.get("DATABASE_URL")),
    }
    try:
        init_db()
        seed_demo_institution()
        with get_db() as conn:
            insts = [dict(r) for r in conn.execute("SELECT id, name, code FROM institution").fetchall()]
            users = [dict(r) for r in conn.execute("SELECT id, institution_id, username FROM users").fetchall()]
            counts = {
                "staff": conn.execute("SELECT count(*) as c FROM staff").fetchone()["c"],
                "subject": conn.execute("SELECT count(*) as c FROM subject").fetchone()["c"],
                "class_section": conn.execute("SELECT count(*) as c FROM class_section").fetchone()["c"],
                "timetable": conn.execute("SELECT count(*) as c FROM timetable").fetchone()["c"],
                "timetable_slot": conn.execute("SELECT count(*) as c FROM timetable_slot").fetchone()["c"],
            }
            info["institutions"] = insts
            info["users"] = users
            info["counts"] = counts
            info["status"] = "OK"
    except Exception as e:
        info["error"] = str(e)
    return jsonify(info)
# ROOT
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/")
def root():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))
    return redirect(url_for("auth_login"))


# ══════════════════════════════════════════════════════════════════════════════
# AUTH — Register / Login / Logout (OWASP Top 10 Hardened)
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/login", methods=["GET", "POST"])
def auth_login():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))
    mode = request.args.get("mode", "login")
    next_url = request.args.get("next") or request.form.get("next") or ""
    
    if request.method == "POST":
        # 1. CSRF Verification (OWASP A07 & A05)
        csrf_token = request.form.get("csrf_token", "")
        if not validate_csrf_token(csrf_token):
            flash("Security validation failed (invalid or expired CSRF token). Please try again.", "danger")
            return render_template("login.html", mode="login", next=next_url)

        # 2. Client identification for rate-limiting
        ip = request.headers.get("X-Forwarded-For", request.remote_addr or "127.0.0.1").split(",")[0].strip()
        username  = request.form.get("username", "").strip()
        password  = request.form.get("password", "")
        inst_code = request.form.get("inst_code", "").strip().upper()
        account_key = f"{inst_code}:{username}"

        # 3. Brute-Force & Credential Stuffing Lockout Check (OWASP A04 & A07)
        ip_locked, ip_wait = auth_limiter.is_locked(ip)
        acc_locked, acc_wait = auth_limiter.is_locked(account_key)
        if ip_locked or acc_locked:
            wait_time = max(ip_wait, acc_wait)
            flash(f"Too many failed login attempts. Access temporarily locked for security. Please wait {wait_time}s before trying again.", "danger")
            return render_template("login.html", mode="login", next=next_url)

        # 4. Input bounds check to prevent payload flooding / DoS (OWASP A03)
        if len(inst_code) > 32 or len(username) > 64 or len(password) > 128 or not inst_code or not username or not password:
            auth_limiter.record_failure(ip)
            flash("Invalid college code, username, or password.", "danger")
            return render_template("login.html", mode="login", next=next_url)

        # 5. Database lookup & timing-attack defense (OWASP A02 & A07)
        with get_db() as conn:
            inst = conn.execute("SELECT * FROM institution WHERE code=?", (inst_code,)).fetchone()
            user = None
            if inst:
                user = conn.execute(
                    "SELECT * FROM users WHERE institution_id=? AND username=?",
                    (dict(inst)["id"], username)
                ).fetchone()

        # Constant-time verification: check dummy hash if user or inst not found to prevent timing side-channel enumeration
        dummy_hash = "pbkdf2:sha256:600000$dummy$0000000000000000000000000000000000000000000000000000000000000000"
        stored_hash = dict(user)["password_hash"] if user else dummy_hash
        pwd_valid = check_password(stored_hash, password)

        if not inst or not user or not pwd_valid:
            auth_limiter.record_failure(ip)
            auth_limiter.record_failure(account_key)
            print(f"[AUTH SECURITY] Failed login attempt from IP={ip} for inst={inst_code} username={username}")
            flash("Invalid college code, username, or password.", "danger")
            return render_template("login.html", mode="login", next=next_url)

        # 6. Login Success: Reset rate limit counters
        auth_limiter.reset(ip)
        auth_limiter.reset(account_key)
        user = dict(user)
        inst = dict(inst)
        print(f"[AUTH SECURITY] Successful login for user='{user['username']}' at institution='{inst['code']}' (IP={ip})")

        # 7. Silent Auto-Upgrade of Legacy Hashes to PBKDF2 (OWASP A02)
        if is_legacy_hash(user.get("password_hash", "")):
            try:
                new_hash = hash_password(password)
                with get_db() as conn:
                    conn.execute("UPDATE users SET password_hash=? WHERE id=?", (new_hash, user["id"]))
                print(f"[AUTH SECURITY] Auto-upgraded password hash to PBKDF2 for user id={user['id']}")
            except Exception as _rehash_err:
                print(f"[AUTH] Silent hash upgrade warning: {_rehash_err}")

        # 8. Session Fixation Defense: clear and regenerate session (OWASP A01 & A07)
        session.clear()
        session.permanent = True
        session.update({
            "user_id": user["id"],
            "username": user["username"],
            "institution_id": inst["id"],
            "institution_name": inst["name"],
            "role": user["role"],
            "department_id": user.get("department_id"),
        })

        # Interactive Onboarding Tour: Trigger every time when logging in with demo credentials
        if inst_code == "DEMO2024":
            session["show_tour"] = True

        # 9. Open Redirect Defense (OWASP A01)
        if next_url and is_safe_url(next_url):
            return redirect(next_url)
        return redirect(url_for("dashboard"))

    return render_template("login.html", mode=mode, next=next_url)


@app.route("/register", methods=["GET", "POST"])
def auth_register():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        # 1. CSRF Verification
        csrf_token = request.form.get("csrf_token", "")
        if not validate_csrf_token(csrf_token):
            flash("Security validation failed (invalid or expired CSRF token). Please try again.", "danger")
            return render_template("login.html", mode="register")

        inst_name   = request.form.get("inst_name", "").strip()
        inst_code   = request.form.get("inst_code", "").strip().upper()
        inst_email  = request.form.get("inst_email", "").strip()
        admin_email = request.form.get("admin_email", "").strip() or inst_email
        username    = request.form.get("username", "").strip()
        password    = request.form.get("password", "")
        confirm_pw  = request.form.get("confirm_password", "")
        address     = request.form.get("address", "").strip()
        phone       = request.form.get("phone", "").strip()
        logo_url    = ""
        logo_text   = "🎓"

        # 2. Field completeness and length constraints (OWASP A03)
        if not inst_name or not inst_code or not username or not password:
            flash("Please fill in all mandatory fields.", "danger")
            return render_template("login.html", mode="register")

        if len(inst_name) > 120 or len(inst_code) > 32 or len(username) > 64 or len(password) > 128:
            flash("One or more fields exceed maximum allowed character limits.", "danger")
            return render_template("login.html", mode="register")

        # 3. Password matching & complexity policy (OWASP A07)
        if password != confirm_pw:
            flash("Passwords do not match. Please verify your password entry.", "danger")
            return render_template("login.html", mode="register")

        pwd_valid, pwd_msg = validate_password_strength(password)
        if not pwd_valid:
            flash(pwd_msg, "danger")
            return render_template("login.html", mode="register")

        # 4. Create institution & master admin
        with get_db() as conn:
            if conn.execute("SELECT 1 FROM institution WHERE code=?", (inst_code,)).fetchone():
                flash(f"Institution code '{inst_code}' is already registered. Please choose another or sign in.", "danger")
                return render_template("login.html", mode="register")

            new_inst_id = conn.insert(
                "INSERT INTO institution (name,code,address,email,phone,logo_text,logo_url) VALUES (?,?,?,?,?,?,?)",
                (inst_name, inst_code, address, inst_email, phone, logo_text, logo_url)
            )
            user_id = conn.insert(
                "INSERT INTO users (institution_id,username,email,password_hash,role) VALUES (?,?,?,?,?)",
                (new_inst_id, username, admin_email, hash_password(password), "admin")
            )
            conn.insert(
                "INSERT INTO time_config (institution_id,periods_per_day,working_days) VALUES (?,?,?)",
                (new_inst_id, 6, "Mon,Tue,Wed,Thu,Fri")
            )
            default_slots = [
                (1, "Period 1", "08:30", "09:20", "period"),
                (2, "Period 2", "09:20", "10:10", "period"),
                (3, "Break",    "10:10", "10:25", "break"),
                (4, "Period 3", "10:25", "11:15", "period"),
                (5, "Period 4", "11:15", "12:05", "period"),
                (6, "Lunch",    "12:05", "13:10", "lunch"),
                (7, "Period 5", "13:10", "14:00", "period"),
                (8, "Period 6", "14:00", "14:50", "period"),
            ]
            for s in default_slots:
                conn.execute(
                    "INSERT INTO period_slot "
                    "(institution_id,slot_order,label,start_time,end_time,slot_type) VALUES (?,?,?,?,?,?)",
                    (new_inst_id,) + s
                )

        # 5. Session Fixation Defense: clear and regenerate session
        session.clear()
        session.permanent = True
        session.update({
            "user_id": user_id,
            "username": username,
            "institution_id": new_inst_id,
            "institution_name": inst_name,
            "role": "admin",
            "first_login": True,
            "show_tour": True,
        })
        flash(f"Institution '{inst_name}' registered successfully! Welcome to SchedHub.", "success")
        return redirect(url_for("dashboard"))
    return render_template("login.html", mode="register")


@app.route("/logout")
def auth_logout():
    session.clear()
    return redirect(url_for("auth_login"))


# ══════════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/dashboard")
@login_required
def dashboard():
    iid = inst_id()
    is_first_login = session.pop("first_login", False)
    with get_db() as conn:
        inst = conn.execute("SELECT * FROM institution WHERE id=?", (iid,)).fetchone()
        stats = {
            "staff":    conn.execute("SELECT COUNT(*) as c FROM staff WHERE institution_id=?", (iid,)).fetchone()["c"],
            "subjects": conn.execute("SELECT COUNT(*) as c FROM subject WHERE institution_id=?", (iid,)).fetchone()["c"],
            "classes":  conn.execute("SELECT COUNT(*) as c FROM class_section WHERE institution_id=?", (iid,)).fetchone()["c"],
        }
        active_tt = conn.execute(
            "SELECT * FROM timetable WHERE institution_id=? AND is_active=1 ORDER BY id DESC LIMIT 1",
            (iid,)
        ).fetchone()
        total_slots = 0
        if active_tt:
            slot_row = conn.execute(
                "SELECT COUNT(*) as c FROM timetable_slot WHERE timetable_id=?", (active_tt["id"],)
            ).fetchone()
            total_slots = slot_row["c"] if slot_row else 0
        recent_tt = conn.execute(
            "SELECT * FROM timetable WHERE institution_id=? ORDER BY id DESC LIMIT 5", (iid,)
        ).fetchall()
    return render_template("dashboard.html",
                           stats=stats,
                           total_slots=total_slots,
                           inst=dict(inst) if inst else {},
                           is_first_login=is_first_login,
                           active_timetable=dict(active_tt) if active_tt else None,
                           recent_timetables=[dict(r) for r in recent_tt],
                           db_backend=DB_BACKEND)


@app.route("/api/dashboard/workload")
@login_required
def api_workload():
    iid = inst_id()
    with get_db() as conn:
        rows = conn.execute(
            "SELECT name,allocated_periods,max_periods_per_week FROM staff WHERE institution_id=? ORDER BY name",
            (iid,)
        ).fetchall()
    return jsonify({
        "labels": [r["name"] for r in rows],
        "allocated": [r["allocated_periods"] for r in rows],
        "max": [r["max_periods_per_week"] for r in rows],
    })


@app.route("/api/dashboard/performance")
@login_required
def api_performance():
    results = compute_analytics(inst_id())[:10]
    cmap = {
        "Promotion": "#10b981", "Salary Hike": "#3b82f6",
        "Overloaded": "#ef4444", "Underutilized": "#f59e0b", "Normal": "#6b7280"
    }
    return jsonify({
        "labels": [r["staff"]["name"] for r in results],
        "scores": [r["staff"]["performance_score"] for r in results],
        "colors": [cmap.get(r["suggestion"], "#6b7280") for r in results],
    })


# ══════════════════════════════════════════════════════════════════════════════
# SETTINGS
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/settings")
@login_required
def settings_page():
    iid = inst_id()
    with get_db() as conn:
        cfg   = conn.execute("SELECT * FROM time_config WHERE institution_id=?", (iid,)).fetchone()
        slots = conn.execute("SELECT * FROM period_slot WHERE institution_id=? ORDER BY slot_order", (iid,)).fetchall()
        inst  = conn.execute("SELECT * FROM institution WHERE id=?", (iid,)).fetchone()
        users = conn.execute("""
            SELECT u.id, u.username, u.email, u.role, u.created_at, u.department_id,
                   d.code as dept_code, d.name as dept_name
            FROM users u
            LEFT JOIN department d ON d.id=u.department_id
            WHERE u.institution_id=?
            ORDER BY u.id
        """, (iid,)).fetchall()
        depts = conn.execute("SELECT * FROM department WHERE institution_id=? ORDER BY category, code", (iid,)).fetchall()
    days_list     = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    selected_days = cfg["working_days"].split(",") if cfg else ["Mon", "Tue", "Wed", "Thu", "Fri"]
    inst_dict = dict(inst) if inst else {}
    inst_type = inst_dict.get("institution_type", "college")
    return render_template("settings.html",
                           cfg=dict(cfg) if cfg else {},
                           slots=[dict(s) for s in slots],
                           inst=inst_dict,
                           users=[dict(u) for u in users],
                           departments=[dict(d) for d in depts],
                           inst_type=inst_type,
                           days_list=days_list,
                           selected_days=selected_days)


@app.route("/api/settings/time", methods=["POST"])
@creator_or_admin_required
def api_save_time_config():
    iid = inst_id()
    d   = request.get_json()
    working_days    = ",".join(d.get("working_days", ["Mon", "Tue", "Wed", "Thu", "Fri"]))
    periods_per_day = int(d.get("periods_per_day", 6))
    with get_db() as conn:
        if conn.execute("SELECT 1 FROM time_config WHERE institution_id=?", (iid,)).fetchone():
            conn.execute(
                "UPDATE time_config SET periods_per_day=?, working_days=? WHERE institution_id=?",
                (periods_per_day, working_days, iid)
            )
        else:
            conn.execute(
                "INSERT INTO time_config (institution_id,periods_per_day,working_days) VALUES (?,?,?)",
                (iid, periods_per_day, working_days)
            )
    return jsonify({"success": True})


@app.route("/api/settings/slots", methods=["POST"])
@creator_or_admin_required
def api_save_slots():
    iid   = inst_id()
    slots = request.get_json()
    with get_db() as conn:
        conn.execute("DELETE FROM period_slot WHERE institution_id=?", (iid,))
        for s in slots:
            conn.execute(
                "INSERT INTO period_slot (institution_id,slot_order,label,start_time,end_time,slot_type) VALUES (?,?,?,?,?,?)",
                (iid, s["slot_order"], s["label"], s["start_time"], s["end_time"], s.get("slot_type", "period"))
            )
    return jsonify({"success": True})


@app.route("/api/settings/institution", methods=["POST"])
@admin_required
def api_update_institution():
    iid = inst_id()
    d   = request.get_json()
    itype = d.get("institution_type", "college")
    with get_db() as conn:
        conn.execute(
            "UPDATE institution SET name=?,address=?,email=?,phone=?,logo_text=?,logo_url=?,institution_type=? WHERE id=?",
            (d.get("name"), d.get("address"), d.get("email"), d.get("phone"), d.get("logo_text", "🏫"), d.get("logo_url", ""), itype, iid)
        )
    session["institution_name"] = d.get("name", session.get("institution_name"))
    return jsonify({"success": True})


@app.route("/api/institution/preset", methods=["POST"])
@creator_or_admin_required
def api_institution_preset():
    """Load a realistic, zero-conflict preset for College or School and immediately schedule."""
    iid = inst_id()
    d = request.get_json() or {}
    mtype = d.get("model_type", "college")
    if mtype not in ("college", "school"):
        mtype = "college"
    seed_realtime_model(iid, mtype)
    tt_id, conflicts = generate_timetable(iid, f"Auto Generated ({mtype.title()} Model)")
    return jsonify({
        "success": True,
        "model_type": mtype,
        "tt_id": tt_id,
        "conflict_count": len(conflicts),
        "message": f"Real-time {mtype.title()} Model loaded and scheduled with {len(conflicts)} conflicts!"
    })


@app.route("/api/institution/type", methods=["POST"])
@creator_or_admin_required
def api_set_institution_type():
    iid = inst_id()
    d = request.get_json() or {}
    itype = d.get("institution_type", "college")
    with get_db() as conn:
        conn.execute("UPDATE institution SET institution_type=? WHERE id=?", (itype, iid))
    return jsonify({"success": True, "institution_type": itype})


@app.route("/api/departments", methods=["GET"])
@login_required
def api_get_departments():
    iid = inst_id()
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM department WHERE institution_id=? ORDER BY category, code", (iid,)).fetchall()
    return jsonify([dict(r) for r in rows])


@app.route("/api/departments", methods=["POST"])
@creator_or_admin_required
def api_add_department():
    iid = inst_id()
    d = request.get_json() or {}
    code = d.get("code", "").strip().upper()
    name = d.get("name", "").strip()
    cat  = d.get("category", "core").strip()
    if not code or not name:
        return jsonify({"success": False, "error": "Department code and name are required"}), 400
    with get_db() as conn:
        if conn.execute("SELECT 1 FROM department WHERE institution_id=? AND code=?", (iid, code)).fetchone():
            return jsonify({"success": False, "error": f"Department code '{code}' already exists"}), 400
        new_id = conn.insert(
            "INSERT INTO department (institution_id, code, name, category) VALUES (?,?,?,?)",
            (iid, code, name, cat)
        )
    return jsonify({"success": True, "id": new_id})


@app.route("/api/departments/<int:did>", methods=["DELETE"])
@creator_or_admin_required
def api_delete_department(did):
    iid = inst_id()
    with get_db() as conn:
        conn.execute("DELETE FROM department WHERE id=? AND institution_id=?", (did, iid))
    return jsonify({"success": True})


@app.route("/api/institution/upload-logo", methods=["POST"])
@admin_required
def api_upload_logo():
    iid = inst_id()
    if "logo_file" not in request.files:
        return jsonify({"success": False, "error": "No file uploaded. Please select an image file."}), 400
    file = request.files["logo_file"]
    if file.filename == "":
        return jsonify({"success": False, "error": "No file selected."}), 400
    if file and allowed_file(file.filename):
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"logo_{iid}_{int(time.time())}.{ext}"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        logo_url = f"/static/uploads/logos/{filename}"
        with get_db() as conn:
            conn.execute("UPDATE institution SET logo_url=? WHERE id=?", (logo_url, iid))
        return jsonify({"success": True, "logo_url": logo_url})
    return jsonify({"success": False, "error": "Invalid format. Allowed formats: PNG, JPG, JPEG, SVG, WEBP"}), 400


@app.route("/api/institution/remove-logo", methods=["POST"])
@admin_required
def api_remove_logo():
    iid = inst_id()
    with get_db() as conn:
        conn.execute("UPDATE institution SET logo_url='' WHERE id=?", (iid,))
    return jsonify({"success": True})


@app.route("/api/institution/logo", methods=["POST"])
@admin_required
def api_update_logo():
    iid = inst_id()
    d   = request.get_json() or {}
    logo_url = d.get("logo_url", "").strip()
    with get_db() as conn:
        conn.execute("UPDATE institution SET logo_url=? WHERE id=?", (logo_url, iid))
    return jsonify({"success": True, "logo_url": logo_url})


@app.route("/api/settings/add_user", methods=["POST"])
@admin_required
def api_add_user():
    iid = inst_id()
    d   = request.get_json() or {}
    username = d.get("username", "").strip()
    password = d.get("password", "")
    email = d.get("email", "").strip()
    role = d.get("role", "viewer").strip().lower()
    dept_id = d.get("department_id")
    if dept_id:
        try:
            dept_id = int(dept_id)
        except (ValueError, TypeError):
            dept_id = None
    else:
        dept_id = None

    if not username or not password:
        return jsonify({"success": False, "error": "Username and password are required"})

    allowed_roles = ("admin", "dean", "hod", "coordinator", "creator", "viewer")
    if role not in allowed_roles:
        role = "viewer"

    with get_db() as conn:
        if conn.execute("SELECT 1 FROM users WHERE institution_id=? AND username=?", (iid, username)).fetchone():
            return jsonify({"success": False, "error": "Username already exists"})

        # Enforce exactly at most 2 coordinators per department rule
        if role in ("coordinator", "creator") and dept_id:
            coord_count = conn.execute("""
                SELECT COUNT(*) as cnt FROM users 
                WHERE institution_id=? AND department_id=? AND role IN ('coordinator', 'creator')
            """, (iid, dept_id)).fetchone()["cnt"]
            if coord_count >= 2:
                dept_row = conn.execute("SELECT code, name FROM department WHERE id=?", (dept_id,)).fetchone()
                dept_name = dept_row["name"] if dept_row else "this department"
                return jsonify({
                    "success": False, 
                    "error": f"Department '{dept_name}' already has the maximum of 2 Timetable Coordinators assigned."
                })

        conn.insert(
            "INSERT INTO users (institution_id, username, email, password_hash, role, department_id) VALUES (?,?,?,?,?,?)",
            (iid, username, email, hash_password(password), role, dept_id)
        )
        log_activity(
            institution_id=iid,
            actor_name=session.get("username", "Admin"),
            actor_role=session.get("role", "admin"),
            action_type="USER_CREATED",
            title=f"User '{username}' Created",
            description=f"Assigned role: {role.upper()}" + (f" for department ID {dept_id}" if dept_id else ""),
            department_id=dept_id
        )
    return jsonify({"success": True})


@app.route("/api/settings/delete_user/<int:uid>", methods=["DELETE"])
@admin_required
def api_delete_user(uid):
    iid = inst_id()
    if uid == session["user_id"]:
        return jsonify({"success": False, "error": "Cannot delete yourself"})
    with get_db() as conn:
        conn.execute("DELETE FROM users WHERE id=? AND institution_id=?", (uid, iid))
    return jsonify({"success": True})


# ══════════════════════════════════════════════════════════════════════════════
# ROOMS
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/rooms")
@login_required
def rooms_page():
    iid = inst_id()
    with get_db() as conn:
        rooms = [dict(r) for r in conn.execute(
            "SELECT * FROM rooms WHERE institution_id=? ORDER BY name", (iid,)
        ).fetchall()]
    return render_template("rooms.html", rooms=rooms)


@app.route("/api/rooms", methods=["GET"])
@login_required
def api_get_rooms():
    iid = inst_id()
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM rooms WHERE institution_id=? ORDER BY name", (iid,)).fetchall()
    return jsonify([dict(r) for r in rows])


@app.route("/api/rooms", methods=["POST"])
@creator_or_admin_required
def api_add_room():
    iid = inst_id()
    d   = request.get_json()
    with get_db() as conn:
        if conn.execute("SELECT 1 FROM rooms WHERE institution_id=? AND name=?", (iid, d["name"])).fetchone():
            return jsonify({"success": False, "error": "Room name already exists"})
        new_id = conn.insert(
            "INSERT INTO rooms (institution_id,name,capacity,room_type) VALUES (?,?,?,?)",
            (iid, d["name"], int(d.get("capacity", 60)), d.get("room_type", "classroom"))
        )
    return jsonify({"success": True, "id": new_id})


@app.route("/api/rooms/<int:rid>", methods=["PUT"])
@creator_or_admin_required
def api_update_room(rid):
    iid = inst_id()
    d   = request.get_json()
    with get_db() as conn:
        conn.execute(
            "UPDATE rooms SET name=?,capacity=?,room_type=? WHERE id=? AND institution_id=?",
            (d["name"], int(d.get("capacity", 60)), d.get("room_type", "classroom"), rid, iid)
        )
    return jsonify({"success": True})


@app.route("/api/rooms/<int:rid>", methods=["DELETE"])
@creator_or_admin_required
def api_delete_room(rid):
    iid = inst_id()
    with get_db() as conn:
        conn.execute("DELETE FROM rooms WHERE id=? AND institution_id=?", (rid, iid))
    return jsonify({"success": True})


# ══════════════════════════════════════════════════════════════════════════════
# STAFF
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/staff")
@login_required
def staff_page():
    iid = inst_id()
    with get_db() as conn:
        staff_rows = conn.execute("SELECT * FROM staff WHERE institution_id=? ORDER BY name", (iid,)).fetchall()
        subj_rows  = conn.execute("SELECT * FROM subject WHERE institution_id=? ORDER BY subject_name", (iid,)).fetchall()
        dept_rows  = conn.execute("SELECT * FROM department WHERE institution_id=? ORDER BY category, code", (iid,)).fetchall()

        # Batch load all staff-subject mappings for this institution in 1 query
        mapping_rows = conn.execute("""
            SELECT ss.staff_id, ss.subject_id, s.subject_name
            FROM staff_subjects ss
            JOIN subject s ON s.id = ss.subject_id
            JOIN staff st ON st.id = ss.staff_id
            WHERE st.institution_id=?
        """, (iid,)).fetchall()

        from collections import defaultdict
        staff_sids = defaultdict(list)
        staff_snames = defaultdict(list)
        for m in mapping_rows:
            staff_sids[m["staff_id"]].append(m["subject_id"])
            staff_snames[m["staff_id"]].append(m["subject_name"])

        staff_list = []
        for s in staff_rows:
            s = dict(s)
            sid = s["id"]
            sids = staff_sids.get(sid, [])
            snames = staff_snames.get(sid, [])
            pct = round(s["allocated_periods"] / s["max_periods_per_week"] * 100
                        if s["max_periods_per_week"] else 0, 1)
            staff_list.append({
                **s, "subject_ids": sids, "subject_names": snames, "pct": pct,
                "performance_score": round(s["allocated_periods"] * 0.4 + s["experience"] * 0.3, 2)
            })
    return render_template("staff.html", staff=staff_list, subjects=[dict(r) for r in subj_rows], departments=[dict(r) for r in dept_rows])


@app.route("/api/staff", methods=["GET"])
@login_required
def api_get_staff():
    iid = inst_id()
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM staff WHERE institution_id=? ORDER BY name", (iid,)).fetchall()
        mapping_rows = conn.execute("""
            SELECT ss.staff_id, ss.subject_id
            FROM staff_subjects ss
            JOIN staff st ON st.id = ss.staff_id
            WHERE st.institution_id=?
        """, (iid,)).fetchall()
        from collections import defaultdict
        staff_sids = defaultdict(list)
        for m in mapping_rows:
            staff_sids[m["staff_id"]].append(m["subject_id"])

        result = []
        for s in rows:
            s = dict(s)
            result.append({**s, "subjects": staff_sids.get(s["id"], [])})
    return jsonify(result)


@app.route("/api/staff/<int:sid>", methods=["GET"])
@login_required
def api_get_one_staff(sid):
    iid = inst_id()
    with get_db() as conn:
        s = conn.execute("SELECT * FROM staff WHERE id=? AND institution_id=?", (sid, iid)).fetchone()
        if not s:
            return jsonify({"error": "Not found"}), 404
        s = dict(s)
        sids = [r["subject_id"] for r in conn.execute(
            "SELECT subject_id FROM staff_subjects WHERE staff_id=?", (sid,)
        ).fetchall()]
    return jsonify({**s, "subjects": sids})


@app.route("/api/staff", methods=["POST"])
@creator_or_admin_required
def api_add_staff():
    iid = inst_id()
    d   = request.get_json()
    avail = ",".join(d.get("available_days", ["Mon", "Tue", "Wed", "Thu", "Fri"]))
    with get_db() as conn:
        new_id = conn.insert(
            "INSERT INTO staff (institution_id,name,department,experience,"
            "max_periods_per_week,max_periods_per_day,email,available_days) VALUES (?,?,?,?,?,?,?,?)",
            (iid, d["name"], d["department"], int(d.get("experience", 0)),
             int(d.get("max_periods_per_week", 20)), int(d.get("max_periods_per_day", 4)),
             d.get("email", ""), avail)
        )
        for sid2 in d.get("subjects", []):
            conn.execute("INSERT OR IGNORE INTO staff_subjects VALUES (?,?)", (new_id, sid2))
    return jsonify({"success": True, "id": new_id})


@app.route("/api/staff/<int:sid>", methods=["PUT"])
@creator_or_admin_required
def api_update_staff(sid):
    iid = inst_id()
    d   = request.get_json()
    avail = ",".join(d.get("available_days", ["Mon", "Tue", "Wed", "Thu", "Fri"]))
    with get_db() as conn:
        conn.execute(
            "UPDATE staff SET name=?,department=?,experience=?,max_periods_per_week=?,"
            "max_periods_per_day=?,email=?,available_days=? WHERE id=? AND institution_id=?",
            (d["name"], d["department"], int(d.get("experience", 0)),
             int(d.get("max_periods_per_week", 20)), int(d.get("max_periods_per_day", 4)),
             d.get("email", ""), avail, sid, iid)
        )
        conn.execute("DELETE FROM staff_subjects WHERE staff_id=?", (sid,))
        for sid2 in d.get("subjects", []):
            conn.execute("INSERT OR IGNORE INTO staff_subjects VALUES (?,?)", (sid, sid2))
    return jsonify({"success": True})


@app.route("/api/staff/<int:sid>", methods=["DELETE"])
@creator_or_admin_required
def api_delete_staff(sid):
    iid = inst_id()
    with get_db() as conn:
        conn.execute("DELETE FROM staff WHERE id=? AND institution_id=?", (sid, iid))
    return jsonify({"success": True})


# ══════════════════════════════════════════════════════════════════════════════
# SUBJECTS
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/subjects")
@login_required
def subjects_page():
    iid = inst_id()
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM subject WHERE institution_id=? ORDER BY subject_name", (iid,)).fetchall()
        staff_rows = conn.execute("SELECT id, name, department FROM staff WHERE institution_id=? ORDER BY name", (iid,)).fetchall()
    return render_template("subjects.html", subjects=[dict(r) for r in rows], staff_list=[dict(r) for r in staff_rows])


@app.route("/api/subjects", methods=["GET"])
@login_required
def api_get_subjects():
    iid = inst_id()
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM subject WHERE institution_id=? ORDER BY subject_name", (iid,)).fetchall()
    return jsonify([dict(r) for r in rows])


@app.route("/api/subjects", methods=["POST"])
@creator_or_admin_required
def api_add_subject():
    iid = inst_id()
    d   = request.get_json()
    abbr = (d.get("abbreviation") or "").strip()
    if not abbr:
        abbr = generate_abbreviation(d["subject_name"], bool(int(d.get("is_lab", 0))))
    lab_staff2 = d.get("lab_staff2_id") or None
    is_mm = int(bool(d.get("is_mentor_meeting", False)))
    with get_db() as conn:
        new_id = conn.insert(
            "INSERT INTO subject (institution_id,subject_name,subject_code,abbreviation,department,"
            "periods_per_week,difficulty_level,is_lab,lab_duration,lab_staff2_id,is_mentor_meeting) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (iid, d["subject_name"], d.get("subject_code", ""), abbr, d["department"],
             int(d.get("periods_per_week", 3)), int(d.get("difficulty_level", 3)),
             int(d.get("is_lab", 0)), int(d.get("lab_duration", 2)),
             int(lab_staff2) if lab_staff2 else None, is_mm)
        )
    return jsonify({"success": True, "id": new_id})


@app.route("/api/subjects/<int:sid>", methods=["PUT"])
@creator_or_admin_required
def api_update_subject(sid):
    iid = inst_id()
    d   = request.get_json()
    abbr = (d.get("abbreviation") or "").strip()
    if not abbr:
        abbr = generate_abbreviation(d["subject_name"], bool(int(d.get("is_lab", 0))))
    lab_staff2 = d.get("lab_staff2_id") or None
    is_mm = int(bool(d.get("is_mentor_meeting", False)))
    with get_db() as conn:
        conn.execute(
            "UPDATE subject SET subject_name=?,subject_code=?,abbreviation=?,department=?,periods_per_week=?,"
            "difficulty_level=?,is_lab=?,lab_duration=?,lab_staff2_id=?,is_mentor_meeting=? WHERE id=? AND institution_id=?",
            (d["subject_name"], d.get("subject_code", ""), abbr, d["department"],
             int(d.get("periods_per_week", 3)), int(d.get("difficulty_level", 3)),
             int(d.get("is_lab", 0)), int(d.get("lab_duration", 2)),
             int(lab_staff2) if lab_staff2 else None, is_mm, sid, iid)
        )
    return jsonify({"success": True})


@app.route("/api/subjects/<int:sid>", methods=["DELETE"])
@creator_or_admin_required
def api_delete_subject(sid):
    iid = inst_id()
    with get_db() as conn:
        conn.execute("DELETE FROM subject WHERE id=? AND institution_id=?", (sid, iid))
    return jsonify({"success": True})


@app.route("/api/subjects/<int:sid>/recommend")
@login_required
def api_recommend(sid):
    return jsonify(get_recommendations(sid, inst_id()))


# ══════════════════════════════════════════════════════════════════════════════
# CLASSES
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/classes")
@login_required
def classes_page():
    iid = inst_id()
    with get_db() as conn:
        cls_rows  = conn.execute("SELECT * FROM class_section WHERE institution_id=? ORDER BY name", (iid,)).fetchall()
        subj_rows = conn.execute("SELECT * FROM subject WHERE institution_id=? ORDER BY subject_name", (iid,)).fetchall()
        staff_rows = conn.execute("SELECT id, name, department FROM staff WHERE institution_id=? ORDER BY name", (iid,)).fetchall()

        # Batch load all class-subject mappings in 1 query
        cs_rows = conn.execute("""
            SELECT cs.class_id, s.subject_name
            FROM class_subjects cs
            JOIN subject s ON s.id = cs.subject_id
            JOIN class_section c ON c.id = cs.class_id
            WHERE c.institution_id=?
        """, (iid,)).fetchall()
        from collections import defaultdict
        class_subjs = defaultdict(list)
        for r in cs_rows:
            class_subjs[r["class_id"]].append(r["subject_name"])

        # Batch load all class mentors in 1 query
        mentor_rows = conn.execute("""
            SELECT cm.class_id, cm.staff_id, st.name as staff_name
            FROM class_mentor cm
            JOIN staff st ON st.id = cm.staff_id
            JOIN class_section c ON c.id = cm.class_id
            WHERE c.institution_id=?
            ORDER BY cm.mentor_order
        """, (iid,)).fetchall()
        class_mentors = defaultdict(list)
        for m in mentor_rows:
            class_mentors[m["class_id"]].append(dict(m))

        classes = []
        for c in cls_rows:
            c = dict(c)
            cid = c["id"]
            classes.append({
                **c,
                "subject_names": class_subjs.get(cid, []),
                "mentors": class_mentors.get(cid, [])
            })
    return render_template("classes.html", classes=classes,
                           subjects=[dict(r) for r in subj_rows],
                           staff_list=[dict(r) for r in staff_rows])


@app.route("/api/classes", methods=["GET"])
@login_required
def api_get_classes():
    iid = inst_id()
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM class_section WHERE institution_id=? ORDER BY name", (iid,)).fetchall()

        # Batch load class subjects
        cs_rows = conn.execute("""
            SELECT cs.class_id, cs.subject_id
            FROM class_subjects cs
            JOIN class_section c ON c.id = cs.class_id
            WHERE c.institution_id=?
        """, (iid,)).fetchall()
        from collections import defaultdict
        class_sids = defaultdict(list)
        for r in cs_rows:
            class_sids[r["class_id"]].append(r["subject_id"])

        # Batch load class mentors
        mentor_rows = conn.execute("""
            SELECT cm.class_id, cm.staff_id
            FROM class_mentor cm
            JOIN class_section c ON c.id = cm.class_id
            WHERE c.institution_id=?
            ORDER BY cm.mentor_order
        """, (iid,)).fetchall()
        class_mentors = defaultdict(list)
        for m in mentor_rows:
            class_mentors[m["class_id"]].append(m["staff_id"])

        result = []
        for c in rows:
            c = dict(c)
            cid = c["id"]
            result.append({
                **c,
                "subjects": class_sids.get(cid, []),
                "mentor_ids": class_mentors.get(cid, [])
            })
    return jsonify(result)


@app.route("/api/classes/<int:cid>", methods=["GET"])
@login_required
def api_get_one_class(cid):
    iid = inst_id()
    with get_db() as conn:
        c = conn.execute("SELECT * FROM class_section WHERE id=? AND institution_id=?", (cid, iid)).fetchone()
        if not c:
            return jsonify({"error": "Not found"}), 404
        c = dict(c)
        sids = [r["subject_id"] for r in conn.execute(
            "SELECT subject_id FROM class_subjects WHERE class_id=?", (cid,)
        ).fetchall()]
        mentor_ids = [r["staff_id"] for r in conn.execute(
            "SELECT staff_id FROM class_mentor WHERE class_id=? ORDER BY mentor_order", (cid,)
        ).fetchall()]
    return jsonify({**c, "subjects": sids, "mentor_ids": mentor_ids})


@app.route("/api/classes", methods=["POST"])
@creator_or_admin_required
def api_add_class():
    iid = inst_id()
    d   = request.get_json()
    with get_db() as conn:
        new_id = conn.insert(
            "INSERT INTO class_section (institution_id,name,department,semester,strength) VALUES (?,?,?,?,?)",
            (iid, d["name"], d["department"], int(d.get("semester", 1)), int(d.get("strength", 60)))
        )
        for sid2 in d.get("subjects", []):
            conn.execute("INSERT OR IGNORE INTO class_subjects VALUES (?,?)", (new_id, sid2))
        # Save mentors
        conn.execute("DELETE FROM class_mentor WHERE class_id=?", (new_id,))
        for order, m_id in enumerate(d.get("mentor_ids", [])[:2], start=1):
            if m_id:
                conn.execute("INSERT OR IGNORE INTO class_mentor (class_id,staff_id,mentor_order) VALUES (?,?,?)",
                             (new_id, int(m_id), order))
    return jsonify({"success": True, "id": new_id})


@app.route("/api/classes/<int:cid>", methods=["PUT"])
@creator_or_admin_required
def api_update_class(cid):
    iid = inst_id()
    d   = request.get_json()
    with get_db() as conn:
        conn.execute(
            "UPDATE class_section SET name=?,department=?,semester=?,strength=? WHERE id=? AND institution_id=?",
            (d["name"], d["department"], int(d.get("semester", 1)), int(d.get("strength", 60)), cid, iid)
        )
        conn.execute("DELETE FROM class_subjects WHERE class_id=?", (cid,))
        for sid2 in d.get("subjects", []):
            conn.execute("INSERT OR IGNORE INTO class_subjects VALUES (?,?)", (cid, sid2))
        # Save mentors (max 2)
        conn.execute("DELETE FROM class_mentor WHERE class_id=?", (cid,))
        for order, m_id in enumerate(d.get("mentor_ids", [])[:2], start=1):
            if m_id:
                conn.execute("INSERT OR IGNORE INTO class_mentor (class_id,staff_id,mentor_order) VALUES (?,?,?)",
                             (cid, int(m_id), order))
    return jsonify({"success": True})


@app.route("/api/classes/<int:cid>/mentors", methods=["GET"])
@login_required
def api_get_class_mentors(cid):
    iid = inst_id()
    with get_db() as conn:
        rows = conn.execute(
            "SELECT cm.staff_id, st.name, cm.mentor_order FROM class_mentor cm "
            "JOIN staff st ON st.id=cm.staff_id WHERE cm.class_id=? "
            "AND st.institution_id=? ORDER BY cm.mentor_order",
            (cid, iid)
        ).fetchall()
    return jsonify([dict(r) for r in rows])


@app.route("/api/classes/<int:cid>/mentors", methods=["PUT"])
@creator_or_admin_required
def api_set_class_mentors(cid):
    iid = inst_id()
    d = request.get_json() or {}
    with get_db() as conn:
        # Verify class belongs to this institution
        if not conn.execute("SELECT 1 FROM class_section WHERE id=? AND institution_id=?", (cid, iid)).fetchone():
            return jsonify({"success": False, "error": "Class not found"}), 404
        conn.execute("DELETE FROM class_mentor WHERE class_id=?", (cid,))
        for order, m_id in enumerate(d.get("mentor_ids", [])[:2], start=1):
            if m_id:
                conn.execute(
                    "INSERT OR IGNORE INTO class_mentor (class_id,staff_id,mentor_order) VALUES (?,?,?)",
                    (cid, int(m_id), order)
                )
    return jsonify({"success": True})


@app.route("/api/classes/<int:cid>", methods=["DELETE"])
@creator_or_admin_required
def api_delete_class(cid):
    iid = inst_id()
    with get_db() as conn:
        conn.execute("DELETE FROM class_section WHERE id=? AND institution_id=?", (cid, iid))
    return jsonify({"success": True})




# ══════════════════════════════════════════════════════════════════════════════
# SYLLABUS & CURRICULUM IMPORTER
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/syllabus-import")
@login_required
def syllabus_import_page():
    iid = inst_id()
    with get_db() as conn:
        staff_rows = conn.execute("SELECT id, name, department FROM staff WHERE institution_id=? ORDER BY name", (iid,)).fetchall()
        rooms_rows = conn.execute("SELECT id, name, room_type FROM rooms WHERE institution_id=? ORDER BY name", (iid,)).fetchall()
    return render_template("syllabus_import.html", staff_list=[dict(r) for r in staff_rows], rooms_list=[dict(r) for r in rooms_rows])


@app.route("/api/syllabus/presets", methods=["GET"])
@login_required
def api_syllabus_presets():
    return jsonify(syllabus_parser.get_regulation_presets())


@app.route("/api/curriculum/index", methods=["GET"])
@login_required
def api_curriculum_index():
    import curriculum_data
    return jsonify(curriculum_data.get_all_curricula_index())


@app.route("/api/curriculum/get", methods=["GET"])
@login_required
def api_curriculum_get():
    import curriculum_data
    reg = request.args.get("regulation", "R2021")
    deg = request.args.get("degree", "B.E.")
    dept = request.args.get("department", "CSE")
    sem = request.args.get("semester", "Semester 1")
    res = curriculum_data.get_curriculum(reg, deg, dept, sem)
    if res:
        return jsonify(res)

    # Database query fallback
    try:
        with get_db() as conn:
            rows = conn.execute("""
                SELECT subject_code, subject_name, abbreviation, periods_per_week, difficulty_level, is_lab, lab_duration, credits
                FROM inbuilt_curriculum
                WHERE (regulation=? OR regulation LIKE ?) AND (department=? OR department LIKE ?) AND (semester=? OR semester LIKE ?)
                ORDER BY id
            """, (reg, f"%{reg}%", dept, f"%{dept}%", sem, f"%{sem}%")).fetchall()
            if rows:
                subjects = [dict(r) for r in rows]
                sem_num = sem.split()[-1] if " " in sem else sem
                return jsonify({
                    "success": True,
                    "regulation": f"Anna University {reg}",
                    "degree": deg,
                    "department": dept,
                    "semester": sem,
                    "class_name": f"{deg} {dept} - Sem {sem_num} (Sec A)",
                    "subjects": subjects
                })
    except Exception:
        pass

    return jsonify({"success": False, "error": "Curriculum not found"}), 404


@app.route("/api/syllabus/parse", methods=["POST"])
@creator_or_admin_required
def api_syllabus_parse():
    if "syllabus_pdf" not in request.files:
        return jsonify({"success": False, "error": "No PDF file uploaded"}), 400
    file = request.files["syllabus_pdf"]
    if file.filename == "":
        return jsonify({"success": False, "error": "No file selected"}), 400
    
    file_bytes = file.read()
    if len(file_bytes) == 0:
        return jsonify({"success": False, "error": "Uploaded file is empty"}), 400
        
    result = syllabus_parser.parse_syllabus_pdf(file_bytes)
    return jsonify(result)


@app.route("/api/syllabus/import", methods=["POST"])
@creator_or_admin_required
def api_syllabus_import():
    iid = inst_id()
    d = request.get_json() or {}
    
    class_name = (d.get("class_name") or "").strip()
    department = (d.get("department") or "CSE").strip()
    semester = int(d.get("semester", 3))
    strength = int(d.get("strength", 60))
    subjects = d.get("subjects", [])
    
    if not class_name:
        return jsonify({"success": False, "error": "Class name is required"}), 400
    if not subjects:
        return jsonify({"success": False, "error": "At least one subject must be selected"}), 400

    created_subject_ids = []
    with get_db() as conn:
        for s in subjects:
            s_name = (s.get("subject_name") or "").strip()
            s_code = (s.get("subject_code") or "").strip()
            s_abbr = (s.get("abbreviation") or "").strip()
            if not s_abbr:
                s_abbr = syllabus_parser.generate_abbreviation(s_name, bool(s.get("is_lab")))
            s_dept = (s.get("department") or department).strip()
            s_periods = int(s.get("periods_per_week", 3))
            s_diff = int(s.get("difficulty_level", 3))
            s_is_lab = 1 if s.get("is_lab") else 0
            s_lab_dur = int(s.get("lab_duration", 2)) if s_is_lab else 0
            staff_id = s.get("assigned_staff_id")
            lab_staff2_id = s.get("lab_staff2_id")

            # Check if subject already exists for this institution
            existing_sub = None
            if s_code:
                existing_sub = conn.execute(
                    "SELECT id FROM subject WHERE institution_id=? AND subject_code=?",
                    (iid, s_code)
                ).fetchone()
            if not existing_sub:
                existing_sub = conn.execute(
                    "SELECT id FROM subject WHERE institution_id=? AND subject_name=? AND department=?",
                    (iid, s_name, s_dept)
                ).fetchone()

            if existing_sub:
                sub_id = dict(existing_sub)["id"]
                conn.execute(
                    "UPDATE subject SET abbreviation=?, periods_per_week=?, difficulty_level=?, is_lab=?, lab_duration=?, lab_staff2_id=? WHERE id=?",
                    (s_abbr, s_periods, s_diff, s_is_lab, s_lab_dur, int(lab_staff2_id) if lab_staff2_id else None, sub_id)
                )

            else:
                sub_id = conn.insert(
                    "INSERT INTO subject (institution_id, subject_name, subject_code, abbreviation, department, "
                    "periods_per_week, difficulty_level, is_lab, lab_duration, lab_staff2_id, is_mentor_meeting) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)",
                    (iid, s_name, s_code, s_abbr, s_dept, s_periods, s_diff, s_is_lab, s_lab_dur, int(lab_staff2_id) if lab_staff2_id else None)
                )

            created_subject_ids.append(sub_id)

            # Assign faculty to subject if provided
            if staff_id:
                conn.execute(
                    "INSERT OR IGNORE INTO staff_subjects (staff_id, subject_id) VALUES (?, ?)",
                    (int(staff_id), sub_id)
                )
            if lab_staff2_id:
                conn.execute(
                    "INSERT OR IGNORE INTO staff_subjects (staff_id, subject_id) VALUES (?, ?)",
                    (int(lab_staff2_id), sub_id)
                )

        # Create or update Class Section
        existing_cls = conn.execute(
            "SELECT id FROM class_section WHERE institution_id=? AND name=?",
            (iid, class_name)
        ).fetchone()

        if existing_cls:
            class_id = dict(existing_cls)["id"]
            conn.execute(
                "UPDATE class_section SET department=?, semester=?, strength=? WHERE id=?",
                (department, semester, strength, class_id)
            )
        else:
            class_id = conn.insert(
                "INSERT INTO class_section (institution_id, name, department, semester, strength) VALUES (?, ?, ?, ?, ?)",
                (iid, class_name, department, semester, strength)
            )

        # Link all subjects to this class
        for sub_id in created_subject_ids:
            conn.execute(
                "INSERT OR IGNORE INTO class_subjects (class_id, subject_id) VALUES (?, ?)",
                (class_id, sub_id)
            )

    return jsonify({
        "success": True,
        "class_id": class_id,
        "created_subjects_count": len(created_subject_ids),
        "message": f"Successfully created class '{class_name}' with {len(created_subject_ids)} subjects."
    })


# ══════════════════════════════════════════════════════════════════════════════
# TIMETABLE
# ══════════════════════════════════════════════════════════════════════════════


@app.route("/timetable")
@login_required
def timetable_page():
    iid = inst_id()
    with get_db() as conn:
        classes   = [dict(r) for r in conn.execute(
            "SELECT * FROM class_section WHERE institution_id=? ORDER BY name", (iid,)).fetchall()]
        staff_all = [dict(r) for r in conn.execute(
            "SELECT * FROM staff WHERE institution_id=? ORDER BY name", (iid,)).fetchall()]
        active_tt = conn.execute(
            "SELECT * FROM timetable WHERE institution_id=? AND is_active=1 ORDER BY id DESC LIMIT 1", (iid,)
        ).fetchone()
        all_subjects = [dict(r) for r in conn.execute(
            "SELECT * FROM subject WHERE institution_id=? ORDER BY subject_name", (iid,)).fetchall()]
        depts = [dict(r) for r in conn.execute(
            "SELECT * FROM department WHERE institution_id=? ORDER BY category, code", (iid,)
        ).fetchall()]
        inst = conn.execute("SELECT institution_type FROM institution WHERE id=?", (iid,)).fetchone()
        inst_type = inst["institution_type"] if inst and "institution_type" in inst.keys() else "college"

        days         = get_working_days(iid, conn=conn)
        periods      = get_period_count(iid, conn=conn)
        period_slots = get_period_slots(iid, conn=conn)
        conflicts    = get_conflict_list(iid, conn=conn)

    return render_template("timetable.html",
                           classes=classes,
                           staff_list=staff_all,
                           active_timetable=dict(active_tt) if active_tt else None,
                           days=days,
                           periods=list(range(1, periods + 1)),
                           period_slots=period_slots,
                           all_subjects=all_subjects,
                           departments=depts,
                           inst_type=inst_type,
                           conflicts=conflicts)


@app.route("/api/timetable/validate")
@login_required
def api_validate():
    warnings = validate_before_generate(inst_id())
    return jsonify({"warnings": warnings, "safe": len(warnings) == 0})


@app.route("/api/timetable/generate", methods=["POST"])
@creator_or_admin_required
def api_generate():
    """Synchronous generate (for simple clients). Prefer the SSE endpoint."""
    iid = inst_id()
    d   = request.get_json() or {}
    warnings = validate_before_generate(iid)
    if warnings and not d.get("force"):
        return jsonify({"success": False, "warnings": warnings})
    tt_id, conflicts = generate_timetable(iid, d.get("name", "Auto Generated"))
    uname = session.get("username", "Coordinator")
    role = session.get("role", "coordinator")
    log_activity(
        institution_id=iid,
        actor_name=uname,
        actor_role=role,
        action_type="TIMETABLE_GENERATED",
        title="Timetable Generated",
        description=f"{uname} ({role.upper()}) generated draft timetable with {len(conflicts)} conflict(s)",
        entity_type="timetable",
        entity_id=tt_id
    )
    realtime_hub.publish(iid, "timetable_generated", {"timetable_id": tt_id, "conflicts": len(conflicts)})
    return jsonify({"success": True, "timetable_id": tt_id,
                    "conflicts": conflicts, "conflict_count": len(conflicts)})


@app.route("/api/timetable/generate/stream")
@creator_or_admin_required
def api_generate_stream():
    """
    Server-Sent Events endpoint for real-time generation progress.
    Client connects and receives events:  data: {"pct":30,"msg":"..."}\n\n
    Final event includes tt_id and conflicts list.
    """
    iid   = inst_id()
    name  = request.args.get("name", "Auto Generated")
    force = request.args.get("force", "false").lower() == "true"

    def _sse():
        # Pre-validation
        warnings = validate_before_generate(iid)
        if warnings and not force:
            yield f"data: {json.dumps({'type': 'warnings', 'warnings': warnings})}\n\n"
            return

        for event in generate_timetable_iter(iid, name):
            yield f"data: {json.dumps(event)}\n\n"

    return Response(
        stream_with_context(_sse()),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no", "Connection": "keep-alive"}
    )


@app.route("/api/timetable/delete", methods=["DELETE"])
@creator_or_admin_required
def api_delete_tt():
    iid = inst_id()
    delete_timetable(iid)
    uname = session.get("username", "Coordinator")
    role = session.get("role", "coordinator")
    log_activity(
        institution_id=iid,
        actor_name=uname,
        actor_role=role,
        action_type="TIMETABLE_DELETED",
        title="Timetable Reset",
        description=f"{uname} ({role.upper()}) reset the active timetable slots"
    )
    realtime_hub.publish(iid, "timetable_deleted", {})
    return jsonify({"success": True})


@app.route("/api/timetable/conflicts")
@login_required
def api_get_conflicts():
    return jsonify(get_conflict_list(inst_id()))


@app.route("/api/timetable/class/<int:class_id>")
@login_required
def api_class_tt(class_id):
    iid = inst_id()
    tt_id, grid = get_class_timetable(class_id, iid)
    slots = get_period_slots(iid)
    tt_meta = {}
    if tt_id:
        with get_db() as conn:
            row = conn.execute("""
                SELECT status, name, submitted_by, submitted_at, approved_by, approved_at,
                       published_by, published_at, rejection_note
                FROM timetable WHERE id=? AND institution_id=?
            """, (tt_id, iid)).fetchone()
            if row:
                tt_meta = dict(row)
    return jsonify({
        "timetable_id": tt_id, "grid": grid,
        "days": get_working_days(iid), "periods": get_period_count(iid),
        "period_slots": slots,
        "meta": tt_meta,
    })


@app.route("/api/timetable/staff/<int:staff_id>")
@login_required
def api_staff_tt(staff_id):
    iid = inst_id()
    tt_id, grid = get_staff_timetable(staff_id, iid)
    slots = get_period_slots(iid)
    return jsonify({
        "timetable_id": tt_id, "grid": grid,
        "days": get_working_days(iid), "periods": get_period_count(iid),
        "period_slots": slots,
    })


@app.route("/api/timetable/slot/<int:slot_id>/edit", methods=["PUT"])
@creator_or_admin_required
def api_edit_slot(slot_id):
    """Change the staff member for a slot."""
    iid = inst_id()
    d = request.get_json() or {}
    staff_id = d.get("staff_id")
    ok, msg = edit_slot(slot_id, staff_id, iid)
    if ok:
        uname = session.get("username", "Coordinator")
        role = session.get("role", "coordinator")
        cell_lock_manager.release(iid, slot_id, session.get("user_id", 0))
        realtime_hub.publish(iid, "slot_updated", {
            "slot_id": slot_id,
            "action": "edit",
            "staff_id": staff_id,
            "user": uname
        })
        log_activity(
            institution_id=iid,
            actor_name=uname,
            actor_role=role,
            action_type="SLOT_EDITED",
            title="Slot Faculty Reassigned",
            description=f"{uname} ({role.upper()}) reassigned faculty on slot #{slot_id}",
            entity_type="slot",
            entity_id=slot_id
        )
    return jsonify({"success": ok, "message": msg})


@app.route("/api/timetable/slot/<int:slot_id>/move", methods=["PUT"])
@creator_or_admin_required
def api_move_slot(slot_id):
    """Move slot to a different day and period."""
    iid = inst_id()
    d = request.get_json() or {}
    day = d.get("day", "")
    period = int(d.get("period", 0))
    ok, msg = move_slot(slot_id, day, period, iid)
    if ok:
        uname = session.get("username", "Coordinator")
        role = session.get("role", "coordinator")
        cell_lock_manager.release(iid, slot_id, session.get("user_id", 0))
        realtime_hub.publish(iid, "slot_updated", {
            "slot_id": slot_id,
            "action": "move",
            "day": day,
            "period": period,
            "user": uname
        })
        log_activity(
            institution_id=iid,
            actor_name=uname,
            actor_role=role,
            action_type="SLOT_MOVED",
            title="Slot Relocated",
            description=f"{uname} moved slot #{slot_id} to {day} Period {period}",
            entity_type="slot",
            entity_id=slot_id
        )
    return jsonify({"success": ok, "message": msg})


@app.route("/api/timetable/slot/<int:slot_id>/swap", methods=["PUT"])
@creator_or_admin_required
def api_swap_slot(slot_id):
    """Swap two slots' day/period positions."""
    iid = inst_id()
    d = request.get_json() or {}
    target_slot_id = int(d.get("target_slot_id", 0))
    ok, msg = swap_slots(slot_id, target_slot_id, iid)
    if ok:
        uname = session.get("username", "Coordinator")
        role = session.get("role", "coordinator")
        cell_lock_manager.release(iid, slot_id, session.get("user_id", 0))
        cell_lock_manager.release(iid, target_slot_id, session.get("user_id", 0))
        realtime_hub.publish(iid, "slot_updated", {
            "slot_id": slot_id,
            "target_slot_id": target_slot_id,
            "action": "swap",
            "user": uname
        })
        log_activity(
            institution_id=iid,
            actor_name=uname,
            actor_role=role,
            action_type="SLOTS_SWAPPED",
            title="Slots Swapped",
            description=f"{uname} swapped slots #{slot_id} and #{target_slot_id}",
            entity_type="slot",
            entity_id=slot_id
        )
    return jsonify({"success": ok, "message": msg})


@app.route("/api/timetable/slot/<int:slot_id>/check_move")
@login_required
def api_check_move(slot_id):
    """Real-time conflict check for drag-over validation (called rapidly during drag)."""
    day    = request.args.get("day", "")
    period = int(request.args.get("period", 0))
    conflicts = check_move_valid(slot_id, day, period, inst_id())
    return jsonify({"ok": len(conflicts) == 0, "conflicts": conflicts})


@app.route("/api/timetable/slot/<int:slot_id>/staff_options")
@login_required
def api_slot_staff_options(slot_id):
    return jsonify(get_slot_staff_options(slot_id, inst_id()))


# ══════════════════════════════════════════════════════════════════════════════
# REAL-TIME SSE & LIVE COLLABORATION ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/api/realtime/stream")
@login_required
def api_realtime_stream():
    """
    Persistent SSE connection for instant grid synchronization, cell lock presence,
    and institutional live activity notifications.
    """
    iid = inst_id()
    q = realtime_hub.subscribe(iid)

    def event_generator():
        # Initial greeting event
        yield realtime_hub.format_sse("connected", {"status": "connected", "institution_id": iid})
        try:
            while True:
                try:
                    # Wait up to 15 seconds for a message
                    msg = q.get(timeout=15.0)
                    yield realtime_hub.format_sse(msg["event"], msg["data"])
                except Exception:
                    # Timeout reached -> emit lightweight heartbeat ping
                    yield ": ping\n\n"
        except GeneratorExit:
            pass
        finally:
            realtime_hub.unsubscribe(iid, q)

    return Response(
        stream_with_context(event_generator()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive"
        }
    )


@app.route("/api/timetable/locks", methods=["GET"])
@login_required
def api_get_cell_locks():
    """Retrieve all current cell presence locks for the institution."""
    return jsonify(cell_lock_manager.get_active_locks(inst_id()))


@app.route("/api/timetable/slot/<int:slot_id>/lock", methods=["POST"])
@creator_or_admin_required
def api_acquire_cell_lock(slot_id):
    """Acquire a temporary 60-second edit lock on a timetable slot."""
    iid = inst_id()
    uid = session.get("user_id")
    uname = session.get("username", "User")
    role = session.get("role", "coordinator")
    success, lock_info = cell_lock_manager.acquire(iid, slot_id, uid, uname, role)
    if success:
        realtime_hub.publish(iid, "slot_locked", lock_info)
        return jsonify({"success": True, "lock": lock_info})
    return jsonify({
        "success": False,
        "error": f"Slot is currently being edited by {lock_info.get('username')} ({lock_info.get('role')}).",
        "lock": lock_info
    }), 409


@app.route("/api/timetable/slot/<int:slot_id>/unlock", methods=["POST"])
@creator_or_admin_required
def api_release_cell_lock(slot_id):
    """Release an edit lock held by the current user."""
    iid = inst_id()
    uid = session.get("user_id")
    released = cell_lock_manager.release(iid, slot_id, uid)
    if released:
        realtime_hub.publish(iid, "slot_unlocked", {"slot_id": slot_id})
    return jsonify({"success": released})


@app.route("/api/timetable/slot/<int:slot_id>/override-lock", methods=["POST"])
@admin_required
def api_override_cell_lock(slot_id):
    """Master Admin emergency lock override."""
    iid = inst_id()
    uid = session.get("user_id")
    uname = session.get("username", "Admin")
    success, old_lock = cell_lock_manager.override(iid, slot_id, uid, uname)
    lock_info = {"slot_id": slot_id, "user_id": uid, "username": uname, "role": "admin"}
    realtime_hub.publish(iid, "slot_locked", lock_info)
    log_activity(
        institution_id=iid,
        actor_name=uname,
        actor_role="admin",
        action_type="LOCK_OVERRIDDEN",
        title="Admin Lock Override",
        description=f"Master Admin overridden edit lock on slot #{slot_id}" + (f" previously held by {old_lock.get('username')}" if old_lock else ""),
        entity_type="slot",
        entity_id=slot_id
    )
    return jsonify({"success": True, "lock": lock_info})


# ══════════════════════════════════════════════════════════════════════════════
# TIMETABLE APPROVAL & PUBLISHING WORKFLOW
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/api/timetable/<int:timetable_id>/submit", methods=["POST"])
@creator_or_admin_required
def api_submit_timetable(timetable_id):
    iid = inst_id()
    uname = session.get("username", "Coordinator")
    role = session.get("role", "coordinator")
    ok, msg = submit_timetable(timetable_id, iid, uname, role)
    if ok:
        realtime_hub.publish(iid, "timetable_status_changed", {"timetable_id": timetable_id, "status": "submitted", "actor": uname})
    return jsonify({"success": ok, "message": msg})


@app.route("/api/timetable/<int:timetable_id>/approve", methods=["POST"])
@hod_or_admin_required
def api_approve_timetable(timetable_id):
    iid = inst_id()
    uname = session.get("username", "HOD")
    role = session.get("role", "hod")
    ok, msg = approve_timetable(timetable_id, iid, uname, role)
    if ok:
        realtime_hub.publish(iid, "timetable_status_changed", {"timetable_id": timetable_id, "status": "approved", "actor": uname})
    return jsonify({"success": ok, "message": msg})


@app.route("/api/timetable/<int:timetable_id>/reject", methods=["POST"])
@hod_or_admin_required
def api_reject_timetable(timetable_id):
    iid = inst_id()
    uname = session.get("username", "HOD")
    role = session.get("role", "hod")
    data = request.get_json() or {}
    reason = data.get("reason", "")
    ok, msg = reject_timetable(timetable_id, iid, uname, role, reason)
    if ok:
        realtime_hub.publish(iid, "timetable_status_changed", {"timetable_id": timetable_id, "status": "draft", "actor": uname, "reason": reason})
    return jsonify({"success": ok, "message": msg})


@app.route("/api/timetable/<int:timetable_id>/publish", methods=["POST"])
@hod_or_admin_required
def api_publish_timetable(timetable_id):
    iid = inst_id()
    uname = session.get("username", "Admin")
    role = session.get("role", "admin")
    ok, msg = publish_timetable(timetable_id, iid, uname, role)
    if ok:
        realtime_hub.publish(iid, "timetable_status_changed", {"timetable_id": timetable_id, "status": "published", "actor": uname})
    return jsonify({"success": ok, "message": msg})


# ══════════════════════════════════════════════════════════════════════════════
# LIVE ACTIVITY FEED ENDPOINT
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/api/activity/feed", methods=["GET"])
@login_required
def api_activity_feed():
    iid = inst_id()
    role = session.get("role")
    dept_id = session.get("department_id")
    # Master Admin and Dean monitor institution-wide; HOD & Coordinators see department
    if role in ("admin", "dean"):
        dept_id = None
    activities = get_recent_activities(iid, department_id=dept_id, limit=35)
    return jsonify(activities)


# ── Export ──────────────────────────────────────────────────────────────────

@app.route("/api/timetable/export/csv/<int:class_id>")
@login_required
def api_export_csv(class_id):
    iid = inst_id()
    tt_id, grid = get_class_timetable(class_id, iid)
    if not tt_id:
        return "No timetable", 404
    days  = get_working_days(iid)
    slots = get_period_slots(iid)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Slot/Time"] + days)
    for s in slots:
        row = [f"{s['label']} ({s['start_time']}-{s['end_time']})"]
        for day in days:
            cell = grid.get(day, {}).get(s["slot_order"])
            if s["slot_type"] != "period":
                row.append(f"── {s['label']} ──")
            elif cell:
                row.append(f"{cell['subject_name']} ({cell.get('staff_display') or cell['staff_name']})")
            else:
                row.append("")
        writer.writerow(row)
    resp = make_response(output.getvalue())
    resp.headers["Content-Type"]        = "text/csv"
    resp.headers["Content-Disposition"] = f"attachment; filename=timetable_class_{class_id}.csv"
    return resp


@app.route("/api/timetable/export/pdf/<int:class_id>")
@login_required
def api_export_pdf(class_id):
    """Redirect to official 1-page printable timetable with Print/PDF and PNG download."""
    return redirect(url_for("timetable_print_page", class_id=class_id))


@app.route("/timetable/print/<int:class_id>")
@app.route("/timetable/download/<int:class_id>")
@login_required
def timetable_print_page(class_id):
    """Institutional printable & image download view with dynamic college name, logo, department."""
    iid = inst_id()
    data = get_class_printable_data(class_id, iid)
    if not data:
        flash("No active timetable found for this class.", "warning")
        return redirect(url_for("timetable_page"))

    with get_db() as conn:
        classes = [dict(r) for r in conn.execute(
            "SELECT id, name, department FROM class_section WHERE institution_id=? ORDER BY name",
            (iid,)
        ).fetchall()]

    return render_template("timetable_print.html", data=data, current_class_id=class_id, classes=classes)


@app.route("/api/classes/<int:cid>/meta", methods=["PUT"])
@creator_or_admin_required
def api_update_class_meta(cid):
    iid = inst_id()
    d = request.get_json()
    with get_db() as conn:
        conn.execute(
            "UPDATE class_section SET venue=?, academic_year=?, strength=?, department=? WHERE id=? AND institution_id=?",
            (d.get("venue", ""), d.get("academic_year", "2026-27"), int(d.get("strength", 60)), d.get("department", "CSE"), cid, iid)
        )
    return jsonify({"success": True})


# ══════════════════════════════════════════════════════════════════════════════
# ANALYTICS
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/analytics")
@login_required
def analytics_page():
    results = compute_analytics(inst_id())
    return render_template("analytics.html", results=results)


# ══════════════════════════════════════════════════════════════════════════════
# STARTUP
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    init_db()
    seed_demo_institution()
    print(f"[START] SchedHub v3 starting (backend: {DB_BACKEND})")
    app.run(debug=True, threaded=True)
