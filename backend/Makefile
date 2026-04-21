.PHONY: help install db migrate seed run test clean setup reset-db format lint

help:
	@echo "Available commands:"
	@echo "  make setup      - Complete setup (install + create db + migrate + seed)"
	@echo "  make install    - Install dependencies"
	@echo "  make db         - Create the database (if it doesn't exist)"
	@echo "  make migrate    - Run database migrations"
	@echo "  make reset-db   - Downgrade all migrations and re-run them"
	@echo "  make seed       - Seed the database with sample data"
	@echo "  make run        - Start the development server"
	@echo "  make test       - Run tests"
	@echo "  make format     - Format code with ruff"
	@echo "  make lint       - Lint code with ruff and mypy"
	@echo "  make clean      - Remove generated files"

install:
	uv sync

db:
	uv run python scripts/create_db.py

migrate:
	uv run alembic upgrade head

reset-db:
	uv run alembic downgrade base
	uv run alembic upgrade head

seed:
	uv run python scripts/seed_data.py

setup: install db migrate seed
	@echo "✅ Setup complete! Run 'make run' to start the server."

run:
	uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

test:
	@echo "Running tests with coverage..."
	uv run pytest tests/ -v --cov=src --cov-report=term-missing --cov-report=html

format:
	uv run ruff format .
	uv run ruff check --fix .

lint:
	uv run ruff check .
	uv run mypy src

clean:
	rm -rf .venv
	rm -rf **/__pycache__
	rm -rf .pytest_cache
	rm -rf .ruff_cache
	rm -rf .mypy_cache
	rm -rf htmlcov
	rm -rf .coverage
