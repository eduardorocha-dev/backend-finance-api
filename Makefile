.PHONY: doctor install env setup up down start logs logs-api logs-worker admin \
        migrate migration db-reset \
        test test-full coverage coverage-docker \
        lint format typecheck check ci dev worker beat

PYTHON ?= python3.12
OPEN := $(if $(filter Darwin,$(shell uname -s)),open,xdg-open)

# ── Setup ─────────────────────────────────────────────────────────────────────

doctor:
	@ok=1; \
	command -v $(PYTHON) > /dev/null || { echo "✗ $(PYTHON) not found (install Python 3.12, e.g. 'uv python install 3.12')"; ok=0; }; \
	command -v docker > /dev/null || { echo "✗ docker not found (install Docker Desktop, OrbStack or Colima)"; ok=0; }; \
	docker info > /dev/null 2>&1 || { echo "✗ docker daemon is not running"; ok=0; }; \
	docker compose version > /dev/null 2>&1 || { echo "✗ docker compose plugin not found"; ok=0; }; \
	[ $$ok = 1 ] && echo "✓ All prerequisites found" || exit 1

install:
	$(PYTHON) -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -r requirements.txt

env:
	@if [ -f .env ]; then echo ".env already exists, leaving it alone"; \
	else sed "s/^SECRET_KEY=$$/SECRET_KEY=$$(openssl rand -hex 32)/" .env.example > .env; \
	echo "Created .env with a generated SECRET_KEY"; fi

setup: doctor install env up migrate
	@echo "Setup complete. Run 'make dev' to start the server."

# ── Docker ────────────────────────────────────────────────────────────────────

up: env
	docker compose up -d --wait db db_test redis

down:
	docker compose down

start: env
	docker compose up -d --build
	@echo "API running at http://localhost:8000"

logs:
	docker compose logs -f

logs-api:
	docker compose logs -f api

logs-worker:
	docker compose logs -f worker

# ── Database ──────────────────────────────────────────────────────────────────

migrate:
	.venv/bin/alembic upgrade head

migration:
	@test -n "$(name)" || (echo "Usage: make migration name=<description>" && exit 1)
	.venv/bin/alembic revision --autogenerate -m "$(name)"

admin:
	@test -n "$(email)" || (echo "Usage: make admin email=<user email>" && exit 1)
	.venv/bin/python -m app.cli make-admin $(email)

db-reset:
	@echo "Resetting database..."
	.venv/bin/alembic downgrade base
	.venv/bin/alembic upgrade head
	@echo "Database reset complete."

# ── Tests & Coverage ──────────────────────────────────────────────────────────

test:
	.venv/bin/pytest -v

test-full: up
	$(MAKE) coverage

coverage:
	.venv/bin/pytest --cov=app --cov-report=term-missing --cov-report=html
	-$(OPEN) htmlcov/index.html

coverage-docker:
	docker compose run --rm api pytest --cov=app --cov-report=term-missing

# ── Code quality ──────────────────────────────────────────────────────────────

lint:
	.venv/bin/ruff check app tests

format:
	.venv/bin/ruff format app tests

typecheck:
	.venv/bin/mypy app

check: lint typecheck test

ci: up
	$(MAKE) lint
	$(MAKE) typecheck
	$(MAKE) coverage
	@echo "CI passed."

# ── Dev server ────────────────────────────────────────────────────────────────

dev: up migrate
	.venv/bin/uvicorn app.main:app --reload

worker:
	.venv/bin/celery -A app.workers.celery_app worker --loglevel=info

beat:
	.venv/bin/celery -A app.workers.celery_app beat --loglevel=info
