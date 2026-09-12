"""
database.py — Dual-backend database layer (SQLite or Supabase/PostgreSQL).

Switching between backends:
  - SQLite   : Default when DATABASE_URL is not set.  Great for local dev.
  - Supabase : Set DATABASE_URL=postgresql://... in .env to switch to cloud.

Both backends share the same Python API:
  - get_db()      : Context manager yielding a DBAdapter (auto-commit/rollback).
  - conn.execute(sql, params)  : Returns cursor; uses ? placeholders (auto-converted for PG).
  - conn.insert(sql, params)   : INSERT that returns the new row id.
  - conn.executescript(sql)    : Run multiple semicolon-separated statements.
"""
import sqlite3, os, hashlib, secrets, re
from contextlib import contextmanager
from config import DB_BACKEND, DATABASE_URL, SQLITE_PATH


# ══════════════════════════════════════════════════════════════════════════════
# DBAdapter — Unified connection wrapper for SQLite & PostgreSQL
# ══════════════════════════════════════════════════════════════════════════════

class DBAdapter:
    """Wraps a raw sqlite3/psycopg2 connection with a unified interface."""

    def __init__(self, raw_conn, backend: str):
        self._conn = raw_conn
        self.backend = backend
        if backend == "postgres":
            import psycopg2.extras
            self._dict_cursor = psycopg2.extras.RealDictCursor
        else:
            self._dict_cursor = None

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _adapt(self, sql: str) -> str:
        """Convert ? placeholders to %s for PostgreSQL."""
        if self.backend == "postgres":
            return sql.replace("?", "%s")
        return sql

    def _cursor(self):
        if self.backend == "postgres":
            return self._conn.cursor(cursor_factory=self._dict_cursor)
        # SQLite: conn.execute() returns a cursor directly; use raw conn here
        return None

    # ── Public interface ──────────────────────────────────────────────────────

    def execute(self, sql: str, params=()):
        """Execute SQL and return a cursor/result object."""
        sql = self._adapt(sql)
        if self.backend == "sqlite":
            return self._conn.execute(sql, params)
        else:
            cur = self._conn.cursor(cursor_factory=self._dict_cursor)
            cur.execute(sql, params)
            return cur

    def executemany(self, sql: str, param_list):
        sql = self._adapt(sql)
        if self.backend == "sqlite":
            self._conn.executemany(sql, param_list)
        else:
            cur = self._conn.cursor()
            cur.executemany(sql, param_list)

    def executescript(self, script: str):
        """Execute multiple SQL statements (DDL migration scripts)."""
        if self.backend == "sqlite":
            self._conn.executescript(script)
        else:
            # Convert SQLite DDL syntax to PostgreSQL
            pg_script = _sqlite_ddl_to_pg(script)
            cur = self._conn.cursor()
            for stmt in _split_statements(pg_script):
                try:
                    cur.execute(stmt)
                except Exception as e:
                    if "already exists" not in str(e).lower():
                        raise

    def insert(self, sql: str, params=()) -> int:
        """Execute an INSERT and return the new row's ID."""
        sql = self._adapt(sql)
        if self.backend == "sqlite":
            self._conn.execute(sql, params)
            return self._conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        else:
            cur = self._conn.cursor(cursor_factory=self._dict_cursor)
            cur.execute(sql + " RETURNING id", params)
            row = cur.fetchone()
            return row["id"] if row else None

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        self._conn.close()


# ══════════════════════════════════════════════════════════════════════════════
# Connection factory
# ══════════════════════════════════════════════════════════════════════════════

def _make_raw_conn():
    """Return a raw DB connection based on the configured backend, with SQLite fallback if PG is unreachable."""
    if DB_BACKEND == "sqlite":
        conn = sqlite3.connect(SQLITE_PATH, timeout=30, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA busy_timeout = 5000")
        return conn, "sqlite"
    else:
        import psycopg2
        try:
            conn = psycopg2.connect(DATABASE_URL, connect_timeout=5)
            conn.autocommit = False
            return conn, "postgres"
        except Exception as e:
            print(f"[WARN] PostgreSQL connection failed ({e}). Falling back to SQLite: {SQLITE_PATH}")
            conn = sqlite3.connect(SQLITE_PATH, timeout=30, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("PRAGMA busy_timeout = 5000")
            return conn, "sqlite"


@contextmanager
def get_db():
    """Context manager that yields a DBAdapter with auto-commit / rollback."""
    raw, active_backend = _make_raw_conn()
    conn = DBAdapter(raw, active_backend)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ══════════════════════════════════════════════════════════════════════════════
# DDL conversion helpers (SQLite → PostgreSQL)
# ══════════════════════════════════════════════════════════════════════════════

def _split_statements(sql: str):
    """Split SQL by semicolons, ignoring empty statements."""
    return [s.strip() for s in sql.split(";") if s.strip()]


def _sqlite_ddl_to_pg(sql: str) -> str:
    """Best-effort conversion of SQLite CREATE TABLE DDL to PostgreSQL."""
    # AUTOINCREMENT → SERIAL
    sql = re.sub(
        r"\bINTEGER\s+PRIMARY\s+KEY\s+AUTOINCREMENT\b",
        "SERIAL PRIMARY KEY",
        sql, flags=re.IGNORECASE
    )
    # datetime('now') → NOW()
    sql = re.sub(r"datetime\('now'\)", "NOW()", sql, flags=re.IGNORECASE)
    # TEXT DEFAULT (NOW()) → TEXT DEFAULT (NOW()::TEXT)
    sql = re.sub(r"TEXT\s+DEFAULT\s+\(NOW\(\)\)", "TEXT DEFAULT (NOW()::TEXT)", sql, flags=re.IGNORECASE)
    return sql


# ══════════════════════════════════════════════════════════════════════════════
# Auth helpers
# ══════════════════════════════════════════════════════════════════════════════

def hash_password(pw: str) -> str:
    salt = secrets.token_hex(16)
    h = hashlib.sha256((salt + pw).encode()).hexdigest()
    return f"{salt}:{h}"


def check_password(stored: str, pw: str) -> bool:
    try:
        salt, h = stored.split(":", 1)
        return hashlib.sha256((salt + pw).encode()).hexdigest() == h
    except Exception:
        return False


# ══════════════════════════════════════════════════════════════════════════════
# Schema: SQLite DDL (source of truth; auto-converted for PostgreSQL)
# ══════════════════════════════════════════════════════════════════════════════

_SCHEMA_SQL = """
-- ── Institutions ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS institution (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    name              TEXT NOT NULL,
    code              TEXT UNIQUE NOT NULL,
    address           TEXT,
    email             TEXT,
    phone             TEXT,
    logo_text         TEXT DEFAULT '',
    logo_url          TEXT DEFAULT '',
    institution_type  TEXT DEFAULT 'college',
    created_at        TEXT DEFAULT (datetime('now'))
);

-- ── Departments ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS department (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    institution_id  INTEGER NOT NULL REFERENCES institution(id) ON DELETE CASCADE,
    code            TEXT NOT NULL,
    name            TEXT NOT NULL,
    category        TEXT DEFAULT 'core', -- 'basic_science' / 'core' / 'general' / 'allied'
    created_at      TEXT DEFAULT (datetime('now')),
    UNIQUE(institution_id, code)
);

-- ── Users ─────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    institution_id  INTEGER NOT NULL REFERENCES institution(id) ON DELETE CASCADE,
    username        TEXT NOT NULL,
    email           TEXT,
    password_hash   TEXT NOT NULL,
    role            TEXT DEFAULT 'admin',
    created_at      TEXT DEFAULT (datetime('now')),
    UNIQUE(institution_id, username)
);

-- ── Time Configuration ────────────────────────────────────────
CREATE TABLE IF NOT EXISTS time_config (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    institution_id  INTEGER UNIQUE NOT NULL REFERENCES institution(id) ON DELETE CASCADE,
    periods_per_day INTEGER DEFAULT 6,
    working_days    TEXT DEFAULT 'Mon,Tue,Wed,Thu,Fri',
    updated_at      TEXT DEFAULT (datetime('now'))
);

-- ── Period Slots ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS period_slot (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    institution_id  INTEGER NOT NULL REFERENCES institution(id) ON DELETE CASCADE,
    slot_order      INTEGER NOT NULL,
    label           TEXT NOT NULL,
    start_time      TEXT NOT NULL,
    end_time        TEXT NOT NULL,
    slot_type       TEXT DEFAULT 'period',
    UNIQUE(institution_id, slot_order)
);

-- ── Rooms ─────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS rooms (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    institution_id  INTEGER NOT NULL REFERENCES institution(id) ON DELETE CASCADE,
    name            TEXT NOT NULL,
    capacity        INTEGER DEFAULT 60,
    room_type       TEXT DEFAULT 'classroom',
    created_at      TEXT DEFAULT (datetime('now')),
    UNIQUE(institution_id, name)
);

-- ── Staff ─────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS staff (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    institution_id       INTEGER NOT NULL REFERENCES institution(id) ON DELETE CASCADE,
    name                 TEXT NOT NULL,
    department           TEXT NOT NULL,
    experience           INTEGER DEFAULT 0,
    max_periods_per_week INTEGER DEFAULT 20,
    max_periods_per_day  INTEGER DEFAULT 4,
    allocated_periods    INTEGER DEFAULT 0,
    email                TEXT,
    available_days       TEXT DEFAULT 'Mon,Tue,Wed,Thu,Fri',
    created_at           TEXT DEFAULT (datetime('now'))
);

-- ── Subjects ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS subject (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    institution_id   INTEGER NOT NULL REFERENCES institution(id) ON DELETE CASCADE,
    subject_name     TEXT NOT NULL,
    subject_code     TEXT,
    abbreviation     TEXT,
    department       TEXT NOT NULL,
    periods_per_week INTEGER DEFAULT 3,
    difficulty_level INTEGER DEFAULT 3,
    is_lab           INTEGER DEFAULT 0,
    lab_duration     INTEGER DEFAULT 2,
    created_at       TEXT DEFAULT (datetime('now'))
);

-- ── Staff ↔ Subjects ──────────────────────────────────────────
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
    venue           TEXT DEFAULT '',
    academic_year   TEXT DEFAULT '2026-27',
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
    room_id         INTEGER REFERENCES rooms(id) ON DELETE SET NULL,
    is_manual_edit  INTEGER DEFAULT 0,
    created_at      TEXT DEFAULT (datetime('now'))
);

-- ── Conflict Log ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS conflict_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    institution_id  INTEGER NOT NULL REFERENCES institution(id) ON DELETE CASCADE,
    timetable_id    INTEGER REFERENCES timetable(id) ON DELETE CASCADE,
    class_name      TEXT,
    subject_name    TEXT,
    day             TEXT,
    period          INTEGER,
    reason          TEXT,
    suggested_action TEXT,
    created_at      TEXT DEFAULT (datetime('now'))
);

-- ── Allocation History ────────────────────────────────────────
CREATE TABLE IF NOT EXISTS allocation_history (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    institution_id  INTEGER NOT NULL REFERENCES institution(id) ON DELETE CASCADE,
    staff_id        INTEGER REFERENCES staff(id) ON DELETE CASCADE,
    subject_id      INTEGER REFERENCES subject(id) ON DELETE CASCADE,
    timetable_id    INTEGER REFERENCES timetable(id) ON DELETE CASCADE,
    periods_count   INTEGER DEFAULT 0,
    allocation_date TEXT DEFAULT (datetime('now'))
);
"""

def generate_abbreviation(name: str, is_lab: bool = False) -> str:
    """Auto-generate institutional course abbreviation e.g. Data Structures -> DS, Deep Learning Lab -> DL LAB."""
    if not name:
        return ""
    words = re.findall(r'[A-Za-z0-9]+', name)
    if not words:
        return name[:4].upper()
    lab_detected = is_lab or words[-1].lower() in ("lab", "laboratory")
    core_words = words[:-1] if lab_detected and len(words) > 1 and words[-1].lower() in ("lab", "laboratory") else words

    stop_words = {"and", "of", "the", "in", "for", "to", "on", "with", "a", "an"}
    filtered = [w for w in core_words if w.lower() not in stop_words]
    if not filtered:
        filtered = core_words

    if len(filtered) == 1:
        abbr = filtered[0][:4].upper()
    else:
        abbr = "".join(w[0].upper() for w in filtered)[:5]

    if lab_detected and not abbr.endswith("LAB"):
        abbr = f"{abbr} LAB"
    return abbr


# SQLite migration: add new columns to existing tables if they don't exist
_MIGRATION_SQL_SQLITE = [
    "ALTER TABLE staff ADD COLUMN max_periods_per_day INTEGER DEFAULT 4",
    "ALTER TABLE timetable_slot ADD COLUMN room_id INTEGER REFERENCES rooms(id) ON DELETE SET NULL",
    "ALTER TABLE subject ADD COLUMN abbreviation TEXT",
    "ALTER TABLE institution ADD COLUMN logo_url TEXT DEFAULT ''",
    "ALTER TABLE institution ADD COLUMN institution_type TEXT DEFAULT 'college'",
    "ALTER TABLE class_section ADD COLUMN venue TEXT DEFAULT ''",
    "ALTER TABLE class_section ADD COLUMN academic_year TEXT DEFAULT '2026-27'",
]

# PostgreSQL migration (same intent, PostgreSQL syntax)
_MIGRATION_SQL_PG = [
    "ALTER TABLE staff ADD COLUMN IF NOT EXISTS max_periods_per_day INTEGER DEFAULT 4",
    "ALTER TABLE timetable_slot ADD COLUMN IF NOT EXISTS room_id INTEGER REFERENCES rooms(id) ON DELETE SET NULL",
    "ALTER TABLE subject ADD COLUMN IF NOT EXISTS abbreviation TEXT",
    "ALTER TABLE institution ADD COLUMN IF NOT EXISTS logo_url TEXT DEFAULT ''",
    "ALTER TABLE institution ADD COLUMN IF NOT EXISTS institution_type TEXT DEFAULT 'college'",
    "ALTER TABLE class_section ADD COLUMN IF NOT EXISTS venue TEXT DEFAULT ''",
    "ALTER TABLE class_section ADD COLUMN IF NOT EXISTS academic_year TEXT DEFAULT '2026-27'",
]


def init_db():
    """Create all tables, run migrations, ensure default abbreviations and departments exist."""
    with get_db() as conn:
        conn.executescript(_SCHEMA_SQL)

        # Run migrations (use conn.backend to handle SQLite fallback properly)
        migrations = _MIGRATION_SQL_PG if conn.backend == "postgres" else _MIGRATION_SQL_SQLITE
        for stmt in migrations:
            try:
                conn.execute(stmt)
            except Exception:
                pass  # Column already exists — safe to ignore

        # Auto-fill empty abbreviations for subjects
        try:
            rows = conn.execute("SELECT id, subject_name, is_lab, abbreviation FROM subject").fetchall()
            for r in rows:
                if not r["abbreviation"]:
                    auto_abbr = generate_abbreviation(r["subject_name"], bool(r["is_lab"]))
                    conn.execute("UPDATE subject SET abbreviation=? WHERE id=?", (auto_abbr, r["id"]))
        except Exception:
            pass

        # Seed default departments for institutions if none exist
        try:
            institutions = conn.execute("SELECT id, COALESCE(institution_type, 'college') as itype FROM institution").fetchall()
            for inst in institutions:
                iid = inst["id"]
                itype = inst["itype"]
                if not conn.execute("SELECT 1 FROM department WHERE institution_id=?", (iid,)).fetchone():
                    if itype == "school":
                        default_depts = [
                            ("LANG", "Languages & English", "general"),
                            ("MATH", "Mathematics", "general"),
                            ("SCI", "General Science", "basic_science"),
                            ("SOC", "Social Sciences", "general"),
                            ("CS", "Computer Science", "core"),
                            ("PE", "Physical Education & Arts", "allied"),
                        ]
                    else:
                        default_depts = [
                            ("S&H", "Basic Sciences & Humanities", "basic_science"),
                            ("CSE", "Computer Science & Engineering", "core"),
                            ("ECE", "Electronics & Communication", "core"),
                            ("MECH", "Mechanical Engineering", "core"),
                            ("CIVIL", "Civil Engineering", "core"),
                            ("IT", "Information Technology", "core"),
                            ("AIDS", "AI & Data Science", "core"),
                        ]
                    for code, dname, cat in default_depts:
                        conn.execute(
                            "INSERT OR IGNORE INTO department (institution_id, code, name, category) VALUES (?,?,?,?)",
                            (iid, code, dname, cat)
                        )
        except Exception:
            pass

    print(f"[OK] Database schema ready ({DB_BACKEND}).")


# ══════════════════════════════════════════════════════════════════════════════
# Demo data seeder
# ══════════════════════════════════════════════════════════════════════════════

def seed_demo_institution():
    """Seed a demo institution with sample staff, subjects, and classes."""
    with get_db() as conn:
        if conn.execute("SELECT 1 FROM institution LIMIT 1").fetchone():
            return  # Already seeded

        # Institution
        inst_id = conn.insert(
            "INSERT INTO institution (name, code, address, email, logo_text) VALUES (?,?,?,?,?)",
            ("LK's Project", "DEMO2024",
             "123 College Road, Tech City", "admin@lksproject.edu", "🎓")
        )

        # Admin user
        conn.insert(
            "INSERT INTO users (institution_id, username, email, password_hash, role) VALUES (?,?,?,?,?)",
            (inst_id, "admin", "admin@democollege.edu", hash_password("admin123"), "admin")
        )

        # Time config
        conn.insert(
            "INSERT INTO time_config (institution_id, periods_per_day, working_days) VALUES (?,?,?)",
            (inst_id, 6, "Mon,Tue,Wed,Thu,Fri")
        )

        # Period slots
        slots = [
            (1, "Period 1", "09:00", "09:50", "period"),
            (2, "Period 2", "09:50", "10:40", "period"),
            (3, "Break",    "10:40", "11:00", "break"),
            (4, "Period 3", "11:00", "11:50", "period"),
            (5, "Period 4", "11:50", "12:40", "period"),
            (6, "Lunch",    "12:40", "13:20", "lunch"),
            (7, "Period 5", "13:20", "14:10", "period"),
            (8, "Period 6", "14:10", "15:00", "period"),
        ]
        for s in slots:
            conn.execute(
                "INSERT INTO period_slot (institution_id, slot_order, label, start_time, end_time, slot_type) VALUES (?,?,?,?,?,?)",
                (inst_id,) + s
            )

        # Rooms
        for rname, rtype, cap in [
            ("CSE Lab 1", "lab", 40), ("CSE Lab 2", "lab", 40),
            ("ECE Lab",   "lab", 30), ("Room 101",  "classroom", 60),
            ("Room 102",  "classroom", 60), ("Room 201", "classroom", 60),
        ]:
            conn.execute(
                "INSERT INTO rooms (institution_id, name, capacity, room_type) VALUES (?,?,?,?)",
                (inst_id, rname, cap, rtype)
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
                "INSERT INTO subject (institution_id,subject_name,subject_code,department,"
                "periods_per_week,difficulty_level,is_lab,lab_duration) VALUES (?,?,?,?,?,?,?,?)",
                (inst_id,) + row
            )

        def sid(code):
            r = conn.execute(
                "SELECT id FROM subject WHERE subject_code=? AND institution_id=?",
                (code, inst_id)
            ).fetchone()
            return r["id"] if r else None

        # Staff
        staff_data = [
            ("Dr. Rajesh Kumar",   "CSE",    12, 18, 3),
            ("Prof. Priya Sharma", "CSE",    8,  16, 3),
            ("Mr. Arun Nair",      "CSE",    5,  20, 4),
            ("Dr. Meera Pillai",   "ECE",    10, 18, 3),
            ("Prof. Suresh Babu",  "ECE",    7,  16, 4),
            ("Dr. Anita Roy",      "COMMON", 15, 20, 4),
        ]
        for name, dept, exp, max_w, max_d in staff_data:
            conn.execute(
                "INSERT INTO staff (institution_id,name,department,experience,"
                "max_periods_per_week,max_periods_per_day,available_days) VALUES (?,?,?,?,?,?,?)",
                (inst_id, name, dept, exp, max_w, max_d, "Mon,Tue,Wed,Thu,Fri")
            )

        def stid(name_part):
            r = conn.execute(
                "SELECT id FROM staff WHERE name LIKE ? AND institution_id=?",
                (f"%{name_part}%", inst_id)
            ).fetchone()
            return r["id"] if r else None

        # Staff ↔ Subjects
        assignments = [
            ("Rajesh",  ["DS101", "AL102", "CN401"]),
            ("Priya",   ["DS101", "DB201", "ML501"]),
            ("Arun",    ["AL102", "OSL301", "DB201"]),
            ("Meera",   ["CT101", "SS201", "EL301"]),
            ("Suresh",  ["DE101", "SS201", "EL301"]),
            ("Anita",   ["MA101", "PH101"]),
        ]
        for name_part, codes in assignments:
            st_id = stid(name_part)
            if not st_id:
                continue
            for code in codes:
                s_id = sid(code)
                if s_id:
                    conn.execute(
                        "INSERT OR IGNORE INTO staff_subjects VALUES (?,?)",
                        (st_id, s_id)
                    )

        # Classes
        for cname, dept, sem in [
            ("CS-A", "CSE", 3), ("CS-B", "CSE", 3),
            ("EC-A", "ECE", 3),
        ]:
            class_id = conn.insert(
                "INSERT INTO class_section (institution_id,name,department,semester,strength) VALUES (?,?,?,?,?)",
                (inst_id, cname, dept, sem, 60)
            )
            if dept == "CSE":
                codes = ["DS101", "AL102", "DB201", "OSL301", "CN401"]
            else:
                codes = ["CT101", "SS201", "EL301", "DE101", "MA101"]
            for code in codes:
                s_id = sid(code)
                if s_id:
                    conn.execute(
                        "INSERT OR IGNORE INTO class_subjects VALUES (?,?)",
                        (class_id, s_id)
                    )

    print("[OK] Demo institution seeded.")


def seed_realtime_model(institution_id: int, model_type: str = "college"):
    """
    Seeds a rich, production-grade real-world model for Colleges or Schools.
    Engineered with realistic department structures, shared faculty (e.g. S&H / Language),
    hands-on lab consecutive blocks, and zero timetable conflicts.
    """
    with get_db() as conn:
        # Update institution type
        conn.execute("UPDATE institution SET institution_type=? WHERE id=?", (model_type, institution_id))

        # Clear existing schedule and relational academic data for this institution
        conn.execute("DELETE FROM conflict_log WHERE institution_id=?", (institution_id,))
        conn.execute("DELETE FROM allocation_history WHERE institution_id=?", (institution_id,))
        conn.execute("DELETE FROM timetable_slot WHERE institution_id=?", (institution_id,))
        conn.execute("DELETE FROM timetable WHERE institution_id=?", (institution_id,))
        conn.execute(
            "DELETE FROM class_subjects WHERE class_id IN (SELECT id FROM class_section WHERE institution_id=?)",
            (institution_id,)
        )
        conn.execute("DELETE FROM class_section WHERE institution_id=?", (institution_id,))
        conn.execute(
            "DELETE FROM staff_subjects WHERE staff_id IN (SELECT id FROM staff WHERE institution_id=?)",
            (institution_id,)
        )
        conn.execute("DELETE FROM staff WHERE institution_id=?", (institution_id,))
        conn.execute("DELETE FROM subject WHERE institution_id=?", (institution_id,))
        conn.execute("DELETE FROM rooms WHERE institution_id=?", (institution_id,))
        conn.execute("DELETE FROM department WHERE institution_id=?", (institution_id,))

        def sid(code):
            r = conn.execute(
                "SELECT id FROM subject WHERE subject_code=? AND institution_id=?",
                (code, institution_id)
            ).fetchone()
            return r["id"] if r else None

        def stid(name_part):
            r = conn.execute(
                "SELECT id FROM staff WHERE name LIKE ? AND institution_id=?",
                (f"%{name_part}%", institution_id)
            ).fetchone()
            return r["id"] if r else None

        if model_type == "school":
            # ══════════════════════════════════════════════════════════
            # K-12 SCHOOL PRODUCTION MODEL
            # ══════════════════════════════════════════════════════════
            depts = [
                ("LANG", "Languages & Literature", "general"),
                ("MATH", "Mathematics", "general"),
                ("SCI", "General & Applied Sciences", "basic_science"),
                ("SOC", "Social Studies & History", "general"),
                ("CS", "Computer Science & ICT", "core"),
                ("PE", "Physical Education & Arts", "allied"),
            ]
            for code, dname, cat in depts:
                conn.execute(
                    "INSERT INTO department (institution_id, code, name, category) VALUES (?,?,?,?)",
                    (institution_id, code, dname, cat)
                )

            rooms = [
                ("School Science Lab", "lab", 40),
                ("Junior Computer Lab", "lab", 40),
                ("Sports Ground & Gym", "lab", 60),
                ("Classroom 6-A", "classroom", 40),
                ("Classroom 7-A", "classroom", 40),
                ("Classroom 8-A", "classroom", 40),
                ("Classroom 9-A", "classroom", 40),
                ("Classroom 10-A", "classroom", 40),
            ]
            for rname, rtype, cap in rooms:
                conn.execute(
                    "INSERT INTO rooms (institution_id, name, capacity, room_type) VALUES (?,?,?,?)",
                    (institution_id, rname, cap, rtype)
                )

            # Subjects
            school_subjects = [
                ("English Literature", "ENG101", "ENG", "LANG", 4, 3, 0, 1),
                ("Mathematics", "MTH101", "MATH", "MATH", 4, 4, 0, 1),
                ("General Science", "SCI101", "SCI", "SCI", 4, 3, 0, 1),
                ("Science Practical Lab", "SCILAB", "S-LAB", "SCI", 2, 3, 1, 2),
                ("Social Studies", "SOC101", "SOC", "SOC", 3, 2, 0, 1),
                ("Computer Coding", "CS101", "CS", "CS", 2, 3, 0, 1),
                ("Physical Education & Sports", "PE101", "PET", "PE", 2, 1, 1, 2),
                ("Visual Arts & Craft", "ART101", "ART", "PE", 1, 1, 0, 1),
            ]
            for sname, scode, abbr, dept, pw, diff, is_lab, ldur in school_subjects:
                conn.execute(
                    "INSERT INTO subject (institution_id, subject_name, subject_code, abbreviation, "
                    "department, periods_per_week, difficulty_level, is_lab, lab_duration) "
                    "VALUES (?,?,?,?,?,?,?,?,?)",
                    (institution_id, sname, scode, abbr, dept, pw, diff, is_lab, ldur)
                )

            # Staff
            school_staff = [
                ("Mrs. Sunita Sharma", "LANG", 12, 20, 4, "Mon,Tue,Wed,Thu,Fri", ["ENG101"]),
                ("Ms. Radhika Nair", "LANG", 8, 18, 4, "Mon,Tue,Wed,Thu,Fri", ["ENG101"]),
                ("Mr. Rajesh Gupta", "MATH", 15, 20, 4, "Mon,Tue,Wed,Thu,Fri", ["MTH101"]),
                ("Mr. Manoj Kumar", "MATH", 7, 18, 4, "Mon,Tue,Wed,Thu,Fri", ["MTH101"]),
                ("Mrs. Ananya Sen", "SCI", 11, 20, 4, "Mon,Tue,Wed,Thu,Fri", ["SCI101", "SCILAB"]),
                ("Dr. Sanjay Bose", "SCI", 14, 20, 4, "Mon,Tue,Wed,Thu,Fri", ["SCI101", "SCILAB"]),
                ("Mr. David Paul", "SOC", 9, 20, 4, "Mon,Tue,Wed,Thu,Fri", ["SOC101"]),
                ("Ms. Neha Kapoor", "CS", 6, 18, 4, "Mon,Tue,Wed,Thu,Fri", ["CS101"]),
                ("Coach Victor Singh", "PE", 12, 20, 4, "Mon,Tue,Wed,Thu,Fri", ["PE101"]),
                ("Mrs. Clara D'Souza", "PE", 8, 16, 4, "Mon,Tue,Wed,Thu,Fri", ["ART101"]),
            ]
            for sname, sdept, exp, max_w, max_d, av, codes in school_staff:
                st_id = conn.insert(
                    "INSERT INTO staff (institution_id, name, department, experience, "
                    "max_periods_per_week, max_periods_per_day, available_days) VALUES (?,?,?,?,?,?,?)",
                    (institution_id, sname, sdept, exp, max_w, max_d, av)
                )
                for code in codes:
                    s_id = sid(code)
                    if s_id:
                        conn.execute("INSERT OR IGNORE INTO staff_subjects VALUES (?,?)", (st_id, s_id))

            # Classes: Grade 6 to Grade 10
            class_names = ["Grade 6-A", "Grade 7-A", "Grade 8-A", "Grade 9-A", "Grade 10-A"]
            for cname in class_names:
                cls_id = conn.insert(
                    "INSERT INTO class_section (institution_id, name, department, semester, strength) "
                    "VALUES (?,?,?,?,?)",
                    (institution_id, cname, "General", 1, 35)
                )
                # All 8 subjects enrolled for each grade (Total 22 periods per week)
                for code in ["ENG101", "MTH101", "SCI101", "SCILAB", "SOC101", "CS101", "PE101", "ART101"]:
                    s_id = sid(code)
                    if s_id:
                        conn.execute("INSERT OR IGNORE INTO class_subjects VALUES (?,?)", (cls_id, s_id))

        else:
            # ══════════════════════════════════════════════════════════
            # REAL-TIME COLLEGE & ENGINEERING PRODUCTION MODEL
            # Features multi-department architecture:
            # S&H (Basic Sciences), CSE, ECE, MECH, CIVIL, IT, AIDS
            # with cross-department shared faculty (Maths, Physics, English)
            # ══════════════════════════════════════════════════════════
            depts = [
                ("S&H", "Basic Sciences & Humanities", "basic_science"),
                ("CSE", "Computer Science & Engineering", "core"),
                ("ECE", "Electronics & Communication", "core"),
                ("MECH", "Mechanical Engineering", "core"),
                ("CIVIL", "Civil Engineering", "core"),
                ("IT", "Information Technology", "core"),
                ("AIDS", "AI & Data Science", "core"),
            ]
            for code, dname, cat in depts:
                conn.execute(
                    "INSERT INTO department (institution_id, code, name, category) VALUES (?,?,?,?)",
                    (institution_id, code, dname, cat)
                )

            rooms = [
                ("Deep Learning & AI Lab", "lab", 60),
                ("Big Data & Cloud Lab", "lab", 60),
                ("Cyber Security & Networks Lab", "lab", 60),
                ("DSP & VLSI Design Lab", "lab", 60),
                ("Embedded Systems & IoT Lab", "lab", 60),
                ("Thermal & Fluid Machinery Lab", "lab", 60),
                ("CAD/CAM & Metrology Lab", "lab", 60),
                ("Central Digital Library", "library", 100),
                ("Room 101", "classroom", 60),
                ("Room 102", "classroom", 60),
                ("Room 201", "classroom", 60),
                ("Room 202", "classroom", 60),
                ("Room 301", "classroom", 60),
            ]
            for rname, rtype, cap in rooms:
                conn.execute(
                    "INSERT INTO rooms (institution_id, name, capacity, room_type) VALUES (?,?,?,?)",
                    (institution_id, rname, cap, rtype)
                )

            # ══════════════════════════════════════════════════════════
            # SUBJECTS: 7 Theory Courses, 4 Laboratories, 1 MM, 1 Library
            # Fits standard 30-period academic week (5 days × 6 periods or 8 periods)
            # ══════════════════════════════════════════════════════════
            college_subjects = [
                # ── Shared Common Course across Engineering Branches ──
                ("Disaster Risk Reduction and Management", "DRRM101", "DRRM", "S&H", 2, 2, 0, 1),

                # ── CSE Department (Exact Curriculum from Image 1) ────
                # Theory Courses (7)
                ("Deep Learning", "DL401", "DL", "CSE", 3, 5, 0, 1),
                ("Data and Information Security", "DIS401", "DIS", "CSE", 3, 4, 0, 1),
                ("Distributed Computing", "DC401", "DC", "CSE", 3, 4, 0, 1),
                ("Big Data Analytics", "BDA401", "BDA", "CSE", 3, 4, 0, 1),
                ("Cloud Computing", "CC401", "CC", "CSE", 3, 4, 0, 1),
                ("Cyber Security", "CS401", "CSEC", "CSE", 3, 4, 0, 1),
                # Laboratory Courses (4, consecutive 2-period hands-on blocks)
                ("Deep Learning Laboratory", "DLLAB", "DL-LAB", "CSE", 2, 4, 1, 2),
                ("Big Data Analytics Laboratory", "BDALAB", "BDA-LAB", "CSE", 2, 3, 1, 2),
                ("Cloud Computing Laboratory", "CCLAB", "CC-LAB", "CSE", 2, 3, 1, 2),
                ("Cyber Security Laboratory", "CSLAB", "CSEC-LAB", "CSE", 2, 3, 1, 2),
                # Mentoring & Self-Study
                ("Mentor Meeting", "MM_CSE", "MM", "CSE", 1, 1, 0, 1),
                ("Library", "LIB_CSE", "LIB", "CSE", 1, 1, 0, 1),

                # ── ECE Department (7 Theory, 4 Labs, 1 MM, 1 Library) ──
                # Theory Courses (7)
                ("Digital Signal Processing", "DSP301", "DSP", "ECE", 3, 5, 0, 1),
                ("VLSI Design", "VLSI301", "VLSI", "ECE", 3, 5, 0, 1),
                ("Embedded Systems & IoT", "EMB301", "EMB", "ECE", 3, 4, 0, 1),
                ("Wireless Communication", "WC301", "WC", "ECE", 3, 4, 0, 1),
                ("Optical Communication", "OC301", "OC", "ECE", 3, 4, 0, 1),
                ("Microwave & Radar Engineering", "MRE301", "MRE", "ECE", 3, 4, 0, 1),
                # Laboratory Courses (4)
                ("Digital Signal Processing Lab", "DSPLAB", "DSP-LAB", "ECE", 2, 4, 1, 2),
                ("VLSI Design Laboratory", "VLSILAB", "VLSI-LAB", "ECE", 2, 4, 1, 2),
                ("Embedded Systems & IoT Lab", "EMBLAB", "EMB-LAB", "ECE", 2, 3, 1, 2),
                ("Microwave & Optical Lab", "MROLAB", "MRO-LAB", "ECE", 2, 3, 1, 2),
                # Mentoring & Self-Study
                ("Mentor Meeting", "MM_ECE", "MM", "ECE", 1, 1, 0, 1),
                ("Library", "LIB_ECE", "LIB", "ECE", 1, 1, 0, 1),

                # ── MECH Department (7 Theory, 4 Labs, 1 MM, 1 Library) ─
                # Theory Courses (7)
                ("Heat and Mass Transfer", "HMT301", "HMT", "MECH", 3, 5, 0, 1),
                ("Design of Transmission Systems", "DTS301", "DTS", "MECH", 3, 5, 0, 1),
                ("Finite Element Analysis", "FEA301", "FEA", "MECH", 3, 4, 0, 1),
                ("Computer Integrated Manufacturing", "CIM301", "CIM", "MECH", 3, 4, 0, 1),
                ("Automobile Engineering", "AUTO301", "AUTO", "MECH", 3, 4, 0, 1),
                ("Power Plant Engineering", "PPE301", "PPE", "MECH", 3, 4, 0, 1),
                # Laboratory Courses (4)
                ("Heat Transfer Laboratory", "HMTLAB", "HMT-LAB", "MECH", 2, 4, 1, 2),
                ("CAD / CAM & FEA Laboratory", "CADLAB", "CAD-LAB", "MECH", 2, 4, 1, 2),
                ("Dynamics & Metrology Laboratory", "DYNLAB", "DYN-LAB", "MECH", 2, 3, 1, 2),
                ("Mechatronics & Automation Lab", "MTRLAB", "MTR-LAB", "MECH", 2, 3, 1, 2),
                # Mentoring & Self-Study
                ("Mentor Meeting", "MM_MECH", "MM", "MECH", 1, 1, 0, 1),
                ("Library", "LIB_MECH", "LIB", "MECH", 1, 1, 0, 1),
            ]
            for sname, scode, abbr, dept, pw, diff, is_lab, ldur in college_subjects:
                conn.execute(
                    "INSERT INTO subject (institution_id, subject_name, subject_code, abbreviation, "
                    "department, periods_per_week, difficulty_level, is_lab, lab_duration) "
                    "VALUES (?,?,?,?,?,?,?,?,?)",
                    (institution_id, sname, scode, abbr, dept, pw, diff, is_lab, ldur)
                )

            # ══════════════════════════════════════════════════════════
            # STAFF: Theory Teacher ALSO Takes Corresponding Lab!
            # ══════════════════════════════════════════════════════════
            college_staff = [
                # Shared Interdisciplinary Faculty & Library Incharge
                ("Dr. Anita Roy", "S&H", 16, 22, 4, "Mon,Tue,Wed,Thu,Fri", ["DRRM101"]),
                ("Mrs. Meenakshi S", "S&H", 10, 16, 4, "Mon,Tue,Wed,Thu,Fri", ["LIB_CSE", "LIB_ECE", "LIB_MECH"]),

                # ── CSE Faculty (Theory Teacher Takes Corresponding Lab) ──
                ("Dr. Arun Kumar", "CSE", 15, 22, 4, "Mon,Tue,Wed,Thu,Fri", ["DL401", "DLLAB"]),       # DL Theory + Lab
                ("Dr. Priya Sharma", "CSE", 13, 22, 4, "Mon,Tue,Wed,Thu,Fri", ["BDA401", "BDALAB"]),   # BDA Theory + Lab
                ("Dr. Ravi Verma", "CSE", 12, 22, 4, "Mon,Tue,Wed,Thu,Fri", ["CC401", "CCLAB"]),       # CC Theory + Lab
                ("Ms. Kavitha Nair", "CSE", 9, 22, 4, "Mon,Tue,Wed,Thu,Fri", ["CS401", "CSLAB"]),      # CSEC Theory + Lab
                ("Dr. Karthik Raman", "CSE", 11, 20, 4, "Mon,Tue,Wed,Thu,Fri", ["DIS401"]),            # DIS Theory
                ("Prof. Rajesh Gupta", "CSE", 10, 20, 4, "Mon,Tue,Wed,Thu,Fri", ["DC401"]),            # DC Theory
                ("Prof. K. Rajan", "CSE", 14, 12, 3, "Mon,Tue,Wed,Thu,Fri", ["MM_CSE"]),               # CSE Class Mentor

                # ── ECE Faculty (Theory Teacher Takes Corresponding Lab) ──
                ("Dr. M. Soundararajan", "ECE", 16, 22, 4, "Mon,Tue,Wed,Thu,Fri", ["DSP301", "DSPLAB"]),    # DSP Theory + Lab
                ("Dr. Preethi Vijay", "ECE", 14, 22, 4, "Mon,Tue,Wed,Thu,Fri", ["VLSI301", "VLSILAB"]),     # VLSI Theory + Lab
                ("Prof. Naveen Chandar", "ECE", 11, 22, 4, "Mon,Tue,Wed,Thu,Fri", ["EMB301", "EMBLAB"]),    # EMB Theory + Lab
                ("Dr. Geetha Mohan", "ECE", 13, 22, 4, "Mon,Tue,Wed,Thu,Fri", ["MRE301", "MROLAB"]),        # MRE Theory + Lab
                ("Prof. Anandh Krishnan", "ECE", 10, 20, 4, "Mon,Tue,Wed,Thu,Fri", ["WC301"]),              # WC Theory
                ("Prof. Sneha Menon", "ECE", 8, 20, 4, "Mon,Tue,Wed,Thu,Fri", ["OC301"]),                   # OC Theory
                ("Prof. R. Vasudevan", "ECE", 12, 12, 3, "Mon,Tue,Wed,Thu,Fri", ["MM_ECE"]),                # ECE Class Mentor

                # ── MECH Faculty (Theory Teacher Takes Corresponding Lab) ─
                ("Dr. Vikram Seth", "MECH", 17, 22, 4, "Mon,Tue,Wed,Thu,Fri", ["HMT301", "HMTLAB"]),       # HMT Theory + Lab
                ("Prof. Anand Rao", "MECH", 12, 22, 4, "Mon,Tue,Wed,Thu,Fri", ["FEA301", "CADLAB"]),        # FEA Theory + Lab
                ("Dr. Balaji Govind", "MECH", 14, 22, 4, "Mon,Tue,Wed,Thu,Fri", ["DTS301", "DYNLAB"]),      # DTS Theory + Lab
                ("Prof. Vigneshwaran K", "MECH", 10, 22, 4, "Mon,Tue,Wed,Thu,Fri", ["CIM301", "MTRLAB"]),   # CIM Theory + Lab
                ("Prof. D. Murugan", "MECH", 9, 20, 4, "Mon,Tue,Wed,Thu,Fri", ["AUTO301"]),                 # AUTO Theory
                ("Dr. S. Saravanan", "MECH", 11, 20, 4, "Mon,Tue,Wed,Thu,Fri", ["PPE301"]),                 # PPE Theory
                ("Prof. T. Selvam", "MECH", 13, 12, 3, "Mon,Tue,Wed,Thu,Fri", ["MM_MECH"]),                 # MECH Class Mentor
            ]
            for sname, sdept, exp, max_w, max_d, av, codes in college_staff:
                st_id = conn.insert(
                    "INSERT INTO staff (institution_id, name, department, experience, "
                    "max_periods_per_week, max_periods_per_day, available_days) VALUES (?,?,?,?,?,?,?)",
                    (institution_id, sname, sdept, exp, max_w, max_d, av)
                )
                for code in codes:
                    s_id = sid(code)
                    if s_id:
                        conn.execute("INSERT OR IGNORE INTO staff_subjects VALUES (?,?)", (st_id, s_id))

            # ══════════════════════════════════════════════════════════
            # CLASSES: Enrolled in 7 Theory + 4 Labs + 1 MM + 1 Library
            # ══════════════════════════════════════════════════════════
            classes_info = [
                ("CSE-A", "CSE", 7, [
                    "DL401", "DIS401", "DC401", "BDA401", "CC401", "CS401", "DRRM101",
                    "DLLAB", "BDALAB", "CCLAB", "CSLAB", "MM_CSE", "LIB_CSE"
                ]),
                ("CSE-B", "CSE", 7, [
                    "DL401", "DIS401", "DC401", "BDA401", "CC401", "CS401", "DRRM101",
                    "DLLAB", "BDALAB", "CCLAB", "CSLAB", "MM_CSE", "LIB_CSE"
                ]),
                ("ECE-A", "ECE", 6, [
                    "DSP301", "VLSI301", "EMB301", "WC301", "OC301", "MRE301", "DRRM101",
                    "DSPLAB", "VLSILAB", "EMBLAB", "MROLAB", "MM_ECE", "LIB_ECE"
                ]),
                ("ECE-B", "ECE", 6, [
                    "DSP301", "VLSI301", "EMB301", "WC301", "OC301", "MRE301", "DRRM101",
                    "DSPLAB", "VLSILAB", "EMBLAB", "MROLAB", "MM_ECE", "LIB_ECE"
                ]),
                ("MECH-A", "MECH", 6, [
                    "HMT301", "DTS301", "FEA301", "CIM301", "AUTO301", "PPE301", "DRRM101",
                    "HMTLAB", "CADLAB", "DYNLAB", "MTRLAB", "MM_MECH", "LIB_MECH"
                ]),
            ]
            for cname, cdept, sem, codes in classes_info:
                cls_id = conn.insert(
                    "INSERT INTO class_section (institution_id, name, department, semester, strength) "
                    "VALUES (?,?,?,?,?)",
                    (institution_id, cname, cdept, sem, 60)
                )
                for code in codes:
                    s_id = sid(code)
                    if s_id:
                        conn.execute("INSERT OR IGNORE INTO class_subjects VALUES (?,?)", (cls_id, s_id))

    print(f"[OK] Real-time {model_type} model seeded for institution #{institution_id}.")

