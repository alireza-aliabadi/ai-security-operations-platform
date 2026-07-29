#!/usr/bin/env bash
# Bring up the AISOC local stack
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ ! -f .env ]]; then
  echo "Creating .env from .env.example"
  cp .env.example .env
fi

PROFILE_ARGS=()
if [[ "${WITH_OIDC:-0}" == "1" ]]; then
  PROFILE_ARGS+=(--profile oidc)
fi

echo "Starting AISOC stack..."
docker compose "${PROFILE_ARGS[@]}" up -d --build "$@"

echo ""
echo "Services:"
echo "  Frontend   http://localhost:3000"
echo "  API        http://localhost:8000"
echo "  Grafana    http://localhost:3002  (admin/admin)"
echo "  Prometheus http://localhost:9090"
echo "  Qdrant     http://localhost:6333"
echo ""
echo "Password auth works without OIDC."
echo "Optional OIDC mock: WITH_OIDC=1 $0"
echo ""
echo "Seed demo users: ./scripts/seed.sh"
