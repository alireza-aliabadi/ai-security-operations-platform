.PHONY: install test lint up up-obs up-all down down-obs down-all migrate seed

COMPOSE_APP := docker compose -f docker-compose.yml
COMPOSE_OBS := docker compose -f docker-compose.observability.yml
COMPOSE_ALL := docker compose -f docker-compose.yml -f docker-compose.observability.yml

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
	$(COMPOSE_APP) up -d --build

up-obs:
	$(COMPOSE_OBS) up -d

up-all:
	$(COMPOSE_ALL) up -d --build

down:
	$(COMPOSE_APP) down

down-obs:
	$(COMPOSE_OBS) down

down-all:
	$(COMPOSE_ALL) down

migrate:
	cd backend && poetry run alembic upgrade head

seed:
	./scripts/seed.sh
