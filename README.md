# 🏫 Zoho School Management System — Enterprise Education ERP

> A full-stack, enterprise-grade School Management System built with **Flask + SQLAlchemy** on the backend and a **Zoho CRM + Zoho Creator** integration layer. Deployed live on Render.

[![Live Demo](https://img.shields.io/badge/Live_Demo-school--management--hrk8.onrender.com-4f46e5?style=for-the-badge)](https://school-management-hrk8.onrender.com/)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0.3-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-red?style=for-the-badge)](https://www.sqlalchemy.org/)
[![Render](https://img.shields.io/badge/Deployed_on-Render-46E3B7?style=for-the-badge&logo=render&logoColor=white)](https://render.com/)

---

## 🌐 Live Application

| Link | Description |
|------|-------------|
| **[🚀 Live App](https://school-management-hrk8.onrender.com/)** | Main school admin dashboard |
| **[📋 Staff Dashboard](https://school-management-hrk8.onrender.com/dashboard)** | Metrics, funnel, and at-risk overview |
| **[🎓 Leads](https://school-management-hrk8.onrender.com/leads)** | Admission enquiry pipeline |
| **[👩‍🎓 Students](https://school-management-hrk8.onrender.com/students)** | Student directory |
| **[📅 Attendance](https://school-management-hrk8.onrender.com/attendance)** | Daily attendance marking |
| **[📝 Exams](https://school-management-hrk8.onrender.com/exams)** | Examination results |
| **[💰 Fees](https://school-management-hrk8.onrender.com/fees)** | Fee collection ledger |
| **[👨‍👩‍👧 Parent Portal](https://school-management-hrk8.onrender.com/parent)** | Secure parent login |

**Test Parent Credentials:**
- `parent1@example.com` → Student: Aarav Patel (Grade 5)
- `parent2@example.com` → Student: Meera Sharma (Grade 6)

---

## 📖 Table of Contents

1. [Executive Summary](#-executive-summary)
2. [Features](#-features)
3. [System Architecture](#-system-architecture)
4. [Data Models](#-data-models)
5. [Module Breakdown](#-module-breakdown)
6. [Tech Stack](#-tech-stack)
7. [Project Structure](#-project-structure)
8. [Local Setup](#-local-setup)
9. [Deployment (Render)](#-deployment-render)
10. [API Routes](#-api-routes)
11. [Zoho CRM Integration](#-zoho-crm-integration)
12. [Deluge Automation Scripts](#-deluge-automation-scripts)
13. [Zoho Creator Parent Portal](#-zoho-creator-parent-portal)
14. [Security Model](#-security-model)
15. [Automated Grading Engine](#-automated-grading-engine)

---

## 📋 Executive Summary

This project presents the end-to-end architecture, technical implementation, Deluge automation engine, and parent-facing application for an **Enterprise School Management System**.

The solution uses **Flask + SQLAlchemy** as the interactive demonstration layer, fully mirroring a production **Zoho CRM** implementation as the system of record for all school operations — admissions, student lifecycle, academic hierarchy, daily attendance, examination performance, and installment fee collection.

A **Zoho Creator** parent portal provides real-time, row-level-secure visibility into student attendance, progress report cards, and fee ledgers.

---

## ✨ Features

### 🎯 Admission & Lead Management
- Web-to-Lead admission enquiry webform (`admission_webform.html`)
- Full admission pipeline: `Enquiry` → `Interview Scheduled` → `Offered` → `Confirmed` → `Converted to Student`
- One-click lead-to-student conversion with auto-generated Student ID (`STU-YYYY-NNNN`)
- Duplicate student prevention before conversion

### 👩‍🎓 Student Management
- Full student directory with class, section, and academic year
- Auto-generated unique Student IDs — format: `STU-2026-0001`
- Dual-horizon data model: active snapshot + full enrollment history per year
- Academic status tracking: `Active` / `At-Risk`

### 📅 Attendance System
- Daily per-student attendance marking (Present / Absent / Late / Excused)
- Duplicate prevention via composite unique key: `{student_id}_{date}`
- Real-time attendance percentage calculated per student
- At-risk flagging: students below **75% attendance** are auto-flagged

### 📝 Examination & Grading Engine
- Multi-exam, multi-subject marks entry
- Automated letter grading (A+, A, B, C, F)
- Average marks tracking with at-risk detection below **40% average**
- Class rank computation per exam

### 💰 Fee Management
- Per-student annual fee configuration
- Multi-installment payment tracking
- Real-time outstanding balance: `Total Fee - Collected`
- Auto payment status: `Paid` / `Partial` / `Unpaid`

### 📊 Executive Dashboard
- KPI cards: total students, total fees, collected, outstanding
- Admission funnel visualization (all stages)
- Class-wise fee collection breakdown table
- **At-Risk Early Warning Engine** — live defaulter panel

### 👨‍👩‍👧 Parent Portal
- Secure email-based parent login (email as identity key)
- Multi-child family switcher — one login for all children
- View per child: attendance log, exam results, fee ledger
- Complete row-level data isolation per family

---

## 🏗 System Architecture

```
+--------------------------------------------------------------+
|                   Zoho School ERP Platform                   |
+--------------------+-----------------------------------------+
|   Staff Interface  |           Parent Portal                  |
|   (Flask Web App)  |       (Zoho Creator / Flask)             |
+--------------------+-----------------------------------------+
|                  Flask Application Layer                      |
|   Routes: / /leads /students /attendance /exams /fees        |
|           /parent /parent/dashboard /webform/submit          |
+--------------------------------------------------------------+
|           SQLAlchemy ORM  (SQLite / PostgreSQL-ready)        |
+--------------------------------------------------------------+
|  Models: Lead | Student | Attendance | ExamResult | FeeRecord|
+--------------------------------------------------------------+
          |                                   |
+---------+----------+          +-------------+------------+
|     Zoho CRM       |          |      Zoho Creator        |
| (System of Record) |          |  (Parent Self-Service)   |
| Leads, Students,   |          |  Row-level security      |
| Attendance, Marks, |          |  Multi-child switcher    |
| Fees, Workflows,   |          |  Glassmorphic portal UI  |
| Deluge Automation  |          |                          |
+--------------------+          +--------------------------+
```

---

## 🗄 Data Models

### Lead
| Field | Type | Notes |
|-------|------|-------|
| `id` | Integer PK | Auto-increment |
| `first_name` | String(100) | Required |
| `last_name` | String(100) | Required |
| `parent_email` | String(150) | Required |
| `grade_applied` | String(50) | Required |
| `lead_status` | String(50) | Default: `Enquiry` |
| `created_at` | DateTime | Auto-set |

### Student
| Field | Type | Notes |
|-------|------|-------|
| `id` | Integer PK | Auto-increment |
| `student_id` | String(50) UNIQUE | Format: `STU-YYYY-NNNN` |
| `first_name` | String(100) | Required |
| `last_name` | String(100) | Required |
| `parent_email` | String(150) | Portal login key |
| `current_class` | String(50) | e.g. Grade 5 |
| `section` | String(20) | Default: A |
| `academic_year` | String(20) | e.g. 2026-2027 |
| `academic_status` | String(50) | Active / At-Risk |
| `admission_date` | Date | Auto-set |

### Attendance
| Field | Type | Notes |
|-------|------|-------|
| `id` | Integer PK | Auto-increment |
| `student_id` | FK → Student | Required |
| `attendance_date` | Date | Required |
| `status` | String(20) | Present/Absent/Late |
| `class_name` | String(50) | Denormalized |
| `section` | String(20) | Denormalized |
| `unique_key` | String(100) UNIQUE | `{student_id}_{date}` |

### ExamResult
| Field | Type | Notes |
|-------|------|-------|
| `id` | Integer PK | Auto-increment |
| `student_id` | FK → Student | Required |
| `exam_name` | String(50) | e.g. Mid-Term |
| `subject` | String(50) | e.g. Math |
| `marks_obtained` | Float | Required |
| `max_marks` | Float | Required |

### FeeRecord
| Field | Type | Notes |
|-------|------|-------|
| `id` | Integer PK | Auto-increment |
| `student_id` | FK → Student | Required |
| `academic_year` | String(20) | e.g. 2026-2027 |
| `total_fee` | Float | Default: 5000.0 |
| `collected_amount` | Float | Default: 0.0 |
| `payment_status` | String(30) | Paid/Partial/Unpaid |

---

## 📦 Module Breakdown

| Module | Route | Description |
|--------|-------|-------------|
| **Dashboard** | `/` or `/dashboard` | KPI metrics, funnel, at-risk students |
| **Leads** | `/leads` | Admission enquiry pipeline |
| **Students** | `/students` | Full student directory |
| **Attendance** | `/attendance` | Daily attendance with dedup |
| **Exams** | `/exams` | Multi-subject exam results |
| **Fees** | `/fees` | Fee collection & status |
| **Parent Login** | `/parent` | Email-based parent auth |
| **Parent Dashboard** | `/parent/dashboard` | Student profile, attendance, exams, fees |
| **Admission Webform** | `/admission-webform` | Public enquiry form |
| **Webform Submit** | `/webform/submit` | Processes form → creates Lead |

---

## 🛠 Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.11, Flask 3.0.3 |
| **ORM** | Flask-SQLAlchemy 3.1.1, SQLAlchemy 2.0.36 |
| **Database** | SQLite (dev), PostgreSQL-ready via `DATABASE_URL` |
| **WSGI Server** | Gunicorn 22.0.0 |
| **Frontend** | HTML5, Jinja2 Templates, Vanilla CSS |
| **Deployment** | Render (free tier) |
| **Version Control** | Git + GitHub |
| **CRM Platform** | Zoho CRM |
| **Parent App** | Zoho Creator |
| **Automation** | Zoho Deluge Scripts |

---

## 📁 Project Structure

```
School-management/
├── app.py                           # Flask app — models, routes, business logic
├── requirements.txt                 # Python dependencies
├── render.yaml                      # Render deployment blueprint
├── gunicorn.conf.py                 # Production WSGI server config
├── admission_webform.html           # Public admission enquiry form
├── index.html                       # Landing page
├── .gitignore
│
├── templates/
│   ├── base.html                    # Base layout with nav
│   ├── dashboard.html               # Executive dashboard
│   ├── leads.html                   # Admission leads
│   ├── students.html                # Student directory
│   ├── attendance.html              # Attendance marking
│   ├── exams.html                   # Exam results
│   ├── fees.html                    # Fee management
│   ├── parent_login.html            # Parent portal login
│   └── parent_dashboard.html        # Parent self-service
│
├── static/
│   └── style.css                    # Global glassmorphic styles
│
├── 01-CRM-Build-Guide.md            # Zoho CRM setup guide
├── 02-Deluge-Scripts.md             # All Deluge automation scripts
├── 03-Creator-Build-Guide.md        # Zoho Creator app guide
├── LIVE-BUILD-CHECKLIST.md          # Step-by-step build checklist
├── SMS_SUBMISSION_REPORT.md         # Master technical submission report
└── School-Management-System-Design.md  # Architecture design document
```

---

## 💻 Local Setup

**Prerequisites:** Python 3.11+, Git

```bash
# 1. Clone the repository
git clone https://github.com/kiran312003/School-management.git
cd School-management

# 2. Create & activate virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
python app.py
```

Open **http://127.0.0.1:5000**

> ✅ Demo data is automatically seeded on first run — sample leads, students, attendance records, exam results, and fee records are pre-loaded.

---

## 🚀 Deployment (Render)

### One-Click Deploy via Blueprint

1. Go to [render.com](https://render.com) → **New +** → **Blueprint**
2. Connect GitHub repo: `kiran312003/School-management`
3. Render auto-detects `render.yaml`
4. Click **Apply** — builds and deploys automatically

### `render.yaml`
```yaml
services:
  - type: web
    name: school-management
    runtime: python
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn app:app --config gunicorn.conf.py
    plan: free
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.0
      - key: FLASK_ENV
        value: production
      - key: SECRET_KEY
        generateValue: true
```

### `gunicorn.conf.py`
```python
bind = f"0.0.0.0:{os.environ.get('PORT', '5000')}"
workers = 2
worker_class = "sync"
timeout = 120
accesslog = "-"
errorlog  = "-"
loglevel  = "info"
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Flask session secret (auto-generated by Render) | Dev fallback |
| `FLASK_ENV` | Environment mode | `production` |
| `PYTHON_VERSION` | Python runtime | `3.11.0` |
| `DATABASE_URL` | Optional PostgreSQL URL | SQLite in `/tmp` |

---

## 🔗 API Routes

| Method | Route | Description |
|--------|-------|-------------|
| `GET` | `/` | Redirect to dashboard |
| `GET` | `/dashboard` | Executive dashboard |
| `GET, POST` | `/leads` | List / Create lead |
| `POST` | `/lead/<id>/confirm` | Convert lead to student |
| `GET` | `/students` | Student directory |
| `GET, POST` | `/attendance` | List / Mark attendance |
| `GET, POST` | `/exams` | List / Record exam results |
| `GET, POST` | `/fees` | List / Update fee record |
| `GET, POST` | `/parent` | Parent email login |
| `GET` | `/parent/dashboard` | Parent self-service |
| `GET` | `/parent/select/<student_id>` | Switch child |
| `GET` | `/logout` | Clear session |
| `GET` | `/admission-webform` | Public enquiry form |
| `POST` | `/webform/submit` | Submit enquiry → create Lead |

---

## 🏢 Zoho CRM Integration

### CRM Module Reference

| Module | Type | Purpose |
|--------|------|---------|
| **Leads** | Standard | Admission enquiry ingestion via webform |
| **Students** | Custom Master | Central student identity & lifecycle |
| **Academic_Years** | Custom | School year definitions |
| **Classes** | Custom | Grade levels (Grade 1–10) |
| **Sections** | Custom | Class subdivisions per year |
| **Subjects** | Custom | Course catalog |
| **Teachers** | Custom | Faculty directory |
| **Subject_Assignments** | Junction | Teacher-Subject-Section timetable (M:N) |
| **Enrollment_History** | Child | Year-on-year academic progression archive |
| **Parents** | Custom | Guardian master records |
| **Attendance** | Custom | Daily attendance ledger |
| **Fee_Structure** | Custom | Fee config by class & academic year |
| **Fee_Payments** | Child | Installment transaction ledger |
| **Examinations** | Custom | Exam event definitions |
| **Marks** | Custom | Subject-level marks per student per exam |

### Data Model Relationships

```
LEADS ─────────────────────────► STUDENTS
                                      │
                    ┌─────────────────┼──────────────────┐
                    │                 │                  │
               ATTENDANCE       EXAMRESULT          FEEDRECORD
```

---

## ⚡ Deluge Automation Scripts

Full scripts documented in [`02-Deluge-Scripts.md`](02-Deluge-Scripts.md):

| Script | Trigger | Description |
|--------|---------|-------------|
| `generateStudentId` | Before Create (Student) | Generates `STU-YYYY-NNNN` unique ID |
| `convertLeadToStudent` | Workflow (Lead Confirmed) | Full lead-to-student with parent + enrollment + fee init |
| `preventDuplicateAttendance` | Before Create (Attendance) | COQL-based duplicate rejection with user alert |
| `calculateAttendancePercentage` | After Save (Attendance) | Live rollup of attendance % onto Student record |
| `calculateRanksAndGrades` | After Save (Marks) | Assigns A+/A/B/C/F grades + class rank |
| `recalculateFeeStatus` | After Save (Fee_Payments) | Recalculates outstanding dues + payment status |
| `studentAtRiskEarlyWarning` | Scheduled Daily | Scans all students, flags At-Risk, sends staff alerts |

---

## 👪 Zoho Creator Parent Portal

Built in **Zoho Creator** as `School_Parent_App`.

### 4 Core Dashboard Sections

| Section | What Parents See |
|---------|-----------------|
| **Student Profile** | Photo, Student ID, class, section, class teacher contact |
| **Attendance Tracker** | Real-time %, total school days, present/absent count, full chronological log |
| **Examination Report Card** | Grade sheet per subject — marks, letter grade, class rank per exam |
| **Fee Ledger & Receipts** | Annual fee, amount paid, outstanding dues, full installment history |

### Multi-Child Family Switcher
- Parents with multiple enrolled children see a **Student Switcher** tab
- Switching updates all four sections dynamically without page reload
- Single login covers all children — no separate accounts

---

## 🔒 Security Model

### Row-Level Data Isolation
All parent portal queries are filtered at the database level:
```javascript
// Zoho Creator criterion on every report:
Parent_Email == zoho.loginuser
```
- URL tampering or parameter injection returns zero records
- Session-scoped in Flask: `session["parent_email"]` controls all queries

### Student ID Integrity
- `Student_ID` is **read-only** post-creation via CRM field-level security
- Cannot be edited manually — format integrity enforced at generation

### Duplicate Attendance Guard (Two Layers)
1. **DB Constraint**: Unique index on `unique_key = "{student_id}_{date}"`
2. **App Layer**: Pre-check before insert — rejects with a descriptive flash message

---

## 📈 Automated Grading Engine

```
Percentage = (Marks Obtained / Max Marks) × 100

Percentage     Grade
────────────────────
90% – 100%  →  A+
75% –  89%  →  A
60% –  74%  →  B
40% –  59%  →  C
 < 40%      →  F
```

### At-Risk Early Warning Logic

```python
def evaluate_defaulters():
    for student in Student.query.all():
        if student.attendance_percentage < 75 or student.average_marks < 40:
            student.academic_status = "At-Risk"
        else:
            student.academic_status = "Active"
    db.session.commit()
```

Runs on every dashboard load + scheduled daily in Zoho CRM with automated staff alert emails.

---

## 👤 Author

**Kiran**
- GitHub: [@kiran312003](https://github.com/kiran312003)
- Platform: Zoho CRM & Zoho Creator
- Submission: September 2026

---

## 📄 License

Submitted as part of a Zoho School Management System technical assessment.

---

*Built with Flask, SQLAlchemy, Gunicorn, and the Zoho One platform*
