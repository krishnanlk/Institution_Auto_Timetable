"""
scheduler.py — SchedHub v3 — Production-grade constraint-based engine.

KEY FIXES over v2:
  1. GLOBAL staff_busy tracking — staff cannot be double-booked ACROSS classes.
  2. FIXED lab consecutive check — skips slots that have a break/lunch between them.
  3. DAILY PERIOD LIMIT — each staff has max_periods_per_day (default 4).
  4. WEEKLY PERIOD LIMIT — hard cap on periods_per_week per staff.
  5. SORTED-BY-CONSTRAINT queue — most constrained subjects placed first.
  6. CONFLICT DETAIL — every conflict has class, subject, day, period, reason,
     and suggested_action fields. Stored in conflict_log table.
  7. GENERATOR-BASED generation — generate_timetable_iter() yields live progress
     events for Server-Sent Events streaming.
  8. ConflictDetector class — instant validation for drag-and-drop editing.
  9. move_slot() / swap_slots() — atomic move/swap for the edit UI.
"""
from __future__ import annotations
import math
import random
from collections import defaultdict
from typing import Generator, Optional, Iterator
from database import get_db, generate_abbreviation

# ── Day name map ───────────────────────────────────────────────────────────────
DAY_MAP = {
    "Mon": "Monday", "Tue": "Tuesday", "Wed": "Wednesday",
    "Thu": "Thursday", "Fri": "Friday", "Sat": "Saturday"
}
DAY_SHORT = {v: k for k, v in DAY_MAP.items()}


# ══════════════════════════════════════════════════════════════════════════════
# Config helpers
# ══════════════════════════════════════════════════════════════════════════════

def get_working_days(institution_id: int, conn=None) -> list[str]:
    if conn is not None:
        cfg = conn.execute(
            "SELECT working_days FROM time_config WHERE institution_id=?",
            (institution_id,)
        ).fetchone()
    else:
        with get_db() as c:
            cfg = c.execute(
                "SELECT working_days FROM time_config WHERE institution_id=?",
                (institution_id,)
            ).fetchone()
    if not cfg:
        return ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    return [DAY_MAP.get(d.strip(), d.strip()) for d in cfg["working_days"].split(",")]


def get_period_count(institution_id: int, conn=None) -> int:
    """Count of teaching (non-break/lunch) slots per day."""
    def _fetch(c):
        row = c.execute(
            "SELECT COUNT(*) as cnt FROM period_slot WHERE institution_id=? AND slot_type='period'",
            (institution_id,)
        ).fetchone()
        cnt = row["cnt"] if row else 0
        if cnt:
            return cnt
        cfg = c.execute(
            "SELECT periods_per_day FROM time_config WHERE institution_id=?",
            (institution_id,)
        ).fetchone()
        return cfg["periods_per_day"] if cfg else 6

    if conn is not None:
        return _fetch(conn)
    with get_db() as c:
        return _fetch(c)


def get_teaching_slot_orders(institution_id: int, conn=None) -> list[int]:
    """Sorted slot_order values for period-type slots only (no breaks/lunch)."""
    if conn is not None:
        rows = conn.execute(
            "SELECT slot_order FROM period_slot WHERE institution_id=? AND slot_type='period' ORDER BY slot_order",
            (institution_id,)
        ).fetchall()
    else:
        with get_db() as c:
            rows = c.execute(
                "SELECT slot_order FROM period_slot WHERE institution_id=? AND slot_type='period' ORDER BY slot_order",
                (institution_id,)
            ).fetchall()
    if rows:
        return [r["slot_order"] for r in rows]
    return list(range(1, get_period_count(institution_id, conn=conn) + 1))


def get_period_slots(institution_id: int, conn=None) -> list[dict]:
    """All slots including breaks for display."""
    if conn is not None:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM period_slot WHERE institution_id=? ORDER BY slot_order",
            (institution_id,)
        ).fetchall()]
    with get_db() as c:
        return [dict(r) for r in c.execute(
            "SELECT * FROM period_slot WHERE institution_id=? ORDER BY slot_order",
            (institution_id,)
        ).fetchall()]


def _has_break_between(conn, institution_id: int, slot_orders: list[int]) -> bool:
    """
    Return True if any break or lunch slot exists BETWEEN the given slot_orders.
    E.g. slots [2, 3, 4] where slot 3 is a break → True.
    """
    if len(slot_orders) < 2:
        return False
    min_so = min(slot_orders)
    max_so = max(slot_orders)
    rows = conn.execute(
        "SELECT slot_order, slot_type FROM period_slot "
        "WHERE institution_id=? AND slot_order BETWEEN ? AND ? ORDER BY slot_order",
        (institution_id, min_so, max_so)
    ).fetchall()
    return any(r["slot_type"] in ("break", "lunch") for r in rows)


def get_max_consecutive_teaching_block(conn, institution_id: int, teaching_slots: list[int]) -> int:
    """Find the max uninterrupted consecutive teaching period block (without break/lunch)."""
    if not teaching_slots:
        return 1
    max_len = 1
    current_run = 1
    for i in range(1, len(teaching_slots)):
        prev_so = teaching_slots[i - 1]
        so = teaching_slots[i]
        if so == prev_so + 1 and not _has_break_between(conn, institution_id, [prev_so, so]):
            current_run += 1
        else:
            current_run = 1
        if current_run > max_len:
            max_len = current_run
    return max_len



# ══════════════════════════════════════════════════════════════════════════════
# Pre-generation validation
# ══════════════════════════════════════════════════════════════════════════════

def validate_before_generate(institution_id: int) -> list[str]:
    warnings = []
    with get_db() as conn:
        classes = conn.execute(
            "SELECT id, name FROM class_section WHERE institution_id=?", (institution_id,)
        ).fetchall()
        if not classes:
            warnings.append("No classes defined. Add at least one class.")
            return warnings

        days = get_working_days(institution_id)
        teaching_slots = get_teaching_slot_orders(institution_id)
        slots_per_week = len(days) * len(teaching_slots)

        for cls in classes:
            subjs = conn.execute("""
                SELECT s.id, s.subject_name, s.periods_per_week, s.is_lab, s.lab_duration,
                       s.lab_staff2_id, s.is_mentor_meeting
                FROM subject s JOIN class_subjects cs ON cs.subject_id=s.id WHERE cs.class_id=?
            """, (cls["id"],)).fetchall()

            if not subjs:
                warnings.append(f"Class '{cls['name']}' has no subjects assigned.")
                continue

            total_needed = sum(s["periods_per_week"] for s in subjs)
            if total_needed > slots_per_week:
                warnings.append(
                    f"Class '{cls['name']}': needs {total_needed} periods/week but only "
                    f"{slots_per_week} slots available ({len(days)} days × {len(teaching_slots)} periods)."
                )

            # Check mentor meeting has a mentor assigned
            mm_subjects = [s for s in subjs if s["is_mentor_meeting"]]
            if mm_subjects:
                mentor_rows = conn.execute(
                    "SELECT staff_id FROM class_mentor WHERE class_id=?", (cls["id"],)
                ).fetchall()
                if not mentor_rows:
                    warnings.append(
                        f"Class '{cls['name']}' has Mentor Meeting subjects but NO mentor assigned. "
                        "Assign mentors via Classes → Edit → Mentors."
                    )

            for subj in subjs:
                eligible_count = conn.execute("""
                    SELECT COUNT(*) as cnt FROM staff st
                    JOIN staff_subjects ss ON ss.staff_id=st.id
                    WHERE ss.subject_id=? AND st.institution_id=?
                """, (subj["id"], institution_id)).fetchone()["cnt"]
                if eligible_count == 0:
                    warnings.append(
                        f"'{subj['subject_name']}' in {cls['name']} has NO eligible staff assigned."
                    )

                # Warn if lab has no secondary staff
                if subj["is_lab"] and not subj["lab_staff2_id"]:
                    warnings.append(
                        f"Lab '{subj['subject_name']}' in {cls['name']} has no secondary (co-teacher) staff set. "
                        "The lab will be assigned to a single teacher. Consider setting a second lab staff."
                    )

        if not conn.execute("SELECT 1 FROM staff WHERE institution_id=?", (institution_id,)).fetchone():
            warnings.append("No staff defined.")
        if not teaching_slots:
            warnings.append("No teaching period slots configured. Go to Settings → Period Slots.")
        if not days:
            warnings.append("No working days configured in Settings.")

    return warnings


# ══════════════════════════════════════════════════════════════════════════════
# Staff selection (score-based)
# ══════════════════════════════════════════════════════════════════════════════

def _best_staff(
    conn,
    subject_id: int,
    difficulty: int,
    day: str,
    slot_order: int,
    staff_busy: dict,
    alloc_counts: dict,
    max_p: dict,
    max_pd: dict,
    staff_daily: dict,
    exp_map: dict,
    avail_map: dict,
    institution_id: int,
    exclude_staff_id: Optional[int] = None,
) -> Optional[int]:
    """
    Score-based staff selector. Returns best available staff_id or None.
    Constraints checked (in order):
      1. Not already in a slot at (day, slot_order)
      2. Has not exceeded weekly period limit
      3. Has not exceeded daily period limit (max_periods_per_day)
      4. Available on this day (available_days)
      5. Not equal to exclude_staff_id (e.g. secondary lab staff)
    """
    busy_set = staff_busy.get((day, slot_order), set())

    candidates = []
    for row in conn.execute(
        "SELECT ss.staff_id FROM staff_subjects ss JOIN staff st ON st.id=ss.staff_id "
        "WHERE ss.subject_id=? AND st.institution_id=?",
        (subject_id, institution_id)
    ).fetchall():
        sid = row["staff_id"]

        if exclude_staff_id and sid == exclude_staff_id:
            continue
        if sid in busy_set:
            continue
        if alloc_counts.get(sid, 0) >= max_p.get(sid, 20):
            continue
        if staff_daily.get((sid, day), 0) >= max_pd.get(sid, 4):
            continue

        day_short = day[:3]
        avail = avail_map.get(sid, "Mon,Tue,Wed,Thu,Fri")
        if day_short not in avail:
            continue

        # Score: experience × difficulty + remaining weekly capacity + remaining daily capacity
        weekly_remaining = max_p.get(sid, 20) - alloc_counts.get(sid, 0)
        daily_remaining = max_pd.get(sid, 4) - staff_daily.get((sid, day), 0)
        score = (
            exp_map.get(sid, 0) * difficulty * 0.5
            + weekly_remaining
            + daily_remaining * 2
        )
        candidates.append((score, sid))

    if not candidates:
        return None
    candidates.sort(reverse=True)
    return candidates[0][1]


def _mark_slot(
    conn, institution_id: int, tt_id: int,
    day: str, slot_order: int, cls_id: int, subj_id: int, staff_id: int,
    staff_busy: dict, class_busy: dict, alloc_counts: dict, staff_daily: dict,
    staff2_id: Optional[int] = None
):
    """Insert a slot record and update all in-memory tracking dicts.
    If staff2_id is provided (lab co-teacher) it is also stored and marked busy.
    """
    conn.execute(
        "INSERT INTO timetable_slot "
        "(institution_id,timetable_id,day,period,class_id,subject_id,staff_id,staff2_id) "
        "VALUES (?,?,?,?,?,?,?,?)",
        (institution_id, tt_id, day, slot_order, cls_id, subj_id, staff_id, staff2_id)
    )
    staff_busy.setdefault((day, slot_order), set()).add(staff_id)
    if staff2_id:
        staff_busy.setdefault((day, slot_order), set()).add(staff2_id)
    class_busy[(cls_id, day, slot_order)] = True
    alloc_counts[staff_id] = alloc_counts.get(staff_id, 0) + 1
    if staff2_id:
        alloc_counts[staff2_id] = alloc_counts.get(staff2_id, 0) + 1
    staff_daily[(staff_id, day)] = staff_daily.get((staff_id, day), 0) + 1
    if staff2_id:
        staff_daily[(staff2_id, day)] = staff_daily.get((staff2_id, day), 0) + 1


# ══════════════════════════════════════════════════════════════════════════════
# Generator-based timetable generation (yields SSE progress events)
# ══════════════════════════════════════════════════════════════════════════════

def generate_timetable_iter(institution_id: int, name: str = "Auto Generated") -> Iterator[dict]:
    """
    Generator that yields progress dicts during timetable generation.
    Each event: {"pct": int, "msg": str}
    Final event: {"pct": 100, "msg": "...", "tt_id": int, "conflicts": list, "conflict_count": int}
    Error event: {"pct": -1, "error": str}

    Usage in SSE endpoint:
        for event in generate_timetable_iter(iid, name):
            yield f"data: {json.dumps(event)}\\n\\n"
    """
    conflicts: list[dict] = []
    tt_id: Optional[int] = None

    yield {"pct": 0, "msg": "Initializing generation engine…"}

    try:
        with get_db() as conn:
            # Deactivate previous timetable
            conn.execute("UPDATE timetable SET is_active=0 WHERE institution_id=?", (institution_id,))
            conn.execute("UPDATE staff SET allocated_periods=0 WHERE institution_id=?", (institution_id,))
            conn.execute("DELETE FROM conflict_log WHERE institution_id=?", (institution_id,))

            # Create the new timetable record
            tt_id = conn.insert(
                "INSERT INTO timetable (institution_id, name, is_active) VALUES (?,?,1)",
                (institution_id, name)
            )

            yield {"pct": 5, "msg": "Loading institution configuration…"}

            days = get_working_days(institution_id)
            teaching_slots = get_teaching_slot_orders(institution_id)

            if not days or not teaching_slots:
                yield {"pct": -1, "error": "No working days or period slots configured."}
                return

            # ── Load all classes ────────────────────────────────────────────
            classes = conn.execute(
                "SELECT id, name FROM class_section WHERE institution_id=?",
                (institution_id,)
            ).fetchall()

            # ── GLOBAL constraint tables (the critical fix) ─────────────────
            # These are NOT reset per-class. They track the entire timetable.
            staff_busy: dict   = {}              # (day, slot) → set(staff_ids)
            class_busy: dict   = {}              # (cls_id, day, slot) → True
            alloc_counts: dict = {}              # staff_id → total allocated this timetable
            staff_daily: dict  = {}              # (staff_id, day) → count this day

            # Staff metadata
            max_p: dict   = {}
            max_pd: dict  = {}
            exp_map: dict = {}
            avail_map: dict = {}

            for r in conn.execute("SELECT * FROM staff WHERE institution_id=?", (institution_id,)).fetchall():
                sid = r["id"]
                alloc_counts[sid] = 0
                max_p[sid]   = r["max_periods_per_week"]
                max_pd[sid]  = r["max_periods_per_day"] if r["max_periods_per_day"] else 4
                exp_map[sid] = r["experience"]
                avail_map[sid] = r["available_days"]

            yield {"pct": 10, "msg": f"Loaded {len(classes)} classes. Scanning subjects…"}

            # ── Pre-scan: separate labs from lectures ───────────────────────
            max_consec = get_max_consecutive_teaching_block(conn, institution_id, teaching_slots)
            all_labs     = []   # (cls_id, cls_name, subj_dict, repeat_count, duration)
            all_lectures = []   # (cls_id, cls_name, subj_dict)

            for cls in classes:
                subjs = conn.execute("""
                    SELECT s.* FROM subject s
                    JOIN class_subjects cs ON cs.subject_id=s.id
                    WHERE cs.class_id=?
                    ORDER BY s.periods_per_week DESC
                """, (cls["id"],)).fetchall()
                for s in subjs:
                    if s["is_lab"]:
                        raw_dur = s["lab_duration"] or 2
                        eff_dur = max(1, min(raw_dur, max_consec))
                        reps = max(1, s["periods_per_week"] // eff_dur)
                        all_labs.append((cls["id"], cls["name"], dict(s), reps, eff_dur))
                    else:
                        for _ in range(s["periods_per_week"]):
                            all_lectures.append((cls["id"], cls["name"], dict(s)))

            # ── Department categories lookup for Academic Pipeline ───────────
            dept_rows = conn.execute("SELECT name, code, category FROM department WHERE institution_id=?", (institution_id,)).fetchall()
            dept_cat_map = {}
            for dr in dept_rows:
                dept_cat_map[dr["name"].lower()] = dr["category"]
                dept_cat_map[dr["code"].lower()] = dr["category"]

            def _is_bs(s):
                if s.get("is_basic_science"):
                    return True
                d = (s.get("department") or "").strip().lower()
                if dept_cat_map.get(d) == "basic_science":
                    return True
                return d in ("s&h", "basic science", "basic sciences", "math", "mathematics", "physics", "chemistry", "english", "pe", "sports", "lang")

            def _is_mm(s):
                return bool(s.get("is_mentor_meeting")) or "mentor" in s.get("subject_name", "").lower() or s.get("subject_code", "").upper().startswith("MM")

            def _is_lib(s):
                return bool(s.get("is_library")) or "library" in s.get("subject_name", "").lower() or s.get("subject_code", "").upper().startswith("LIB")

            # Step 1 & 2: Basic Science Labs placed before Core Department Labs
            all_labs.sort(key=lambda item: (0 if _is_bs(item[2]) else 1, -item[2]["periods_per_week"]))

            # Step 1, 3, 4, 5: BS Theory -> Core Theory -> Mentor Meetings -> Library Hours
            def _lec_stage(item):
                s = item[2]
                if _is_bs(s):
                    return (0, -s["periods_per_week"], -s["difficulty_level"])
                elif _is_mm(s):
                    return (3, 0, 0)
                elif _is_lib(s):
                    return (4, 0, 0)
                else:
                    return (1, -s["periods_per_week"], -s["difficulty_level"])

            all_lectures.sort(key=_lec_stage)

            total_labs = sum(r for _, _, _, r, _ in all_labs)
            total_lecs = len(all_lectures)

            yield {
                "pct": 12,
                "msg": f"Pipeline Initialized: Step 1 (Basic Science) & Step 2 (Core Labs) ({total_labs} lab sessions)…"
            }

            # ── Load per-class mentor assignments ──────────────────────────
            # {cls_id: [staff_id, ...]}  (1 or 2 mentors)
            class_mentors: dict[int, list[int]] = {}
            for row in conn.execute(
                "SELECT class_id, staff_id FROM class_mentor WHERE class_id IN "
                f"(SELECT id FROM class_section WHERE institution_id={institution_id}) "
                "ORDER BY class_id, mentor_order"
            ).fetchall():
                class_mentors.setdefault(row["class_id"], []).append(row["staff_id"])

            # Fresh run-level RNG for true random slot selection each generation
            import time as _time_mod
            run_rng = random.Random(int(_time_mod.time() * 1000))

            # ══════════════════════════════════════════════════════════════
            # STEP 1 & 2: Place Basic Science & Core Department Laboratories
            # ══════════════════════════════════════════════════════════════
            labs_placed = 0

            for cls_idx, (cls_id, cls_name, subj, reps, duration) in enumerate(all_labs):
                subj_id   = subj["id"]
                staff2_id = subj.get("lab_staff2_id")   # may be None

                for rep_idx in range(reps):
                    placed = False

                    # Shuffle days freshly so labs don't cluster on the same day
                    candidate_days = list(days)
                    run_rng.shuffle(candidate_days)
                    # Secondary sort: prefer days with fewest class slots used
                    candidate_days.sort(
                        key=lambda d: sum(1 for so in teaching_slots if class_busy.get((cls_id, d, so)))
                    )

                    for day in candidate_days:
                        # Free teaching slots for this class on this day
                        free_slots = [
                            so for so in teaching_slots
                            if not class_busy.get((cls_id, day, so))
                        ]

                        # Shuffle the free slots so labs land in a random position
                        run_rng.shuffle(free_slots)

                        # Find `duration` consecutive free teaching slots
                        for i in range(len(free_slots) - duration + 1):
                            group = free_slots[i:i + duration]

                            # Must be numerically consecutive (no break between)
                            group_sorted = sorted(group)
                            if group_sorted != list(range(group_sorted[0], group_sorted[0] + duration)):
                                continue
                            if _has_break_between(conn, institution_id, group_sorted):
                                continue

                            # ── Find primary staff free for ALL slots in the group ──
                            # Check first slot to get candidate, then verify the rest
                            staff_id = _best_staff(
                                conn, subj_id, subj["difficulty_level"], day, group_sorted[0],
                                staff_busy, alloc_counts, max_p, max_pd, staff_daily,
                                exp_map, avail_map, institution_id,
                                exclude_staff_id=staff2_id
                            )
                            if not staff_id:
                                continue

                            # Primary must be free across ALL group slots
                            if any(staff_id in staff_busy.get((day, so), set()) for so in group_sorted):
                                continue

                            # Primary daily limit check across all lab periods
                            if staff_daily.get((staff_id, day), 0) + duration > max_pd.get(staff_id, 4):
                                continue

                            # ── Secondary staff (co-teacher) availability check ──
                            if staff2_id:
                                # Staff2 must also be free for all slots
                                if any(staff2_id in staff_busy.get((day, so), set()) for so in group_sorted):
                                    continue
                                # Staff2 daily limit
                                if staff_daily.get((staff2_id, day), 0) + duration > max_pd.get(staff2_id, 4):
                                    continue
                                # Staff2 weekly limit
                                if alloc_counts.get(staff2_id, 0) + duration > max_p.get(staff2_id, 20):
                                    continue
                                # Staff2 available on this day
                                if day[:3] not in avail_map.get(staff2_id, "Mon,Tue,Wed,Thu,Fri"):
                                    continue

                            # ── Place the lab ──────────────────────────────────
                            for so in group_sorted:
                                _mark_slot(
                                    conn, institution_id, tt_id,
                                    day, so, cls_id, subj_id, staff_id,
                                    staff_busy, class_busy, alloc_counts, staff_daily,
                                    staff2_id=staff2_id
                                )
                            placed = True
                            break
                        if placed:
                            break

                    if not placed:
                        reason = f"No consecutive {duration}-period block found where both lab staff are free (all days checked)"
                        action = "Reduce lab_duration, add more working days/period slots, or check secondary staff availability"
                        conflicts.append({
                            "class": cls_name, "subject": subj["subject_name"],
                            "day": "—", "period": 0,
                            "reason": reason, "suggested_action": action
                        })
                        conn.execute(
                            "INSERT INTO conflict_log (institution_id,timetable_id,class_name,"
                            "subject_name,day,period,reason,suggested_action) VALUES (?,?,?,?,?,?,?,?)",
                            (institution_id, tt_id, cls_name, subj["subject_name"], "—", 0, reason, action)
                        )

                    labs_placed += 1
                    pct = 12 + int((labs_placed / max(total_labs, 1)) * 28)
                    yield {"pct": pct, "msg": f"Lab placement: {labs_placed}/{total_labs}"}

            yield {"pct": 40, "msg": f"Labs complete. Distributing {total_lecs} lecture periods with variety…"}

            # ══════════════════════════════════════════════════════════════
            # PHASE 2: GLOBAL INTERLEAVED ALLOCATION (MRV Engine)
            # Prioritizes shared faculty (Basic Sciences & Humanities, e.g. Maths, Physics, English)
            # and constrained subjects across all departments simultaneously.
            # Includes intelligent Kempe-chain local swaps to eliminate deadlocks.
            # ══════════════════════════════════════════════════════════════
            yield {"pct": 42, "msg": f"Labs placed. Analyzing multi-department constraints across {len(classes)} classes…"}

            # Map each subject to its eligible staff
            subj_eligible_staff: dict[int, list[int]] = {}
            for r in conn.execute(
                "SELECT ss.subject_id, ss.staff_id FROM staff_subjects ss "
                "JOIN staff st ON st.id=ss.staff_id WHERE st.institution_id=?",
                (institution_id,)
            ).fetchall():
                subj_eligible_staff.setdefault(r["subject_id"], []).append(r["staff_id"])

            # Count in how many classes each staff member is needed (cross-department shared demand)
            staff_class_demand: dict[int, set[int]] = {}
            for cls in classes:
                subjs_in_cls = conn.execute(
                    "SELECT s.id FROM subject s JOIN class_subjects cs ON cs.subject_id=s.id WHERE cs.class_id=?",
                    (cls["id"],)
                ).fetchall()
                for s_row in subjs_in_cls:
                    for st_id in subj_eligible_staff.get(s_row["id"], []):
                        staff_class_demand.setdefault(st_id, set()).add(cls["id"])

            # Build all lecture units across ALL classes
            lecture_units = []
            for cls in classes:
                cls_id = cls["id"]
                cls_name = cls["name"]
                subjs = conn.execute("""
                    SELECT s.* FROM subject s
                    JOIN class_subjects cs ON cs.subject_id=s.id
                    WHERE cs.class_id=? AND s.is_lab=0
                    ORDER BY s.periods_per_week DESC, s.difficulty_level DESC
                """, (cls_id,)).fetchall()

                for s in subjs:
                    s_dict = dict(s)
                    sid = s_dict["id"]
                    el_staff = subj_eligible_staff.get(sid, [])
                    max_shared = max([len(staff_class_demand.get(st, set())) for st in el_staff], default=1)
                    staff_scarcity = 1.0 / max(len(el_staff), 1)

                    # Constraint weight:
                    # - Shared faculty across multiple classes (like Maths/Physics) placed first
                    # - Single-faculty subjects placed earlier
                    # - High-frequency courses (4-5 periods/wk) placed earlier
                    is_this_mm = bool(s_dict.get("is_mentor_meeting")) or "mentor" in (s_dict.get("subject_name") or "").lower() or (s_dict.get("subject_code") or "").upper().startswith("MM")
                    if is_this_mm:
                        weight = 10000  # Highest priority to secure slots where both assigned mentors are free
                    else:
                        weight = (
                            max_shared * 200
                            + staff_scarcity * 100
                            + s_dict["periods_per_week"] * 15
                            + s_dict["difficulty_level"] * 4
                        )

                    for rep in range(s_dict["periods_per_week"]):
                        lecture_units.append({
                            "cls_id": cls_id,
                            "cls_name": cls_name,
                            "subj": s_dict,
                            "rep_idx": rep,
                            "weight": weight,
                            "max_shared": max_shared,
                        })

            # Sort globally by constraint tightness (MRV heuristic)
            lecture_units.sort(
                key=lambda u: (
                    -u["weight"],
                    u["cls_id"],
                    u["subj"]["id"],
                    u["rep_idx"]
                )
            )

            total_units = len(lecture_units)
            lec_placed = 0

            # Tracking dicts
            class_day_subj: dict = {}   # (cls_id, day) -> list of subj_ids
            class_slot_subj: dict = {}  # (cls_id, day, slot_order) -> subj_id
            class_slot_staff: dict = {} # (cls_id, day, slot_order) -> staff_id
            class_slot_id: dict = {}    # (cls_id, day, slot_order) -> slot_row_id
            unplaced_units: list[dict] = []

            for unit in lecture_units:
                cls_id = unit["cls_id"]
                cls_name = unit["cls_name"]
                subj = unit["subj"]
                sid = subj["id"]
                rep_idx = unit["rep_idx"]
                placed = False
                is_mm = bool(subj.get("is_mentor_meeting")) or "mentor" in (subj.get("subject_name") or "").lower() or (subj.get("subject_code") or "").upper().startswith("MM")

                max_allowed_on_day = max(1, math.ceil(subj["periods_per_week"] / len(days)))

                # ── Helper: resolve the staff to place for this unit ──────────────
                def _resolve_staff(day: str, so: int) -> Optional[int]:
                    """Return a valid staff_id or None.
                    For MM subjects: only the assigned class mentor(s) may teach it,
                    and ALL assigned mentors must be free at that slot.
                    For regular subjects: use the score-based _best_staff selector.
                    Returns a tuple (primary_staff_id, secondary_staff_id_or_None).
                    For MM with two mentors both are returned so the slot stores staff2_id.
                    """
                    if is_mm:
                        mentor_list = class_mentors.get(cls_id, [])
                        if not mentor_list:
                            # No mentor assigned — fall back to regular selection
                            s = _best_staff(
                                conn, sid, subj["difficulty_level"], day, so,
                                staff_busy, alloc_counts, max_p, max_pd, staff_daily,
                                exp_map, avail_map, institution_id
                            )
                            return (s, None)
                        # All assigned mentors must be free at this slot
                        for m_id in mentor_list:
                            if m_id in staff_busy.get((day, so), set()):
                                return (None, None)
                            if staff_daily.get((m_id, day), 0) >= max_pd.get(m_id, 4):
                                return (None, None)
                            if alloc_counts.get(m_id, 0) >= max_p.get(m_id, 20):
                                return (None, None)
                            if day[:3] not in avail_map.get(m_id, "Mon,Tue,Wed,Thu,Fri"):
                                return (None, None)
                        # Return primary mentor + optional secondary mentor
                        m2 = mentor_list[1] if len(mentor_list) > 1 else None
                        return (mentor_list[0], m2)
                    s = _best_staff(
                        conn, sid, subj["difficulty_level"], day, so,
                        staff_busy, alloc_counts, max_p, max_pd, staff_daily,
                        exp_map, avail_map, institution_id
                    )
                    return (s, None)

                # ── PASS 1: Strict daily subject cap + random slot order ─────
                candidate_days = list(days)
                run_rng.shuffle(candidate_days)
                candidate_days.sort(key=lambda d: (
                    class_day_subj.get((cls_id, d), []).count(sid),
                    len([so for so in teaching_slots if class_busy.get((cls_id, d, so))])
                ))

                for day in candidate_days:
                    if class_day_subj.get((cls_id, day), []).count(sid) >= max_allowed_on_day:
                        continue

                    free_slots = [so for so in teaching_slots if not class_busy.get((cls_id, day, so))]
                    if not free_slots:
                        continue
                    run_rng.shuffle(free_slots)
                    free_slots.sort(key=lambda so: (
                        sum(1 for d in days if class_slot_subj.get((cls_id, d, so)) == sid)
                    ))

                    for so in free_slots:
                        staff_id, staff2_id = _resolve_staff(day, so)
                        if staff_id:
                            _mark_slot(
                                conn, institution_id, tt_id,
                                day, so, cls_id, sid, staff_id,
                                staff_busy, class_busy, alloc_counts, staff_daily,
                                staff2_id=staff2_id
                            )
                            last_id = conn.execute("SELECT MAX(id) as mid FROM timetable_slot").fetchone()["mid"]
                            class_day_subj.setdefault((cls_id, day), []).append(sid)
                            class_slot_subj[(cls_id, day, so)] = sid
                            class_slot_staff[(cls_id, day, so)] = staff_id
                            class_slot_id[(cls_id, day, so)] = last_id
                            placed = True
                            break

                    if placed:
                        break

                # ── PASS 2: Relaxed daily subject cap (for high load courses) ──
                if not placed:
                    for day in candidate_days:
                        free_slots = [so for so in teaching_slots if not class_busy.get((cls_id, day, so))]
                        run_rng.shuffle(free_slots)
                        for so in free_slots:
                            staff_id, staff2_id = _resolve_staff(day, so)
                            if staff_id:
                                _mark_slot(
                                    conn, institution_id, tt_id,
                                    day, so, cls_id, sid, staff_id,
                                    staff_busy, class_busy, alloc_counts, staff_daily,
                                    staff2_id=staff2_id
                                )
                                last_id = conn.execute("SELECT MAX(id) as mid FROM timetable_slot").fetchone()["mid"]
                                class_day_subj.setdefault((cls_id, day), []).append(sid)
                                class_slot_subj[(cls_id, day, so)] = sid
                                class_slot_staff[(cls_id, day, so)] = staff_id
                                class_slot_id[(cls_id, day, so)] = last_id
                                placed = True
                                break
                        if placed:
                            break

                # Collect unplaced units for the dynamic shifting / backtracking repair phase
                if not placed:
                    unplaced_units.append(unit)

                lec_placed += 1
                if lec_placed % 4 == 0 or lec_placed == total_units:
                    pct = 42 + int((lec_placed / max(total_units, 1)) * 40)
                    yield {"pct": pct, "msg": f"Scheduling multi-department lectures: {lec_placed}/{total_units}"}

            # ══════════════════════════════════════════════════════════════
            # PHASE 3: DYNAMIC BACKTRACKING & PRE-FITTED CLASS SHIFTING ENGINE
            # If any bottlenecks / clashes occurred, dynamically shift pre-fitted
            # slots (inter-class ejections, intra-class vacating, 2-way swaps)
            # so that every single period is placed with ZERO conflicts.
            # ══════════════════════════════════════════════════════════════
            if unplaced_units:
                yield {
                    "pct": 84,
                    "msg": f"Resolving clashes: dynamically shifting {len(unplaced_units)} pre-fitted classes for 0-conflict placement…"
                }

                def _relocate_slot_entry(slot_row_id: int, c_id: int, from_day: str, from_so: int, to_day: str, to_so: int):
                    """Atomically relocate a placed slot from (from_day, from_so) to (to_day, to_so)."""
                    slot_info = conn.execute(
                        "SELECT subject_id, staff_id, staff2_id FROM timetable_slot WHERE id=?",
                        (slot_row_id,)
                    ).fetchone()
                    if not slot_info:
                        return
                    s_id, st_id, st2_id = slot_info["subject_id"], slot_info["staff_id"], slot_info["staff2_id"]

                    conn.execute("UPDATE timetable_slot SET day=?, period=? WHERE id=?", (to_day, to_so, slot_row_id))

                    # Free old slot
                    class_busy.pop((c_id, from_day, from_so), None)
                    if st_id:
                        staff_busy.get((from_day, from_so), set()).discard(st_id)
                        staff_daily[(st_id, from_day)] = max(0, staff_daily.get((st_id, from_day), 1) - 1)
                    if st2_id:
                        staff_busy.get((from_day, from_so), set()).discard(st2_id)
                        staff_daily[(st2_id, from_day)] = max(0, staff_daily.get((st2_id, from_day), 1) - 1)
                    if (c_id, from_day) in class_day_subj and s_id in class_day_subj[(c_id, from_day)]:
                        class_day_subj[(c_id, from_day)].remove(s_id)
                    class_slot_subj.pop((c_id, from_day, from_so), None)
                    class_slot_staff.pop((c_id, from_day, from_so), None)
                    class_slot_id.pop((c_id, from_day, from_so), None)

                    # Occupy new slot
                    class_busy[(c_id, to_day, to_so)] = True
                    if st_id:
                        staff_busy.setdefault((to_day, to_so), set()).add(st_id)
                        staff_daily[(st_id, to_day)] = staff_daily.get((st_id, to_day), 0) + 1
                    if st2_id:
                        staff_busy.setdefault((to_day, to_so), set()).add(st2_id)
                        staff_daily[(st2_id, to_day)] = staff_daily.get((st2_id, to_day), 0) + 1
                    class_day_subj.setdefault((c_id, to_day), []).append(s_id)
                    class_slot_subj[(c_id, to_day, to_so)] = s_id
                    class_slot_staff[(c_id, to_day, to_so)] = st_id
                    class_slot_id[(c_id, to_day, to_so)] = slot_row_id

                # Iterative repair loops
                for repair_round in range(12):
                    if not unplaced_units:
                        break
                    still_unplaced = []

                    for unit in unplaced_units:
                        c_id = unit["cls_id"]
                        c_name = unit["cls_name"]
                        subj = unit["subj"]
                        sid = subj["id"]
                        unit_is_mm = bool(subj.get("is_mentor_meeting")) or "mentor" in (subj.get("subject_name") or "").lower() or (subj.get("subject_code") or "").upper().startswith("MM")
                        el_staff_list = subj_eligible_staff.get(sid, [])
                        resolved = False

                        # ── Strategy 1: Inter-Class Ejection (shift another class's slot to free shared staff) ──
                        for day in days:
                            if resolved:
                                break
                            free_in_this_class = [so for so in teaching_slots if not class_busy.get((c_id, day, so))]
                            for so in free_in_this_class:
                                if resolved:
                                    break
                                # Find candidate staff who could teach our subject here
                                for st_cand in el_staff_list:
                                    if st_cand in staff_busy.get((day, so), set()):
                                        # Faculty is busy here teaching another class. Can we shift that other class?
                                        other_slot = conn.execute(
                                            "SELECT ts.id, ts.class_id, ts.subject_id, ts.staff_id, ts.staff2_id, s.is_lab "
                                            "FROM timetable_slot ts JOIN subject s ON s.id=ts.subject_id "
                                            "WHERE ts.timetable_id=? AND ts.day=? AND ts.period=? "
                                            "AND (ts.staff_id=? OR ts.staff2_id=?)",
                                            (tt_id, day, so, st_cand, st_cand)
                                        ).fetchone()
                                        if other_slot and other_slot["class_id"] != c_id and not other_slot["is_lab"]:
                                            other_cid = other_slot["class_id"]
                                            other_sid = other_slot["id"]
                                            other_st1 = other_slot["staff_id"]
                                            other_st2 = other_slot["staff2_id"]

                                            # Find an alternative free slot for other_cid where other_st1 & other_st2 are free
                                            for alt_d in days:
                                                if resolved:
                                                    break
                                                alt_slots = [s for s in teaching_slots if not class_busy.get((other_cid, alt_d, s))]
                                                for alt_so in alt_slots:
                                                    if other_st1 not in staff_busy.get((alt_d, alt_so), set()):
                                                        if other_st2 and other_st2 in staff_busy.get((alt_d, alt_so), set()):
                                                            continue
                                                        if alt_d != day and staff_daily.get((other_st1, alt_d), 0) >= max_pd.get(other_st1, 4):
                                                            continue
                                                        if alt_d[:3] not in avail_map.get(other_st1, "Mon,Tue,Wed,Thu,Fri"):
                                                            continue

                                                        # Shift other class's slot to (alt_d, alt_so)!
                                                        _relocate_slot_entry(other_sid, other_cid, day, so, alt_d, alt_so)

                                                        # Now st_cand is free at (day, so)! Place our subject
                                                        _mark_slot(
                                                            conn, institution_id, tt_id,
                                                            day, so, c_id, sid, st_cand,
                                                            staff_busy, class_busy, alloc_counts, staff_daily
                                                        )
                                                        new_id = conn.execute("SELECT MAX(id) as mid FROM timetable_slot").fetchone()["mid"]
                                                        class_day_subj.setdefault((c_id, day), []).append(sid)
                                                        class_slot_subj[(c_id, day, so)] = sid
                                                        class_slot_staff[(c_id, day, so)] = st_cand
                                                        class_slot_id[(c_id, day, so)] = new_id
                                                        resolved = True
                                                        break

                        # ── Strategy 2: Intra-Class Vacate (shift another subject in this class to open a slot) ──
                        if not resolved:
                            for day in days:
                                if resolved:
                                    break
                                for so in teaching_slots:
                                    if resolved:
                                        break
                                    # Who can teach our subject at (day, so)?
                                    free_staff_for_us = [
                                        st for st in el_staff_list
                                        if st not in staff_busy.get((day, so), set())
                                        and staff_daily.get((st, day), 0) < max_pd.get(st, 4)
                                        and alloc_counts.get(st, 0) < max_p.get(st, 20)
                                        and day[:3] in avail_map.get(st, "Mon,Tue,Wed,Thu,Fri")
                                    ]
                                    if not free_staff_for_us:
                                        continue
                                    chosen_st = free_staff_for_us[0]

                                    # If this slot in our class is occupied by another non-lab subject:
                                    cur_slot_id = class_slot_id.get((c_id, day, so))
                                    cur_subj_id = class_slot_subj.get((c_id, day, so))
                                    cur_staff_id = class_slot_staff.get((c_id, day, so))

                                    if cur_slot_id and cur_subj_id and cur_staff_id:
                                        # Check if it's a lab
                                        is_cur_lab = conn.execute(
                                            "SELECT is_lab FROM subject WHERE id=?", (cur_subj_id,)
                                        ).fetchone()
                                        if is_cur_lab and is_cur_lab["is_lab"]:
                                            continue

                                        # Find an alt slot in our class for cur_subj
                                        for alt_d in days:
                                            if resolved:
                                                break
                                            alt_free = [s for s in teaching_slots if not class_busy.get((c_id, alt_d, s))]
                                            for alt_so in alt_free:
                                                if cur_staff_id not in staff_busy.get((alt_d, alt_so), set()):
                                                    if alt_d != day and staff_daily.get((cur_staff_id, alt_d), 0) >= max_pd.get(cur_staff_id, 4):
                                                        continue
                                                    if alt_d[:3] not in avail_map.get(cur_staff_id, "Mon,Tue,Wed,Thu,Fri"):
                                                        continue

                                                    # Relocate cur_subj to (alt_d, alt_so)
                                                    _relocate_slot_entry(cur_slot_id, c_id, day, so, alt_d, alt_so)

                                                    # Place our unit in the vacated (day, so)!
                                                    _mark_slot(
                                                        conn, institution_id, tt_id,
                                                        day, so, c_id, sid, chosen_st,
                                                        staff_busy, class_busy, alloc_counts, staff_daily
                                                    )
                                                    new_id = conn.execute("SELECT MAX(id) as mid FROM timetable_slot").fetchone()["mid"]
                                                    class_day_subj.setdefault((c_id, day), []).append(sid)
                                                    class_slot_subj[(c_id, day, so)] = sid
                                                    class_slot_staff[(c_id, day, so)] = chosen_st
                                                    class_slot_id[(c_id, day, so)] = new_id
                                                    resolved = True
                                                    break

                        if not resolved:
                            still_unplaced.append(unit)

                    unplaced_units = still_unplaced

                # Any units that mathematically cannot fit in the weekly hours log a conflict
                for unit in unplaced_units:
                    cls_name = unit["cls_name"]
                    subj = unit["subj"]
                    reason = ("Could not place period even after multi-class slot shifting — "
                              "faculty workload limits or class slot capacity fully exhausted")
                    action = (f"Add more faculty for '{subj['subject_name']}' in {cls_name} "
                              "or increase weekly capacity")
                    conflicts.append({
                        "class": cls_name, "subject": subj["subject_name"],
                        "day": "—", "period": 0,
                        "reason": reason, "suggested_action": action
                    })
                    conn.execute(
                        "INSERT INTO conflict_log (institution_id,timetable_id,class_name,"
                        "subject_name,day,period,reason,suggested_action) VALUES (?,?,?,?,?,?,?,?)",
                        (institution_id, tt_id, cls_name, subj["subject_name"], "—", 0, reason, action)
                    )

            # ── Post-processing: GUARANTEE no two days have the exact same period order ──
            for cls in classes:
                c_id = cls["id"]
                for i in range(len(days)):
                    for j in range(i + 1, len(days)):
                        day1, day2 = days[i], days[j]
                        seq1 = [class_slot_subj.get((c_id, day1, so)) for so in teaching_slots]
                        seq2 = [class_slot_subj.get((c_id, day2, so)) for so in teaching_slots]
                        non_empty = [s for s in seq1 if s is not None]
                        if len(non_empty) >= 2 and seq1 == seq2:
                            slots_day2 = [so for so in teaching_slots if class_slot_subj.get((c_id, day2, so))]
                            swapped = False
                            for idx_a in range(len(slots_day2)):
                                for idx_b in range(idx_a + 1, len(slots_day2)):
                                    so_a, so_b = slots_day2[idx_a], slots_day2[idx_b]
                                    subj_a = class_slot_subj.get((c_id, day2, so_a))
                                    subj_b = class_slot_subj.get((c_id, day2, so_b))
                                    if subj_a != subj_b:
                                        slot_row_a = conn.execute(
                                            "SELECT id, staff_id FROM timetable_slot WHERE timetable_id=? AND class_id=? AND day=? AND period=?",
                                            (tt_id, c_id, day2, so_a)
                                        ).fetchone()
                                        slot_row_b = conn.execute(
                                            "SELECT id, staff_id FROM timetable_slot WHERE timetable_id=? AND class_id=? AND day=? AND period=?",
                                            (tt_id, c_id, day2, so_b)
                                        ).fetchone()
                                        if slot_row_a and slot_row_b:
                                            staff_a = slot_row_a["staff_id"]
                                            staff_b = slot_row_b["staff_id"]
                                            other_busy_a = staff_a in (staff_busy.get((day2, so_b), set()) - {staff_a})
                                            other_busy_b = staff_b in (staff_busy.get((day2, so_a), set()) - {staff_b})
                                            if not other_busy_a and not other_busy_b:
                                                conn.execute("UPDATE timetable_slot SET period=? WHERE id=?", (so_b, slot_row_a["id"]))
                                                conn.execute("UPDATE timetable_slot SET period=? WHERE id=?", (so_a, slot_row_b["id"]))
                                                class_slot_subj[(c_id, day2, so_a)] = subj_b
                                                class_slot_subj[(c_id, day2, so_b)] = subj_a
                                                staff_busy.setdefault((day2, so_b), set()).discard(staff_b)
                                                staff_busy.setdefault((day2, so_b), set()).add(staff_a)
                                                staff_busy.setdefault((day2, so_a), set()).discard(staff_a)
                                                staff_busy.setdefault((day2, so_a), set()).add(staff_b)
                                                swapped = True
                                                break
                                if swapped:
                                    break

            yield {"pct": 90, "msg": "Finalizing — saving allocation records…"}

            # ── Persist allocated_periods ───────────────────────────────────
            for staff_id, count in alloc_counts.items():
                conn.execute("UPDATE staff SET allocated_periods=? WHERE id=?", (count, staff_id))

            # ── Save allocation history ─────────────────────────────────────
            for row in conn.execute(
                "SELECT staff_id, subject_id, COUNT(*) as cnt FROM timetable_slot "
                "WHERE timetable_id=? GROUP BY staff_id, subject_id",
                (tt_id,)
            ).fetchall():
                conn.execute(
                    "INSERT INTO allocation_history "
                    "(institution_id,staff_id,subject_id,timetable_id,periods_count) VALUES (?,?,?,?,?)",
                    (institution_id, row["staff_id"], row["subject_id"], tt_id, row["cnt"])
                )

            # ── Update conflict count ───────────────────────────────────────
            conn.execute(
                "UPDATE timetable SET conflicts=? WHERE id=?",
                (len(conflicts), tt_id)
            )

    except Exception as e:
        yield {"pct": -1, "error": f"Generation failed: {str(e)}"}
        return

    yield {
        "pct": 100,
        "msg": f"Done! Generated with {len(conflicts)} conflict(s).",
        "tt_id": tt_id,
        "conflicts": conflicts,
        "conflict_count": len(conflicts),
    }


def generate_timetable(institution_id: int, name: str = "Auto Generated") -> tuple[int, list]:
    """
    Synchronous wrapper around generate_timetable_iter().
    Returns (tt_id, conflicts_list).
    """
    tt_id = None
    conflicts = []
    for event in generate_timetable_iter(institution_id, name):
        if event.get("pct") == 100:
            tt_id = event.get("tt_id")
            conflicts = event.get("conflicts", [])
        elif event.get("pct") == -1:
            raise RuntimeError(event.get("error", "Generation failed"))
    return tt_id, conflicts


# ══════════════════════════════════════════════════════════════════════════════
# ConflictDetector — real-time slot validation for the edit UI
# ══════════════════════════════════════════════════════════════════════════════

class ConflictDetector:
    """Check if a slot move/edit would cause conflicts."""

    @staticmethod
    def check_slot(
        conn,
        timetable_id: int,
        day: str,
        period: int,
        staff_id: int,
        class_id: int,
        institution_id: int,
        exclude_slot_id: Optional[int] = None,
        staff2_id: Optional[int] = None
    ) -> list[dict]:
        """
        Returns a list of conflict dicts. Empty list = no conflicts.
        Each conflict: {"type": str, "reason": str}
        """
        conflicts = []

        ex = (exclude_slot_id,) if exclude_slot_id else (-1,)

        # Primary staff clash: same staff in same slot (different class)
        if conn.execute(
            "SELECT 1 FROM timetable_slot WHERE timetable_id=? AND day=? AND period=? "
            "AND (staff_id=? OR staff2_id=?) AND id!=?",
            (timetable_id, day, period, staff_id, staff_id, ex[0])
        ).fetchone():
            staff_name = conn.execute("SELECT name FROM staff WHERE id=?", (staff_id,)).fetchone()
            name = dict(staff_name)["name"] if staff_name else "Staff"
            conflicts.append({"type": "staff_clash", "reason": f"{name} is already teaching another class in this slot"})

        # Secondary staff clash:
        if staff2_id and conn.execute(
            "SELECT 1 FROM timetable_slot WHERE timetable_id=? AND day=? AND period=? "
            "AND (staff_id=? OR staff2_id=?) AND id!=?",
            (timetable_id, day, period, staff2_id, staff2_id, ex[0])
        ).fetchone():
            staff2_name = conn.execute("SELECT name FROM staff WHERE id=?", (staff2_id,)).fetchone()
            name2 = dict(staff2_name)["name"] if staff2_name else "Secondary Staff"
            conflicts.append({"type": "staff_clash", "reason": f"{name2} is already teaching another class in this slot"})

        # Class clash: same class already has a subject in this slot
        if conn.execute(
            "SELECT 1 FROM timetable_slot WHERE timetable_id=? AND day=? AND period=? "
            "AND class_id=? AND id!=?",
            (timetable_id, day, period, class_id, ex[0])
        ).fetchone():
            conflicts.append({"type": "class_clash", "reason": "This class already has a lesson in this slot"})

        return conflicts


# ══════════════════════════════════════════════════════════════════════════════
# Slot edit operations
# ══════════════════════════════════════════════════════════════════════════════

def edit_slot(slot_id: int, new_staff_id: int, institution_id: int) -> tuple[bool, str]:
    """Change the staff member for an existing slot (staff swap)."""
    with get_db() as conn:
        slot = conn.execute(
            "SELECT * FROM timetable_slot WHERE id=? AND institution_id=?",
            (slot_id, institution_id)
        ).fetchone()
        if not slot:
            return False, "Slot not found"

        slot = dict(slot)
        conflicts = ConflictDetector.check_slot(
            conn, slot["timetable_id"], slot["day"], slot["period"],
            new_staff_id, slot["class_id"], institution_id,
            exclude_slot_id=slot_id
        )
        if conflicts:
            return False, conflicts[0]["reason"]

        old_staff = slot["staff_id"]
        conn.execute(
            "UPDATE timetable_slot SET staff_id=?, is_manual_edit=1 WHERE id=?",
            (new_staff_id, slot_id)
        )
        conn.execute("UPDATE staff SET allocated_periods=MAX(0,allocated_periods-1) WHERE id=?", (old_staff,))
        conn.execute("UPDATE staff SET allocated_periods=allocated_periods+1 WHERE id=?", (new_staff_id,))

    return True, "Staff updated successfully"


def move_slot(slot_id: int, new_day: str, new_period: int, institution_id: int) -> tuple[bool, str]:
    """Move a slot to a different (day, period). Checks all constraints."""
    with get_db() as conn:
        slot = conn.execute(
            "SELECT * FROM timetable_slot WHERE id=? AND institution_id=?",
            (slot_id, institution_id)
        ).fetchone()
        if not slot:
            return False, "Slot not found"

        slot = dict(slot)

        # Check if target day/period is a valid teaching slot
        target_slot = conn.execute(
            "SELECT slot_type FROM period_slot WHERE institution_id=? AND slot_order=?",
            (institution_id, new_period)
        ).fetchone()
        if target_slot and dict(target_slot)["slot_type"] != "period":
            return False, "Cannot place a lesson in a break or lunch slot"

        conflicts = ConflictDetector.check_slot(
            conn, slot["timetable_id"], new_day, new_period,
            slot["staff_id"], slot["class_id"], institution_id,
            exclude_slot_id=slot_id,
            staff2_id=slot.get("staff2_id")
        )
        if conflicts:
            return False, conflicts[0]["reason"]

        conn.execute(
            "UPDATE timetable_slot SET day=?, period=?, is_manual_edit=1 WHERE id=?",
            (new_day, new_period, slot_id)
        )

    return True, "Slot moved successfully"


def swap_slots(slot_id_1: int, slot_id_2: int, institution_id: int) -> tuple[bool, str]:
    """
    Atomically swap the (day, period) of two slots.
    Useful for drag-and-drop where user drops one card onto another.
    """
    with get_db() as conn:
        s1 = conn.execute(
            "SELECT * FROM timetable_slot WHERE id=? AND institution_id=?",
            (slot_id_1, institution_id)
        ).fetchone()
        s2 = conn.execute(
            "SELECT * FROM timetable_slot WHERE id=? AND institution_id=?",
            (slot_id_2, institution_id)
        ).fetchone()

        if not s1 or not s2:
            return False, "One or both slots not found"

        s1, s2 = dict(s1), dict(s2)

        # Validate s1's staff in s2's position (excluding s2 itself)
        c1 = ConflictDetector.check_slot(
            conn, s1["timetable_id"], s2["day"], s2["period"],
            s1["staff_id"], s1["class_id"], institution_id,
            exclude_slot_id=slot_id_2,
            staff2_id=s1.get("staff2_id")
        )
        # Validate s2's staff in s1's position (excluding s1 itself)
        c2 = ConflictDetector.check_slot(
            conn, s2["timetable_id"], s1["day"], s1["period"],
            s2["staff_id"], s2["class_id"], institution_id,
            exclude_slot_id=slot_id_1,
            staff2_id=s2.get("staff2_id")
        )

        if c1 or c2:
            reasons = [(c["reason"]) for c in (c1 or c2)]
            return False, "; ".join(reasons)

        # Perform the swap
        conn.execute(
            "UPDATE timetable_slot SET day=?, period=?, is_manual_edit=1 WHERE id=?",
            (s2["day"], s2["period"], slot_id_1)
        )
        conn.execute(
            "UPDATE timetable_slot SET day=?, period=?, is_manual_edit=1 WHERE id=?",
            (s1["day"], s1["period"], slot_id_2)
        )

    return True, "Slots swapped successfully"


def check_move_valid(slot_id: int, new_day: str, new_period: int, institution_id: int) -> list[dict]:
    """Quick read-only check for drag-over highlighting. Returns conflicts list."""
    with get_db() as conn:
        slot = conn.execute(
            "SELECT * FROM timetable_slot WHERE id=? AND institution_id=?",
            (slot_id, institution_id)
        ).fetchone()
        if not slot:
            return [{"type": "error", "reason": "Slot not found"}]
        slot = dict(slot)

        # Check if target is a teaching slot
        target = conn.execute(
            "SELECT slot_type FROM period_slot WHERE institution_id=? AND slot_order=?",
            (institution_id, new_period)
        ).fetchone()
        if target and dict(target)["slot_type"] != "period":
            return [{"type": "break_slot", "reason": "Cannot place lesson in break/lunch slot"}]

        return ConflictDetector.check_slot(
            conn, slot["timetable_id"], new_day, new_period,
            slot["staff_id"], slot["class_id"], institution_id,
            exclude_slot_id=slot_id,
            staff2_id=slot.get("staff2_id")
        )


# ══════════════════════════════════════════════════════════════════════════════
# Timetable fetch
# ══════════════════════════════════════════════════════════════════════════════

def get_active_timetable_id(institution_id: int) -> Optional[int]:
    with get_db() as conn:
        row = conn.execute(
            "SELECT id FROM timetable WHERE institution_id=? AND is_active=1 ORDER BY id DESC LIMIT 1",
            (institution_id,)
        ).fetchone()
        return row["id"] if row else None


def get_class_timetable(class_id: int, institution_id: int) -> tuple[Optional[int], dict]:
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
                   s.subject_name, s.subject_code, s.abbreviation, s.is_lab, s.lab_duration, s.department,
                   st.name as staff_name, st.id as staff_id,
                   st2.name as staff2_name, ts.staff2_id,
                   cs.name as class_name, cs.department as class_department, cs.semester as class_semester,
                   cs.strength as class_strength, cs.venue as class_venue, cs.academic_year as class_academic_year,
                   s.id as subject_id
            FROM timetable_slot ts
            JOIN subject s  ON s.id  = ts.subject_id
            JOIN staff st   ON st.id = ts.staff_id
            LEFT JOIN staff st2 ON st2.id = ts.staff2_id
            JOIN class_section cs ON cs.id = ts.class_id
            WHERE ts.class_id=? AND ts.timetable_id=?
        """, (class_id, tt["id"])).fetchall()

        grid = {day: {} for day in days}
        for row in slots:
            r_dict = dict(row)
            if not r_dict.get("abbreviation"):
                r_dict["abbreviation"] = generate_abbreviation(r_dict["subject_name"], bool(r_dict.get("is_lab")))
            # Build a combined display name for cells with two teachers
            if r_dict.get("staff2_name"):
                r_dict["staff_display"] = f"{r_dict['staff_name']} & {r_dict['staff2_name']}"
            else:
                r_dict["staff_display"] = r_dict["staff_name"]
            grid[row["day"]][row["period"]] = r_dict

        return tt["id"], grid


def get_class_printable_data(class_id: int, institution_id: int) -> Optional[dict]:
    """Compile comprehensive institutional timetable data matching official institutional format."""
    with get_db() as conn:
        tt = conn.execute(
            "SELECT id, name, generated_at FROM timetable WHERE institution_id=? AND is_active=1 ORDER BY id DESC LIMIT 1",
            (institution_id,)
        ).fetchone()
        if not tt:
            return None

        inst = conn.execute("SELECT * FROM institution WHERE id=?", (institution_id,)).fetchone()
        cls_row = conn.execute("SELECT * FROM class_section WHERE id=? AND institution_id=?", (class_id, institution_id)).fetchone()
        if not cls_row:
            return None

        days = get_working_days(institution_id)
        period_slots = [dict(r) for r in conn.execute(
            "SELECT * FROM period_slot WHERE institution_id=? ORDER BY slot_order", (institution_id,)
        ).fetchall()]

        slots = conn.execute("""
            SELECT ts.day, ts.period, ts.id as slot_id, ts.is_manual_edit,
                   s.subject_name, s.subject_code, s.abbreviation, s.is_lab, s.lab_duration, s.department,
                   st.name as staff_name, st.id as staff_id,
                   st2.name as staff2_name, ts.staff2_id,
                   s.id as subject_id
            FROM timetable_slot ts
            JOIN subject s  ON s.id  = ts.subject_id
            JOIN staff st   ON st.id = ts.staff_id
            LEFT JOIN staff st2 ON st2.id = ts.staff2_id
            WHERE ts.class_id=? AND ts.timetable_id=?
            ORDER BY ts.day, ts.period
        """, (class_id, tt["id"])).fetchall()

        grid = {day: {} for day in days}
        theory_courses = {}
        lab_courses = {}

        for row in slots:
            r_dict = dict(row)
            abbr = r_dict.get("abbreviation") or generate_abbreviation(r_dict["subject_name"], bool(r_dict.get("is_lab")))
            r_dict["abbreviation"] = abbr
            # Build combined display name
            if r_dict.get("staff2_name"):
                r_dict["staff_display"] = f"{r_dict['staff_name']} & {r_dict['staff2_name']}"
            else:
                r_dict["staff_display"] = r_dict["staff_name"]
            grid[r_dict["day"]][r_dict["period"]] = r_dict

            sid = r_dict["subject_id"]
            code = r_dict["subject_code"] or f"CS{sid:04d}"
            target = lab_courses if r_dict["is_lab"] else theory_courses
            if sid not in target:
                target[sid] = {
                    "abbr": abbr,
                    "code": code,
                    "name": r_dict["subject_name"],
                    "faculty": [r_dict["staff_name"]],
                }
                # Add co-teacher immediately for labs
                if r_dict.get("staff2_name") and r_dict["staff2_name"] not in target[sid]["faculty"]:
                    target[sid]["faculty"].append(r_dict["staff2_name"])
            else:
                if r_dict["staff_name"] not in target[sid]["faculty"]:
                    target[sid]["faculty"].append(r_dict["staff_name"])
                if r_dict.get("staff2_name") and r_dict["staff2_name"] not in target[sid]["faculty"]:
                    target[sid]["faculty"].append(r_dict["staff2_name"])

        for t in [theory_courses, lab_courses]:
            for sid, c in t.items():
                c["faculty_str"] = ", ".join(c["faculty"])

        cls_dict = dict(cls_row)
        dept_name = cls_dict.get("department", "Engineering")
        if not dept_name.lower().startswith("department"):
            dept_display = f"Department of {dept_name}"
        else:
            dept_display = dept_name

        # ── Pre-calculate merged day rows for print & PDF template ──────
        day_rows = []
        teaching_slots = [s for s in period_slots if s.get("slot_type") == "period"]

        for day in days:
            day_slots = []
            skip_orders = set()

            for s in period_slots:
                stype = s.get("slot_type", "period")
                order = s.get("slot_order", 0)

                if stype != "period":
                    day_slots.append({
                        "type": "break",
                        "label": s.get("label", "Break"),
                        "start_time": s.get("start_time", ""),
                        "end_time": s.get("end_time", ""),
                        "colspan": 1,
                    })
                    continue

                if order in skip_orders:
                    continue

                cell = grid[day].get(order)
                if not cell:
                    day_slots.append({
                        "type": "empty",
                        "colspan": 1,
                    })
                    continue

                # Check consecutive slots for identical subject + staff
                colspan = 1
                cur_idx = next((idx for idx, ts in enumerate(teaching_slots) if ts["slot_order"] == order), None)
                if cur_idx is not None:
                    j = cur_idx + 1
                    while j < len(teaching_slots):
                        next_ts = teaching_slots[j]
                        prev_ts = teaching_slots[j - 1]

                        # Stop if non-consecutive or if a break intervenes
                        if next_ts["slot_order"] != prev_ts["slot_order"] + 1:
                            break
                        has_break = any(
                            ps.get("slot_type") != "period"
                            and prev_ts["slot_order"] < ps.get("slot_order", 0) < next_ts["slot_order"]
                            for ps in period_slots
                        )
                        if has_break:
                            break

                        next_cell = grid[day].get(next_ts["slot_order"])
                        if (next_cell
                                and next_cell.get("subject_id") == cell.get("subject_id")
                                and next_cell.get("staff_id") == cell.get("staff_id")):
                            colspan += 1
                            skip_orders.add(next_ts["slot_order"])
                            j += 1
                        else:
                            break

                day_slots.append({
                    "type": "subject",
                    "colspan": colspan,
                    "is_lab": bool(cell.get("is_lab")),
                    "abbreviation": cell.get("abbreviation") or cell.get("subject_name", ""),
                    "subject_name": cell.get("subject_name", ""),
                    "subject_code": cell.get("subject_code", ""),
                    "staff_name": cell.get("staff_display") or cell.get("staff_name", ""),
                })

            day_rows.append({
                "name": day,
                "slots": day_slots,
            })

        inst_dict = dict(inst) if inst else {}
        if not inst_dict.get("name"):
            inst_dict["name"] = "INSTITUTION OF ENGINEERING AND TECHNOLOGY"

        return {
            "timetable_id": tt["id"],
            "institution": inst_dict,
            "class": cls_dict,
            "department_display": dept_display,
            "days": days,
            "period_slots": period_slots,
            "grid": grid,
            "day_rows": day_rows,
            "theory_courses": list(theory_courses.values()),
            "lab_courses": list(lab_courses.values()),
        }


def get_staff_timetable(staff_id: int, institution_id: int) -> tuple[Optional[int], dict]:
    with get_db() as conn:
        tt = conn.execute(
            "SELECT id FROM timetable WHERE institution_id=? AND is_active=1 ORDER BY id DESC LIMIT 1",
            (institution_id,)
        ).fetchone()
        if not tt:
            return None, {}

        days = get_working_days(institution_id)
        # Fetch slots where this staff is PRIMARY teacher or CO-TEACHER (staff2)
        slots = conn.execute("""
            SELECT ts.day, ts.period, ts.id as slot_id,
                   s.subject_name, s.is_lab, s.department,
                   st.name as staff_name,
                   st2.name as staff2_name,
                   cs.name as class_name, s.id as subject_id
            FROM timetable_slot ts
            JOIN subject s  ON s.id  = ts.subject_id
            JOIN staff st   ON st.id = ts.staff_id
            LEFT JOIN staff st2 ON st2.id = ts.staff2_id
            JOIN class_section cs ON cs.id = ts.class_id
            WHERE (ts.staff_id=? OR ts.staff2_id=?) AND ts.timetable_id=?
        """, (staff_id, staff_id, tt["id"])).fetchall()

        grid = {day: {} for day in days}
        for row in slots:
            r_dict = dict(row)
            if r_dict.get("staff2_name"):
                r_dict["staff_display"] = f"{r_dict['staff_name']} & {r_dict['staff2_name']}"
            else:
                r_dict["staff_display"] = r_dict["staff_name"]
            grid[row["day"]][row["period"]] = r_dict

        return tt["id"], grid


def get_conflict_list(institution_id: int, conn=None) -> list[dict]:
    """Fetch detailed conflict list from the conflict_log table."""
    def _fetch(c):
        tt = c.execute(
            "SELECT id FROM timetable WHERE institution_id=? AND is_active=1 ORDER BY id DESC LIMIT 1",
            (institution_id,)
        ).fetchone()
        if not tt:
            return []
        rows = c.execute(
            "SELECT * FROM conflict_log WHERE timetable_id=? AND institution_id=? ORDER BY id",
            (tt["id"], institution_id)
        ).fetchall()
        return [dict(r) for r in rows]

    if conn is not None:
        return _fetch(conn)
    with get_db() as c:
        return _fetch(c)


def get_slot_staff_options(slot_id: int, institution_id: int) -> list[dict]:
    """Return staff eligible for the subject in a given slot, with availability info."""
    with get_db() as conn:
        slot = conn.execute(
            "SELECT * FROM timetable_slot WHERE id=? AND institution_id=?",
            (slot_id, institution_id)
        ).fetchone()
        if not slot:
            return []
        slot = dict(slot)

        eligible = conn.execute("""
            SELECT st.id, st.name, st.department, st.allocated_periods,
                   st.max_periods_per_week, st.available_days
            FROM staff st JOIN staff_subjects ss ON ss.staff_id=st.id
            WHERE ss.subject_id=? AND st.institution_id=?
            ORDER BY st.name
        """, (slot["subject_id"], institution_id)).fetchall()

        busy = {r["staff_id"] for r in conn.execute(
            "SELECT staff_id FROM timetable_slot WHERE timetable_id=? AND day=? AND period=? AND id!=?",
            (slot["timetable_id"], slot["day"], slot["period"], slot_id)
        ).fetchall()}

        result = []
        for s in eligible:
            s = dict(s)
            s["is_busy"]    = s["id"] in busy
            s["is_current"] = s["id"] == slot["staff_id"]
            s["remaining"]  = s["max_periods_per_week"] - s["allocated_periods"]
            day_short = slot["day"][:3]
            s["available_today"] = day_short in s["available_days"]
            result.append(s)

        return result


def delete_timetable(institution_id: int) -> None:
    with get_db() as conn:
        conn.execute("DELETE FROM timetable WHERE institution_id=? AND is_active=1", (institution_id,))
        conn.execute("DELETE FROM conflict_log WHERE institution_id=?", (institution_id,))
        conn.execute("UPDATE staff SET allocated_periods=0 WHERE institution_id=?", (institution_id,))


# ══════════════════════════════════════════════════════════════════════════════
# Timetable Workflow & Approval Engine (Coordinator -> HOD -> Master Admin)
# ══════════════════════════════════════════════════════════════════════════════

def submit_timetable(timetable_id: int, institution_id: int, actor_name: str, actor_role: str) -> tuple[bool, str]:
    """Coordinator submits the draft timetable to HOD for formal review."""
    import datetime
    from database import log_activity
    with get_db() as conn:
        tt = conn.execute("SELECT * FROM timetable WHERE id=? AND institution_id=?", (timetable_id, institution_id)).fetchone()
        if not tt:
            return False, "Timetable not found"
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn.execute("""
            UPDATE timetable 
            SET status='submitted', submitted_by=?, submitted_at=?
            WHERE id=? AND institution_id=?
        """, (actor_name, now_str, timetable_id, institution_id))

    log_activity(
        institution_id=institution_id,
        actor_name=actor_name,
        actor_role=actor_role,
        action_type="TIMETABLE_SUBMITTED",
        title=f"Timetable Submitted for Review",
        description=f"{actor_name} ({actor_role.upper()}) submitted '{tt['name']}' to HOD for approval.",
        entity_type="timetable",
        entity_id=timetable_id
    )
    return True, "Timetable submitted to HOD successfully."


def approve_timetable(timetable_id: int, institution_id: int, actor_name: str, actor_role: str) -> tuple[bool, str]:
    """HOD or Master Admin approves the timetable."""
    import datetime
    from database import log_activity
    with get_db() as conn:
        tt = conn.execute("SELECT * FROM timetable WHERE id=? AND institution_id=?", (timetable_id, institution_id)).fetchone()
        if not tt:
            return False, "Timetable not found"
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn.execute("""
            UPDATE timetable 
            SET status='approved', approved_by=?, approved_at=?, rejection_note=NULL
            WHERE id=? AND institution_id=?
        """, (actor_name, now_str, timetable_id, institution_id))

    log_activity(
        institution_id=institution_id,
        actor_name=actor_name,
        actor_role=actor_role,
        action_type="TIMETABLE_APPROVED",
        title=f"Timetable Approved by HOD",
        description=f"{actor_name} ({actor_role.upper()}) approved timetable '{tt['name']}'. Ready for publishing.",
        entity_type="timetable",
        entity_id=timetable_id
    )
    return True, "Timetable approved successfully."


def reject_timetable(timetable_id: int, institution_id: int, actor_name: str, actor_role: str, reason: str = "") -> tuple[bool, str]:
    """HOD returns timetable to Coordinator with feedback."""
    from database import log_activity
    with get_db() as conn:
        tt = conn.execute("SELECT * FROM timetable WHERE id=? AND institution_id=?", (timetable_id, institution_id)).fetchone()
        if not tt:
            return False, "Timetable not found"
        conn.execute("""
            UPDATE timetable 
            SET status='draft', rejection_note=?
            WHERE id=? AND institution_id=?
        """, (reason or "Changes requested by HOD", timetable_id, institution_id))

    log_activity(
        institution_id=institution_id,
        actor_name=actor_name,
        actor_role=actor_role,
        action_type="TIMETABLE_REJECTED",
        title=f"Timetable Revisions Requested",
        description=f"HOD {actor_name} returned '{tt['name']}' with notes: {reason or 'Please revise conflicts'}",
        entity_type="timetable",
        entity_id=timetable_id
    )
    return True, "Timetable returned to Coordinator with feedback."


def publish_timetable(timetable_id: int, institution_id: int, actor_name: str, actor_role: str) -> tuple[bool, str]:
    """Master Admin or HOD officially publishes the approved timetable institution-wide."""
    import datetime
    from database import log_activity
    with get_db() as conn:
        tt = conn.execute("SELECT * FROM timetable WHERE id=? AND institution_id=?", (timetable_id, institution_id)).fetchone()
        if not tt:
            return False, "Timetable not found"
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Deactivate any previous active timetable
        conn.execute("UPDATE timetable SET is_active=0 WHERE institution_id=?", (institution_id,))
        conn.execute("""
            UPDATE timetable 
            SET status='published', is_active=1, published_by=?, published_at=?
            WHERE id=? AND institution_id=?
        """, (actor_name, now_str, timetable_id, institution_id))

    log_activity(
        institution_id=institution_id,
        actor_name=actor_name,
        actor_role=actor_role,
        action_type="TIMETABLE_PUBLISHED",
        title=f"Official Timetable Published",
        description=f"{actor_name} ({actor_role.upper()}) published '{tt['name']}'. Live across the institution.",
        entity_type="timetable",
        entity_id=timetable_id
    )
    return True, "Timetable published successfully across the institution."


# ══════════════════════════════════════════════════════════════════════════════
# Recommendations & Analytics
# ══════════════════════════════════════════════════════════════════════════════

def get_recommendations(subject_id: int, institution_id: int, top_n: int = 5) -> list[dict]:
    with get_db() as conn:
        subj = conn.execute(
            "SELECT * FROM subject WHERE id=? AND institution_id=?",
            (subject_id, institution_id)
        ).fetchone()
        if not subj:
            return []

        eligible = conn.execute("""
            SELECT st.* FROM staff st JOIN staff_subjects ss ON ss.staff_id=st.id
            WHERE ss.subject_id=? AND st.institution_id=?
        """, (subject_id, institution_id)).fetchall()

        hist = {r["staff_id"]: r["total"] for r in conn.execute(
            "SELECT staff_id, SUM(periods_count) as total FROM allocation_history "
            "WHERE subject_id=? AND institution_id=? GROUP BY staff_id",
            (subject_id, institution_id)
        ).fetchall()}

        results = []
        for s in eligible:
            s = dict(s)
            past  = hist.get(s["id"], 0)
            avail = max(0, s["max_periods_per_week"] - s["allocated_periods"])
            score = round(
                (past * 2) + (s["experience"] * dict(subj)["difficulty_level"]) + (avail * 0.5), 2
            )
            results.append({**s, "past_periods": past, "availability": avail,
                             "recommendation_score": score})

        results.sort(key=lambda x: -x["recommendation_score"])
        return results[:top_n]


def compute_analytics(institution_id: int, conn=None) -> list[dict]:
    def _compute(c):
        staff_list = c.execute(
            "SELECT * FROM staff WHERE institution_id=? ORDER BY name", (institution_id,)
        ).fetchall()
        if not staff_list:
            return []

        # Batch 1: Average difficulty level for active timetable per staff (1 query instead of N)
        avg_diff_rows = c.execute("""
            SELECT ts.staff_id, AVG(sub.difficulty_level) as avg_diff
            FROM timetable_slot ts
            JOIN subject sub ON sub.id=ts.subject_id
            JOIN timetable tt ON tt.id=ts.timetable_id
            WHERE tt.is_active=1 AND tt.institution_id=?
            GROUP BY ts.staff_id
        """, (institution_id,)).fetchall()
        avg_diff_map = {
            r["staff_id"]: (float(r["avg_diff"]) if r["avg_diff"] is not None else 0.0)
            for r in avg_diff_rows
        }

        # Batch 2: Staff subjects mapping for this institution (1 query instead of N)
        subj_rows = c.execute("""
            SELECT ss.staff_id, sub.subject_name
            FROM subject sub
            JOIN staff_subjects ss ON ss.subject_id=sub.id
            JOIN staff st ON st.id=ss.staff_id
            WHERE st.institution_id=?
        """, (institution_id,)).fetchall()
        staff_subjs = defaultdict(list)
        for r in subj_rows:
            staff_subjs[r["staff_id"]].append(r["subject_name"])

        scored = []
        for s in staff_list:
            s = dict(s)
            sid = s["id"]
            avg_diff = float(avg_diff_map.get(sid, 0.0) or 0.0)
            alloc_p = float(s["allocated_periods"] or 0)
            exp = float(s["experience"] or 0)
            max_p = float(s["max_periods_per_week"] or 0)
            score = round(alloc_p * 0.4 + exp * 0.3 + avg_diff * 0.3, 2)
            subjs = staff_subjs.get(sid, [])
            pct = round(alloc_p / max_p * 100 if max_p else 0, 1)
            scored.append({**s, "performance_score": score, "subject_names": subjs, "overload_pct": pct})

        scored.sort(key=lambda x: -x["performance_score"])
        total = len(scored)
        top10  = max(1, int(total * 0.10))
        next20 = max(1, int(total * 0.20))
        results = []
        for i, s in enumerate(scored):
            if i < top10:               suggestion, badge = "Promotion",    "success"
            elif i < top10 + next20:    suggestion, badge = "Salary Hike",  "info"
            elif s["overload_pct"] > 90: suggestion, badge = "Overloaded",  "danger"
            elif s["overload_pct"] < 30: suggestion, badge = "Underutilized","warning"
            else:                        suggestion, badge = "Normal",       "secondary"
            results.append({
                "rank": i + 1, "staff": s, "suggestion": suggestion,
                "badge": badge, "overload_pct": s["overload_pct"]
            })
        return results

    if conn is not None:
        return _compute(conn)
    with get_db() as c:
        return _compute(c)
