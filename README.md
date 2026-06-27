# Alma Lead Management System

A full-stack lead management application for an immigration law firm. Prospects submit their information through a public form; attorneys manage leads through a private dashboard.

## Architecture

```
frontend/    Next.js 14 (App Router, TypeScript, Tailwind)
src/         FastAPI backend (Python, async SQLAlchemy, Alembic)
tests/       Pytest integration tests (SQLite)
uploads/     Local resume storage (gitignored)
```

**Stack:** FastAPI · PostgreSQL · Next.js 14 · NextAuth.js · Resend · Docker Compose

## Quick Start (Docker Compose)

```bash
# 1. Copy and fill in environment files
cp .env.example .env
cp frontend/.env.local.example frontend/.env.local
# Edit both files with your Resend API key and secrets

# 2. Start everything
docker compose up --build

# Backend API:   http://localhost:8000
# Frontend:      http://localhost:3000
# API docs:      http://localhost:8000/docs
```

## Local Development (without Docker)

### Backend

Requirements: Python 3.9+, PostgreSQL running locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .

# Copy and edit environment
cp .env.example .env

# Run database migrations
alembic upgrade head

# Start the API server
uvicorn alma_assignment.main:app --reload
# → http://localhost:8000
```

### Frontend

Requirements: Node.js 20+

```bash
cd frontend
npm install

cp .env.local.example .env.local
# Edit with your NEXTAUTH_SECRET

npm run dev
# → http://localhost:3000
```

## Running Tests

```bash
# From the project root with the venv active
pytest tests/ -v
```

Tests use an in-memory SQLite database and mock no external services — email sending is skipped when `RESEND_API_KEY` is not set.

## API Reference

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/api/v1/leads` | Public | Submit a lead (multipart/form-data with resume file) |
| `POST` | `/api/v1/auth/register` | Public | Register an attorney account |
| `POST` | `/api/v1/auth/login` | Public | Obtain a JWT access token |
| `GET` | `/api/v1/leads` | Bearer JWT | List leads (paginated, filterable by state) |
| `GET` | `/api/v1/leads/{id}` | Bearer JWT | Get a single lead |
| `PATCH` | `/api/v1/leads/{id}/state` | Bearer JWT | Transition lead to `REACHED_OUT` |
| `GET` | `/api/v1/leads/{id}/resume` | Bearer JWT | Download the resume file |

Interactive docs: `http://localhost:8000/docs`

## Key Environment Variables

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | Async PostgreSQL URL (`postgresql+asyncpg://...`) |
| `SECRET_KEY` | JWT signing secret (generate with `python -c "import secrets; print(secrets.token_hex(32))"`) |
| `RESEND_API_KEY` | Resend API key for transactional email |
| `ATTORNEY_EMAIL` | Inbox that receives new lead notifications |
| `EMAIL_FROM` | Sender address for outgoing emails |
| `STORAGE_BACKEND` | `local` (default) or `s3` |
| `NEXTAUTH_SECRET` | NextAuth signing secret |
| `NEXT_PUBLIC_API_URL` | URL of the FastAPI backend (for the frontend) |

## Lead States

```
PENDING  ──(attorney clicks "Mark as Reached Out")──►  REACHED_OUT
```

State transitions are one-way and enforced on both the API and frontend.
