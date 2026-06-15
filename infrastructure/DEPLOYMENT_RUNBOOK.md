# NeuralAlpha Deployment Runbook

## 1. Profiles

- Development profile: hot reload + dev frontend + dev backend + worker
- Production profile: nginx frontend + stable backend + worker

Compose profiles are defined in [docker-compose.yml](../docker-compose.yml).

## 2. Pre-release Checklist

1. Ensure `.env` values are set for target environment.
2. Rotate and set `GOOGLE_API_KEY` in GCP and restrict it to Generative Language API + backend egress IP.
3. Ensure MySQL credentials are valid and reachable.
4. Run backend tests: `cd backend && python -m pytest -m "not integration" -q`
5. Run frontend tests: `cd frontend && npm run test`
6. Build frontend: `cd frontend && npm run build`
7. Apply migrations: `cd backend && python -m alembic upgrade head`
8. Verify model runtime endpoint: `GET /api/model-runtime`

## 3. Start Commands

### Development stack

```bash
docker compose --profile dev up --build
```

### Production-like stack

```bash
docker compose --profile prod up -d --build
```

### Direct backend run (non-container)

```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
```

## 4. Health Verification

1. Backend health: `GET http://localhost:8000/health`
2. Frontend health (prod profile): `GET http://localhost:8080/`
3. Nginx reverse proxy path: `GET http://localhost:8080/api/v1/monitoring`
4. Run smoke tests:

```bash
cd backend
python scripts\smoke_test_stack.py
```

## 5. Rollback Strategy

1. Stop current deployment:

```bash
docker compose --profile prod down
```

2. Re-deploy previous known-good image tag set (if using registry tags) or previous commit.
3. If migration introduced incompatibility, roll back one revision:

```bash
cd backend
python -m alembic downgrade -1
```

4. Start stack again and re-run smoke tests.

## 6. Incident Notes

- If backend fails on startup, first verify DB credentials and migration state.
- If predictions degrade, inspect `/api/model-runtime` for fallback mode and artifact existence.
- If monitoring remains zero after traffic, verify writes to `prediction_logs` and `inference_audits`.
