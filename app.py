"""
SchedHub v3 — Automated Institutional Timetable & Faculty Allocation Portal
Supports SQLite (dev) and Supabase/PostgreSQL (production) via DATABASE_URL env var.
Run: python app.py
"""
import os, json, csv, io, time
from werkzeug.utils import secure_filename
from flask import (Flask, render_template, request, jsonify, redirect,
                   url_for, session, flash, make_response, Response,
                   stream_with_context)
from database import get_db, init_db, seed_demo_institution, seed_realtime_model, check_password, hash_password, generate_abbreviation
from scheduler import (
    generate_timetable, generate_timetable_iter,
    get_class_timetable, get_staff_timetable,
    get_recommendations, compute_analytics, validate_before_generate,
    get_working_days, get_period_count, get_period_slots,
    edit_slot, move_slot, swap_slots, check_move_valid,
    delete_timetable, get_conflict_list, get_slot_staff_options,
    get_class_printable_data,
)
from auth import login_required, admin_required, creator_or_admin_required, inject_user, get_current_user
from config import FLASK_SECRET_KEY, DB_BACKEND

app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY

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
try:
    init_db()
    seed_demo_institution()
except Exception as _e:
    print(f"[INIT] Serverless startup check: {_e}")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

inject_user(app)

def inst_id():
    return session.get("institution_id")


# ══════════════════════════════════════════════════════════════════════════════
# ROOT
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/")
def root():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))
    return redirect(url_for("auth_login"))


# ══════════════════════════════════════════════════════════════════════════════
# AUTH — Register / Login / Logout
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/login", methods=["GET", "POST"])
def auth_login():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))
    mode = request.args.get("mode", "login")
    if request.method == "POST":
        username  = request.form.get("username", "").strip()
        password  = request.form.get("password", "")
        inst_code = request.form.get("inst_code", "").strip().upper()
        with get_db() as conn:
            inst = conn.execute("SELECT * FROM institution WHERE code=?", (inst_code,)).fetchone()
            if not inst:
                flash("Institution code not found. Please verify code or register.", "danger")
                return render_template("login.html", mode="login")
            user = conn.execute(
                "SELECT * FROM users WHERE institution_id=? AND username=?",
                (dict(inst)["id"], username)
            ).fetchone()
        if user and check_password(dict(user)["password_hash"], password):
            user = dict(user)
            inst = dict(inst)
            session.update({
                "user_id": user["id"],
                "username": user["username"],
                "institution_id": inst["id"],
                "institution_name": inst["name"],
                "role": user["role"],
            })
            return redirect(url_for("dashboard"))
        flash("Invalid username or password for this institution.", "danger")
        return render_template("login.html", mode="login")
    return render_template("login.html", mode=mode)


@app.route("/register", methods=["GET", "POST"])
def auth_register():
    if request.method == "POST":
        inst_name   = request.form.get("inst_name", "").strip()
        inst_code   = request.form.get("inst_code", "").strip().upper()
        inst_email  = request.form.get("inst_email", "").strip()
        admin_email = request.form.get("admin_email", "").strip() or inst_email
        username    = request.form.get("username", "").strip()
        password    = request.form.get("password", "")
        address     = request.form.get("address", "").strip()
        phone       = request.form.get("phone", "").strip()
        logo_url    = ""
        logo_text   = "🎓"

        if not inst_name or not inst_code or not username or not password:
            flash("Please fill in all mandatory fields.", "danger")
            return render_template("login.html", mode="register")

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

        session.update({
            "user_id": user_id,
            "username": username,
            "institution_id": new_inst_id,
            "institution_name": inst_name,
            "role": "admin",
            "first_login": True,
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
        users = conn.execute("SELECT id,username,email,role,created_at FROM users WHERE institution_id=?", (iid,)).fetchall()
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
    d   = request.get_json()
    with get_db() as conn:
        if conn.execute("SELECT 1 FROM users WHERE institution_id=? AND username=?", (iid, d["username"])).fetchone():
            return jsonify({"success": False, "error": "Username already exists"})
        role = d.get("role", "viewer")
        if role not in ("admin", "creator", "viewer"):
            role = "viewer"
        conn.insert(
            "INSERT INTO users (institution_id,username,email,password_hash,role) VALUES (?,?,?,?,?)",
            (iid, d["username"], d.get("email", ""), hash_password(d["password"]), role)
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
        staff_list = []
        for s in staff_rows:
            s = dict(s)
            sids = [r["subject_id"] for r in conn.execute(
                "SELECT subject_id FROM staff_subjects WHERE staff_id=?", (s["id"],)
            ).fetchall()]
            snames = []
            if sids:
                placeholders = ",".join("?" * len(sids))
                snames = [dict(r)["subject_name"] for r in conn.execute(
                    f"SELECT subject_name FROM subject WHERE id IN ({placeholders})", sids
                ).fetchall()]
            pct = round(s["allocated_periods"] / s["max_periods_per_week"] * 100
                        if s["max_periods_per_week"] else 0, 1)
            staff_list.append({**s, "subject_ids": sids, "subject_names": snames, "pct": pct,
                               "performance_score": round(s["allocated_periods"] * 0.4 + s["experience"] * 0.3, 2)})
    return render_template("staff.html", staff=staff_list, subjects=[dict(r) for r in subj_rows], departments=[dict(r) for r in dept_rows])


@app.route("/api/staff", methods=["GET"])
@login_required
def api_get_staff():
    iid = inst_id()
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM staff WHERE institution_id=? ORDER BY name", (iid,)).fetchall()
        result = []
        for s in rows:
            s = dict(s)
            sids = [r["subject_id"] for r in conn.execute(
                "SELECT subject_id FROM staff_subjects WHERE staff_id=?", (s["id"],)
            ).fetchall()]
            result.append({**s, "subjects": sids})
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
    return render_template("subjects.html", subjects=[dict(r) for r in rows])


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
    with get_db() as conn:
        new_id = conn.insert(
            "INSERT INTO subject (institution_id,subject_name,subject_code,abbreviation,department,"
            "periods_per_week,difficulty_level,is_lab,lab_duration) VALUES (?,?,?,?,?,?,?,?,?)",
            (iid, d["subject_name"], d.get("subject_code", ""), abbr, d["department"],
             int(d.get("periods_per_week", 3)), int(d.get("difficulty_level", 3)),
             int(d.get("is_lab", 0)), int(d.get("lab_duration", 2)))
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
    with get_db() as conn:
        conn.execute(
            "UPDATE subject SET subject_name=?,subject_code=?,abbreviation=?,department=?,periods_per_week=?,"
            "difficulty_level=?,is_lab=?,lab_duration=? WHERE id=? AND institution_id=?",
            (d["subject_name"], d.get("subject_code", ""), abbr, d["department"],
             int(d.get("periods_per_week", 3)), int(d.get("difficulty_level", 3)),
             int(d.get("is_lab", 0)), int(d.get("lab_duration", 2)), sid, iid)
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
        classes = []
        for c in cls_rows:
            c = dict(c)
            snames = [dict(r)["subject_name"] for r in conn.execute("""
                SELECT s.subject_name FROM subject s
                JOIN class_subjects cs ON cs.subject_id=s.id WHERE cs.class_id=?
            """, (c["id"],)).fetchall()]
            classes.append({**c, "subject_names": snames})
    return render_template("classes.html", classes=classes, subjects=[dict(r) for r in subj_rows])


@app.route("/api/classes", methods=["GET"])
@login_required
def api_get_classes():
    iid = inst_id()
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM class_section WHERE institution_id=? ORDER BY name", (iid,)).fetchall()
        result = []
        for c in rows:
            c = dict(c)
            sids = [r["subject_id"] for r in conn.execute(
                "SELECT subject_id FROM class_subjects WHERE class_id=?", (c["id"],)
            ).fetchall()]
            result.append({**c, "subjects": sids})
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
    return jsonify({**c, "subjects": sids})


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
    return jsonify({"success": True})


@app.route("/api/classes/<int:cid>", methods=["DELETE"])
@creator_or_admin_required
def api_delete_class(cid):
    iid = inst_id()
    with get_db() as conn:
        conn.execute("DELETE FROM class_section WHERE id=? AND institution_id=?", (cid, iid))
    return jsonify({"success": True})


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

    days         = get_working_days(iid)
    periods      = get_period_count(iid)
    period_slots = get_period_slots(iid)
    conflicts    = get_conflict_list(iid)

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
    delete_timetable(inst_id())
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
    return jsonify({
        "timetable_id": tt_id, "grid": grid,
        "days": get_working_days(iid), "periods": get_period_count(iid),
        "period_slots": slots,
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
    d = request.get_json()
    ok, msg = edit_slot(slot_id, d["staff_id"], inst_id())
    return jsonify({"success": ok, "message": msg})


@app.route("/api/timetable/slot/<int:slot_id>/move", methods=["PUT"])
@creator_or_admin_required
def api_move_slot(slot_id):
    """Move slot to a different day and period."""
    d = request.get_json()
    ok, msg = move_slot(slot_id, d["day"], int(d["period"]), inst_id())
    return jsonify({"success": ok, "message": msg})


@app.route("/api/timetable/slot/<int:slot_id>/swap", methods=["PUT"])
@creator_or_admin_required
def api_swap_slot(slot_id):
    """Swap two slots' day/period positions."""
    d = request.get_json()
    ok, msg = swap_slots(slot_id, int(d["target_slot_id"]), inst_id())
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
                row.append(f"{cell['subject_name']} ({cell['staff_name']})")
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
