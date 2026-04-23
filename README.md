# HackIE3 | Event Management API

A feature-rich Event Management REST API built with Flask, featuring JWT authentication, role-based access control, QR ticketing, team registrations, automated certificate dispatch, mass email, and admin analytics.

---

## Key Features

### 1. Authentication & RBAC
- **Sign Up / Sign In / Logout** with JWT tokens.
- Two roles: **Admin** (full management) and **Participant** (browse, register, view history).
- Admins can activate/deactivate user accounts.

### 2. Event Management (Admin)
- Full **CRUD** for events (workshops, hackathons, seminars, competitions).
- **Filtering** by status, event type, branch, and batch year.
- **Bulk status updates** on registrations (Registered -> Shortlisted -> Selected).
- **Dashboard stats**: participant count, event count, registrations, attendance rate.

### 3. Registration & Ticketing
- Participants register for events with **eligibility enforcement** (CGPA, branch, batch year).
- Each registration generates a unique **ticket ID** with a **QR code** (base64 PNG).
- Admins scan QR tickets to **mark attendance**.

### 4. Team Code System
- Team events define a `max_team_size`.
- Participants join teams by sharing a **team code** during registration.
- `GET /my/team/<code>` shows all teammates.

### 5. Certificates & Notifications
- **Auto-generated PDF certificates** dispatched via email to attendees (Celery async).
- **Selection letters** (PDF) auto-sent when a registration is marked "Selected".
- **Mass email** with optional branch/batch filters.
- **Daily deadline reminders** for eligible unregistered participants (Celery Beat).
- **Monthly PDF analytics report** sent to admin (Celery Beat).

### 6. Data Export
- Admin can export **participants, events, or registrations** as CSV via email.
- Participants can export their own **registration history** as CSV.

### 7. Performance
- **Redis caching** on participant profiles and event listings.
- **Celery + Redis** for all background tasks (emails, exports, certificates, reports).

---

## Technology Stack

- **Backend**: Flask + Flask-RESTful
- **Database**: SQLite (SQLAlchemy ORM)
- **Auth**: Flask-Security-Too + Flask-JWT-Extended
- **Task Queue**: Celery with Redis
- **Caching**: Flask-Caching with Redis
- **QR Codes**: qrcode + Pillow
- **PDF Generation**: xhtml2pdf / ReportLab
- **Email**: Flask-Mail (Gmail SMTP)
- **Documentation**: Flasgger (Swagger UI) + Postman Collection
- **Testing**: pytest + pytest-flask

---

## Installation

1. **Clone & setup**:
    ```bash
    python -m venv venv
    source venv/bin/activate        # Linux/Mac
    .\venv\Scripts\activate         # Windows
    pip install -r requirements.txt
    ```

2. **Environment variables**: Create a `.env` file:
    ```env
    SECRET_KEY=your-secret-key
    JWT_SECRET_KEY=your-jwt-secret
    MAIL_USERNAME=your-email@gmail.com
    MAIL_PASSWORD=your-app-password
    ```

3. **Start Redis** (required for caching and Celery):
    ```bash
    redis-server
    ```

---

## Running the Application

### Terminal 1 - Flask API
```bash
python app.py
```

### Terminal 2 - Celery Worker
```bash
celery -A app.celery_app worker --loglevel=info
```

### Terminal 3 - Celery Beat (scheduled tasks)
```bash
celery -A app.celery_app beat --loglevel=info
```

---

## API Documentation

- **Swagger UI**: `http://localhost:5000/apidocs` (interactive, auto-generated from code)
- **Postman Collection**: Import `postman_collection.json` into Postman
- **OpenAPI Spec**: `api.yaml`

---

## Seeding Sample Data

```bash
python seed_db.py
```

| Role        | Username       | Password      |
|-------------|----------------|---------------|
| Admin       | admin          | admin         |
| Participant | john_doe       | password123   |

This creates 12 participants, 10 events, and randomized registrations with team codes.

---

## Running Tests

```bash
pytest tests/ -v
```

Tests cover: authentication (signup, login, duplicates, wrong password), event lifecycle (create, register, duplicate block, QR, team codes), and admin operations (stats, list events, scan attendance, bulk status, certificates, RBAC enforcement).

---

## Project Structure

```
app.py                  # Flask entry point, Swagger config, Celery init
config.py               # App configuration (DB, JWT, Redis, Mail, Celery Beat)
seed_db.py              # Database seeder with sample data

api/
  auth_apis.py          # Sign up, Login, Logout
  event_api.py          # Browse events, register, QR ticket, team view
  participant_api.py    # Profile, stats, self-export
  admin_api.py          # Dashboard, CRUD, filtering, scan, certificates, mass email, export

models/
  user.py               # User model with RBAC
  students.py           # Participant profile model
  placement.py          # Event model
  application.py        # Registration model (ticket_id, team_code, attendance, certificate)

services/
  qr_service.py         # QR code generation (base64 PNG)
  certificate_service.py# PDF certificate generation & email dispatch
  AdminStudentCSV.py    # CSV export, mass email, monthly report, daily reminders, selection letters

tests/
  conftest.py           # Test fixtures (in-memory DB, admin/participant tokens)
  test_auth.py          # Authentication tests
  test_events.py        # Event & registration tests
  test_admin.py         # Admin dashboard & operations tests

api.yaml                # OpenAPI 3.0 specification
postman_collection.json # Postman collection with auto-token scripts
```

---

## AI Usage Disclosure

AI was used to assist with:
- **Scaffolding** the Swagger docstrings across all API endpoints.
- **Generating** the Postman collection JSON with auto-token test scripts.
- **Writing** the unit test suite (conftest fixtures, test cases).
- **Designing** the HTML templates for PDF certificates and selection letters.
- **Reviewing** the codebase for consistency, security issues, and Task C compliance.
