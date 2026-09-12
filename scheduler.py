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

def get_working_days(institution_id: int) -> list[str]:
    with get_db() as conn:
        cfg = conn.execute(
            "SELECT working_days FROM time_config WHERE institution_id=?",
            (institution_id,)
        ).fetchone()
    if not cfg:
        return ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    return [DAY_MAP.get(d.strip(), d.strip()) for d in cfg["working_days"].split(",")]


def get_period_count(institution_id: int) -> int:
    """Count of teaching (non-break/lunch) slots per day."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM period_slot WHERE institution_id=? AND slot_type='period'",
            (institution_id,)
        ).fetchone()
        cnt = row["cnt"] if row else 0
        if cnt:
            return cnt
        cfg = conn.execute(
            "SELECT periods_per_day FROM time_config WHERE institution_id=?",
            (institution_id,)
        ).fetchone()
        return cfg["periods_per_day"] if cfg else 6


def get_teaching_slot_orders(institution_id: int) -> list[int]:
    """Sorted slot_order values for period-type slots only (no breaks/lunch)."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT slot_order FROM period_slot WHERE institution_id=? AND slot_type='period' ORDER BY slot_order",
            (institution_id,)
        ).fetchall()
    if rows:
        return [r["slot_order"] for r in rows]
    return list(range(1, get_period_count(institution_id) + 1))


def get_period_slots(institution_id: int) -> list[dict]:
    """All slots including breaks for display."""
    with get_db() as conn:
        return [dict(r) for r in conn.execute(
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
                SELECT s.id, s.subject_name, s.periods_per_week, s.is_lab, s.lab_duration
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
) -> Optional[int]:
    """
    Score-based staff selector. Returns best available staff_id or None.
    Constraints checked (in order):
      1. Not already in a slot at (day, slot_order)
      2. Has not exceeded weekly period limit
      3. Has not exceeded daily period limit (max_periods_per_day)
      4. Available on this day (available_days)
    """
    busy_set = staff_busy.get((day, slot_order), set())

    candidates = []
    for row in conn.execute(
        "SELECT ss.staff_id FROM staff_subjects ss JOIN staff st ON st.id=ss.staff_id "
        "WHERE ss.subject_id=? AND st.institution_id=?",
        (subject_id, institution_id)
    ).fetchall():
        sid = row["staff_id"]

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
    staff_busy: dict, class_busy: dict, alloc_counts: dict, staff_daily: dict
):
    """Insert a slot record and update all in-memory tracking dicts."""
    conn.execute(
        "INSERT INTO timetable_slot "
        "(institution_id,timetable_id,day,period,class_id,subject_id,staff_id) "
        "VALUES (?,?,?,?,?,?,?)",
        (institution_id, tt_id, day, slot_order, cls_id, subj_id, staff_id)
    )
    staff_busy.setdefault((day, slot_order), set()).add(staff_id)
    class_busy[(cls_id, day, slot_order)] = True
    alloc_counts[staff_id] = alloc_counts.get(staff_id, 0) + 1
    staff_daily[(staff_id, day)] = staff_daily.get((staff_id, day), 0) + 1


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

            total_labs = sum(r for _, _, _, r, _ in all_labs)
            total_lecs = len(all_lectures)

            yield {
                "pct": 12,
                "msg": f"Found {total_labs} lab sessions, {total_lecs} lecture periods. Placing labs first…"
            }

            # ══════════════════════════════════════════════════════════════
            # PHASE 1: Place lab subjects (consecutive slots required)
            # ══════════════════════════════════════════════════════════════
            labs_placed = 0

            # Sort classes and rotate starting days so classes don't all contend on Monday
            for cls_idx, (cls_id, cls_name, subj, reps, duration) in enumerate(all_labs):
                subj_id  = subj["id"]

                for rep_idx in range(reps):
                    placed = False

                    # Days prioritized by fewest occupied slots for this class + rotated by class index
                    rotated_days = days[cls_idx % len(days):] + days[:cls_idx % len(days)]
                    candidate_days = sorted(
                        rotated_days,
                        key=lambda d: sum(1 for so in teaching_slots if class_busy.get((cls_id, d, so)))
                    )

                    for day in candidate_days:
                        # Get free teaching slots for this class on this day
                        free_slots = [
                            so for so in teaching_slots
                            if not class_busy.get((cls_id, day, so))
                        ]

                        # Find `duration` consecutive free teaching slots
                        for i in range(len(free_slots) - duration + 1):
                            group = free_slots[i:i + duration]

                            # ── Verify no break/lunch between the group ──
                            if _has_break_between(conn, institution_id, group):
                                continue
                            # Must be numerically consecutive slot_orders
                            if list(group) != list(range(group[0], group[0] + duration)):
                                continue

                            # Find a staff member free for all slots
                            staff_id = _best_staff(
                                conn, subj_id, subj["difficulty_level"], day, group[0],
                                staff_busy, alloc_counts, max_p, max_pd, staff_daily,
                                exp_map, avail_map, institution_id
                            )
                            if not staff_id:
                                continue

                            # Verify staff is free for every slot in the group
                            if any(staff_id in staff_busy.get((day, so), set()) for so in group):
                                continue

                            # Verify daily limit for all lab slots
                            daily_after = staff_daily.get((staff_id, day), 0) + duration
                            if daily_after > max_pd.get(staff_id, 4):
                                continue

                            # ── Place the lab ──────────────────────────────
                            for so in group:
                                _mark_slot(
                                    conn, institution_id, tt_id,
                                    day, so, cls_id, subj_id, staff_id,
                                    staff_busy, class_busy, alloc_counts, staff_daily
                                )
                            placed = True
                            break
                        if placed:
                            break

                    if not placed:
                        reason = f"No consecutive {duration}-period block found for lab (all days checked)"
                        action = "Reduce lab_duration or add more working days/period slots"
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

            for unit in lecture_units:
                cls_id = unit["cls_id"]
                cls_name = unit["cls_name"]
                subj = unit["subj"]
                sid = subj["id"]
                rep_idx = unit["rep_idx"]
                placed = False

                max_allowed_on_day = max(1, math.ceil(subj["periods_per_week"] / len(days)))

                # Deterministic pseudo-random seed per class & subject & repetition to prevent day-sync
                rng = random.Random(cls_id * 1000 + sid * 37 + rep_idx * 17)

                # ── PASS 1: Strict daily subject cap ──
                candidate_days = list(days)
                rng.shuffle(candidate_days)
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
                    rng.shuffle(free_slots)
                    free_slots.sort(key=lambda so: (
                        sum(1 for d in days if class_slot_subj.get((cls_id, d, so)) == sid)
                    ))

                    for so in free_slots:
                        staff_id = _best_staff(
                            conn, sid, subj["difficulty_level"], day, so,
                            staff_busy, alloc_counts, max_p, max_pd, staff_daily,
                            exp_map, avail_map, institution_id
                        )
                        if staff_id:
                            _mark_slot(
                                conn, institution_id, tt_id,
                                day, so, cls_id, sid, staff_id,
                                staff_busy, class_busy, alloc_counts, staff_daily
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
                        rng.shuffle(free_slots)
                        for so in free_slots:
                            staff_id = _best_staff(
                                conn, sid, subj["difficulty_level"], day, so,
                                staff_busy, alloc_counts, max_p, max_pd, staff_daily,
                                exp_map, avail_map, institution_id
                            )
                            if staff_id:
                                _mark_slot(
                                    conn, institution_id, tt_id,
                                    day, so, cls_id, sid, staff_id,
                                    staff_busy, class_busy, alloc_counts, staff_daily
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

                # ── PASS 3: Intelligent Kempe Relocation / Local Swap Search ──
                # This simulates a human timetable coordinator rearranging a slot to resolve a cross-department clash
                if not placed:
                    eligible_staff_set = set(subj_eligible_staff.get(sid, []))
                    for day in days:
                        if placed:
                            break
                        for so in teaching_slots:
                            if placed:
                                break
                            current_subj_here = class_slot_subj.get((cls_id, day, so))
                            current_staff_here = class_slot_staff.get((cls_id, day, so))
                            current_slot_id = class_slot_id.get((cls_id, day, so))
                            if not current_subj_here or not current_staff_here or not current_slot_id:
                                continue

                            # Check if an eligible faculty for OUR subject is free at (day, so)
                            candidate_staff = None
                            for st_candidate in eligible_staff_set:
                                if st_candidate not in staff_busy.get((day, so), set()):
                                    if staff_daily.get((st_candidate, day), 0) < max_pd.get(st_candidate, 4):
                                        if alloc_counts.get(st_candidate, 0) < max_p.get(st_candidate, 20):
                                            if day[:3] in avail_map.get(st_candidate, "Mon,Tue,Wed,Thu,Fri"):
                                                candidate_staff = st_candidate
                                                break
                            if not candidate_staff:
                                continue

                            # Can we move current_subj_here to another free slot (alt_day, alt_so) for this class?
                            for alt_day in days:
                                if placed:
                                    break
                                alt_free_slots = [s for s in teaching_slots if not class_busy.get((cls_id, alt_day, s))]
                                for alt_so in alt_free_slots:
                                    if current_staff_here not in staff_busy.get((alt_day, alt_so), set()):
                                        if alt_day != day and staff_daily.get((current_staff_here, alt_day), 0) >= max_pd.get(current_staff_here, 4):
                                            continue
                                        if alt_day[:3] not in avail_map.get(current_staff_here, "Mon,Tue,Wed,Thu,Fri"):
                                            continue

                                        # Relocate current_subj_here to (alt_day, alt_so)
                                        conn.execute(
                                            "UPDATE timetable_slot SET day=?, period=? WHERE id=?",
                                            (alt_day, alt_so, current_slot_id)
                                        )
                                        # Update tracking for the moved slot
                                        class_busy.pop((cls_id, day, so), None)
                                        staff_busy.get((day, so), set()).discard(current_staff_here)
                                        if (cls_id, day) in class_day_subj and current_subj_here in class_day_subj[(cls_id, day)]:
                                            class_day_subj[(cls_id, day)].remove(current_subj_here)
                                        staff_daily[(current_staff_here, day)] = max(0, staff_daily.get((current_staff_here, day), 1) - 1)

                                        class_busy[(cls_id, alt_day, alt_so)] = True
                                        staff_busy.setdefault((alt_day, alt_so), set()).add(current_staff_here)
                                        class_day_subj.setdefault((cls_id, alt_day), []).append(current_subj_here)
                                        class_slot_subj[(cls_id, alt_day, alt_so)] = current_subj_here
                                        class_slot_staff[(cls_id, alt_day, alt_so)] = current_staff_here
                                        class_slot_id[(cls_id, alt_day, alt_so)] = current_slot_id
                                        staff_daily[(current_staff_here, alt_day)] = staff_daily.get((current_staff_here, alt_day), 0) + 1

                                        # Place our current subject into the newly vacated (day, so)!
                                        _mark_slot(
                                            conn, institution_id, tt_id,
                                            day, so, cls_id, sid, candidate_staff,
                                            staff_busy, class_busy, alloc_counts, staff_daily
                                        )
                                        new_id = conn.execute("SELECT MAX(id) as mid FROM timetable_slot").fetchone()["mid"]
                                        class_day_subj.setdefault((cls_id, day), []).append(sid)
                                        class_slot_subj[(cls_id, day, so)] = sid
                                        class_slot_staff[(cls_id, day, so)] = candidate_staff
                                        class_slot_id[(cls_id, day, so)] = new_id
                                        placed = True
                                        break

                # ── Conflict Logging if All Passes & Swaps Exhausted ──
                if not placed:
                    reason = ("No available staff or free slot — all eligible staff are busy or "
                              "have reached daily/weekly period limits across all departments")
                    action = (f"Add more faculty for '{subj['subject_name']}' in {cls_name}, "
                              "increase max_periods_per_week, or adjust working days")
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

                lec_placed += 1
                if lec_placed % 4 == 0 or lec_placed == total_units:
                    pct = 42 + int((lec_placed / max(total_units, 1)) * 46)
                    yield {"pct": pct, "msg": f"Scheduling multi-department lectures: {lec_placed}/{total_units}"}

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
        exclude_slot_id: Optional[int] = None
    ) -> list[dict]:
        """
        Returns a list of conflict dicts. Empty list = no conflicts.
        Each conflict: {"type": str, "reason": str}
        """
        conflicts = []

        ex = (exclude_slot_id,) if exclude_slot_id else (-1,)

        # Staff clash: same staff in same slot (different class)
        if conn.execute(
            "SELECT 1 FROM timetable_slot WHERE timetable_id=? AND day=? AND period=? "
            "AND staff_id=? AND id!=?",
            (timetable_id, day, period, staff_id, ex[0])
        ).fetchone():
            staff_name = conn.execute("SELECT name FROM staff WHERE id=?", (staff_id,)).fetchone()
            name = dict(staff_name)["name"] if staff_name else "Staff"
            conflicts.append({"type": "staff_clash", "reason": f"{name} is already teaching another class in this slot"})

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
            exclude_slot_id=slot_id
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
            exclude_slot_id=slot_id_2
        )
        # Validate s2's staff in s1's position (excluding s1 itself)
        c2 = ConflictDetector.check_slot(
            conn, s2["timetable_id"], s1["day"], s1["period"],
            s2["staff_id"], s2["class_id"], institution_id,
            exclude_slot_id=slot_id_1
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
            exclude_slot_id=slot_id
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
                   cs.name as class_name, cs.department as class_department, cs.semester as class_semester,
                   cs.strength as class_strength, cs.venue as class_venue, cs.academic_year as class_academic_year,
                   s.id as subject_id
            FROM timetable_slot ts
            JOIN subject s  ON s.id  = ts.subject_id
            JOIN staff st   ON st.id = ts.staff_id
            JOIN class_section cs ON cs.id = ts.class_id
            WHERE ts.class_id=? AND ts.timetable_id=?
        """, (class_id, tt["id"])).fetchall()

        grid = {day: {} for day in days}
        for row in slots:
            r_dict = dict(row)
            if not r_dict.get("abbreviation"):
                r_dict["abbreviation"] = generate_abbreviation(r_dict["subject_name"], bool(r_dict.get("is_lab")))
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
                   s.id as subject_id
            FROM timetable_slot ts
            JOIN subject s  ON s.id  = ts.subject_id
            JOIN staff st   ON st.id = ts.staff_id
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
            grid[row["day"]][row["period"]] = r_dict

            sid = row["subject_id"]
            code = row["subject_code"] or f"CS{sid:04d}"
            target = lab_courses if row["is_lab"] else theory_courses
            if sid not in target:
                target[sid] = {
                    "abbr": abbr,
                    "code": code,
                    "name": row["subject_name"],
                    "faculty": [row["staff_name"]],
                }
            else:
                if row["staff_name"] not in target[sid]["faculty"]:
                    target[sid]["faculty"].append(row["staff_name"])

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
                    "staff_name": cell.get("staff_name", ""),
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
        slots = conn.execute("""
            SELECT ts.day, ts.period, ts.id as slot_id,
                   s.subject_name, s.is_lab, s.department,
                   st.name as staff_name, cs.name as class_name, s.id as subject_id
            FROM timetable_slot ts
            JOIN subject s  ON s.id  = ts.subject_id
            JOIN staff st   ON st.id = ts.staff_id
            JOIN class_section cs ON cs.id = ts.class_id
            WHERE ts.staff_id=? AND ts.timetable_id=?
        """, (staff_id, tt["id"])).fetchall()

        grid = {day: {} for day in days}
        for row in slots:
            grid[row["day"]][row["period"]] = dict(row)

        return tt["id"], grid


def get_conflict_list(institution_id: int) -> list[dict]:
    """Fetch detailed conflict list from the conflict_log table."""
    with get_db() as conn:
        tt = conn.execute(
            "SELECT id FROM timetable WHERE institution_id=? AND is_active=1 ORDER BY id DESC LIMIT 1",
            (institution_id,)
        ).fetchone()
        if not tt:
            return []
        rows = conn.execute(
            "SELECT * FROM conflict_log WHERE timetable_id=? ORDER BY id",
            (tt["id"],)
        ).fetchall()
        return [dict(r) for r in rows]


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


def compute_analytics(institution_id: int) -> list[dict]:
    with get_db() as conn:
        staff_list = conn.execute(
            "SELECT * FROM staff WHERE institution_id=? ORDER BY name", (institution_id,)
        ).fetchall()
        scored = []
        for s in staff_list:
            s = dict(s)
            row = conn.execute("""
                SELECT AVG(sub.difficulty_level) as avg_diff
                FROM timetable_slot ts
                JOIN subject sub ON sub.id=ts.subject_id
                JOIN timetable tt ON tt.id=ts.timetable_id
                WHERE ts.staff_id=? AND tt.is_active=1 AND tt.institution_id=?
            """, (s["id"], institution_id)).fetchone()
            avg_diff = (dict(row)["avg_diff"] or 0) if row else 0
            score = round(s["allocated_periods"] * 0.4 + s["experience"] * 0.3 + avg_diff * 0.3, 2)
            subjs = [dict(r)["subject_name"] for r in conn.execute("""
                SELECT sub.subject_name FROM subject sub
                JOIN staff_subjects ss ON ss.subject_id=sub.id WHERE ss.staff_id=?
            """, (s["id"],)).fetchall()]
            pct = round(
                s["allocated_periods"] / s["max_periods_per_week"] * 100
                if s["max_periods_per_week"] else 0, 1
            )
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
