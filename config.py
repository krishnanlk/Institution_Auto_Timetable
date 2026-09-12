"""
config.py — Environment-based configuration.
Supports SQLite (default) or Supabase / any PostgreSQL via DATABASE_URL.

Usage:
  - Local development: leave DATABASE_URL unset → uses SQLite (edupro.db)
  - Production/Supabase: set DATABASE_URL=postgresql://... in .env or environment
"""
import os

# Load .env if present (no error if python-dotenv not installed)
try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except ImportError:
    pass

# ── Database ───────────────────────────────────────────────────────────────────
DATABASE_URL: str = os.environ.get("DATABASE_URL", "")

# Auto-detect backend from URL
if DATABASE_URL.startswith(("postgres://", "postgresql://")):
    DB_BACKEND = "postgres"
    # Normalize postgres:// → postgresql:// (Supabase sometimes uses the short form)
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = "postgresql://" + DATABASE_URL[len("postgres://"):]
else:
    DB_BACKEND = "sqlite"

# Handle filesystem on Vercel (read-only except /tmp)
if os.environ.get("VERCEL"):
    tmp_db = "/tmp/edupro.db"
    orig_db = os.path.join(os.path.dirname(os.path.abspath(__file__)), "edupro.db")
    if not os.path.exists(tmp_db) and os.path.exists(orig_db):
        import shutil
        try:
            shutil.copy2(orig_db, tmp_db)
        except Exception:
            pass
    SQLITE_PATH: str = tmp_db
else:
    SQLITE_PATH: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), "edupro.db")

# ── Flask ──────────────────────────────────────────────────────────────────────
FLASK_SECRET_KEY: str = os.environ.get("FLASK_SECRET_KEY", "edupro-v2-secret-xK9mP2024")

# ── Debug info ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"DB backend : {DB_BACKEND}")
    print(f"DB URL     : {DATABASE_URL or SQLITE_PATH}")
