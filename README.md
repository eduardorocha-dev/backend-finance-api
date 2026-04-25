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
- 📊 **Transaction management** — immutable ledger with soft-delete and correction entries
- 🏷️ **Categories & Budgets** — user-defined categories with monthly spending limits and alert thresholds
- 📈 **Financial reports** — monthly summaries, category breakdowns, and cash flow using PostgreSQL CTEs and window functions
- 📤 **Async exports** — request CSV or PDF exports that are generated in the background and delivered via email
- ⏰ **Scheduled jobs** — monthly budget resets, weekly summary emails, and daily balance snapshots via Celery Beat
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
│   │       │   └── exports.py
│   │       └── router.py
│   ├── core/
│   │   ├── config.py          # Pydantic Settings
│   │   ├── security.py        # JWT + bcrypt
│   │   └── dependencies.py    # FastAPI deps (get_current_user, etc.)
│   ├── db/
│   │   ├── base.py            # DeclarativeBase + TimestampMixin
│   │   └── session.py         # Async engine + session factory
│   ├── models/
│   │   ├── user.py
│   │   ├── account.py
│   │   ├── transaction.py     # Transaction + CorrectionEntry
│   │   ├── category.py
│   │   ├── budget.py
│   │   └── export.py          # ExportJob
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
│   ├── api/                   # Integration tests
│   └── services/              # Unit tests
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

- [Python 3.12+](https://www.python.org/downloads/)
- [Docker + Docker Compose](https://docs.docker.com/get-docker/)
- [Git](https://git-scm.com/)

### 1. Clone the repository

```bash
git clone https://github.com/eduardorocha-dev/backend-finance-api
cd fintrack-api
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate        # macOS/Linux
# .venv\Scripts\activate         # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root and populate it with the variables listed in the [Environment Variables](#-environment-variables) section below.

Generate a secret key and set it as `SECRET_KEY`:

```bash
openssl rand -hex 32
```

### 5. Start infrastructure (PostgreSQL + Redis)

```bash
docker compose up -d
```

Verify containers are running:

```bash
docker compose ps
```

### 6. Run database migrations

```bash
alembic upgrade head
```

### 7. Start all services

Open three terminal tabs:

```bash
# Tab 1 — API server
uvicorn app.main:app --reload

# Tab 2 — Celery worker
celery -A app.workers.celery_app worker --loglevel=info

# Tab 3 — Celery Beat scheduler
celery -A app.workers.celery_app beat --loglevel=info
```

### 8. Verify

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
| `make install` | Create `.venv` and install all dependencies |
| `make setup` | First-time setup: install + start infra + run migrations |

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
GET /api/v1/reports/cashflow      # daily/weekly net cash flow
```

### Exports

```http
POST /api/v1/exports              # request async CSV or PDF
GET  /api/v1/exports/{id}         # poll status + get download link
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
| `reset_monthly_budgets` | 1st of month, 00:00 | Resets monthly spend counters |
| `send_weekly_summaries` | Monday, 08:00 | Emails each user a weekly spending summary |
| `snapshot_balances` | Daily, 23:59 | Caches account balances for fast lookups |

---

## 🧪 Running Tests

```bash
# Run all tests with coverage
pytest

# Run only unit tests
pytest tests/services/

# Run only integration tests
pytest tests/api/

# Generate HTML coverage report
pytest --cov=app --cov-report=html
open htmlcov/index.html
```

Tests use a dedicated PostgreSQL database (`fintrack_test` on port 5433) spun up via Docker Compose. Make sure the test database container is running before executing the test suite.

---

## 💡 Design Decisions

**Immutable transactions**
Financial records are never edited or hard-deleted. Updates create a correcting entry that references the original, matching the behavior of real accounting systems. This also provides a complete audit trail out of the box.

**NUMERIC(12,2) for money**
All monetary values are stored as `NUMERIC(12,2)` in PostgreSQL — never `FLOAT`. Floating-point arithmetic is unsuitable for money due to precision errors.

**Snapshot balances**
Recalculating an account balance by summing all transactions gets expensive over time. A `balance_snapshot` field is updated daily by a Celery Beat task, so balance queries only need to sum transactions since the last snapshot.

**Repository pattern**
All database queries live in repository classes. Services never write raw SQL. This makes it trivial to swap the database layer in tests (SQLite instead of PostgreSQL) and keeps service logic readable.

**Celery Beat over cron**
Scheduled tasks are defined in code alongside the rest of the application, version-controlled, and don't require any external cron server or infrastructure configuration.

---

## 🗺 Roadmap

- [ ] Multi-currency support with exchange rate table
- [ ] Recurring transaction templates
- [ ] CSV import from bank statements
- [ ] Spending insights endpoint (month-over-month comparisons)
- [ ] WebSocket support for real-time budget alerts
- [ ] Frontend client (React + Recharts)

---

## 📄 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

<p align="center">Built as a backend engineering portfolio project — <a href="https://github.com/eduardorocha-dev">@eduardorocha-dev</a></p>
