# EduSchedule Pro v2 — Multi-Tenant Timetable Generator

## Quick Start

```bash
pip install flask reportlab
python app.py
```
Open: http://localhost:5000

## Demo Login
Institution Code: **DEMO2024**  |  Username: **admin**  |  Password: **admin123**

## Register New Institution
Go to /register → fill form → get your own isolated workspace

## What's New in v2
- Multi-tenant: each institution has 100% isolated data
- Institution registration system
- Time Allocator: configure periods/day, working days, break/lunch slots
- Staff availability (per day)
- Lab/practical subjects (consecutive periods)
- Pre-generation validation with conflict warnings
- Timetable slot editing (click any filled slot)
- Timetable delete/reset
- Search & filter on Staff, Subjects, Classes
- User management per institution (admin/viewer roles)
- Institution profile settings
- Timetable history on dashboard
- Print-ready timetable grid

## Features
| Feature | Status |
|---------|--------|
| Multi-Institution | ✅ |
| Institution Registration | ✅ |
| Time Config (periods/day, working days) | ✅ |
| Custom Period & Break Schedule | ✅ |
| Staff Availability per Day | ✅ |
| Lab/Consecutive Period Support | ✅ |
| Pre-gen Validation Checks | ✅ |
| Greedy Algorithm Generation | ✅ |
| Timetable Slot Editing | ✅ |
| Timetable Delete/Reset | ✅ |
| Class & Staff Timetable Views | ✅ |
| CSV & PDF Export | ✅ |
| Staff Recommendation Engine | ✅ |
| Performance Analytics | ✅ |
| Promotion/Hike Suggestions | ✅ |
| Search & Filter (all pages) | ✅ |
| User Management | ✅ |
| Dashboard Charts | ✅ |
| Session Auth | ✅ |
