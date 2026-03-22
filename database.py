"""
database.py — Multi-tenant SQLite3 layer for EduSchedule Pro v2
Every institution has its own isolated data via institution_id foreign key.
"""
import sqlite3, os, hashlib, secrets
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(__file__), 'edupro.db')

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn

@contextmanager
def get_db():
    conn = get_conn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def hash_password(pw):
    salt = secrets.token_hex(16)
    h = hashlib.sha256((salt + pw).encode()).hexdigest()
    return f"{salt}:{h}"

def check_password(stored, pw):
    try:
        salt, h = stored.split(":", 1)
        return hashlib.sha256((salt + pw).encode()).hexdigest() == h
    except Exception:
        return False

def init_db():
    with get_db() as conn:
        conn.executescript("""
        -- ── Institutions ──────────────────────────────────────────────
        CREATE TABLE IF NOT EXISTS institution (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL,
            code        TEXT UNIQUE NOT NULL,       -- short login code e.g. "MIT2024"
            address     TEXT,
            email       TEXT,
            phone       TEXT,
            logo_text   TEXT DEFAULT '',            -- emoji / short text for avatar
            created_at  TEXT DEFAULT (datetime('now'))
        );

        -- ── Users (one or more per institution, role: admin/viewer) ──
        CREATE TABLE IF NOT EXISTS users (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            institution_id  INTEGER NOT NULL REFERENCES institution(id) ON DELETE CASCADE,
            username        TEXT NOT NULL,
            email           TEXT,
            password_hash   TEXT NOT NULL,
            role            TEXT DEFAULT 'admin',   -- admin | viewer
            created_at      TEXT DEFAULT (datetime('now')),
            UNIQUE(institution_id, username)
        );

        -- ── Time Configuration (per institution) ─────────────────────
        CREATE TABLE IF NOT EXISTS time_config (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            institution_id  INTEGER UNIQUE NOT NULL REFERENCES institution(id) ON DELETE CASCADE,
            periods_per_day INTEGER DEFAULT 6,
            working_days    TEXT DEFAULT 'Mon,Tue,Wed,Thu,Fri',  -- comma-separated
            updated_at      TEXT DEFAULT (datetime('now'))
        );

        -- ── Period Slots (per institution: period number → time range) ─
        CREATE TABLE IF NOT EXISTS period_slot (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            institution_id  INTEGER NOT NULL REFERENCES institution(id) ON DELETE CASCADE,
            slot_order      INTEGER NOT NULL,        -- 1,2,3...
            label           TEXT NOT NULL,           -- "Period 1", "Break", "Lunch"
            start_time      TEXT NOT NULL,           -- "09:00"
            end_time        TEXT NOT NULL,           -- "09:50"
            slot_type       TEXT DEFAULT 'period',   -- period | break | lunch
            UNIQUE(institution_id, slot_order)
        );

        -- ── Staff ─────────────────────────────────────────────────────
        CREATE TABLE IF NOT EXISTS staff (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            institution_id      INTEGER NOT NULL REFERENCES institution(id) ON DELETE CASCADE,
            name                TEXT NOT NULL,
            department          TEXT NOT NULL,
            experience          INTEGER DEFAULT 0,
            max_periods_per_week INTEGER DEFAULT 20,
            allocated_periods   INTEGER DEFAULT 0,
            email               TEXT,
            available_days      TEXT DEFAULT 'Mon,Tue,Wed,Thu,Fri',
            created_at          TEXT DEFAULT (datetime('now'))
        );

        -- ── Subjects ──────────────────────────────────────────────────
        CREATE TABLE IF NOT EXISTS subject (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            institution_id  INTEGER NOT NULL REFERENCES institution(id) ON DELETE CASCADE,
            subject_name    TEXT NOT NULL,
            subject_code    TEXT,
            department      TEXT NOT NULL,
            periods_per_week INTEGER DEFAULT 3,
            difficulty_level INTEGER DEFAULT 3,
            is_lab          INTEGER DEFAULT 0,       -- 0=lecture, 1=lab (needs consecutive periods)
            lab_duration    INTEGER DEFAULT 2,       -- consecutive periods if is_lab=1
            created_at      TEXT DEFAULT (datetime('now'))
        );

        -- ── Staff ↔ Subjects (per institution) ───────────────────────
        CREATE TABLE IF NOT EXISTS staff_subjects (
            staff_id    INTEGER REFERENCES staff(id) ON DELETE CASCADE,
            subject_id  INTEGER REFERENCES subject(id) ON DELETE CASCADE,
            PRIMARY KEY (staff_id, subject_id)
        );

        -- ── Classes ───────────────────────────────────────────────────
        CREATE TABLE IF NOT EXISTS class_section (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            institution_id  INTEGER NOT NULL REFERENCES institution(id) ON DELETE CASCADE,
            name            TEXT NOT NULL,
            department      TEXT NOT NULL,
            semester        INTEGER DEFAULT 1,
            strength        INTEGER DEFAULT 60,
            created_at      TEXT DEFAULT (datetime('now')),
            UNIQUE(institution_id, name)
        );

        -- ── Class ↔ Subjects ──────────────────────────────────────────
        CREATE TABLE IF NOT EXISTS class_subjects (
            class_id    INTEGER REFERENCES class_section(id) ON DELETE CASCADE,
            subject_id  INTEGER REFERENCES subject(id) ON DELETE CASCADE,
            PRIMARY KEY (class_id, subject_id)
        );

        -- ── Timetable ─────────────────────────────────────────────────
        CREATE TABLE IF NOT EXISTS timetable (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            institution_id  INTEGER NOT NULL REFERENCES institution(id) ON DELETE CASCADE,
            name            TEXT DEFAULT 'Generated Timetable',
            generated_at    TEXT DEFAULT (datetime('now')),
            is_active       INTEGER DEFAULT 1,
            conflicts       INTEGER DEFAULT 0,
            notes           TEXT
        );

        -- ── Timetable Slots ───────────────────────────────────────────
        CREATE TABLE IF NOT EXISTS timetable_slot (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            institution_id  INTEGER NOT NULL REFERENCES institution(id) ON DELETE CASCADE,
            timetable_id    INTEGER NOT NULL REFERENCES timetable(id) ON DELETE CASCADE,
            day             TEXT NOT NULL,
            period          INTEGER NOT NULL,
            class_id        INTEGER REFERENCES class_section(id) ON DELETE CASCADE,
            subject_id      INTEGER REFERENCES subject(id) ON DELETE CASCADE,
            staff_id        INTEGER REFERENCES staff(id) ON DELETE CASCADE,
            is_manual_edit  INTEGER DEFAULT 0,
            created_at      TEXT DEFAULT (datetime('now'))
        );

        -- ── Allocation History ─────────────────────────────────────────
        CREATE TABLE IF NOT EXISTS allocation_history (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            institution_id  INTEGER NOT NULL REFERENCES institution(id) ON DELETE CASCADE,
            staff_id        INTEGER REFERENCES staff(id) ON DELETE CASCADE,
            subject_id      INTEGER REFERENCES subject(id) ON DELETE CASCADE,
            timetable_id    INTEGER REFERENCES timetable(id) ON DELETE CASCADE,
            periods_count   INTEGER DEFAULT 0,
            allocation_date TEXT DEFAULT (datetime('now'))
        );
        """)
    print("✅ Database schema ready.")

def seed_demo_institution():
    """Create a demo institution with sample data if none exists."""
    with get_db() as conn:
        if conn.execute("SELECT 1 FROM institution LIMIT 1").fetchone():
            return  # already seeded

        # Institution
        conn.execute(
            "INSERT INTO institution (name, code, address, email, logo_text) VALUES (?,?,?,?,?)",
            ("Demo College of Engineering", "DEMO2024",
             "123 College Road, Tech City", "admin@democollege.edu", "🎓")
        )
        inst_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

        # Admin user
        conn.execute(
            "INSERT INTO users (institution_id, username, email, password_hash, role) VALUES (?,?,?,?,?)",
            (inst_id, "admin", "admin@democollege.edu", hash_password("admin123"), "admin")
        )

        # Time config
        conn.execute(
            "INSERT INTO time_config (institution_id, periods_per_day, working_days) VALUES (?,?,?)",
            (inst_id, 6, "Mon,Tue,Wed,Thu,Fri")
        )

        # Period slots
        slots = [
            (1, "Period 1",  "09:00", "09:50", "period"),
            (2, "Period 2",  "09:50", "10:40", "period"),
            (3, "Break",     "10:40", "11:00", "break"),
            (4, "Period 3",  "11:00", "11:50", "period"),
            (5, "Period 4",  "11:50", "12:40", "period"),
            (6, "Lunch",     "12:40", "13:20", "lunch"),
            (7, "Period 5",  "13:20", "14:10", "period"),
            (8, "Period 6",  "14:10", "15:00", "period"),
        ]
        for s in slots:
            conn.execute(
                "INSERT INTO period_slot (institution_id, slot_order, label, start_time, end_time, slot_type) VALUES (?,?,?,?,?,?)",
                (inst_id,) + s
            )

        # Subjects
        subjects_data = [
            ("Data Structures",    "DS101",  "CSE",    4, 4, 0, 1),
            ("Algorithms",         "AL102",  "CSE",    3, 5, 0, 1),
            ("Database Systems",   "DB201",  "CSE",    3, 3, 0, 1),
            ("OS Lab",             "OSL301", "CSE",    2, 4, 1, 2),
            ("Computer Networks",  "CN401",  "CSE",    3, 4, 0, 1),
            ("Machine Learning",   "ML501",  "CSE",    4, 5, 0, 1),
            ("Circuit Theory",     "CT101",  "ECE",    4, 4, 0, 1),
            ("Signals & Systems",  "SS201",  "ECE",    3, 5, 0, 1),
            ("Electronics Lab",    "EL301",  "ECE",    2, 3, 1, 2),
            ("Digital Electronics","DE101",  "ECE",    4, 3, 0, 1),
            ("Engineering Maths",  "MA101",  "COMMON", 4, 3, 0, 1),
            ("Physics",            "PH101",  "COMMON", 3, 2, 0, 1),
        ]
        for row in subjects_data:
            conn.execute(
                "INSERT INTO subject (institution_id,subject_name,subject_code,department,periods_per_week,difficulty_level,is_lab,lab_duration) VALUES (?,?,?,?,?,?,?,?)",
                (inst_id,) + row
            )

        def sid(code):
            r = conn.execute("SELECT id FROM subject WHERE subject_code=? AND institution_id=?", (code, inst_id)).fetchone()
            return r['id'] if r else None

        # Staff
        staff_data = [
            ("Dr. Arun Kumar",    "CSE",    15, 22, "arun@college.edu",    ['DS101','AL102','ML501']),
            ("Prof. Priya Sharma","CSE",    10, 20, "priya@college.edu",   ['DB201','DS101','OSL301']),
            ("Dr. Ravi Verma",    "CSE",    8,  18, "ravi@college.edu",    ['CN401','AL102','OSL301']),
            ("Ms. Kavitha Nair",  "CSE",    5,  16, "kavitha@college.edu", ['DB201','ML501']),
            ("Dr. Suresh Babu",   "ECE",    12, 20, "suresh@college.edu",  ['CT101','SS201','EL301']),
            ("Prof. Meena Devi",  "ECE",    9,  18, "meena@college.edu",   ['DE101','CT101','EL301']),
            ("Dr. Karthik R",     "ECE",    7,  18, "karthik@college.edu", ['SS201','DE101']),
            ("Prof. Lakshmi T",   "COMMON", 14, 22, "lakshmi@college.edu", ['MA101','PH101']),
            ("Mr. Ganesh P",      "COMMON", 6,  16, "ganesh@college.edu",  ['MA101','PH101']),
        ]
        for name, dept, exp, maxp, email, codes in staff_data:
            conn.execute(
                "INSERT INTO staff (institution_id,name,department,experience,max_periods_per_week,email) VALUES (?,?,?,?,?,?)",
                (inst_id, name, dept, exp, maxp, email)
            )
            st_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            for code in codes:
                subj_id = sid(code)
                if subj_id:
                    conn.execute("INSERT OR IGNORE INTO staff_subjects VALUES (?,?)", (st_id, subj_id))

        # Classes
        classes_data = [
            ("CSE-A", "CSE", 3, 65, ['DS101','AL102','DB201','OSL301','MA101']),
            ("CSE-B", "CSE", 3, 60, ['DS101','AL102','CN401','OSL301','PH101']),
            ("ECE-A", "ECE", 3, 62, ['CT101','SS201','EL301','MA101']),
            ("ECE-B", "ECE", 3, 58, ['DE101','CT101','EL301','PH101']),
        ]
        for name, dept, sem, strength, codes in classes_data:
            conn.execute(
                "INSERT INTO class_section (institution_id,name,department,semester,strength) VALUES (?,?,?,?,?)",
                (inst_id, name, dept, sem, strength)
            )
            cls_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            for code in codes:
                subj_id = sid(code)
                if subj_id:
                    conn.execute("INSERT OR IGNORE INTO class_subjects VALUES (?,?)", (cls_id, subj_id))

    print("✅ Demo institution seeded.")
