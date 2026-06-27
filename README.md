# Alma Lead Management System

A full-stack lead management application for an immigration law firm. Prospects submit their information through a public form; attorneys manage leads through a private dashboard.

## Table of Contents

- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Quick Start — Docker Compose](#quick-start--docker-compose)
- [Local Development (without Docker)](#local-development-without-docker)
  - [Backend](#backend-setup)
  - [Frontend](#frontend-setup)
- [Running Tests](#running-tests)
- [API Reference](#api-reference)
- [Environment Variables](#environment-variables)
- [Lead States](#lead-states)

---

## Architecture

```
frontend/    Next.js 14 (App Router, TypeScript, Tailwind CSS)
src/         FastAPI backend (Python, async SQLAlchemy, Alembic)
tests/       Pytest integration tests (SQLite in-memory)
uploads/     Local resume file storage (gitignored)
```

**Stack:** FastAPI · PostgreSQL · Next.js 14 · NextAuth.js · Resend · Docker Compose

---

## Prerequisites

Depending on the setup path you choose:

| Tool | Version | Required for |
|------|---------|--------------|
| Docker & Docker Compose | v2+ | Docker path |
| Python | 3.9+ | Local backend |
| Node.js | 20+ | Local frontend |
| PostgreSQL | 14+ | Local backend (without Docker) |

---

## Quick Start — Docker Compose

This is the recommended path. It starts PostgreSQL, the FastAPI backend, and the Next.js frontend with a single command.

**Step 1 — Copy environment files**

```bash
cp .env.example .env
cp frontend/.env.local.example frontend/.env.local
```

**Step 2 — Fill in required values**

Open `.env` and set at minimum:

```dotenv
SECRET_KEY=<output of: python -c "import secrets; print(secrets.token_hex(32))">
RESEND_API_KEY=re_...          # from https://resend.com (optional — email is skipped if unset)
ATTORNEY_EMAIL=you@example.com
EMAIL_FROM=noreply@yourdomain.com
```

Open `frontend/.env.local` and set:

```dotenv
NEXTAUTH_SECRET=<any long random string>
```

**Step 3 — Build and start all services**

```bash
docker compose up --build
```

The first run downloads base images and installs dependencies — this takes a few minutes. Subsequent starts are fast.

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| Interactive API docs | http://localhost:8000/docs |

**Step 4 — Create an attorney account**

Open http://localhost:3000/register and create your first account, or use the API directly:

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "you@example.com", "password": "secret"}'
```

**Stopping the stack**

```bash
docker compose down          # stop containers, keep DB volume
docker compose down -v       # stop and delete the DB volume (full reset)
```

---

## Local Development (without Docker)

Use this path if you want hot-reload for both services during development.

### Backend Setup

**Requirements:** Python 3.9+, a running PostgreSQL instance

**1. Create and activate a virtual environment**

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
```

**2. Install Python dependencies**

```bash
pip install -r requirements.txt
pip install -e .                   # installs the alma_assignment package in editable mode
```

**3. Configure environment variables**

```bash
cp .env.example .env
```

Edit `.env` — the values you must change for local development:

```dotenv
DATABASE_URL=postgresql+asyncpg://alma:alma@localhost:5432/alma
SECRET_KEY=<generate with: python -c "import secrets; print(secrets.token_hex(32))">
RESEND_API_KEY=re_...              # optional; email is skipped when unset
ATTORNEY_EMAIL=you@example.com
EMAIL_FROM=noreply@yourdomain.com
CORS_ORIGINS=["http://localhost:3000"]
```

**4. Create the database and run migrations**

Make sure PostgreSQL is running and the `alma` database exists:

```bash
psql -U postgres -c "CREATE USER alma WITH PASSWORD 'alma';"
psql -U postgres -c "CREATE DATABASE alma OWNER alma;"
```

Then apply migrations:

```bash
alembic upgrade head
```

**5. Start the API server**

```bash
uvicorn alma_assignment.main:app --reload
```

The backend is now available at http://localhost:8000.  
Interactive docs are at http://localhost:8000/docs.

---

### Frontend Setup

Open a **new terminal** (keep the backend running).

**Requirements:** Node.js 20+

**1. Install dependencies**

```bash
cd frontend
npm install
```

**2. Configure environment variables**

```bash
cp .env.local.example .env.local
```

The defaults work for local development, but you must set `NEXTAUTH_SECRET`:

```dotenv
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=<any long random string>
```

**3. Start the development server**

```bash
npm run dev
```

The frontend is now available at http://localhost:3000.

---

## Running Tests

Tests run against an in-memory SQLite database. No running PostgreSQL or external services needed.

```bash
# From the project root with the virtual environment active
pytest tests/ -v
```

Email sending is automatically skipped when `RESEND_API_KEY` is not set, so tests are fully self-contained.

---

## API Reference

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/api/v1/leads` | Public | Submit a lead (`multipart/form-data` with resume file) |
| `POST` | `/api/v1/auth/register` | Public | Register an attorney account |
| `POST` | `/api/v1/auth/login` | Public | Obtain a JWT access token |
| `GET` | `/api/v1/leads` | Bearer JWT | List leads (paginated, filterable by state) |
| `GET` | `/api/v1/leads/{id}` | Bearer JWT | Get a single lead |
| `PATCH` | `/api/v1/leads/{id}/state` | Bearer JWT | Transition lead to `REACHED_OUT` |
| `GET` | `/api/v1/leads/{id}/resume` | Bearer JWT | Download the resume file |
| `GET` | `/health` | Public | Health check |

Full interactive docs: http://localhost:8000/docs

---

## Environment Variables

### Backend (`.env`)

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | Async PostgreSQL URL — `postgresql+asyncpg://user:pass@host:port/db` |
| `SECRET_KEY` | Yes | JWT signing secret — generate with `python -c "import secrets; print(secrets.token_hex(32))"` |
| `ACCESS_TOKEN_EXPIRE_HOURS` | No | JWT lifetime in hours (default: `8`) |
| `RESEND_API_KEY` | No | Resend API key for transactional email — email is skipped when unset |
| `ATTORNEY_EMAIL` | No | Inbox that receives new lead notifications |
| `EMAIL_FROM` | No | Sender address for outgoing emails |
| `STORAGE_BACKEND` | No | `local` (default) or `s3` |
| `UPLOADS_DIR` | No | Local upload path (default: `./uploads`) |
| `CORS_ORIGINS` | No | JSON array of allowed frontend origins (default: `["http://localhost:3000"]`) |

S3 variables (`AWS_BUCKET`, `AWS_REGION`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`) are only required when `STORAGE_BACKEND=s3`.

### Frontend (`frontend/.env.local`)

| Variable | Required | Description |
|----------|----------|-------------|
| `NEXT_PUBLIC_API_URL` | Yes | URL of the FastAPI backend visible to the browser |
| `NEXTAUTH_URL` | Yes | Canonical URL of the Next.js app |
| `NEXTAUTH_SECRET` | Yes | NextAuth signing secret — any long random string |

---

## Lead States

```
PENDING  ──(attorney clicks "Mark as Reached Out")──►  REACHED_OUT
```

State transitions are one-way and enforced on both the API and the frontend.
