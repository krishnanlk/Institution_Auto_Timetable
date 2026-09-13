"""
migrate_to_supabase.py
Cleanly migrates ALL local data from SQLite (edupro.db) to Supabase PostgreSQL.
Uses the verified Supabase Pooler endpoint (IPv4 compatible).
"""
import sqlite3
import psycopg2
import psycopg2.extras
import os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SQLITE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "edupro.db")
PG_URL = "postgresql://postgres.kideyapfhvqbjfvsbqay:s6QGPpow4c7OBrQ9@aws-0-ap-southeast-2.pooler.supabase.com:6543/postgres"

print("=" * 65)
print("  SchedHub: Full SQLite -> Supabase Production Migration")
print("=" * 65)

# 1. Connect
print("\n[1] Connecting to SQLite & Supabase PostgreSQL...")
lite = sqlite3.connect(SQLITE_PATH)
lite.row_factory = sqlite3.Row
lcur = lite.cursor()

pg = psycopg2.connect(PG_URL, connect_timeout=15, sslmode="require")
pg.autocommit = False
pcur = pg.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
print("    SQLite: OK (edupro.db)")
print("    Supabase: OK (aws-0-ap-southeast-2.pooler.supabase.com)")

# 2. Truncate existing application tables to avoid ID conflicts
print("\n[2] Truncating stale data on Supabase (CASCADE)...")
TRUNCATE_TABLES = [
    "allocation_history", "conflict_log", "timetable_slot", "timetable",
    "class_mentor", "class_subjects", "class_section", "staff_subjects",
    "subject", "staff", "rooms", "department", "period_slot",
    "time_config", "users", "institution"
]
pcur.execute(f"TRUNCATE TABLE {', '.join(TRUNCATE_TABLES)} CASCADE;")
pg.commit()
print("    Truncated successfully. Database is clean for migration.")

# 3. Order of migration (foreign-key safe)
MIGRATE_ORDER = [
    ("institution", True),
    ("users", True),
    ("time_config", True),
    ("period_slot", True),
    ("department", True),
    ("rooms", True),
    ("staff", True),
    ("subject", True),
    ("staff_subjects", False),
    ("class_section", True),
    ("class_subjects", False),
    ("class_mentor", False),
    ("timetable", True),
    ("timetable_slot", True),
    ("conflict_log", True),
    ("allocation_history", True),
]

def get_sqlite_rows(table):
    rows = lite.execute(f"SELECT * FROM {table}").fetchall()
    return [dict(r) for r in rows]

def insert_pg_rows(table, rows):
    if not rows:
        return 0
    cols = list(rows[0].keys())
    col_str = ", ".join(f'"{c}"' for c in cols)
    placeholders = ", ".join(["%s"] * len(cols))
    sql = f'INSERT INTO {table} ({col_str}) VALUES ({placeholders})'
    batch_data = [[r[c] for c in cols] for r in rows]
    
    # Use executemany for high performance
    psycopg2.extras.execute_batch(pcur, sql, batch_data, page_size=500)
    pg.commit()
    return len(rows)

def reset_sequence(table, id_col="id"):
    try:
        pcur.execute(f"SELECT MAX({id_col}) as m FROM {table}")
        row = pcur.fetchone()
        max_id = row["m"] if row else None
        if max_id is not None:
            pcur.execute(f"SELECT setval(pg_get_serial_sequence('{table}', '{id_col}'), %s)", (max_id,))
            pg.commit()
    except Exception as e:
        pg.rollback()
        print(f"    Sequence reset note for {table}: {e}")

print("\n[3] Migrating data from SQLite to Supabase...")
for table, has_id in MIGRATE_ORDER:
    rows = get_sqlite_rows(table)
    count = insert_pg_rows(table, rows)
    if has_id:
        reset_sequence(table)
    print(f"    -> {table:20s}: {count:5d} rows migrated successfully")

# Inbuilt curriculum check
pcur.execute("SELECT COUNT(*) as c FROM inbuilt_curriculum")
cur_pg_count = pcur.fetchone()["c"]
lcur.execute("SELECT COUNT(*) FROM inbuilt_curriculum")
cur_lite_count = lcur.fetchone()[0]

if cur_pg_count == 0 and cur_lite_count > 0:
    print("\n[4] Migrating inbuilt_curriculum...")
    rows = get_sqlite_rows("inbuilt_curriculum")
    count = insert_pg_rows("inbuilt_curriculum", rows)
    reset_sequence("inbuilt_curriculum")
    print(f"    -> inbuilt_curriculum: {count} rows migrated")
else:
    print(f"\n[4] inbuilt_curriculum already populated ({cur_pg_count} rows in Supabase, {cur_lite_count} in SQLite).")

# 5. Verification
print("\n[5] Verification (Row counts on Supabase):")
all_tables = [t[0] for t in MIGRATE_ORDER] + ["inbuilt_curriculum"]
success = True
for t in all_tables:
    pcur.execute(f"SELECT COUNT(*) as c FROM {t}")
    pg_c = pcur.fetchone()["c"]
    lcur.execute(f"SELECT COUNT(*) FROM {t}")
    lt_c = lcur.fetchone()[0]
    status = "MATCH" if pg_c == lt_c else "MISMATCH"
    if status != "MATCH":
        success = False
    print(f"    {t:20s} | SQLite: {lt_c:5d} | Supabase: {pg_c:5d} | {status}")

print("\n" + "=" * 65)
if success:
    print("  MIGRATION SUCCESSFUL! All production data is on Supabase.")
else:
    print("  MIGRATION FINISHED WITH WARNINGS. Check counts above.")
print("=" * 65)

lite.close()
pg.close()
