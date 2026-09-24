# 💰 fintrack-api

> A production-grade personal finance tracker REST API built with **FastAPI**, **PostgreSQL**, **Redis**, and **Celery**. Designed as a backend engineering portfolio project showcasing async architecture, domain modeling, scheduled background jobs, and complex SQL aggregations.

![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.135.1-009688?style=flat-square&logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=flat-square&logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-7-DC382D?style=flat-square&logo=redis&logoColor=white)
![Celery](https://img.shields.io/badge/Celery-5.6.3-37814A?style=flat-square&logo=celery&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

---

## 📋 Table of Contents

- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Architecture](#-architecture)
- [Project Structure](#-project-structure)
- [Getting Started](#-getting-started)
- [Environment Variables](#-environment-variables)
- [API Reference](#-api-reference)
- [Background Jobs](#-background-jobs)
- [Running Tests](#-running-tests)
- [Design Decisions](#-design-decisions)
- [Roadmap](#-roadmap)

---

## ✨ Features

- 🔐 **JWT Authentication** — secure register/login with bcrypt password hashing and refresh tokens
- 🏦 **Multi-account support** — track Checking, Savings, Credit Card, and Cash accounts
- 📊 **Transaction management** — soft-delete (records are never physically removed) with created/updated timestamps
- 🏷️ **Categories & Budgets** — user-defined categories with monthly spending limits and alert thresholds
- 📈 **Financial reports** — monthly summaries, category breakdowns, and daily cash flow with a running total (PostgreSQL CTE + window function)
- 📤 **Async exports** — request CSV or PDF exports that are generated in the background and delivered via email
- ⏰ **Scheduled jobs** — monthly budget carry-over, weekly summary emails, recurring transactions, and daily balance snapshots via Celery Beat
- 🔔 **Budget alerts** — automatic notifications when spending reaches 80% of a monthly budget
- 🐳 **Fully containerized** — Docker Compose setup for one-command local development
- ✅ **80%+ test coverage** — pytest with async support and factory-based test data

---

## 🛠 Tech Stack

| Layer | Tool | Version |
|---|---|---|
| Web Framework | FastAPI | 0.135.1 |
| ORM | SQLAlchemy (async) | 2.0 |
| Migrations | Alembic | 1.13.3 |
| Database | PostgreSQL | 16 |
| Cache / Broker | Redis | 7 |
| Task Queue | Celery + Celery Beat | 5.6.3 |
| Auth | python-jose + passlib | — |
| Config | Pydantic Settings | 2.x |
| Email | FastAPI-Mail | 1.4 |
| Testing | pytest + pytest-asyncio | — |
| Linting | Ruff + mypy | — |
| CI/CD | GitHub Actions | — |
| Containers | Docker + Docker Compose | — |

---

## 🏗 Architecture

The project follows a strict **three-layer architecture** to keep concerns separated and make each layer independently testable:

```
HTTP Request
     │
     ▼
┌─────────────┐
│  Endpoints  │  ← Input validation (Pydantic), HTTP status codes
│  app/api/   │    No business logic here
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Services   │  ← Business logic, orchestration, Celery task dispatch
│ app/services│    Immutability rules, budget checks, event triggers
└──────┬──────┘
       │
       ▼
┌──────────────┐
│ Repositories │  ← All SQL queries, no raw SQL in services
│  app/repos/  │    One repository per model
└──────┬───────┘
       │
       ▼
  PostgreSQL
```

**Background task flow:**

```
API Request → Celery Task → Redis Broker → Worker → Email / File / Notification
                                  │
                          Celery Beat Scheduler
                      (cron-style periodic tasks)
```

---

## 📁 Project Structure

```
backend-finance-api/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   ├── auth.py
│   │       │   ├── accounts.py
│   │       │   ├── transactions.py
│   │       │   ├── categories.py
│   │       │   ├── budgets.py
│   │       │   ├── reports.py
│   │       │   ├── exports.py
│   │       │   ├── exchange_rates.py
│   │       │   └── recurring_transactions.py
│   │       └── router.py
│   ├── core/
│   │   ├── config.py          # Pydantic Settings
│   │   ├── security.py        # JWT + bcrypt
│   │   └── dependencies.py    # FastAPI deps (get_current_user, etc.)
│   ├── db/
│   │   ├── base.py            # DeclarativeBase + TimestampMixin
│   │   ├── session.py         # Async engine + session factory
│   │   └── sync_session.py    # Sync session for Celery tasks
│   ├── models/
│   │   ├── user.py
│   │   ├── account.py
│   │   ├── transaction.py
│   │   ├── category.py
│   │   ├── budget.py
│   │   ├── export.py          # ExportJob
│   │   ├── exchange_rate.py
│   │   └── recurring_transaction.py
│   ├── schemas/               # Pydantic request/response models
│   ├── services/              # Business logic layer
│   ├── repositories/          # DB query layer
│   ├── workers/
│   │   ├── celery_app.py      # Celery + Beat config
│   │   ├── tasks.py           # Async notification + export tasks
│   │   └── schedules.py       # Beat periodic schedule definitions
│   ├── utils/
│   │   ├── email.py
│   │   ├── export.py          # CSV / PDF generation
│   │   └── currency.py        # NUMERIC(12,2) helpers
│   └── main.py                # FastAPI app entrypoint
├── tests/
│   ├── conftest.py            # Fixtures, test DB, client setup
│   └── test_*.py              # One file per feature (HTTP-level tests)
├── alembic/
│   ├── versions/
│   └── env.py
├── .github/
│   └── workflows/
│       └── ci.yml             # Lint + test + coverage pipeline
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── pytest.ini
├── .coveragerc
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites

- [Python 3.12](https://www.python.org/downloads/) — on macOS the simplest route is
  [uv](https://docs.astral.sh/uv/): `curl -LsSf https://astral.sh/uv/install.sh | sh && uv python install 3.12`
- A Docker runtime with Compose v2 — [Docker Desktop](https://docs.docker.com/get-docker/),
  [OrbStack](https://orbstack.dev/) or [Colima](https://github.com/abiosoft/colima)
- [Git](https://git-scm.com/)

Run `make doctor` to check that everything is in place.

### Quick start

```bash
git clone https://github.com/eduardorocha-dev/backend-finance-api
cd backend-finance-api
make setup   # checks prerequisites, creates .venv, creates .env, starts Postgres + Redis, runs migrations
make dev     # API with hot-reload at http://localhost:8000
```

Background jobs (exports, emails, scheduled tasks) need Celery. Run each in its own terminal:

```bash
make worker  # Celery worker
make beat    # Celery Beat scheduler
```

Run the tests with `make test`. They use the `db_test` container on port 5433, which `make setup` already started.

To run everything in containers instead (API, worker and beat included), use `make start`. Don't run it at
the same time as `make dev`, because both use port 8000.

### Manual setup

`make setup` runs these steps:

1. `python3.12 -m venv .venv && .venv/bin/pip install -r requirements.txt`
2. `cp .env.example .env`, then set `SECRET_KEY` to the output of `openssl rand -hex 32`
3. `docker compose up -d --wait db db_test redis` (infrastructure only)
4. `.venv/bin/alembic upgrade head`

### Verify

| URL | Description |
|---|---|
| http://localhost:8000/docs | Swagger UI (interactive API docs) |
| http://localhost:8000/redoc | ReDoc API docs |
| http://localhost:8000/health | Health check endpoint |

---

## 🛠 Makefile Reference

All common tasks are available via `make`. Run `make <command>` from the project root.

### Setup

| Command | Description |
|---|---|
| `make doctor` | Check that Python 3.12 and Docker are installed and running |
| `make install` | Create `.venv` and install all dependencies |
| `make env` | Create `.env` from `.env.example` with a generated `SECRET_KEY` |
| `make setup` | First-time setup: doctor + install + env + start infra + run migrations |

### Docker

| Command | Description |
|---|---|
| `make up` | Start infrastructure only (PostgreSQL + Redis) |
| `make down` | Stop and remove all containers |
| `make start` | Start all services in background, including API and Celery workers |
| `make logs` | Stream logs from all containers |
| `make logs-api` | Stream logs from the API container only |
| `make logs-worker` | Stream logs from the Celery worker container only |

### Database

| Command | Description |
|---|---|
| `make migrate` | Apply all pending Alembic migrations |
| `make migration name=<desc>` | Auto-generate a new migration from model changes |
| `make db-reset` | Wipe and recreate the database from scratch |

### Tests & Coverage

| Command | Description |
|---|---|
| `make test` | Run test suite locally using `.venv` |
| `make test-full` | Start infra, wait for readiness, then run coverage locally |
| `make coverage` | Run tests with coverage report (opens HTML report in browser) |
| `make coverage-docker` | Run tests with coverage report inside a Docker container |

### Code Quality

| Command | Description |
|---|---|
| `make lint` | Check code style with Ruff |
| `make format` | Auto-format code with Ruff |
| `make typecheck` | Run static type checking with mypy |
| `make check` | Run lint + typecheck + tests in sequence |
| `make ci` | Full CI pipeline: start infra + lint + typecheck + coverage |

### Development

| Command | Description |
|---|---|
| `make dev` | Start infra + run migrations + start local Uvicorn server with hot-reload |
| `make worker` | Run the Celery worker locally |
| `make beat` | Run the Celery Beat scheduler locally |

---

## 🔑 Environment Variables

| Variable | Description | Default |
|---|---|---|
| `SECRET_KEY` | JWT signing key (use `openssl rand -hex 32`) | **required** |
| `DATABASE_URL` | Async PostgreSQL URL | `postgresql+asyncpg://...` |
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379/0` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT access token lifetime | `30` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | JWT refresh token lifetime | `7` |
| `MAIL_SERVER` | SMTP server hostname | `smtp.gmail.com` |
| `MAIL_USERNAME` | SMTP username / email | — |
| `MAIL_PASSWORD` | SMTP password or app password | — |
| `AWS_ACCESS_KEY_ID` | S3 key for file uploads (optional) | — |
| `AWS_SECRET_ACCESS_KEY` | S3 secret key for file uploads (optional) | — |
| `AWS_BUCKET_NAME` | S3 bucket name for exports (optional) | — |

See `app/core/config.py` for the full list of settings and their defaults.

---

## 📡 API Reference

Full interactive documentation is available at `/docs` when the server is running.

### Authentication

```http
POST /api/v1/auth/register
POST /api/v1/auth/login
POST /api/v1/auth/refresh
GET  /api/v1/auth/me
```

### Accounts

```http
GET    /api/v1/accounts
POST   /api/v1/accounts
GET    /api/v1/accounts/{id}
PATCH  /api/v1/accounts/{id}
DELETE /api/v1/accounts/{id}
GET    /api/v1/accounts/{id}/balance
```

### Transactions

```http
GET    /api/v1/transactions?account_id=&category_id=&type=&date_from=&date_to=
POST   /api/v1/transactions
GET    /api/v1/transactions/{id}
PATCH  /api/v1/transactions/{id}
DELETE /api/v1/transactions/{id}
```

### Categories

```http
GET    /api/v1/categories
POST   /api/v1/categories
GET    /api/v1/categories/{id}
PATCH  /api/v1/categories/{id}
DELETE /api/v1/categories/{id}
```

### Budgets

```http
GET    /api/v1/budgets
POST   /api/v1/budgets
GET    /api/v1/budgets/usage        # spend % per category this month
GET    /api/v1/budgets/{id}
PATCH  /api/v1/budgets/{id}
DELETE /api/v1/budgets/{id}
```

### Reports

```http
GET /api/v1/reports/monthly       # income vs expense summary
GET /api/v1/reports/categories    # breakdown by category
GET /api/v1/reports/cashflow      # daily net cash flow + running total
```

### Exports

```http
POST /api/v1/exports              # request async CSV or PDF
GET  /api/v1/exports/{id}         # poll status + get download link
```

### Exchange Rates

```http
GET    /api/v1/exchange-rates?from_currency=&to_currency=&limit=   # rate history for a pair
POST   /api/v1/exchange-rates
GET    /api/v1/exchange-rates/latest?from_currency=&to_currency=
POST   /api/v1/exchange-rates/convert
GET    /api/v1/exchange-rates/{id}
PATCH  /api/v1/exchange-rates/{id}
DELETE /api/v1/exchange-rates/{id}
```

### Recurring Transactions

```http
GET    /api/v1/recurring-transactions
POST   /api/v1/recurring-transactions
GET    /api/v1/recurring-transactions/{id}
PATCH  /api/v1/recurring-transactions/{id}
DELETE /api/v1/recurring-transactions/{id}
```

---

## ⏰ Background Jobs

### Event-Driven

| Task | Trigger | Description |
|---|---|---|
| `send_budget_alert` | Transaction creation | Fires when a category reaches 80% of its monthly budget |
| `generate_export` | `POST /exports` | Generates CSV or PDF file asynchronously |

### Scheduled (Celery Beat)

| Task | Schedule | Description |
|---|---|---|
| `reset_monthly_budgets` | 1st of month, 00:00 | Copies last month's budgets into the new month |
| `send_weekly_summaries` | Monday, 08:00 | Emails each user a weekly spending summary |
| `snapshot_balances` | Daily, 23:59 | Caches account balances for fast lookups |
| `process_recurring_transactions` | Daily, 00:05 | Creates transactions from due recurring templates |

---

## 🧪 Running Tests

```bash
# Run all tests
make test

# Run one feature's tests
.venv/bin/pytest tests/test_transactions.py

# Tests with coverage report (opens the HTML report)
make coverage
```

Tests use a dedicated PostgreSQL database (`fintrack_test` on port 5433) spun up via Docker Compose. Make sure the test database container is running before executing the test suite.

---

## 💡 Design Decisions

**Soft-deleted transactions**
Transactions are never physically removed: `DELETE` sets `is_deleted`, and every query filters deleted rows out. Each row carries `created_at` and `updated_at`. Edits currently update the row in place; turning them into correcting entries that reference the original (a fully immutable ledger) is on the roadmap.

**CTEs and window functions for reports**
The cash-flow report aggregates one row per day in a CTE, then adds `SUM(net) OVER (ORDER BY period)` so each day also carries the running total since the start of the range. Postgres computes it in a single query.

**NUMERIC(12,2) for money**
All monetary values are stored as `NUMERIC(12,2)` in PostgreSQL — never `FLOAT`. Floating-point arithmetic is unsuitable for money due to precision errors.

**Balance snapshots**
A Celery Beat task stores each account's balance in `balance_snapshot` every night. The balance endpoint still sums all transactions live, which is always correct but gets slower as history grows. Reading the snapshot and summing only the transactions since it was taken is on the roadmap.

**Repository pattern**
All database queries live in repository classes. Services never write raw SQL. This keeps service logic readable and database access in one place.

**Celery Beat over cron**
Scheduled tasks are defined in code alongside the rest of the application, version-controlled, and don't require any external cron server or infrastructure configuration.

---

## 🗺 Roadmap

- [x] Multi-currency support with exchange rate table
- [x] Recurring transaction templates
- [ ] Immutable ledger: edits create correcting entries instead of updating in place
- [ ] Serve account balances from the nightly snapshot plus transactions since then
- [ ] CSV import from bank statements
- [ ] Spending insights endpoint (month-over-month comparisons)
- [ ] WebSocket support for real-time budget alerts
- [ ] Frontend client (React + Recharts)

---

## 📄 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

<p align="center">Built as a backend engineering portfolio project — <a href="https://github.com/eduardorocha-dev">@eduardorocha-dev</a></p>
