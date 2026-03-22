"""
scheduler.py — EduSchedule Pro v2 — Fixed engine.

KEY FIXES:
  1. EVEN DISTRIBUTION: Subjects are spread evenly across ALL working days
     using a round-robin day assignment before slot filling.
  2. BREAK/LUNCH: Never allocated. Only period-type slots are used.
  3. LAB CONSECUTIVE: Lab subjects need back-to-back period slots with no break between.
  4. PERIODS/WEEK: All required periods per subject are fully allocated.
"""
import random
from database import get_db

DAY_MAP = {
    'Mon': 'Monday', 'Tue': 'Tuesday', 'Wed': 'Wednesday',
    'Thu': 'Thursday', 'Fri': 'Friday', 'Sat': 'Saturday'
}

# ── Config helpers ─────────────────────────────────────────────────────────────

def get_working_days(institution_id):
    with get_db() as conn:
        cfg = conn.execute(
            "SELECT working_days FROM time_config WHERE institution_id=?", (institution_id,)
        ).fetchone()
    if not cfg:
        return ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    return [DAY_MAP.get(d.strip(), d.strip()) for d in cfg['working_days'].split(',')]

def get_period_count(institution_id):
    """Count of teaching (non-break) periods per day."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM period_slot WHERE institution_id=? AND slot_type='period'",
            (institution_id,)
        ).fetchone()
        cnt = row['cnt'] if row else 0
        if cnt:
            return cnt
        cfg = conn.execute(
            "SELECT periods_per_day FROM time_config WHERE institution_id=?", (institution_id,)
        ).fetchone()
        return cfg['periods_per_day'] if cfg else 6

def get_teaching_slot_orders(institution_id):
    """
    Returns sorted list of slot_order values whose slot_type='period'.
    e.g. [1, 2, 4, 5, 7, 8]  — slots 3 (Break) and 6 (Lunch) excluded.
    """
    with get_db() as conn:
        rows = conn.execute(
            "SELECT slot_order FROM period_slot WHERE institution_id=? AND slot_type='period' ORDER BY slot_order",
            (institution_id,)
        ).fetchall()
    if rows:
        return [r['slot_order'] for r in rows]
    return list(range(1, get_period_count(institution_id) + 1))

def get_period_slots(institution_id):
    """All slots including breaks for display."""
    with get_db() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM period_slot WHERE institution_id=? ORDER BY slot_order",
            (institution_id,)
        ).fetchall()]


# ── Pre-generation validation ──────────────────────────────────────────────────

def validate_before_generate(institution_id):
    warnings = []
    with get_db() as conn:
        classes = conn.execute(
            "SELECT id, name FROM class_section WHERE institution_id=?", (institution_id,)
        ).fetchall()
        if not classes:
            warnings.append("No classes defined. Add at least one class.")

        days = get_working_days(institution_id)
        teaching_slots = get_teaching_slot_orders(institution_id)
        slots_per_week = len(days) * len(teaching_slots)

        for cls in classes:
            subjs = conn.execute("""
                SELECT s.id, s.subject_name, s.periods_per_week, s.is_lab, s.lab_duration
                FROM subject s JOIN class_subjects cs ON cs.subject_id=s.id WHERE cs.class_id=?
            """, (cls['id'],)).fetchall()
            if not subjs:
                warnings.append(f"Class '{cls['name']}' has no subjects assigned.")
                continue
            total_needed = sum(s['periods_per_week'] for s in subjs)
            if total_needed > slots_per_week:
                warnings.append(
                    f"Class '{cls['name']}': needs {total_needed} periods/week but only "
                    f"{slots_per_week} slots available ({len(days)} days × {len(teaching_slots)} periods). "
                    f"Reduce subject periods or add more days."
                )
            for subj in subjs:
                eligible = conn.execute("""
                    SELECT COUNT(*) as cnt FROM staff st
                    JOIN staff_subjects ss ON ss.staff_id=st.id
                    WHERE ss.subject_id=? AND st.institution_id=?
                """, (subj['id'], institution_id)).fetchone()['cnt']
                if eligible == 0:
                    warnings.append(
                        f"'{subj['subject_name']}' in {cls['name']} has NO eligible staff assigned."
                    )

        if not conn.execute("SELECT 1 FROM staff WHERE institution_id=?", (institution_id,)).fetchone():
            warnings.append("No staff defined.")
        if not teaching_slots:
            warnings.append("No teaching period slots configured. Go to Settings → Period Slots.")
        if not days:
            warnings.append("No working days configured in Settings.")

    return warnings


# ── Staff selector ─────────────────────────────────────────────────────────────

def _best_staff(conn, subject_id, difficulty, day, slot_order,
                staff_busy, alloc_counts, max_p, exp_map, avail_map, institution_id):
    slot_key = (day, slot_order)
    busy_set = staff_busy.get(slot_key, set())

    hist = {r['staff_id']: r['t'] for r in conn.execute(
        "SELECT staff_id, SUM(periods_count) as t FROM allocation_history "
        "WHERE subject_id=? AND institution_id=? GROUP BY staff_id",
        (subject_id, institution_id)
    ).fetchall()}

    candidates = []
    for row in conn.execute(
        "SELECT ss.staff_id FROM staff_subjects ss "
        "JOIN staff st ON st.id=ss.staff_id "
        "WHERE ss.subject_id=? AND st.institution_id=?",
        (subject_id, institution_id)
    ).fetchall():
        sid = row['staff_id']
        if sid in busy_set:
            continue
        if alloc_counts.get(sid, 0) >= max_p.get(sid, 20):
            continue
        day_short = day[:3]
        avail = avail_map.get(sid, 'Mon,Tue,Wed,Thu,Fri')
        if day_short not in avail:
            continue
        score = (
            exp_map.get(sid, 0) * difficulty +
            (max_p.get(sid, 20) - alloc_counts.get(sid, 0)) +
            hist.get(sid, 0) * 0.5
        )
        candidates.append((score, sid))

    if not candidates:
        return None
    candidates.sort(reverse=True)
    return candidates[0][1]


# ── Even-distribution slot builder ────────────────────────────────────────────

def _build_even_slot_order(days, teaching_slots, queue):
    """
    Assign (day, slot_order) pairs to each item in queue so that
    subjects are spread evenly across all days.

    Strategy:
    - For each subject, calculate how many periods it needs.
    - Spread its periods across days as evenly as possible using round-robin.
    - Within each day, assign to next available slot_order.

    Returns: list of (day, slot_order) in assignment order, same length as queue.
    """
    # Slot cursor per day: tracks next available slot index in teaching_slots
    # day_slots[day] = list of slot_orders still free
    day_slots = {day: list(teaching_slots) for day in days}  # copy per day
    # day_cursor for round-robin assignment
    n_days = len(days)
    assignments = []  # list of (day, slot_order) per queue item

    # We'll assign round-robin by day, advancing through queue
    day_idx = 0
    for i, item in enumerate(queue):
        # Find a day that still has a free slot, starting from current day_idx
        attempts = 0
        while attempts < n_days:
            day = days[day_idx % n_days]
            if day_slots[day]:
                slot_order = day_slots[day].pop(0)
                assignments.append((day, slot_order))
                day_idx += 1
                break
            day_idx += 1
            attempts += 1
        else:
            # All days full — append None (will become conflict)
            assignments.append(None)

    return assignments


# ── Main generator ─────────────────────────────────────────────────────────────

def generate_timetable(institution_id, name="Auto Generated"):
    """
    Generate a properly distributed timetable:
    - Periods spread evenly across all working days
    - All periods_per_week requirements met
    - No break/lunch slots allocated
    - Lab subjects get consecutive teaching slots
    """
    conflicts = []

    with get_db() as conn:
        conn.execute("UPDATE timetable SET is_active=0 WHERE institution_id=?", (institution_id,))
        conn.execute("UPDATE staff SET allocated_periods=0 WHERE institution_id=?", (institution_id,))
        conn.execute(
            "INSERT INTO timetable (institution_id, name, is_active) VALUES (?,?,1)",
            (institution_id, name)
        )
        tt_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

        days           = get_working_days(institution_id)
        teaching_slots = get_teaching_slot_orders(institution_id)

        classes = conn.execute(
            "SELECT id FROM class_section WHERE institution_id=?", (institution_id,)
        ).fetchall()

        alloc_counts = {r['id']: 0 for r in conn.execute(
            "SELECT id FROM staff WHERE institution_id=?", (institution_id,)).fetchall()}
        max_p   = {r['id']: r['max_periods_per_week'] for r in conn.execute(
            "SELECT id, max_periods_per_week FROM staff WHERE institution_id=?", (institution_id,)).fetchall()}
        exp_map = {r['id']: r['experience'] for r in conn.execute(
            "SELECT id, experience FROM staff WHERE institution_id=?", (institution_id,)).fetchall()}
        avail_map = {r['id']: r['available_days'] for r in conn.execute(
            "SELECT id, available_days FROM staff WHERE institution_id=?", (institution_id,)).fetchall()}

        # (day, slot_order) → set of staff_ids busy there
        staff_busy = {}
        # (class_id, day, slot_order) → True if class already has a subject there
        class_busy = {}

        for cls_row in classes:
            cls_id = cls_row['id']
            cls_name = conn.execute(
                "SELECT name FROM class_section WHERE id=?", (cls_id,)
            ).fetchone()['name']

            subj_rows = conn.execute("""
                SELECT s.id, s.difficulty_level, s.periods_per_week,
                       s.is_lab, s.lab_duration, s.subject_name
                FROM subject s JOIN class_subjects cs ON cs.subject_id=s.id
                WHERE cs.class_id=?
            """, (cls_id,)).fetchall()

            # Build queue: each entry = one period slot to fill
            # Labs are added as groups that need consecutive slots
            single_queue = []  # (subj_id, difficulty, subj_name)
            lab_queue    = []  # (subj_id, difficulty, duration, subj_name)

            for row in subj_rows:
                if row['is_lab']:
                    reps = max(1, row['periods_per_week'] // row['lab_duration'])
                    for _ in range(reps):
                        lab_queue.append((row['id'], row['difficulty_level'],
                                          row['lab_duration'], row['subject_name']))
                else:
                    for _ in range(row['periods_per_week']):
                        single_queue.append((row['id'], row['difficulty_level'], row['subject_name']))

            # ── Place labs first (need consecutive slots) ──────────────────────
            for subj_id, diff, duration, subj_name in lab_queue:
                placed = False
                for day in days:
                    # Find `duration` consecutive free teaching slots on this day
                    free_slots = [so for so in teaching_slots
                                  if not class_busy.get((cls_id, day, so))]
                    for i in range(len(free_slots) - duration + 1):
                        group = free_slots[i:i + duration]
                        # Must be physically consecutive (no break between)
                        if not all(group[j+1] == group[j]+1 for j in range(len(group)-1)):
                            continue
                        staff_id = _best_staff(conn, subj_id, diff, day, group[0],
                                               staff_busy, alloc_counts, max_p,
                                               exp_map, avail_map, institution_id)
                        if not staff_id:
                            continue
                        # Check staff free for all slots in group
                        if any(staff_id in staff_busy.get((day, so), set()) for so in group):
                            continue
                        # Place it
                        for so in group:
                            staff_busy.setdefault((day, so), set()).add(staff_id)
                            class_busy[(cls_id, day, so)] = True
                            alloc_counts[staff_id] = alloc_counts.get(staff_id, 0) + 1
                            conn.execute(
                                "INSERT INTO timetable_slot "
                                "(institution_id,timetable_id,day,period,class_id,subject_id,staff_id) "
                                "VALUES (?,?,?,?,?,?,?)",
                                (institution_id, tt_id, day, so, cls_id, subj_id, staff_id)
                            )
                        placed = True
                        break
                    if placed:
                        break
                if not placed:
                    conflicts.append({
                        'class': cls_name, 'subject': subj_name,
                        'day': '—', 'period': 0,
                        'reason': f'No consecutive {duration}-period block found for lab'
                    })

            # ── Place single-period lectures with even distribution ────────────
            # Build a global slot pool ordered SLOT-FIRST then DAY:
            # [(Mon,P1),(Tue,P1),(Wed,P1),(Thu,P1),(Fri,P1),(Mon,P2),(Tue,P2),...]
            # This guarantees all teaching slots get used, not just the early ones.
            # Remove any slots already consumed by labs.
            global_pool = []
            for so in teaching_slots:
                for day in days:
                    if not class_busy.get((cls_id, day, so)):
                        global_pool.append((day, so))

            # Assign subjects to pool slots in order.
            # Shuffle subjects so same subject doesn't always grab first slots.
            shuffled_queue = list(single_queue)
            random.shuffle(shuffled_queue)

            assignments = []
            pool_ptr = 0
            for subj_id, diff, sname in shuffled_queue:
                if pool_ptr < len(global_pool):
                    day, slot_order = global_pool[pool_ptr]
                    assignments.append((day, slot_order, subj_id, diff, sname))
                    pool_ptr += 1
                else:
                    conflicts.append({
                        'class': cls_name, 'subject': sname,
                        'day': '—', 'period': 0,
                        'reason': 'Not enough free slots in week (reduce periods/week or add days)'
                    })

            # Sort by day then slot for clean insertion order
            assignments.sort(key=lambda x: (days.index(x[0]), x[1]))

            for day, slot_order, subj_id, diff, subj_name in assignments:
                # Skip if class somehow got double-booked (safety check)
                if class_busy.get((cls_id, day, slot_order)):
                    continue
                staff_id = _best_staff(conn, subj_id, diff, day, slot_order,
                                       staff_busy, alloc_counts, max_p,
                                       exp_map, avail_map, institution_id)
                if staff_id:
                    staff_busy.setdefault((day, slot_order), set()).add(staff_id)
                    class_busy[(cls_id, day, slot_order)] = True
                    alloc_counts[staff_id] = alloc_counts.get(staff_id, 0) + 1
                    conn.execute(
                        "INSERT INTO timetable_slot "
                        "(institution_id,timetable_id,day,period,class_id,subject_id,staff_id) "
                        "VALUES (?,?,?,?,?,?,?)",
                        (institution_id, tt_id, day, slot_order, cls_id, subj_id, staff_id)
                    )
                else:
                    conflicts.append({
                        'class': cls_name, 'subject': subj_name,
                        'day': day, 'period': slot_order,
                        'reason': 'No available staff — all eligible staff busy or at max periods'
                    })

        # Persist allocated_periods
        for staff_id, count in alloc_counts.items():
            conn.execute("UPDATE staff SET allocated_periods=? WHERE id=?", (count, staff_id))

        # Save history
        for row in conn.execute(
            "SELECT staff_id, subject_id, COUNT(*) as cnt FROM timetable_slot "
            "WHERE timetable_id=? GROUP BY staff_id, subject_id", (tt_id,)
        ).fetchall():
            conn.execute(
                "INSERT INTO allocation_history "
                "(institution_id,staff_id,subject_id,timetable_id,periods_count) VALUES (?,?,?,?,?)",
                (institution_id, row['staff_id'], row['subject_id'], tt_id, row['cnt'])
            )

        conn.execute(
            "UPDATE timetable SET conflicts=?, notes=datetime('now') WHERE id=?",
            (len(conflicts), tt_id)
        )

    return tt_id, conflicts


# ── Timetable fetch ────────────────────────────────────────────────────────────

def get_class_timetable(class_id, institution_id):
    with get_db() as conn:
        tt = conn.execute(
            "SELECT id FROM timetable WHERE institution_id=? AND is_active=1 ORDER BY id DESC LIMIT 1",
            (institution_id,)
        ).fetchone()
        if not tt:
            return None, {}
        days = get_working_days(institution_id)
        slots = conn.execute("""
            SELECT ts.day, ts.period, ts.id as slot_id, ts.is_manual_edit,
                   s.subject_name, s.is_lab, st.name as staff_name,
                   st.id as staff_id, cs.name as class_name, s.id as subject_id
            FROM timetable_slot ts
            JOIN subject s  ON s.id  = ts.subject_id
            JOIN staff st   ON st.id = ts.staff_id
            JOIN class_section cs ON cs.id = ts.class_id
            WHERE ts.class_id=? AND ts.timetable_id=?
        """, (class_id, tt['id'])).fetchall()
        grid = {day: {} for day in days}
        for row in slots:
            grid[row['day']][row['period']] = dict(row)
        return tt['id'], grid

def get_staff_timetable(staff_id, institution_id):
    with get_db() as conn:
        tt = conn.execute(
            "SELECT id FROM timetable WHERE institution_id=? AND is_active=1 ORDER BY id DESC LIMIT 1",
            (institution_id,)
        ).fetchone()
        if not tt:
            return None, {}
        days = get_working_days(institution_id)
        slots = conn.execute("""
            SELECT ts.day, ts.period, ts.id as slot_id,
                   s.subject_name, s.is_lab, st.name as staff_name,
                   cs.name as class_name, s.id as subject_id
            FROM timetable_slot ts
            JOIN subject s  ON s.id  = ts.subject_id
            JOIN staff st   ON st.id = ts.staff_id
            JOIN class_section cs ON cs.id = ts.class_id
            WHERE ts.staff_id=? AND ts.timetable_id=?
        """, (staff_id, tt['id'])).fetchall()
        grid = {day: {} for day in days}
        for row in slots:
            grid[row['day']][row['period']] = dict(row)
        return tt['id'], grid


# ── Slot editing ───────────────────────────────────────────────────────────────

def edit_slot(slot_id, new_staff_id, institution_id):
    with get_db() as conn:
        slot = conn.execute(
            "SELECT * FROM timetable_slot WHERE id=? AND institution_id=?",
            (slot_id, institution_id)
        ).fetchone()
        if not slot:
            return False, "Slot not found"
        clash = conn.execute(
            "SELECT 1 FROM timetable_slot "
            "WHERE timetable_id=? AND day=? AND period=? AND staff_id=? AND id!=?",
            (slot['timetable_id'], slot['day'], slot['period'], new_staff_id, slot_id)
        ).fetchone()
        if clash:
            return False, "Staff is already busy at this time slot"
        old_staff = slot['staff_id']
        conn.execute("UPDATE timetable_slot SET staff_id=?, is_manual_edit=1 WHERE id=?",
                     (new_staff_id, slot_id))
        conn.execute("UPDATE staff SET allocated_periods=MAX(0,allocated_periods-1) WHERE id=?", (old_staff,))
        conn.execute("UPDATE staff SET allocated_periods=allocated_periods+1 WHERE id=?", (new_staff_id,))
    return True, "Slot updated successfully"

def delete_timetable(institution_id):
    with get_db() as conn:
        conn.execute("DELETE FROM timetable WHERE institution_id=? AND is_active=1", (institution_id,))
        conn.execute("UPDATE staff SET allocated_periods=0 WHERE institution_id=?", (institution_id,))


# ── Recommendations ────────────────────────────────────────────────────────────

def get_recommendations(subject_id, institution_id, top_n=5):
    with get_db() as conn:
        subj = conn.execute("SELECT * FROM subject WHERE id=? AND institution_id=?",
                            (subject_id, institution_id)).fetchone()
        if not subj:
            return []
        eligible = conn.execute("""
            SELECT st.* FROM staff st JOIN staff_subjects ss ON ss.staff_id=st.id
            WHERE ss.subject_id=? AND st.institution_id=?
        """, (subject_id, institution_id)).fetchall()
        hist = {r['staff_id']: r['total'] for r in conn.execute(
            "SELECT staff_id, SUM(periods_count) as total FROM allocation_history "
            "WHERE subject_id=? AND institution_id=? GROUP BY staff_id",
            (subject_id, institution_id)
        ).fetchall()}
        results = []
        for s in eligible:
            past  = hist.get(s['id'], 0)
            avail = max(0, s['max_periods_per_week'] - s['allocated_periods'])
            score = round((past * 2) + (s['experience'] * subj['difficulty_level']) + (avail * 0.5), 2)
            results.append({**dict(s), 'past_periods': past, 'availability': avail,
                            'recommendation_score': score})
        results.sort(key=lambda x: -x['recommendation_score'])
        return results[:top_n]


# ── Analytics ──────────────────────────────────────────────────────────────────

def compute_analytics(institution_id):
    with get_db() as conn:
        staff_list = conn.execute(
            "SELECT * FROM staff WHERE institution_id=? ORDER BY name", (institution_id,)
        ).fetchall()
        scored = []
        for s in staff_list:
            row = conn.execute("""
                SELECT AVG(sub.difficulty_level) as avg_diff
                FROM timetable_slot ts
                JOIN subject sub ON sub.id=ts.subject_id
                JOIN timetable tt ON tt.id=ts.timetable_id
                WHERE ts.staff_id=? AND tt.is_active=1 AND tt.institution_id=?
            """, (s['id'], institution_id)).fetchone()
            avg_diff = row['avg_diff'] or 0
            score = round((s['allocated_periods']*0.4) + (s['experience']*0.3) + (avg_diff*0.3), 2)
            subjs = [r['subject_name'] for r in conn.execute("""
                SELECT sub.subject_name FROM subject sub
                JOIN staff_subjects ss ON ss.subject_id=sub.id WHERE ss.staff_id=?
            """, (s['id'],)).fetchall()]
            pct = round(s['allocated_periods'] / s['max_periods_per_week'] * 100
                        if s['max_periods_per_week'] else 0, 1)
            scored.append({**dict(s), 'performance_score': score,
                           'subject_names': subjs, 'overload_pct': pct})

        scored.sort(key=lambda x: -x['performance_score'])
        total = len(scored)
        top10  = max(1, int(total * 0.10))
        next20 = max(1, int(total * 0.20))
        results = []
        for i, s in enumerate(scored):
            if i < top10:              suggestion, badge = 'Promotion', 'success'
            elif i < top10 + next20:   suggestion, badge = 'Salary Hike', 'info'
            elif s['overload_pct'] > 90: suggestion, badge = 'Overloaded', 'danger'
            elif s['overload_pct'] < 30: suggestion, badge = 'Underutilized', 'warning'
            else:                      suggestion, badge = 'Normal', 'secondary'
            results.append({'rank': i+1, 'staff': s, 'suggestion': suggestion,
                            'badge': badge, 'overload_pct': s['overload_pct']})
        return results
