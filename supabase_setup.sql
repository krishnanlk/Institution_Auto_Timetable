-- ════════════════════════════════════════════════════════════════════
-- supabase_setup.sql
-- Run this entire file in your Supabase SQL Editor to set up the schema.
-- Steps:
--   1. Go to https://supabase.com → your project → SQL Editor
--   2. Paste this entire file
--   3. Click "Run"
--   4. Copy your connection string from Settings → Database → URI
--   5. Paste it as DATABASE_URL in your .env file
-- ════════════════════════════════════════════════════════════════════

-- ── Institutions ───────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS institution (
    id          SERIAL PRIMARY KEY,
    name        TEXT NOT NULL,
    code        TEXT UNIQUE NOT NULL,
    address     TEXT,
    email       TEXT,
    phone       TEXT,
    logo_text   TEXT DEFAULT '',
    logo_url    TEXT DEFAULT '',
    institution_type TEXT DEFAULT 'college',
    created_at  TEXT DEFAULT (NOW()::TEXT)
);

-- ── Users ──────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id              SERIAL PRIMARY KEY,
    institution_id  INTEGER NOT NULL REFERENCES institution(id) ON DELETE CASCADE,
    username        TEXT NOT NULL,
    email           TEXT,
    password_hash   TEXT NOT NULL,
    role            TEXT DEFAULT 'admin',
    created_at      TEXT DEFAULT (NOW()::TEXT),
    UNIQUE(institution_id, username)
);

-- ── Time Configuration ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS time_config (
    id              SERIAL PRIMARY KEY,
    institution_id  INTEGER UNIQUE NOT NULL REFERENCES institution(id) ON DELETE CASCADE,
    periods_per_day INTEGER DEFAULT 6,
    working_days    TEXT DEFAULT 'Mon,Tue,Wed,Thu,Fri',
    updated_at      TEXT DEFAULT (NOW()::TEXT)
);

-- ── Period Slots ───────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS period_slot (
    id              SERIAL PRIMARY KEY,
    institution_id  INTEGER NOT NULL REFERENCES institution(id) ON DELETE CASCADE,
    slot_order      INTEGER NOT NULL,
    label           TEXT NOT NULL,
    start_time      TEXT NOT NULL,
    end_time        TEXT NOT NULL,
    slot_type       TEXT DEFAULT 'period',
    UNIQUE(institution_id, slot_order)
);

-- ── Rooms ──────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS rooms (
    id              SERIAL PRIMARY KEY,
    institution_id  INTEGER NOT NULL REFERENCES institution(id) ON DELETE CASCADE,
    name            TEXT NOT NULL,
    capacity        INTEGER DEFAULT 60,
    room_type       TEXT DEFAULT 'classroom',
    created_at      TEXT DEFAULT (NOW()::TEXT),
    UNIQUE(institution_id, name)
);

-- ── Staff ──────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS staff (
    id                   SERIAL PRIMARY KEY,
    institution_id       INTEGER NOT NULL REFERENCES institution(id) ON DELETE CASCADE,
    name                 TEXT NOT NULL,
    department           TEXT NOT NULL,
    experience           INTEGER DEFAULT 0,
    max_periods_per_week INTEGER DEFAULT 20,
    max_periods_per_day  INTEGER DEFAULT 4,
    allocated_periods    INTEGER DEFAULT 0,
    email                TEXT,
    available_days       TEXT DEFAULT 'Mon,Tue,Wed,Thu,Fri',
    created_at           TEXT DEFAULT (NOW()::TEXT)
);

-- ── Subjects ───────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS subject (
    id               SERIAL PRIMARY KEY,
    institution_id   INTEGER NOT NULL REFERENCES institution(id) ON DELETE CASCADE,
    subject_name     TEXT NOT NULL,
    subject_code     TEXT,
    abbreviation     TEXT,
    department       TEXT NOT NULL,
    periods_per_week INTEGER DEFAULT 3,
    difficulty_level INTEGER DEFAULT 3,
    is_lab           INTEGER DEFAULT 0,
    lab_duration     INTEGER DEFAULT 2,
    lab_staff2_id    INTEGER REFERENCES staff(id) ON DELETE SET NULL,
    is_mentor_meeting INTEGER DEFAULT 0,
    created_at       TEXT DEFAULT (NOW()::TEXT)
);

-- ── Staff ↔ Subjects ───────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS staff_subjects (
    staff_id    INTEGER REFERENCES staff(id) ON DELETE CASCADE,
    subject_id  INTEGER REFERENCES subject(id) ON DELETE CASCADE,
    PRIMARY KEY (staff_id, subject_id)
);

-- ── Classes ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS class_section (
    id              SERIAL PRIMARY KEY,
    institution_id  INTEGER NOT NULL REFERENCES institution(id) ON DELETE CASCADE,
    name            TEXT NOT NULL,
    department      TEXT NOT NULL,
    semester        INTEGER DEFAULT 1,
    strength        INTEGER DEFAULT 60,
    venue           TEXT DEFAULT '',
    academic_year   TEXT DEFAULT '2026-27',
    created_at      TEXT DEFAULT (NOW()::TEXT),
    UNIQUE(institution_id, name)
);

-- ── Class Mentors ──────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS class_mentor (
    class_id      INTEGER NOT NULL REFERENCES class_section(id) ON DELETE CASCADE,
    staff_id      INTEGER NOT NULL REFERENCES staff(id) ON DELETE CASCADE,
    mentor_order  INTEGER DEFAULT 1,
    PRIMARY KEY (class_id, staff_id)
);

-- ── Class ↔ Subjects ───────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS class_subjects (
    class_id    INTEGER REFERENCES class_section(id) ON DELETE CASCADE,
    subject_id  INTEGER REFERENCES subject(id) ON DELETE CASCADE,
    PRIMARY KEY (class_id, subject_id)
);

-- ── Timetable ──────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS timetable (
    id              SERIAL PRIMARY KEY,
    institution_id  INTEGER NOT NULL REFERENCES institution(id) ON DELETE CASCADE,
    name            TEXT DEFAULT 'Generated Timetable',
    generated_at    TEXT DEFAULT (NOW()::TEXT),
    is_active       INTEGER DEFAULT 1,
    conflicts       INTEGER DEFAULT 0,
    notes           TEXT
);

-- ── Timetable Slots ────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS timetable_slot (
    id              SERIAL PRIMARY KEY,
    institution_id  INTEGER NOT NULL REFERENCES institution(id) ON DELETE CASCADE,
    timetable_id    INTEGER NOT NULL REFERENCES timetable(id) ON DELETE CASCADE,
    day             TEXT NOT NULL,
    period          INTEGER NOT NULL,
    class_id        INTEGER REFERENCES class_section(id) ON DELETE CASCADE,
    subject_id      INTEGER REFERENCES subject(id) ON DELETE CASCADE,
    staff_id        INTEGER REFERENCES staff(id) ON DELETE CASCADE,
    staff2_id       INTEGER REFERENCES staff(id) ON DELETE SET NULL,
    room_id         INTEGER REFERENCES rooms(id) ON DELETE SET NULL,
    is_manual_edit  INTEGER DEFAULT 0,
    created_at      TEXT DEFAULT (NOW()::TEXT)
);

-- ── Conflict Log ───────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS conflict_log (
    id               SERIAL PRIMARY KEY,
    institution_id   INTEGER NOT NULL REFERENCES institution(id) ON DELETE CASCADE,
    timetable_id     INTEGER REFERENCES timetable(id) ON DELETE CASCADE,
    class_name       TEXT,
    subject_name     TEXT,
    day              TEXT,
    period           INTEGER,
    reason           TEXT,
    suggested_action TEXT,
    created_at       TEXT DEFAULT (NOW()::TEXT)
);

-- ── Allocation History ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS allocation_history (
    id              SERIAL PRIMARY KEY,
    institution_id  INTEGER NOT NULL REFERENCES institution(id) ON DELETE CASCADE,
    staff_id        INTEGER REFERENCES staff(id) ON DELETE CASCADE,
    subject_id      INTEGER REFERENCES subject(id) ON DELETE CASCADE,
    timetable_id    INTEGER REFERENCES timetable(id) ON DELETE CASCADE,
    periods_count   INTEGER DEFAULT 0,
    allocation_date TEXT DEFAULT (NOW()::TEXT)
);

-- ── Inbuilt Regulation Curricula Repository ─────────────────────────
CREATE TABLE IF NOT EXISTS inbuilt_curriculum (
    id               SERIAL PRIMARY KEY,
    regulation       TEXT NOT NULL,
    degree           TEXT NOT NULL,
    department       TEXT NOT NULL,
    semester         TEXT NOT NULL,
    semester_num     INTEGER NOT NULL,
    subject_code     TEXT NOT NULL,
    subject_name     TEXT NOT NULL,
    abbreviation     TEXT,
    periods_per_week INTEGER DEFAULT 3,
    difficulty_level INTEGER DEFAULT 3,
    is_lab           INTEGER DEFAULT 0,
    lab_duration     INTEGER DEFAULT 0,
    credits          NUMERIC DEFAULT 3.0,
    created_at       TEXT DEFAULT (NOW()::TEXT)
);
CREATE INDEX IF NOT EXISTS idx_curr_lookup ON inbuilt_curriculum(regulation, department, semester);


-- ════════════════════════════════════════════════════════════════════
-- Optional: Row Level Security (RLS) for production multi-tenancy
-- Uncomment the blocks below to enable RLS.
-- When enabled, users can only access their own institution's data.
-- ════════════════════════════════════════════════════════════════════

-- ALTER TABLE staff ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE subject ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE class_section ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE timetable ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE timetable_slot ENABLE ROW LEVEL SECURITY;

-- CREATE POLICY "Institution isolation" ON staff
--   FOR ALL USING (institution_id = current_setting('app.institution_id')::INTEGER);

-- (Repeat for each table)

SELECT 'Schema created successfully!' as status;
