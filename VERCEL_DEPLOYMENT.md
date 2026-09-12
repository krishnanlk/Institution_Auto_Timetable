# SchedHub — Vercel Deployment Guide

SchedHub is pre-configured and ready for one-click deployment on **Vercel** with serverless Python execution.

---

## 1. Project Configuration Summary

The following files have been prepared:
- [`vercel.json`](./vercel.json) — Routes all web traffic to the serverless function.
- [`api/index.py`](./api/index.py) — WSGI entrypoint for Vercel's Python runtime.
- [`requirements.txt`](./requirements.txt) — Includes `flask`, `psycopg2-binary`, `reportlab`, `gunicorn`, `werkzeug`, etc.
- [`.vercelignore`](./.vercelignore) — Prevents local virtual environments (`.venv/`) and cache from bloating the deployment bundle.
- [`config.py`](./config.py) — Automatically handles Vercel's ephemeral `/tmp` filesystem for SQLite and switches to PostgreSQL when `DATABASE_URL` is provided.

---

## 2. Option A: Deploy via GitHub (Recommended)

1. **Commit and push your code to GitHub:**
   ```bash
   git add .
   git commit -m "Configure Vercel serverless deployment"
   git push origin main
   ```

2. **Go to Vercel:**
   - Log into [vercel.com](https://vercel.com).
   - Click **Add New** → **Project**.
   - Import your GitHub repository.

3. **Configure Environment Variables (in Vercel Project Settings):**
   Under **Environment Variables**, add:
   | Variable | Value | Description |
   |---|---|---|
   | `DATABASE_URL` | `postgresql://postgres.[REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres` | Your Supabase connection string (use Transaction/Session Pooler on port 6543) |
   | `FLASK_SECRET_KEY` | `your-secure-random-secret-string-here` | Session encryption key |

4. **Click Deploy:**
   Vercel will build the dependencies and deploy your app. Once deployed, you will get a live URL like `https://your-project.vercel.app`.

---

## 3. Option B: Deploy via Vercel CLI

If you have Node.js and Vercel CLI installed:
```bash
# 1. Login to Vercel
npx vercel login

# 2. Deploy preview
npx vercel

# 3. Deploy to production
npx vercel --prod
```

---

## 4. Database Setup (Supabase PostgreSQL)

Because Vercel serverless functions have a read-only filesystem (except `/tmp`), using a cloud database like **Supabase** ensures persistent storage across all users and cold starts:

1. Create a free project at [supabase.com](https://supabase.com).
2. Go to the **SQL Editor** in Supabase.
3. Paste and run the contents of [`supabase_setup.sql`](./supabase_setup.sql).
4. In Supabase, go to **Project Settings** → **Database** → **Connection String** → select **URI** (choose **Connection Pooling**, port `6543`).
5. Copy the URI and set it as `DATABASE_URL` in your Vercel Project Environment Variables.

> **Note on SQLite:** If `DATABASE_URL` is omitted, SchedHub safely initializes an ephemeral SQLite database in `/tmp/edupro.db`. This allows the app to run on Vercel immediately for testing, but data will reset across cold starts until `DATABASE_URL` is configured.

---

## 5. Default Login Credentials

- **Username:** `admin`
- **Password:** `admin123`
