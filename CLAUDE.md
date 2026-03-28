# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

This project uses `just` as the task runner (see `justfile`).

```bash
# Development
just run                              # Start API with hot reload (uvicorn)
just infra-up                         # Start Docker services (Postgres + Redis)
just infra-down                       # Stop Docker services
just dev-setup                        # Full dev environment setup
just generate-fernet-key              # Generate a new Fernet key for encrypting SMTP credentials

# Migrations
just migrate-up                       # Apply all pending migrations
just migrate-down                     # Revert last migration
just migrate-create "description"     # Autogenerate migration from model changes
just migrate-status                   # Show current DB version vs heads
just migrate-stamp HEAD               # Mark DB as up-to-date without running SQL

# Admin
just create-admin EMAIL PASSWORD [FULL_NAME]
```

No test suite exists in this project.

The API is accessible at `http://127.0.0.1:8000` with Swagger docs at `/docs`.

## Architecture

FastAPI backend using a **Router → Service → Model** layered pattern.

**Entry point:** `main.py` → `app/main_app.py` (lifespan initializes DB + Redis, registers routers under `/api/v1`)

### Layers

- **`app/routers/`** — Thin route handlers. Validate inputs, call services, return responses.
- **`app/services/`** — All business logic lives here. Services take an `AsyncSession` and sometimes the current user.
- **`app/models/`** — SQLAlchemy 2.0 async ORM models. Two files: `user.py` and `academic.py`.
- **`app/schemas/`** — Pydantic DTOs for request/response validation.
- **`app/core/`** — `config.py` (pydantic-settings, reads `.env`) and `security.py` (JWT, bcrypt, Fernet).
- **`app/db/session.py`** — Async engine, `AsyncSession` factory, Redis client.
- **`app/deps.py`** — FastAPI `Depends()` helpers: DB session, Redis, current authenticated user.

### Data Model

- All primary keys are UUIDs.
- `User` (roles: `admin` / `professor`) → owns `Course`s
- `Subject` + `User(professor)` → `Course` (term + year)
- `Course` → `Evaluation`s (percentage + type) and `Enrollment`s
- `Student` + `Course` → `Enrollment` (unique pair, tracks `final_grade`)
- `Evaluation` + `Enrollment` → `EvaluationGrade` (grade ≤ evaluation.percentage enforced in service layer)

### RBAC

- **Admin**: full visibility and edit rights across all entities.
- **Professor**: can only see and edit entities belonging to their own courses.
- Enforced inside service functions via `_is_admin()` from `app/services/common.py`.

### Auth Flow

JWT-based with refresh tokens stored in Redis (keyed by `jti`).

- `POST /api/v1/auth/login` → returns short-lived access token + long-lived refresh token
- `POST /api/v1/auth/refresh` → validates Redis jti, issues new access token
- `POST /api/v1/auth/logout` → deletes jti from Redis
- Password reset flow sends a time-limited JWT link via SMTP to the user's email.

### SMTP / Email

Per-user SMTP credentials are stored encrypted with Fernet (`SMTP_CREDENTIALS_KEY` env var). If a user has no credentials, the global `SMTP_*` env vars are used as fallback.

### Migrations

Alembic is the source of truth for the production schema. For NOT NULL column additions: add as nullable → deploy + backfill → add NOT NULL constraint in a follow-up migration. Use `just migrate-stamp HEAD` to resolve duplicate-table errors when the schema already exists.

### Deployment

- **Local infra:** Docker Compose (Postgres 16, Redis 7).
- **Production:** Vercel (Python 3.13 runtime, `vercel.json` configured).
- Database is Neon (serverless Postgres); `config.py` rewrites `postgres://` → `postgresql+asyncpg://` and adjusts SSL params automatically.
