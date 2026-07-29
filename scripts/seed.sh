#!/usr/bin/env bash
# Seed demo users / sample data into the running API
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# shellcheck disable=SC1091
if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1090
  source .env
  set +a
fi

API_BASE="${API_BASE_URL:-http://localhost:8000}"

echo "Waiting for API at ${API_BASE}/health ..."
for _ in $(seq 1 60); do
  if curl -sf "${API_BASE}/health" >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

if ! curl -sf "${API_BASE}/health" >/dev/null 2>&1; then
  echo "API not healthy at ${API_BASE}. Is the stack up? (./scripts/dev-up.sh)"
  exit 1
fi

echo "Running seed..."
if docker compose ps --status running --services 2>/dev/null | grep -qx api; then
  docker compose exec -T api python -m aisoc.scripts.seed
else
  echo "API container not running — attempting admin seed endpoint..."
  curl -sf -X POST "${API_BASE}/api/v1/admin/seed" \
    -H "Content-Type: application/json" \
    -d "{}" || {
      echo "Seed endpoint unavailable."
      exit 1
    }
fi

echo ""
echo "Demo accounts (from .env):"
echo "  Admin:   ${SEED_ADMIN_EMAIL:-admin@aisoc.local} / ${SEED_ADMIN_PASSWORD:-ChangeMeAdmin123!}"
echo "  Analyst: ${SEED_ANALYST_EMAIL:-analyst@aisoc.local} / ${SEED_ANALYST_PASSWORD:-ChangeMeAnalyst123!}"
