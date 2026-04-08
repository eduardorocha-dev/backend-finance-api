.PHONY: install setup up down start logs logs-api logs-worker \
        migrate migration db-reset \
        test test-full coverage coverage-docker \
        lint format typecheck check ci dev

# ── Setup ─────────────────────────────────────────────────────────────────────

install:
	python -m venv .venv
	.venv/bin/pip install -r requirements.txt

setup: install up
	@echo "Waiting for db to be healthy..."
	@until docker compose exec db pg_isready -U postgres > /dev/null 2>&1; do sleep 1; done
	$(MAKE) migrate
	@echo "Setup complete. Run 'make dev' to start the server."

# ── Docker ────────────────────────────────────────────────────────────────────

up:
	docker compose up -d db db_test redis

down:
	docker compose down

start:
	docker compose up -d
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

db-reset:
	@echo "Resetting database..."
	.venv/bin/alembic downgrade base
	.venv/bin/alembic upgrade head
	@echo "Database reset complete."

# ── Tests & Coverage ──────────────────────────────────────────────────────────

test:
	.venv/bin/pytest -v

test-full: up
	@echo "Waiting for db_test to be healthy..."
	@until docker compose exec db_test pg_isready -U postgres > /dev/null 2>&1; do sleep 1; done
	$(MAKE) coverage

coverage:
	.venv/bin/pytest --cov=app --cov-report=term-missing --cov-report=html
	xdg-open htmlcov/index.html

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
	@echo "Waiting for db_test to be healthy..."
	@until docker compose exec db_test pg_isready -U postgres > /dev/null 2>&1; do sleep 1; done
	$(MAKE) lint
	$(MAKE) typecheck
	$(MAKE) coverage
	@echo "CI passed."

# ── Dev server ────────────────────────────────────────────────────────────────

dev: up migrate
	.venv/bin/uvicorn app.main:app --reload
