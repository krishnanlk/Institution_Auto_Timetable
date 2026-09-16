"""
generate_pg_dump.py
Generates a PostgreSQL-compatible SQL dump of all local SQLite data.
Output file: supabase_data_migration.sql — paste into Supabase SQL Editor.
"""
import sqlite3
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SQLITE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "edupro.db")

lite = sqlite3.connect(SQLITE_PATH)
lite.row_factory = sqlite3.Row

# Tables in FK-dependency order
TABLES = [
    "institution",
    "users",
    "time_config",
    "period_slot",
    "department",
    "rooms",
    "staff",
    "subject",
    "staff_subjects",
    "class_section",
    "class_subjects",
    "class_mentor",
    "timetable",
    "timetable_slot",
    "conflict_log",
    "allocation_history",
    "inbuilt_curriculum",
]

# Tables with SERIAL/auto-increment ids that need sequence resets
ID_TABLES = [
    "institution", "users", "time_config", "period_slot", "department",
    "rooms", "staff", "subject", "class_section", "timetable",
    "timetable_slot", "conflict_log", "allocation_history", "inbuilt_curriculum",
]

def escape_val(v):
    if v is None:
        return "NULL"
    if isinstance(v, (int, float)):
        return str(v)
    # String - escape single quotes
    s = str(v).replace("'", "''")
    return f"'{s}'"


output_lines = []
output_lines.append("-- ============================================================")
output_lines.append("-- SchedHub: Local SQLite -> Supabase Migration Dump")
output_lines.append("-- Generated automatically. Paste into Supabase SQL Editor.")
output_lines.append("-- Run once, then DELETE this endpoint if using API migration.")
output_lines.append("-- ============================================================")
output_lines.append("")
output_lines.append("BEGIN;")
output_lines.append("")

# Truncate all tables in reverse FK order (to clear old seeded data)
output_lines.append("-- ── Clear existing data (reverse FK order) ──────────────")
output_lines.append("-- This ensures clean migration without ID conflicts")
TRUNC_ORDER = [
    "allocation_history", "conflict_log", "timetable_slot", "timetable",
    "class_mentor", "class_subjects", "class_section",
    "staff_subjects", "subject", "staff",
    "rooms", "department", "period_slot", "time_config",
    "users", "inbuilt_curriculum", "institution",
]
for t in TRUNC_ORDER:
    output_lines.append(f"TRUNCATE TABLE {t} RESTART IDENTITY CASCADE;")
output_lines.append("")

total_rows = 0

for table in TABLES:
    rows = [dict(r) for r in lite.execute(f"SELECT * FROM {table}").fetchall()]
    if not rows:
        output_lines.append(f"-- {table}: 0 rows (skipping)")
        output_lines.append("")
        continue

    output_lines.append(f"-- ── {table} ({len(rows)} rows) ──────────────────────")

    cols = list(rows[0].keys())
    col_str = ", ".join(f'"{c}"' for c in cols)

    # Skip sqlite_sequence internal column if present
    if "sqlite_sequence" in col_str:
        continue

    for row in rows:
        vals = ", ".join(escape_val(row[c]) for c in cols)
        output_lines.append(
            f"INSERT INTO {table} ({col_str}) VALUES ({vals}) ON CONFLICT DO NOTHING;"
        )
    output_lines.append("")
    total_rows += len(rows)

output_lines.append("")
output_lines.append("-- ── Fix sequences so future inserts get correct auto-IDs ──")
for table in ID_TABLES:
    # Get max id from local SQLite
    try:
        row = lite.execute(f"SELECT MAX(id) as m FROM {table}").fetchone()
        max_id = row["m"] if row and row["m"] else 1
        output_lines.append(
            f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), {max_id});"
        )
    except Exception:
        pass

output_lines.append("")
output_lines.append("COMMIT;")
output_lines.append("")
output_lines.append(f"-- Total rows to insert: {total_rows}")
output_lines.append("-- Done! Refresh your Vercel app and login with DEMO2024 / admin / admin123")

lite.close()

out_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "supabase_data_migration.sql")
with open(out_path, "w", encoding="utf-8") as f:
    f.write("\n".join(output_lines))

print(f"[OK] Generated: {out_path}")
print(f"[OK] Total rows: {total_rows}")
print(f"[OK] Tables: {len(TABLES)}")
print()
print("Next steps:")
print("  1. Open Supabase Dashboard > SQL Editor")
print("  2. Open supabase_data_migration.sql")
print("  3. Paste and click 'Run'")
print("  4. All data will be in Supabase!")
