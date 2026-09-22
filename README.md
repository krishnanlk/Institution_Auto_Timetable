# 🏛️ SchedHub (v1.2.0 Enterprise Academic Suite)
### Autonomous Institutional Timetable Scheduler, Real-Time Collaborative Grid & Multi-Department Curriculum Engine

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Framework-Flask%203.0%2B-black.svg?logo=flask&logoColor=white)](https://palletsprojects.com/p/flask/)
[![Database](https://img.shields.io/badge/Dual--DB-SQLite%20%7C%20Supabase%20PostgreSQL-green.svg?logo=postgresql&logoColor=white)](https://supabase.com/)
[![SSE](https://img.shields.io/badge/Real--Time-Server--Sent%20Events%20(SSE)-orange.svg)](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)
[![Security](https://img.shields.io/badge/Security-OWASP%20Top%2010%20Hardened-emerald.svg)](https://owasp.org/)

**SchedHub v1.2.0** is an enterprise-grade, multi-tenant institutional timetable scheduling, curriculum management, and real-time faculty allocation platform engineered for **Universities, Engineering Colleges, Autonomous Institutions, and K-12 School Networks**.

The platform pairs an autonomous **Constraint Satisfaction Problem (CSP) heuristic solver** with a **real-time collaborative grid engine**, **multi-tier academic approval workflows (Coordinator ➔ HOD ➔ Master Admin)**, **consecutive laboratory block merging**, **pre-seeded Anna University regulation curricula (R2021, R2023, R2025 across 10 departments)**, and strict **1-page A4 landscape print formatting**.

---

## 📑 Table of Contents

- [🌟 Key Highlights & Feature Matrix](#-key-highlights--feature-matrix)
- [🏗️ System Architecture](#️-system-architecture)
- [🚀 Quick Start & Steps to Proceed](#-quick-start--steps-to-proceed)
  - [1. Prerequisites](#1-prerequisites)
  - [2. Clone the Repository](#2-clone-the-repository)
  - [3. Virtual Environment Setup](#3-virtual-environment-setup)
  - [4. Install Dependencies](#4-install-dependencies)
  - [5. Environment Configuration](#5-environment-configuration)
  - [6. Launch the Application](#6-launch-the-application)
- [🔑 Role-Based Access & Demo Credentials](#-role-based-access--demo-credentials)
- [🔄 Academic Approval & Publishing Workflow](#-academic-approval--publishing-workflow)
- [⚡ Real-Time Collaboration & Cell Locking](#-real-time-collaboration--cell-locking)
- [📚 Curricula Repository & Syllabus Extraction](#-curricula-repository--syllabus-extraction)
- [📄 Official 1-Page Printable Timetable Format](#-official-1-page-printable-timetable-format)
- [📡 API Documentation](#-api-documentation)
- [🌐 Cloud Deployment (Vercel & Supabase)](#-cloud-deployment-vercel--supabase)
- [📂 Directory Structure](#-directory-structure)
- [🛡️ Security & Hardening](#️-security--hardening)
- [📄 License & Authors](#-license--authors)

---

## 🌟 Key Highlights & Feature Matrix

### 1. ⚡ Autonomous 0-Clash Scheduling Engine
- **Constraint Satisfaction & Backtracking Solver**: Enforces hard constraints (zero faculty double-booking, daily period caps, consecutive lab rules, subject-staff continuity) and soft constraints (balanced daily workload distribution, morning peak optimization).
- **Shared Faculty Matrix Optimization**: Shared professors across Science & Humanities (S&H) and Engineering departments (e.g., Engineering Mathematics, Physics, Chemistry, Professional English) scheduled across multiple sections with zero clash.
- **Autonomous Laboratory Block Merging**: Automatically reserves consecutive 2-period or 3-period lab slots (`⟵ LAB ⟶`), preventing break-crossing and enforcing dual-staff lab assignments (primary and secondary faculty).
- **Special Curricular Periods**: Automated placement of Mentor Meetings (MM), Library, Physical Education, and non-credit courses.
- **Pre-Generation Feasibility Validator**: Pre-flight checks on staff workload capacity, section requirements, and period caps with actionable remediation alerts.
- **Live SSE Generation Progress**: Server-Sent Events stream step-by-step progress and conflict resolution metrics to the frontend in real time.

### 2. 🔄 Live Collaborative Grid & Cell Locking Engine (`realtime.py`)
- **Server-Sent Events (SSE) Pub/Sub Hub**: Multi-tenant, thread-safe in-memory broadcaster without external broker dependencies (Redis/RabbitMQ), operating identically in local dev and cloud serverless environments.
- **Collaborative Cell Edit Locks**: 60-second automatic TTL lock when editing a timetable slot. Prevents concurrent edits and race conditions between multiple department coordinators.
- **Real-Time Visual Cues**: Locked cells display the holding user's badge (`cell-locked`), with real-time glow highlights (`cell-glow`) when updates are broadcast.
- **Master Admin Emergency Override**: Master Admins can unlock or override any active cell edit lock institution-wide.
- **Instant Grid Sync**: Slot moves, swaps, and generation events sync across all active browser sessions without requiring a manual page refresh.

### 3. 📜 Multi-Tier Academic Approval & Publishing Workflow
- **Four-Stage State Machine**:
  $$\text{Draft} \xrightarrow{\text{Submit}} \text{Submitted} \xrightarrow{\text{Approve}} \text{Approved} \xrightarrow{\text{Publish}} \text{Published (Live)}$$
- **Timetable Coordinator**: Generates, adjusts, and submits the draft timetable to the Head of Department.
- **HOD (Head of Department)**: Inspects the submitted department schedule, approves it, or returns it with actionable revision feedback notes.
- **Master Admin / HOD**: Officially publishes the approved schedule institution-wide, deactivating previous schedules and setting it as the live master.

### 4. 📊 Live Campus Audit & Activity Drawer
- **Persistent Activity Logger**: Comprehensive audit trail logging every administrative and scheduling event (timetable generated, slot moved, timetable submitted/approved/rejected/published, lock overridden, user created).
- **Slide-Over Activity Drawer**: Accessible from the top navigation bar with real-time unread event counter badge.
- **Embedded Dashboard Live Feed**: Instant visibility of campus scheduling events on the administrative dashboard.
- **Role-Filtered Feeds**: Master Admin and Dean monitor institution-wide operations; HODs and Coordinators view department-scoped activity.

### 5. 👥 5-Tier Role-Based Access Control (RBAC)
- **Master Admin**: Full control over institutional configuration, logos, departments, coordinator assignments, lock overrides, and global publishing.
- **Dean**: Institution-wide academic monitoring, workload analytics, and schedule overview (read-only campus oversight).
- **HOD (Head of Department)**: Department head authority, faculty workload management, timetable review, approval, and revision requests.
- **Timetable Coordinator**: Department-level schedule builder, interactive drag-and-drop editor, slot swapping (restricted to maximum 2 coordinators per department).
- **Faculty / Staff**: Personalized schedule viewer for assigned classes and room locations.

### 6. 📚 Inbuilt Anna University Curricula Repository (`curriculum_data.py`)
- **Regulation Coverage**: R2021 (CBCS Affiliated), R2023 (Autonomous / AICTE), and R2025 (NextGen AI & Industry 5.0).
- **Degree Streams**: B.E. and B.Tech.
- **10 Core Departments**:
  - Computer Science & Engineering (CSE)
  - Information Technology (IT)
  - Artificial Intelligence & Data Science (AIDS)
  - Electronics & Communication Engineering (ECE)
  - Electrical & Electronics Engineering (EEE)
  - Mechanical Engineering (MECH)
  - Civil Engineering (CIVIL)
  - Biomedical Engineering (BME)
  - Computer Science & Business Systems (CSBS)
  - Cyber Security (CYBER)
- **Full Semester Mapping (Sem 1 – 8)**: Pre-configured with official subject codes, course names, credit values, periods per week, lab durations, and difficulty levels.

### 7. 🧠 Intelligent Curriculum & Syllabus PDF Extractor (`syllabus_parser.py`)
- **PDF Extraction Engine**: Extracts subjects, codes, lecture hours (L), tutorial hours (T), practical hours (P), and credits (C) directly from Anna University curriculum PDFs.
- **Automated Abbreviation Generator**: Heuristic generator matching 30+ core engineering domains or algorithmic fallback.

### 8. 📄 Official 1-Page Printable Timetable Format
- **Rotated Grid Architecture**: Modern university layout with Days as rows (Monday–Saturday) and Periods/Breaks as columns.
- **Strict 1-Page Print Resize Engine**: Dynamic scaling engine guaranteeing that the complete schedule, legends, metadata, and signatures fit **strictly on one single A4 landscape page** (`@page { size: A4 landscape; margin: 4mm 6mm; }`).
- **Toolbar Controls**: Auto-fit 1 page toggle and zoom options (100%, 95%, 90%, 85%, 80%, 75%).
- **High-Resolution PNG & CSV Export**: One-click client-side export using `html2canvas` and standard CSV downloads.

### 9. 🗄️ Dual-Backend Database Architecture
- **SQLite3 (Local Development)**: Zero-config local database (`edupro.db`) with automatic table creation, schema migrations, and demo seeds.
- **Supabase PostgreSQL (Cloud Production)**: High-performance connection pooling via `DATABASE_URL` with full schema migrations (`supabase_setup.sql`, `supabase_data_migration.sql`).

### 10. 🛡️ OWASP Top 10 Security Hardening
- **A01/A05 Access & Session Security**: Role-scoped endpoint decorators, open redirect validation (`is_safe_url`), session fixation protection (`session.clear()`), and `HttpOnly` / `SameSite=Lax` cookies.
- **A02 Cryptographic Protection**: PBKDF2:SHA256 password hashing with constant-time verification (`hmac.compare_digest`), dummy response equalization, and silent legacy hash auto-upgrade.
- **A04 Brute-Force Rate Limiting**: Sliding window rate limiter (`AuthRateLimiter`) enforcing 60s cooldowns after 5 consecutive failed login attempts.
- **A07 Identification & CSRF Defense**: Cryptographic session-bound CSRF tokens across all forms with 8+ character password policy.
- **A05 Security Headers**: HTTP response headers (`X-Frame-Options: SAMEORIGIN`, `X-Content-Type-Options: nosniff`, and strict Content-Security-Policy).

---

## 🏗️ System Architecture

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        CLIENT BROWSER / UI                             │
│  - Vanilla JS / Jinja2 Templates / Design Tokens                       │
│  - Interactive Grid Drag-and-Drop & Slot Edit Modal                    │
│  - Real-Time EventSource Client (/api/realtime/stream)                 │
│  - Slide-Over Activity Audit Drawer & Unread Badge                     │
│  - 1-Page A4 Print Engine & HTML2Canvas PNG Export                     │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTP / SSE Stream
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                       FLASK WEB CORE (app.py)                          │
│  - Authentication & RBAC Gatekeeper (auth.py)                          │
│  - Real-Time Pub/Sub Hub & CellLockManager (realtime.py)               │
│  - Multi-Tier Workflow Engine (Coordinator ➔ HOD ➔ Admin)              │
│  - Curricula & Syllabus Extraction Engine (syllabus_parser.py)         │
│  - Activity Logger & Audit Stream Dispatcher                           │
└───────────────────┬───────────────────────────────┬────────────────────┘
                    │                               │
                    ▼                               ▼
┌──────────────────────────────────────┐  ┌──────────────────────────────┐
│     SCHEDULING SOLVER (scheduler.py) │  │  PERSISTENCE (database.py)   │
│  - Constraint Satisfaction Solver    │  │  - SQLite (Local: edupro.db) │
│  - Backtracking & Heuristics         │  │  - Supabase PostgreSQL       │
│  - Lab Merging (⟵ LAB ⟶)            │  │  - Connection Pooling        │
│  - Shared Faculty Matrix             │  │  - Auto-Schema Migration     │
│  - Feasibility Workload Pre-Check    │  │  - Activity Log Storage      │
└──────────────────────────────────────┘  └──────────────────────────────┘
```

---

## 🚀 Quick Start & Steps to Proceed

Follow these step-by-step instructions to get SchedHub running locally or in production.

### 1. Prerequisites
- **Python**: Version `3.10` or higher installed ([Download Python](https://www.python.org/downloads/)).
- **Git**: Installed and configured on your system.
- **Browser**: Modern web browser (Chrome, Edge, Firefox, or Safari).

### 2. Clone the Repository
Open your terminal (PowerShell, Command Prompt, or Bash) and run:
```bash
git clone https://github.com/krishnanlk/Institution_Auto_Timetable.git
cd Institution_Auto_Timetable
```

### 3. Virtual Environment Setup
Create and activate an isolated Python virtual environment:

**Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```cmd
python -m venv .venv
.venv\Scripts\activate.bat
```

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 4. Install Dependencies
Install all required production packages:
```bash
pip install -r requirements.txt
```

Verify that key packages (`Flask`, `Werkzeug`, `psycopg2-binary`, `reportlab`, `python-dotenv`) are installed cleanly.

### 5. Environment Configuration
Copy the sample environment file:

**Windows:**
```powershell
copy .env.example .env
```

**macOS / Linux:**
```bash
cp .env.example .env
```

#### Choose Your Database Backend:
- **Option A: Local SQLite (Default, Zero-Config)**
  Keep `DATABASE_URL` empty or commented out in `.env`. SchedHub will automatically initialize `edupro.db` and seed the pre-configured demo institution and curricula.
  ```env
  FLASK_SECRET_KEY=your-secure-random-secret-key
  DATABASE_URL=
  ```
- **Option B: Supabase / PostgreSQL (Cloud Production)**
  Provide your Supabase connection string:
  ```env
  FLASK_SECRET_KEY=your-secure-random-secret-key
  DATABASE_URL=postgresql://postgres.your-project-id:your-password@aws-0-ap-south-1.pooler.supabase.com:6543/postgres?sslmode=require
  ```
  *(See [VERCEL_DEPLOYMENT.md](file:///d:/APP/Institution_Claude/VERCEL_DEPLOYMENT.md) for full cloud configuration.)*

### 6. Launch the Application
Start the Flask development server:
```bash
python app.py
```

Once running, access the application in your browser:
```
http://127.0.0.1:5000
```

---

## 🔑 Role-Based Access & Demo Credentials

SchedHub automatically provisions a production-ready engineering college preset on first startup:

| Field | Value |
|---|---|
| **Institution Code** | `DEMO2024` |
| **Default Username** | `admin` |
| **Default Password** | `admin123` |
| **Institution Name** | LK's Project (Engineering & S&H College) |
| **Sample Classes** | CSE-A, CSE-B, ECE-A, MECH-A, AIDS-A |

### Role Hierarchy & Permissions

| Role | Department-Scoped? | Permissions & Capabilities |
|---|---|---|
| **Master Admin** | Institution-Wide | Full administrative access, institution profile, logo upload, user creation, lock overrides, global publishing. |
| **Dean** | Institution-Wide | Comprehensive read-only overview of all department schedules, workload analytics, and compliance reports. |
| **HOD (Head of Department)** | Department-Specific | Reviews draft timetables submitted by coordinators, grants approvals, returns revision feedback with notes, manages department faculty. |
| **Timetable Coordinator** | Department-Specific | Builds and adjusts department schedules, uses interactive drag-and-drop editor, acquires cell edit locks, submits timetable to HOD (maximum 2 coordinators per department). |
| **Faculty / Staff** | User-Specific | Personalized weekly schedule view, room allocations, workload tracking. |

---

## 🔄 Academic Approval & Publishing Workflow

```mermaid
stateDiagram-v2
    [*] --> Draft: Timetable Generated / Seeded
    Draft --> Submitted: Coordinator clicks "Submit to HOD"
    Submitted --> Approved: HOD reviews and clicks "Approve"
    Submitted --> Draft: HOD clicks "Request Revisions" (with notes)
    Approved --> Published: HOD / Admin clicks "Publish Live"
    Published --> [*]: Active Official Campus Schedule
```

1. **Generation & Draft Editing**: The Coordinator creates or edits the department schedule. Cells are locked during edits (`cell-locked`) to prevent conflicting modifications.
2. **Submission to HOD**: Once clash-free, the Coordinator clicks **Submit to HOD**. The status changes to `Submitted`, and an event is logged in the Campus Audit feed.
3. **Department Review & Approval**: The HOD reviews the schedule. If revisions are required, the HOD clicks **Request Revisions**, attaching notes. If satisfactory, the HOD clicks **Approve**.
4. **Campus Publishing**: The Master Admin or HOD clicks **Publish Live**. The timetable status becomes `Published` and is marked active across all campus screens.

---

## ⚡ Real-Time Collaboration & Cell Locking

SchedHub features a built-in real-time collaboration engine implemented in `realtime.py`:

- **Cell Edit Lock Duration**: 60 seconds TTL (`CellLockManager`).
- **Acquire Lock**: Triggered automatically when opening the slot edit modal (`/api/timetable/slot/<id>/lock`).
- **Release Lock**: Automatically released when closing the modal, saving changes, or upon TTL expiration.
- **Admin Emergency Override**: Master Admins can unlock any occupied slot with full activity logging.
- **Live Broadcast Channel**: Connected clients receive updates via `/api/realtime/stream` for:
  - `slot_locked`: Highlights cell with editor's username and lock icon.
  - `slot_unlocked`: Removes lock state from cell.
  - `slot_updated`: Instantly re-renders slot with animated green glow.
  - `timetable_status_changed`: Updates badge status (`DRAFT`, `SUBMITTED`, `APPROVED`, `PUBLISHED`).
  - `activity_logged`: Appends event to slide-over drawer and dashboard feed.

---

## 📚 Curricula Repository & Syllabus Extraction

### Pre-Seeded Curricula (`curriculum_data.py`)
- **Anna University R2021 / R2023 / R2025** integrated curricula for 10 engineering departments.
- Automatic seeding of course codes, credit loads, contact periods, lab durations, and difficulty levels.
- Pre-configured Basic Sciences & Humanities (S&H) 1st-year split (Circuit vs. Non-Circuit branches).

### Syllabus PDF Parsing (`syllabus_parser.py`)
- Upload curriculum PDFs to automatically populate subject lists, abbreviations, and lab hours.
- Built-in heuristic dictionary of 30+ engineering abbreviations (e.g., Data Structures ➔ `DS`, Operating Systems ➔ `OS`, Theory of Computation ➔ `TOC`).

---

## 📄 Official 1-Page Printable Timetable Format

<p align="center">
  <img src="docs/timetable_preview.png" alt="Official 1-Page Printable Timetable Preview" width="950" style="border-radius: 8px; box-shadow: 0 4px 20px rgba(0,0,0,0.15);"/>
  <br>
  <em>Official 1-Page Rotated Grid Timetable Format in SchedHub v1.2.0.</em>
</p>

- **A4 Landscape Enforcement**: Configured via CSS Print Paged Media (`@page { size: A4 landscape; margin: 4mm 6mm; }`).
- **Consecutive Period Merging**: Consecutive lab blocks merge horizontally with outward directional arrows (`⟵ LAB ⟶`).
- **Page-Fit Scaling Toolbar**:
  - `✨ Auto-Fit 1 Page` (calculates viewport ratio to lock to a single printed sheet).
  - Manual overrides: `100%`, `95%`, `90%`, `85%`, `80%`, `75%`.
- **Institutional Metadata & Signatures**: Displays college emblem/logo, w.e.f. date, section strength, classroom venue, complete theory/lab legends with faculty names, and signature blocks for Timetable Coordinator, HOD, and Principal/Dean.

---

## 📡 API Documentation

### Timetable & Scheduling Endpoints

| Endpoint | Method | Role Required | Description |
|---|---|---|---|
| `/api/timetable/class/<id>` | `GET` | Viewer+ | Retrieves class timetable grid with consecutive slot merge metadata. |
| `/api/timetable/staff/<id>` | `GET` | Viewer+ | Retrieves personalized faculty weekly teaching schedule. |
| `/api/timetable/generate/stream` | `GET` | Coordinator+ | Initiates SSE stream for real-time timetable generation with live progress. |
| `/api/timetable/validate` | `GET` | Coordinator+ | Pre-generation feasibility validator checking staff/period limits. |
| `/api/timetable/slot/<id>/move` | `PUT` | Coordinator+ | Moves a scheduled slot to an empty target day/period. |
| `/api/timetable/slot/<id>/swap` | `PUT` | Coordinator+ | Swaps two scheduled slots with conflict verification. |
| `/api/timetable/export/csv/<id>` | `GET` | Viewer+ | Exports class timetable as a CSV spreadsheet. |

### Real-Time Collaboration & Cell Locking

| Endpoint | Method | Role Required | Description |
|---|---|---|---|
| `/api/realtime/stream` | `GET` | Login Required | Persistent SSE connection for live updates, lock presence, and activity alerts. |
| `/api/timetable/locks` | `GET` | Login Required | Retrieves all active cell presence locks for the institution. |
| `/api/timetable/slot/<id>/lock` | `POST` | Coordinator+ | Acquires a temporary 60-second edit lock on a slot. |
| `/api/timetable/slot/<id>/unlock` | `POST` | Coordinator+ | Releases an edit lock held by the current user. |
| `/api/timetable/slot/<id>/override-lock` | `POST` | Master Admin | Emergency administrative lock override. |

### Workflow & Approvals

| Endpoint | Method | Role Required | Description |
|---|---|---|---|
| `/api/timetable/<id>/submit` | `POST` | Coordinator+ | Submits draft timetable to HOD for formal review. |
| `/api/timetable/<id>/approve` | `POST` | HOD / Admin | Approves the submitted timetable for campus release. |
| `/api/timetable/<id>/reject` | `POST` | HOD / Admin | Returns timetable to Coordinator with feedback notes. |
| `/api/timetable/<id>/publish` | `POST` | HOD / Admin | Officially publishes approved timetable as the live campus schedule. |

### Campus Audit & Activity Feed

| Endpoint | Method | Role Required | Description |
|---|---|---|---|
| `/api/activity/feed` | `GET` | Login Required | Returns recent activity logs filtered by role and department. |

---

## 🌐 Cloud Deployment (Vercel & Supabase)

SchedHub is architected for zero-friction serverless deployment:

1. **Database Setup**: Create a project on [Supabase](https://supabase.com). Run `supabase_setup.sql` in the Supabase SQL Editor.
2. **Deploy to Vercel**: Connect your GitHub repository to Vercel. Set the following environment variables:
   - `FLASK_SECRET_KEY`: Random 32+ character string.
   - `DATABASE_URL`: Your Supabase PostgreSQL pooled connection URI.
3. For detailed step-by-step instructions, see the dedicated [VERCEL_DEPLOYMENT.md](file:///d:/APP/Institution_Claude/VERCEL_DEPLOYMENT.md) guide.

---

## 📂 Directory Structure

```text
Institution_Auto_Timetable/
├── api/
│   └── index.py               # Vercel serverless WSGI entrypoint
├── static/
│   ├── css/
│   │   └── style.css          # Design system, collaboration cues & 1-page print CSS
│   ├── js/
│   │   └── app.js             # Client scripts, modals, toast alerts & tour
│   └── uploads/logos/         # Institution emblem uploads
├── templates/
│   ├── base.html              # Main navigation, activity drawer & SSE listener
│   ├── login.html             # Multi-tenant login and registration portal
│   ├── dashboard.html         # Executive overview, live activity feed & metrics
│   ├── timetable.html         # Interactive grid, drag & drop, locking & approvals
│   ├── timetable_print.html   # Official university 1-page printable format
│   ├── staff.html             # Faculty management & workload tracker
│   ├── subjects.html          # Course catalog & allocation recommendations
│   ├── classes.html           # Sections & room assignments
│   ├── analytics.html         # Workload distribution charts & rankings
│   ├── settings.html          # Institution branding, RBAC users & period slots
│   └── user_tour.html         # Interactive onboarding guide component
├── app.py                     # Flask application routes, SSE endpoints & controllers
├── auth.py                    # 5-Tier RBAC decorators, brute-force & CSRF defense
├── config.py                  # Environment configuration & DB backend detection
├── database.py                # Dual DB adapter (SQLite & Supabase PostgreSQL)
├── scheduler.py               # Constraint satisfaction scheduling engine
├── realtime.py                # In-memory thread-safe SSE pub/sub & cell lock manager
├── curriculum_data.py         # Anna University R2021/R2023/R2025 curricula repository
├── syllabus_parser.py         # Intelligent syllabus PDF & abbreviation extractor
├── supabase_setup.sql         # Supabase PostgreSQL schema definition
├── supabase_data_migration.sql# Production database migration script
├── requirements.txt           # Python package dependencies
├── vercel.json                # Vercel serverless configuration
├── .vercelignore              # Serverless bundle exclusion list
├── VERCEL_DEPLOYMENT.md       # Cloud deployment instructions
└── README.md                  # System documentation
```

---

## 🛡️ Security & Hardening

- **CSRF Defense**: All mutating forms require cryptographic session-bound CSRF tokens.
- **Brute-Force Rate Limiting**: Max 5 attempts per window with sliding 60-second lockout.
- **Cryptographic Password Storage**: PBKDF2:SHA256 with constant-time verification.
- **Content Security Policy (CSP)**: Strict headers preventing unauthorized script injection and framing attacks.
- **Safe Redirection**: Parameter validation preventing unvalidated open redirects.

---

## 📄 License & Authors

Distributed under the **MIT License**. See `LICENSE` for details.

Developed with ❤️ for academic institutions, deans, heads of departments, timetable coordinators, and faculty.
