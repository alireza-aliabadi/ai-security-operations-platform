.PHONY: install test lint up down migrate seed

install:
	cd backend && poetry install
	cd frontend && npm ci
	cd mcp-server && poetry install || true

test:
	cd backend && poetry run pytest -q
	cd frontend && npm run lint

lint:
	cd backend && poetry run ruff check src tests
	cd frontend && npm run lint

up:
	docker compose up -d --build

down:
	docker compose down

migrate:
	cd backend && poetry run alembic upgrade head

seed:
	./scripts/seed.sh
