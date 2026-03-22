"""
EduSchedule Pro v2 — Multi-tenant Timetable Generator
Run: python app.py
"""
import os, json, csv, io
from flask import (Flask, render_template, request, jsonify,
                   redirect, url_for, session, flash, make_response)
from database import get_db, init_db, seed_demo_institution, check_password, hash_password
from scheduler import (generate_timetable, get_class_timetable, get_staff_timetable,
                       get_recommendations, compute_analytics, validate_before_generate,
                       get_working_days, get_period_count, get_period_slots,
                       edit_slot, delete_timetable)
from auth import login_required, admin_required, inject_user, get_current_user

app = Flask(__name__)
app.secret_key = 'edupro-v2-secret-xK9mP2024'

inject_user(app)

def inst_id():
    return session.get('institution_id')

# ══════════════════════════════════════════════════════════════
# AUTH — Register / Login / Logout
# ══════════════════════════════════════════════════════════════

@app.route('/login', methods=['GET','POST'])
def auth_login():
    if session.get('user_id'):
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form.get('username','').strip()
        password = request.form.get('password','')
        inst_code = request.form.get('inst_code','').strip()
        with get_db() as conn:
            inst = conn.execute("SELECT * FROM institution WHERE code=?", (inst_code,)).fetchone()
            if not inst:
                flash('Institution code not found.', 'danger')
                return render_template('login.html')
            user = conn.execute(
                "SELECT * FROM users WHERE institution_id=? AND username=?",
                (inst['id'], username)
            ).fetchone()
        if user and check_password(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['institution_id'] = inst['id']
            session['institution_name'] = inst['name']
            session['role'] = user['role']
            return redirect(url_for('dashboard'))
        flash('Invalid credentials.', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET','POST'])
def auth_register():
    if request.method == 'POST':
        inst_name = request.form.get('inst_name','').strip()
        inst_code = request.form.get('inst_code','').strip().upper()
        username  = request.form.get('username','').strip()
        password  = request.form.get('password','')
        email     = request.form.get('email','').strip()
        address   = request.form.get('address','').strip()
        phone     = request.form.get('phone','').strip()
        logo_text = request.form.get('logo_text','🏫').strip() or '🏫'

        if not inst_name or not inst_code or not username or not password:
            flash('All required fields must be filled.', 'danger')
            return render_template('register.html')

        with get_db() as conn:
            existing = conn.execute("SELECT 1 FROM institution WHERE code=?", (inst_code,)).fetchone()
            if existing:
                flash('Institution code already taken. Choose a different one.', 'danger')
                return render_template('register.html')
            conn.execute(
                "INSERT INTO institution (name,code,address,email,phone,logo_text) VALUES (?,?,?,?,?,?)",
                (inst_name, inst_code, address, email, phone, logo_text)
            )
            new_inst_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            conn.execute(
                "INSERT INTO users (institution_id,username,email,password_hash,role) VALUES (?,?,?,?,?)",
                (new_inst_id, username, email, hash_password(password), 'admin')
            )
            # Default time config
            conn.execute(
                "INSERT INTO time_config (institution_id,periods_per_day,working_days) VALUES (?,?,?)",
                (new_inst_id, 6, 'Mon,Tue,Wed,Thu,Fri')
            )
            # Default period slots
            default_slots = [
                (1,"Period 1","09:00","09:50","period"),
                (2,"Period 2","09:50","10:40","period"),
                (3,"Break",   "10:40","11:00","break"),
                (4,"Period 3","11:00","11:50","period"),
                (5,"Period 4","11:50","12:40","period"),
                (6,"Lunch",   "12:40","13:20","lunch"),
                (7,"Period 5","13:20","14:10","period"),
                (8,"Period 6","14:10","15:00","period"),
            ]
            for s in default_slots:
                conn.execute(
                    "INSERT INTO period_slot (institution_id,slot_order,label,start_time,end_time,slot_type) VALUES (?,?,?,?,?,?)",
                    (new_inst_id,)+s
                )
        flash(f'Institution "{inst_name}" registered! Please login.', 'success')
        return redirect(url_for('auth_login'))
    return render_template('register.html')

@app.route('/logout')
def auth_logout():
    session.clear()
    return redirect(url_for('auth_login'))

# ══════════════════════════════════════════════════════════════
# DASHBOARD
# ══════════════════════════════════════════════════════════════

@app.route('/')
@app.route('/dashboard')
@login_required
def dashboard():
    iid = inst_id()
    with get_db() as conn:
        total_staff    = conn.execute("SELECT COUNT(*) FROM staff WHERE institution_id=?", (iid,)).fetchone()[0]
        total_subjects = conn.execute("SELECT COUNT(*) FROM subject WHERE institution_id=?", (iid,)).fetchone()[0]
        total_classes  = conn.execute("SELECT COUNT(*) FROM class_section WHERE institution_id=?", (iid,)).fetchone()[0]
        active_tt = conn.execute(
            "SELECT * FROM timetable WHERE institution_id=? AND is_active=1 ORDER BY id DESC LIMIT 1", (iid,)
        ).fetchone()
        total_slots = 0
        if active_tt:
            total_slots = conn.execute(
                "SELECT COUNT(*) FROM timetable_slot WHERE timetable_id=? AND institution_id=?",
                (active_tt['id'], iid)
            ).fetchone()[0]
        # Recent timetables for history panel
        tt_history = conn.execute(
            "SELECT * FROM timetable WHERE institution_id=? ORDER BY id DESC LIMIT 5", (iid,)
        ).fetchall()
    return render_template('dashboard.html',
        total_staff=total_staff, total_subjects=total_subjects,
        total_classes=total_classes, total_slots=total_slots,
        active_timetable=dict(active_tt) if active_tt else None,
        tt_history=[dict(t) for t in tt_history])

@app.route('/api/dashboard/workload')
@login_required
def api_workload():
    iid = inst_id()
    with get_db() as conn:
        rows = conn.execute(
            "SELECT name,allocated_periods,max_periods_per_week FROM staff WHERE institution_id=? ORDER BY name", (iid,)
        ).fetchall()
    return jsonify({'labels':[r['name'] for r in rows],
                    'allocated':[r['allocated_periods'] for r in rows],
                    'max':[r['max_periods_per_week'] for r in rows]})

@app.route('/api/dashboard/performance')
@login_required
def api_performance():
    results = compute_analytics(inst_id())[:10]
    cmap = {'Promotion':'#10b981','Salary Hike':'#3b82f6','Overloaded':'#ef4444','Underutilized':'#f59e0b','Normal':'#6b7280'}
    return jsonify({'labels':[r['staff']['name'] for r in results],
                    'scores':[r['staff']['performance_score'] for r in results],
                    'colors':[cmap.get(r['suggestion'],'#6b7280') for r in results]})

# ══════════════════════════════════════════════════════════════
# SETTINGS — Time Config + Period Slots
# ══════════════════════════════════════════════════════════════

@app.route('/settings')
@login_required
def settings_page():
    iid = inst_id()
    with get_db() as conn:
        cfg = conn.execute("SELECT * FROM time_config WHERE institution_id=?", (iid,)).fetchone()
        slots = conn.execute(
            "SELECT * FROM period_slot WHERE institution_id=? ORDER BY slot_order", (iid,)
        ).fetchall()
        inst = conn.execute("SELECT * FROM institution WHERE id=?", (iid,)).fetchone()
        users = conn.execute(
            "SELECT id,username,email,role,created_at FROM users WHERE institution_id=?", (iid,)
        ).fetchall()
    days_list = ['Mon','Tue','Wed','Thu','Fri','Sat']
    selected_days = cfg['working_days'].split(',') if cfg else ['Mon','Tue','Wed','Thu','Fri']
    return render_template('settings.html',
        cfg=dict(cfg) if cfg else {},
        slots=[dict(s) for s in slots],
        inst=dict(inst) if inst else {},
        users=[dict(u) for u in users],
        days_list=days_list, selected_days=selected_days)

@app.route('/api/settings/time', methods=['POST'])
@admin_required
def api_save_time_config():
    iid = inst_id()
    d = request.get_json()
    working_days = ','.join(d.get('working_days', ['Mon','Tue','Wed','Thu','Fri']))
    periods_per_day = int(d.get('periods_per_day', 6))
    with get_db() as conn:
        existing = conn.execute("SELECT 1 FROM time_config WHERE institution_id=?", (iid,)).fetchone()
        if existing:
            conn.execute(
                "UPDATE time_config SET periods_per_day=?, working_days=?, updated_at=datetime('now') WHERE institution_id=?",
                (periods_per_day, working_days, iid)
            )
        else:
            conn.execute(
                "INSERT INTO time_config (institution_id,periods_per_day,working_days) VALUES (?,?,?)",
                (iid, periods_per_day, working_days)
            )
    return jsonify({'success': True})

@app.route('/api/settings/slots', methods=['POST'])
@admin_required
def api_save_slots():
    iid = inst_id()
    slots = request.get_json()  # list of {slot_order, label, start_time, end_time, slot_type}
    with get_db() as conn:
        conn.execute("DELETE FROM period_slot WHERE institution_id=?", (iid,))
        for s in slots:
            conn.execute(
                "INSERT INTO period_slot (institution_id,slot_order,label,start_time,end_time,slot_type) VALUES (?,?,?,?,?,?)",
                (iid, s['slot_order'], s['label'], s['start_time'], s['end_time'], s.get('slot_type','period'))
            )
    return jsonify({'success': True})

@app.route('/api/settings/institution', methods=['POST'])
@admin_required
def api_update_institution():
    iid = inst_id()
    d = request.get_json()
    with get_db() as conn:
        conn.execute(
            "UPDATE institution SET name=?,address=?,email=?,phone=?,logo_text=? WHERE id=?",
            (d.get('name'), d.get('address'), d.get('email'), d.get('phone'), d.get('logo_text','🏫'), iid)
        )
    session['institution_name'] = d.get('name', session.get('institution_name'))
    return jsonify({'success': True})

@app.route('/api/settings/add_user', methods=['POST'])
@admin_required
def api_add_user():
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Admin only'}), 403
    iid = inst_id()
    d = request.get_json()
    with get_db() as conn:
        existing = conn.execute(
            "SELECT 1 FROM users WHERE institution_id=? AND username=?", (iid, d['username'])
        ).fetchone()
        if existing:
            return jsonify({'success': False, 'error': 'Username already exists'})
        conn.execute(
            "INSERT INTO users (institution_id,username,email,password_hash,role) VALUES (?,?,?,?,?)",
            (iid, d['username'], d.get('email',''), hash_password(d['password']), d.get('role','viewer'))
        )
    return jsonify({'success': True})

@app.route('/api/settings/delete_user/<int:uid>', methods=['DELETE'])
@admin_required
def api_delete_user(uid):
    if session.get('role') != 'admin':
        return jsonify({'success': False}), 403
    iid = inst_id()
    if uid == session['user_id']:
        return jsonify({'success': False, 'error': "Can't delete yourself"})
    with get_db() as conn:
        conn.execute("DELETE FROM users WHERE id=? AND institution_id=?", (uid, iid))
    return jsonify({'success': True})

# ══════════════════════════════════════════════════════════════
# STAFF
# ══════════════════════════════════════════════════════════════

@app.route('/staff')
@login_required
def staff_page():
    iid = inst_id()
    with get_db() as conn:
        staff_rows = conn.execute("SELECT * FROM staff WHERE institution_id=? ORDER BY name", (iid,)).fetchall()
        subj_rows  = conn.execute("SELECT * FROM subject WHERE institution_id=? ORDER BY subject_name", (iid,)).fetchall()
        staff_list = []
        for s in staff_rows:
            sids = [r['subject_id'] for r in conn.execute(
                "SELECT subject_id FROM staff_subjects WHERE staff_id=?", (s['id'],)).fetchall()]
            snames = [r['subject_name'] for r in conn.execute(
                "SELECT subject_name FROM subject WHERE id IN ({})".format(','.join('?'*len(sids))), sids
            ).fetchall()] if sids else []
            pct = round(s['allocated_periods']/s['max_periods_per_week']*100 if s['max_periods_per_week'] else 0, 1)
            staff_list.append({**dict(s), 'subject_ids': sids, 'subject_names': snames, 'pct': pct,
                               'performance_score': round(s['allocated_periods']*0.4+s['experience']*0.3, 2)})
    return render_template('staff.html', staff=staff_list, subjects=[dict(r) for r in subj_rows])

@app.route('/api/staff', methods=['GET'])
@login_required
def api_get_staff():
    iid = inst_id()
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM staff WHERE institution_id=? ORDER BY name", (iid,)).fetchall()
        result = []
        for s in rows:
            sids = [r['subject_id'] for r in conn.execute(
                "SELECT subject_id FROM staff_subjects WHERE staff_id=?", (s['id'],)).fetchall()]
            result.append({**dict(s), 'subjects': sids})
    return jsonify(result)

@app.route('/api/staff/<int:sid>', methods=['GET'])
@login_required
def api_get_one_staff(sid):
    iid = inst_id()
    with get_db() as conn:
        s = conn.execute("SELECT * FROM staff WHERE id=? AND institution_id=?", (sid, iid)).fetchone()
        if not s: return jsonify({'error':'Not found'}), 404
        sids = [r['subject_id'] for r in conn.execute(
            "SELECT subject_id FROM staff_subjects WHERE staff_id=?", (sid,)).fetchall()]
    return jsonify({**dict(s), 'subjects': sids})

@app.route('/api/staff', methods=['POST'])
@admin_required
def api_add_staff():
    iid = inst_id()
    d = request.get_json()
    avail = ','.join(d.get('available_days', ['Mon','Tue','Wed','Thu','Fri']))
    with get_db() as conn:
        conn.execute(
            "INSERT INTO staff (institution_id,name,department,experience,max_periods_per_week,email,available_days) VALUES (?,?,?,?,?,?,?)",
            (iid, d['name'], d['department'], int(d.get('experience',0)),
             int(d.get('max_periods_per_week',20)), d.get('email',''), avail))
        new_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        for sid2 in d.get('subjects', []):
            conn.execute("INSERT OR IGNORE INTO staff_subjects VALUES (?,?)", (new_id, sid2))
    return jsonify({'success': True, 'id': new_id})

@app.route('/api/staff/<int:sid>', methods=['PUT'])
@admin_required
def api_update_staff(sid):
    iid = inst_id()
    d = request.get_json()
    avail = ','.join(d.get('available_days', ['Mon','Tue','Wed','Thu','Fri']))
    with get_db() as conn:
        conn.execute(
            "UPDATE staff SET name=?,department=?,experience=?,max_periods_per_week=?,email=?,available_days=? WHERE id=? AND institution_id=?",
            (d['name'], d['department'], int(d.get('experience',0)),
             int(d.get('max_periods_per_week',20)), d.get('email',''), avail, sid, iid))
        conn.execute("DELETE FROM staff_subjects WHERE staff_id=?", (sid,))
        for sid2 in d.get('subjects', []):
            conn.execute("INSERT OR IGNORE INTO staff_subjects VALUES (?,?)", (sid, sid2))
    return jsonify({'success': True})

@app.route('/api/staff/<int:sid>', methods=['DELETE'])
@admin_required
def api_delete_staff(sid):
    iid = inst_id()
    with get_db() as conn:
        conn.execute("DELETE FROM staff WHERE id=? AND institution_id=?", (sid, iid))
    return jsonify({'success': True})

# ══════════════════════════════════════════════════════════════
# SUBJECTS
# ══════════════════════════════════════════════════════════════

@app.route('/subjects')
@login_required
def subjects_page():
    iid = inst_id()
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM subject WHERE institution_id=? ORDER BY subject_name", (iid,)).fetchall()
    return render_template('subjects.html', subjects=[dict(r) for r in rows])

@app.route('/api/subjects', methods=['GET'])
@login_required
def api_get_subjects():
    iid = inst_id()
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM subject WHERE institution_id=? ORDER BY subject_name", (iid,)).fetchall()
    return jsonify([dict(r) for r in rows])

@app.route('/api/subjects', methods=['POST'])
@admin_required
def api_add_subject():
    iid = inst_id()
    d = request.get_json()
    with get_db() as conn:
        conn.execute(
            "INSERT INTO subject (institution_id,subject_name,subject_code,department,periods_per_week,difficulty_level,is_lab,lab_duration) VALUES (?,?,?,?,?,?,?,?)",
            (iid, d['subject_name'], d.get('subject_code',''), d['department'],
             int(d.get('periods_per_week',3)), int(d.get('difficulty_level',3)),
             int(d.get('is_lab',0)), int(d.get('lab_duration',2))))
        new_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    return jsonify({'success': True, 'id': new_id})

@app.route('/api/subjects/<int:sid>', methods=['PUT'])
@admin_required
def api_update_subject(sid):
    iid = inst_id()
    d = request.get_json()
    with get_db() as conn:
        conn.execute(
            "UPDATE subject SET subject_name=?,subject_code=?,department=?,periods_per_week=?,difficulty_level=?,is_lab=?,lab_duration=? WHERE id=? AND institution_id=?",
            (d['subject_name'], d.get('subject_code',''), d['department'],
             int(d.get('periods_per_week',3)), int(d.get('difficulty_level',3)),
             int(d.get('is_lab',0)), int(d.get('lab_duration',2)), sid, iid))
    return jsonify({'success': True})

@app.route('/api/subjects/<int:sid>', methods=['DELETE'])
@admin_required
def api_delete_subject(sid):
    iid = inst_id()
    with get_db() as conn:
        conn.execute("DELETE FROM subject WHERE id=? AND institution_id=?", (sid, iid))
    return jsonify({'success': True})

@app.route('/api/subjects/<int:sid>/recommend')
@login_required
def api_recommend(sid):
    return jsonify(get_recommendations(sid, inst_id()))

# ══════════════════════════════════════════════════════════════
# CLASSES
# ══════════════════════════════════════════════════════════════

@app.route('/classes')
@login_required
def classes_page():
    iid = inst_id()
    with get_db() as conn:
        cls_rows  = conn.execute("SELECT * FROM class_section WHERE institution_id=? ORDER BY name", (iid,)).fetchall()
        subj_rows = conn.execute("SELECT * FROM subject WHERE institution_id=? ORDER BY subject_name", (iid,)).fetchall()
        classes = []
        for c in cls_rows:
            snames = [r['subject_name'] for r in conn.execute("""
                SELECT s.subject_name FROM subject s JOIN class_subjects cs ON cs.subject_id=s.id WHERE cs.class_id=?
            """, (c['id'],)).fetchall()]
            classes.append({**dict(c), 'subject_names': snames})
    return render_template('classes.html', classes=classes, subjects=[dict(r) for r in subj_rows])

@app.route('/api/classes', methods=['GET'])
@login_required
def api_get_classes():
    iid = inst_id()
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM class_section WHERE institution_id=? ORDER BY name", (iid,)).fetchall()
        result = []
        for c in rows:
            sids = [r['subject_id'] for r in conn.execute(
                "SELECT subject_id FROM class_subjects WHERE class_id=?", (c['id'],)).fetchall()]
            result.append({**dict(c), 'subjects': sids})
    return jsonify(result)

@app.route('/api/classes/<int:cid>', methods=['GET'])
@login_required
def api_get_one_class(cid):
    iid = inst_id()
    with get_db() as conn:
        c = conn.execute("SELECT * FROM class_section WHERE id=? AND institution_id=?", (cid, iid)).fetchone()
        if not c: return jsonify({'error':'Not found'}), 404
        sids = [r['subject_id'] for r in conn.execute(
            "SELECT subject_id FROM class_subjects WHERE class_id=?", (cid,)).fetchall()]
    return jsonify({**dict(c), 'subjects': sids})

@app.route('/api/classes', methods=['POST'])
@admin_required
def api_add_class():
    iid = inst_id()
    d = request.get_json()
    with get_db() as conn:
        conn.execute(
            "INSERT INTO class_section (institution_id,name,department,semester,strength) VALUES (?,?,?,?,?)",
            (iid, d['name'], d['department'], int(d.get('semester',1)), int(d.get('strength',60))))
        new_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        for sid2 in d.get('subjects', []):
            conn.execute("INSERT OR IGNORE INTO class_subjects VALUES (?,?)", (new_id, sid2))
    return jsonify({'success': True, 'id': new_id})

@app.route('/api/classes/<int:cid>', methods=['PUT'])
@admin_required
def api_update_class(cid):
    iid = inst_id()
    d = request.get_json()
    with get_db() as conn:
        conn.execute(
            "UPDATE class_section SET name=?,department=?,semester=?,strength=? WHERE id=? AND institution_id=?",
            (d['name'], d['department'], int(d.get('semester',1)), int(d.get('strength',60)), cid, iid))
        conn.execute("DELETE FROM class_subjects WHERE class_id=?", (cid,))
        for sid2 in d.get('subjects', []):
            conn.execute("INSERT OR IGNORE INTO class_subjects VALUES (?,?)", (cid, sid2))
    return jsonify({'success': True})

@app.route('/api/classes/<int:cid>', methods=['DELETE'])
@admin_required
def api_delete_class(cid):
    iid = inst_id()
    with get_db() as conn:
        conn.execute("DELETE FROM class_section WHERE id=? AND institution_id=?", (cid, iid))
    return jsonify({'success': True})

# ══════════════════════════════════════════════════════════════
# TIMETABLE
# ══════════════════════════════════════════════════════════════

@app.route('/timetable')
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
    days = get_working_days(iid)
    periods = get_period_count(iid)
    period_slots = get_period_slots(iid)
    return render_template('timetable.html',
        classes=classes, staff_list=staff_all,
        active_timetable=dict(active_tt) if active_tt else None,
        days=days, periods=list(range(1, periods+1)),
        period_slots=period_slots, all_subjects=all_subjects)

@app.route('/api/timetable/validate')
@login_required
def api_validate():
    warnings = validate_before_generate(inst_id())
    return jsonify({'warnings': warnings, 'safe': len(warnings)==0})

@app.route('/api/timetable/generate', methods=['POST'])
@admin_required
def api_generate():
    iid = inst_id()
    d = request.get_json() or {}
    warnings = validate_before_generate(iid)
    if warnings and not d.get('force'):
        return jsonify({'success': False, 'warnings': warnings})
    tt_id, conflicts = generate_timetable(iid, d.get('name','Auto Generated'))
    return jsonify({'success': True, 'timetable_id': tt_id,
                    'conflicts': conflicts, 'conflict_count': len(conflicts)})

@app.route('/api/timetable/delete', methods=['DELETE'])
@admin_required
def api_delete_tt():
    delete_timetable(inst_id())
    return jsonify({'success': True})

@app.route('/api/timetable/class/<int:class_id>')
@login_required
def api_class_tt(class_id):
    iid = inst_id()
    tt_id, grid = get_class_timetable(class_id, iid)
    slots = get_period_slots(iid)
    period_labels = {s['slot_order']: s for s in slots}
    return jsonify({'timetable_id': tt_id, 'grid': grid,
                    'days': get_working_days(iid), 'periods': get_period_count(iid),
                    'period_labels': period_labels})

@app.route('/api/timetable/staff/<int:staff_id>')
@login_required
def api_staff_tt(staff_id):
    iid = inst_id()
    tt_id, grid = get_staff_timetable(staff_id, iid)
    slots = get_period_slots(iid)
    period_labels = {s['slot_order']: s for s in slots}
    return jsonify({'timetable_id': tt_id, 'grid': grid,
                    'days': get_working_days(iid), 'periods': get_period_count(iid),
                    'period_labels': period_labels})

@app.route('/api/timetable/slot/<int:slot_id>/edit', methods=['PUT'])
@admin_required
def api_edit_slot(slot_id):
    d = request.get_json()
    ok, msg = edit_slot(slot_id, d['staff_id'], inst_id())
    return jsonify({'success': ok, 'message': msg})

@app.route('/api/timetable/slot/<int:slot_id>/staff_options')
@login_required
def api_slot_staff_options(slot_id):
    """Return staff eligible for the subject in a given slot."""
    iid = inst_id()
    with get_db() as conn:
        slot = conn.execute(
            "SELECT * FROM timetable_slot WHERE id=? AND institution_id=?", (slot_id, iid)
        ).fetchone()
        if not slot: return jsonify([])
        eligible = conn.execute("""
            SELECT st.id, st.name, st.department, st.allocated_periods, st.max_periods_per_week
            FROM staff st JOIN staff_subjects ss ON ss.staff_id=st.id
            WHERE ss.subject_id=? AND st.institution_id=?
            ORDER BY st.name
        """, (slot['subject_id'], iid)).fetchall()
        # Check who is free at this (day, period)
        busy = {r['staff_id'] for r in conn.execute(
            "SELECT staff_id FROM timetable_slot WHERE timetable_id=? AND day=? AND period=? AND id!=?",
            (slot['timetable_id'], slot['day'], slot['period'], slot_id)
        ).fetchall()}
    result = []
    for s in eligible:
        result.append({**dict(s), 'available': s['id'] not in busy,
                       'is_current': s['id'] == slot['staff_id']})
    return jsonify(result)

@app.route('/api/timetable/export/csv/<int:class_id>')
@login_required
def export_csv(class_id):
    iid = inst_id()
    with get_db() as conn:
        cls = conn.execute("SELECT name FROM class_section WHERE id=? AND institution_id=?", (class_id, iid)).fetchone()
    tt_id, grid = get_class_timetable(class_id, iid)
    days = get_working_days(iid)
    periods = get_period_count(iid)
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(['Day'] + [f'Period {p}' for p in range(1, periods+1)])
    for day in days:
        row = [day]
        for p in range(1, periods+1):
            slot = grid.get(day,{}).get(p)
            row.append(f"{slot['subject_name']} ({slot['staff_name']})" if slot else 'FREE')
        w.writerow(row)
    out.seek(0)
    resp = make_response(out.getvalue())
    resp.headers['Content-Type'] = 'text/csv'
    resp.headers['Content-Disposition'] = f'attachment; filename=timetable_{cls["name"] if cls else class_id}.csv'
    return resp

@app.route('/api/timetable/export/pdf/<int:class_id>')
@login_required
def export_pdf(class_id):
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    iid = inst_id()
    with get_db() as conn:
        cls = conn.execute("SELECT name FROM class_section WHERE id=? AND institution_id=?", (class_id, iid)).fetchone()
        inst = conn.execute("SELECT name FROM institution WHERE id=?", (iid,)).fetchone()
    tt_id, grid = get_class_timetable(class_id, iid)
    days = get_working_days(iid)
    periods = get_period_count(iid)
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4), leftMargin=1.5*cm, rightMargin=1.5*cm)
    styles = getSampleStyleSheet()
    elems = [
        Paragraph(inst['name'] if inst else '', styles['Normal']),
        Paragraph(f"Timetable: {cls['name'] if cls else ''}", styles['Title']),
        Spacer(1, 0.4*cm)
    ]
    col_w = (25*cm - 3*cm) / (periods+1)
    data = [['Day'] + [f'P{p}' for p in range(1, periods+1)]]
    for day in days:
        row = [day]
        for p in range(1, periods+1):
            slot = grid.get(day,{}).get(p)
            row.append(f"{slot['subject_name']}\n{slot['staff_name']}" if slot else 'FREE')
        data.append(row)
    tbl = Table(data, colWidths=[3*cm]+[col_w]*periods)
    tbl.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#0f172a')),
        ('TEXTCOLOR',(0,0),(-1,0),colors.white),
        ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
        ('ALIGN',(0,0),(-1,-1),'CENTER'),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('GRID',(0,0),(-1,-1),0.5,colors.HexColor('#e2e8f0')),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f8fafc')]),
        ('FONTSIZE',(0,0),(-1,-1),8),
        ('TOPPADDING',(0,0),(-1,-1),6),
        ('BOTTOMPADDING',(0,0),(-1,-1),6),
    ]))
    elems.append(tbl)
    doc.build(elems)
    buf.seek(0)
    resp = make_response(buf.read())
    resp.headers['Content-Type'] = 'application/pdf'
    resp.headers['Content-Disposition'] = f'attachment; filename=timetable_{cls["name"] if cls else class_id}.pdf'
    return resp

# ══════════════════════════════════════════════════════════════
# ANALYTICS
# ══════════════════════════════════════════════════════════════

@app.route('/analytics')
@login_required
def analytics_page():
    iid = inst_id()
    results = compute_analytics(iid)
    with get_db() as conn:
        active_tt = conn.execute(
            "SELECT * FROM timetable WHERE institution_id=? AND is_active=1 ORDER BY id DESC LIMIT 1", (iid,)
        ).fetchone()
    return render_template('analytics.html', results=results,
                           active_timetable=dict(active_tt) if active_tt else None)

@app.route('/api/analytics')
@login_required
def api_analytics():
    return jsonify(compute_analytics(inst_id()))

# ══════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════

if __name__ == '__main__':
    init_db()
    seed_demo_institution()
    app.run(debug=True, port=5000, use_reloader=False)
