#!/bin/bash
set -e

echo "==> Applying migrations..."
cd backend
alembic upgrade head

echo "==> Seeding data..."
python scripts/seed_data.py

echo "==> Starting backend on :8000..."
uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!

echo "==> Starting frontend on :3000..."
cd ../frontend
npm run dev -- --host 0.0.0.0 --port 3000

kill $BACKEND_PID
