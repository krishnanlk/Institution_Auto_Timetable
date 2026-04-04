# Institution Auto Timetable

Institution Auto Timetable is a Flask-based timetable management system for schools, colleges, and training institutes. It supports multi-tenant isolation, automated timetable generation, staff and subject management, and export-ready class schedules.

## Overview

Each institution gets its own isolated workspace with its own users, staff, subjects, classes, timetable configuration, and generated schedules. Administrators can configure working days, period slots, and institution settings, then generate and refine timetables through the dashboard.

## Key Features

- Multi-tenant architecture with institution-level data isolation
- Institution registration and login by institution code
- Admin and viewer roles for controlled access
- Staff management with availability and workload tracking
- Subject management with lab and practical support
- Class management and subject assignment
- Configurable working days and period slots, including breaks and lunch
- Pre-generation validation to catch missing data and conflicts
- Automated timetable generation with lab-aware consecutive slot placement
- Timetable editing, deletion, and regeneration
- Class-wise and staff-wise timetable views
- CSV and PDF timetable export
- Dashboard analytics and workload/performance charts
- Recommendation engine for staff allocation insights

## Tech Stack

- Backend: Flask
- Database: SQLite3
- Export: ReportLab
- Frontend: HTML templates, CSS, and JavaScript

## Requirements

- Python 3.10+ recommended
- pip

## Installation

Clone the repository and install the dependencies:

```bash
git clone https://github.com/krishnanlk/Institution_Claude.git
cd Institution_Claude
pip install -r requirements.txt
```

## Run the Application

Start the Flask app:

```bash
python app.py
```

Then open:

```text
http://localhost:5000
```

## Demo Credentials

Use the built-in demo institution to explore the application:

- Institution Code: DEMO2024
- Username: admin
- Password: admin123

## Usage Flow

1. Register a new institution at `/register`, or log in with the demo account.
2. Add staff, subjects, and classes.
3. Assign subjects to staff and classes.
4. Configure working days and period slots in Settings.
5. Validate and generate the timetable.
6. Review class-wise or staff-wise schedules, then export as CSV or PDF.

## Main Pages

- `/dashboard` - summary cards, recent timetables, workload and performance charts
- `/staff` - staff records and assignments
- `/subjects` - subject catalog and staff recommendations
- `/classes` - class sections and subject mapping
- `/timetable` - timetable generation, editing, export, and deletion
- `/analytics` - performance and timetable analytics
- `/settings` - institution profile, time configuration, period slots, and users

## API Highlights

The app also exposes JSON endpoints for dashboard data, entity CRUD, validation, generation, timetable export, and analytics. Key examples include:

- `/api/timetable/generate`
- `/api/timetable/validate`
- `/api/timetable/export/csv/<class_id>`
- `/api/timetable/export/pdf/<class_id>`
- `/api/settings/time`
- `/api/staff`
- `/api/subjects`
- `/api/classes`

## Project Structure

```text
app.py           Flask application routes and page/API handlers
auth.py          Session auth and access-control decorators
database.py      SQLite schema, seeding, and password helpers
scheduler.py     Timetable generation and analytics logic
templates/       Jinja2 HTML templates
static/          CSS, JavaScript, and image assets
requirements.txt Python dependencies
```

## Database

The application uses a local SQLite database file named `edupro.db`. The schema is created automatically on first run, and a demo institution is seeded when the database is empty.

## Notes

- Viewer accounts can inspect data but cannot modify it.
- Lab subjects are scheduled into consecutive teaching periods.
- Break and lunch slots are preserved and are not assigned to classes.

## License

No license file is currently included in this repository.
