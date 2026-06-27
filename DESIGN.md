# Design Choices

This document explains the design decisions made in this project, derived directly from the code. Each section covers what was chosen, why, and the real trade-offs.

---

## Architecture: Decoupled Backend + Frontend

The project is split into two independent services as given in the requirements: a FastAPI backend (`src/`) and a Next.js 14 frontend (`frontend/`). They communicate over HTTP, orchestrated together via Docker Compose with a third service for PostgreSQL.

**Pros:**
- Each service can be built, deployed, and scaled independently.
- The backend API is immediately usable by other clients (mobile, other tools) without changes.
- The Next.js frontend build happens in its own Docker image and doesn't need Python tooling.

**Cons:**
- Two runtimes to maintain (Python + Node).
- Local development requires both services running. The `BACKEND_URL` env var has to be set correctly in each context (`http://backend:8000` inside Docker, `http://localhost:8000` outside it) — the code in `lib/api.ts` handles this with a fallback chain but it can be a source of confusion.
- CORS has to be explicitly configured (`cors_origins` in `core/config.py`), and the default is hardcoded to `http://localhost:3000`.

---

## Backend: FastAPI with Full Async

Every database call, file write, and email dispatch uses async/await. The DB engine is `create_async_engine` with `asyncpg`, sessions are `AsyncSession`, file writes use `aiofiles`, and email sends that would block the response are dispatched via FastAPI's `BackgroundTasks`.

**Pros:**
- The web server (uvicorn) can handle concurrent requests without threads blocking on I/O.
- `BackgroundTasks` for email means the HTTP response returns to the user immediately after the lead is saved, without waiting for Resend's API.
- `pool_pre_ping=True` on the engine means stale DB connections are detected and recycled before use.

**Cons:**
- `BackgroundTasks` run in the same process. If the worker crashes or the process restarts mid-email, the notification is silently lost. There is no retry or queue.
- The email service swallows all exceptions (`except Exception: logger.exception(...)`) so email failures are invisible unless logs are monitored.

---

## Database: PostgreSQL + SQLAlchemy 2.0 + Alembic

Production uses PostgreSQL 16 (via `asyncpg`). The schema is managed by Alembic migrations (one migration: `001_initial_schema.py`). Models use SQLAlchemy 2.0's `Mapped`/`mapped_column` typed API.

**Pros:**
- Alembic gives an explicit, versioned migration history. The `downgrade()` function in the migration can roll back the schema cleanly.
- SQLAlchemy 2.0's typed columns catch type mismatches at static analysis time.
- `server_default=func.now()` means timestamps are set by the database, not by application clock — consistent even across multiple instances.
- The `email` column on both tables is indexed (`index=True`), so lookups by email (used in auth and duplicate checks) are fast.

**Cons:**
- The `updated_at` column uses `onupdate=lambda: datetime.now(timezone.utc)` — this triggers only when SQLAlchemy itself performs an update, not on raw SQL updates. It also uses the application clock rather than the DB clock, which differs from `created_at`.
- There is no foreign key from `leads` to `attorneys`. Any attorney can see all leads, and there is no ownership model.
- Duplicate emails are not prevented on `leads` (no unique constraint). The same person can submit multiple applications.

---

## Data Model: Two-State Lead FSM

Leads have exactly two states: `PENDING` and `REACHED_OUT`, defined as a Python `enum.Enum` that maps to a PostgreSQL `ENUM` type. The state transition is enforced in application code in `leads.py`: only `PENDING → REACHED_OUT` is allowed. Attempting to transition an already-`REACHED_OUT` lead returns `409 Conflict`. Attempting to set any state other than `REACHED_OUT` returns `422`.

**Pros:**
- The finite state machine is small and its rules fit in a few lines of code. Easy to understand.
- The PostgreSQL enum type rejects invalid values at the DB level as a second line of defense.
- The `409` response for a double-transition is semantically correct and is tested explicitly.

**Cons:**
- There is no way to revert a lead back to `PENDING`. If an attorney marks someone by mistake, there is no correction path.
- The enum is defined in both the SQLAlchemy model and the Alembic migration. Adding a new state requires changes in at least three places: the Python enum, the migration, and the frontend `LeadState` type alias in `lib/api.ts`.

---

## File Storage: Local Filesystem with S3 Stub

Uploaded resumes are saved to `./uploads/{lead_id}/{original_filename}` using `aiofiles`. The storage backend is selected by the `STORAGE_BACKEND` config value. When `local`, files go to disk. When `s3`, the code raises `NotImplementedError`.

The lead row is flushed to the DB first (`await db.flush()`) to get the UUID before the file is written, then the path is committed only after the file write succeeds.

**Pros:**
- The `db.flush()` before file write means the lead ID exists when the file is saved, so the directory is namespaced per lead — no filename collisions across leads.
- The upload logic validates MIME type at the API layer and file size after reading the full content, providing two checkpoints.
- The abstraction (`save_resume` dispatching to `_save_locally` or `_save_to_s3`) makes it straightforward to wire up real S3 later.

**Cons:**
- The entire file is read into memory (`content = await file.read()`) before size is checked. A 10 MB file is held in RAM before the check rejects it.
- If the file write succeeds but `db.commit()` fails afterward, the file is left on disk orphaned with no DB record pointing to it.
- In Docker, uploads are bind-mounted (`./uploads:/app/uploads`). If two backend replicas ran, they would write to separate filesystems and the resume would not be found by a different replica.
- The download endpoint (`GET /leads/{id}/resume`) requires attorney auth, but the `/uploads` static mount in `main.py` serves files publicly at their path. Anyone who knows the UUID and filename can bypass auth and access a resume directly.

---

## Authentication: JWT via python-jose + bcrypt

Attorneys register and log in via `/api/v1/auth`. Passwords are hashed with bcrypt (via passlib). On login, a JWT is created with HS256, expiring in 8 hours. The token is validated on every protected request by `get_current_attorney` in `dependencies.py`, which also queries the DB to confirm the attorney still exists.

**Pros:**
- bcrypt is a strong, deliberately slow hashing algorithm suitable for passwords.
- The DB lookup on every request means a deleted attorney is rejected immediately, even if their token has not expired.
- Token expiry is configurable via `access_token_expire_hours` in settings.

**Cons:**
- There is no token revocation mechanism. If a token is stolen, it remains valid until expiry (up to 8 hours).
- The register endpoint (`POST /api/v1/auth/register`) is open — anyone can create an attorney account. There is no invite mechanism, admin approval, or rate limiting.
- `secret_key` defaults to a placeholder string in `config.py`. If `.env` is not configured in production, JWTs are signed with the known default.

---

## Frontend: Next.js 14 App Router with Mixed Rendering

The dashboard (`app/dashboard/page.tsx`) is a server component: it fetches leads server-side using the session token and returns HTML. Interactive parts — the apply form (`app/apply/page.tsx`) and the leads table (`components/LeadsTable.tsx`) — are client components (`"use client"`).

**Pros:**
- The dashboard data fetch happens on the server, so the page loads with data already rendered. No client-side loading state for the initial render.
- `cache: "no-store"` on the list fetch ensures attorneys always see the current state, not a stale cached response.
- Filtering by state and pagination are encoded in the URL (`?page=N&state=X`), so the URL is shareable and bookmarkable, and the browser back button works correctly.
- After marking a lead as reached out, `router.refresh()` re-triggers the server component fetch, updating the table without a full navigation.

**Cons:**
- The `token` is passed as a prop from the server component to `LeadsTable` (a client component). This puts the raw JWT in the client-side JavaScript bundle at runtime.
- The dashboard API call path in `LeadsTable` for resume download hits `/api/v1/leads/${leadId}/resume` — a relative URL — which works when the browser makes the call but relies on the browser being on `localhost:3000` which proxies or the backend being at the same origin. In production this would need a proxy or an absolute URL.
- There is no loading UI or Suspense boundary on the dashboard. If the backend is slow, the server component blocks and the user sees nothing until data arrives.

---

## Frontend Auth: NextAuth Credentials Provider

NextAuth's `CredentialsProvider` is used. On login, NextAuth calls the FastAPI `/auth/login` endpoint, gets a JWT back, and stores it in the NextAuth session under `token.accessToken`. The middleware (`middleware.ts`) uses NextAuth's built-in session check to protect `/dashboard` routes.

**Pros:**
- Route protection is a single file and one `matcher` — easy to extend to other protected paths.
- The FastAPI JWT and NextAuth's session lifetime are aligned: both are 8 hours (`maxAge: 8 * 60 * 60` in `authOptions` matches `access_token_expire_hours: 8` in backend config).
- Session strategy is `"jwt"`, so no database is needed for NextAuth sessions.

**Cons:**
- `(session as any).accessToken` and `(user as any).accessToken` use `any` casts to attach the custom field. TypeScript cannot catch misuse of the access token through the session object.
- If the FastAPI JWT expires before the NextAuth session, API calls will fail with 401 but the user will appear logged in to the frontend.

---

## Form Validation: Zod on the Frontend, MIME Check on the Backend

The apply form (`apply/page.tsx`) uses `react-hook-form` with a `zodResolver`. Zod validates name fields (non-empty), email format, file type (PDF/DOCX), and file size (≤10 MB) before the form submits. The backend independently checks MIME type and file size.

**Pros:**
- Users get immediate inline feedback without a network round-trip.
- The backend validation is independent — it cannot be bypassed by disabling JavaScript or calling the API directly.
- Zod schema doubles as a TypeScript type (`z.infer<typeof schema>`), so `FormValues` is always in sync with the validation rules.

**Cons:**
- MIME type is validated by the browser-reported `file.type` on the frontend and by the `content_type` header on the backend. Neither checks the actual file bytes — a malicious file could have a spoofed MIME type. The backend reads the full content to check size but does not parse or validate the file structure.
- The allowed MIME type list is duplicated: once in `storage.py` (`ALLOWED_MIME_TYPES`) and once in `apply/page.tsx`. They are currently in sync but could drift.

---

## Testing: SQLite with Dependency Override

Tests use `pytest-asyncio` and `httpx.AsyncClient` with `ASGITransport` to call the FastAPI app in-process. The `get_db` dependency is overridden to return a test `AsyncSession` backed by SQLite+aiosqlite. Each test function gets a fresh DB (function-scoped fixtures that `CREATE` and `DROP` all tables).

**Pros:**
- No real network calls, no running server needed. Tests are fast.
- The dependency override is clean — no patching or monkeypatching of the actual code.
- Tests cover the actual HTTP layer, request parsing, and response serialization, not just business logic in isolation.
- The `409` conflict case and `422` MIME rejection are tested explicitly.

**Cons:**
- SQLite and PostgreSQL have behavioral differences. The PostgreSQL `ENUM` type is created manually in the Alembic migration, but SQLite tests use `Base.metadata.create_all` which creates the tables without the Alembic migration — so the enum is handled differently. If a migration step has a PostgreSQL-specific behavior, tests would not catch it.
- Email sending is not tested. The email service is async but the tests never assert that `send_prospect_confirmation` or `send_attorney_notification` were called.
- File download (`GET /leads/{id}/resume`) is not covered by a test. The resume path written during a test is a relative path but the `uploads` directory used in tests is whatever `settings.uploads_dir` resolves to, not a temp directory.

---

## Infrastructure: Docker Compose with Multi-Stage Frontend Build

Docker Compose runs three services: `db` (postgres:16-alpine), `backend` (python:3.11-slim), and `frontend` (node:20-alpine, multi-stage). The backend's `command` runs `alembic upgrade head` before starting uvicorn. The backend `depends_on` the DB with `condition: service_healthy` using `pg_isready`.

**Pros:**
- The health check prevents the backend from starting before Postgres is actually accepting connections, not just running.
- The frontend Dockerfile uses three stages (deps → builder → runner with Next.js standalone output), keeping the final image small — only the compiled output and runtime are in the runner stage.
- Migrations run automatically on container start, so no manual migration step is needed after deployment.

**Cons:**
- Running `alembic upgrade head` on every container start adds latency. In a production cluster with rolling deployments, multiple instances could race to run migrations simultaneously.
- The `uploads` directory is a bind mount (`./uploads:/app/uploads`). This works for a single container but is not compatible with horizontal scaling unless a shared filesystem (NFS, EFS) is used.
- The attorney notification email in `email.py` hardcodes `http://localhost:3000` as the dashboard link, which will be wrong in any deployed environment.
