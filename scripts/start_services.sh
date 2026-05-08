#!/usr/bin/env bash
set -euo pipefail

if ! docker info &>/dev/null; then
  echo "ERROR: Docker is not running."
  exit 1
fi

if [ ! -f .env ]; then
  echo "ERROR: .env file not found."
  exit 1
fi

docker compose up -d

until docker exec postgres-db pg_isready -U "${DB_USER:-postgres}" &>/dev/null; do
  sleep 3
done

until docker compose exec postgres pg_isready -U airflow &>/dev/null; do
  sleep 3
done

until curl -sf http://localhost:8080/api/v2/monitor/health &>/dev/null; do
  sleep 5
done

echo "✅ All services up."
echo "   Airflow UI:  http://localhost:8080"
echo "   pgvector DB: localhost:5433"
