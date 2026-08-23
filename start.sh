#!/usr/bin/env bash
# WaterTriage full stack: PostgreSQL + FastAPI + console
set -e
cd "$(dirname "$0")"

echo "── 1/3 PostgreSQL ──"
docker compose up -d
until docker exec watertriage-db pg_isready -U jjm_user -d jjm_triage >/dev/null 2>&1; do sleep 1; done
echo "   ready"

echo "── 2/3 FastAPI on :8000 ──"
cd backend
export DATABASE_URL="postgresql://jjm_user:jjm_password@localhost:5432/jjm_triage"
uv run python -m uvicorn app.main:app --port 8000 &
API_PID=$!
cd ..

echo "── 3/3 Console ──"
sleep 2
xdg-open "http://127.0.0.1:8000/docs" 2>/dev/null &
xdg-open "$PWD/dashboard/index.html" 2>/dev/null &

trap "kill $API_PID 2>/dev/null" EXIT
echo ""
echo "WaterTriage running."
echo "  API docs : http://127.0.0.1:8000/docs"
echo "  Console  : dashboard/index.html (LIVE chip should turn green)"
echo "  Ctrl-C to stop."
wait $API_PID
