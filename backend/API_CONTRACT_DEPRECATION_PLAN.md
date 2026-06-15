# API Contract Consolidation Plan

## Target State
- Single public API contract: `/api/v1`
- Temporary compatibility layer: `/api` served only by `backend/app/api/legacy_routes.py`
- Legacy routing ownership and usage logging centralized in `backend/app/main.py`

## Current State
- Primary clients already use `/api/v1`
- Compatibility endpoints under `/api` remain for legacy clients and old tests
- Legacy usage is logged by middleware in `backend/app/main.py`
- CI now blocks new legacy usage in production code via `backend/scripts/enforce_api_contract.py`

## Deprecation Timeline
1. Phase 0 (Now - Week 0)
- Freeze legacy surface: no new `/api` endpoints
- Keep `/api` operational for compatibility
- Track volume and endpoint distribution from legacy logs

2. Phase 1 (Week 1-2)
- Publish migration notice in release notes and API docs
- Add response header on `/api` routes: `Deprecation: true` and `Sunset: <date>`
- Share endpoint mapping table (`/api/*` -> `/api/v1/*`)

3. Phase 2 (Week 3-6)
- Migrate all internal scripts and partner clients to `/api/v1`
- Monitor daily legacy call volume trend
- Open remediation tickets for remaining legacy consumers

4. Phase 3 (Week 7-8)
- Gate risky legacy routes with stricter rate limits if still needed
- Keep only minimal read-safe compatibility routes if required
- Final communication: hard shutdown date

5. Phase 4 (Week 9)
- Remove `/api` router include from `backend/app/main.py`
- Delete `backend/app/api/legacy_routes.py`
- Remove compatibility checks from validator

## Migration Strategy
- Contract mapping:
  - `POST /api/predict` -> `POST /api/v1/predict`
  - `POST /api/forecast` -> `POST /api/v1/forecast`
  - `POST /api/ai-insight` -> `POST /api/v1/chat` or dedicated `/api/v1/insight` if retained
  - `GET /api/monitoring/summary` -> `GET /api/v1/monitoring`
- Response normalization:
  - Move clients to envelope format: `{ success, data, error, message }`
- Client updates:
  - Frontend/API SDK default base URL must be `/api/v1`
  - Block merge on any new non-v1 usage in production code

## Enforcement Controls
- CI policy: `.github/workflows/ci.yml` runs `backend/scripts/enforce_api_contract.py`
- Scope checked: `backend/app`, `frontend/src`, and `frontend/vite.config.js`
- Allowlist: only `backend/app/main.py` may reference `/api` for temporary compatibility

## Exit Criteria For Legacy Removal
- 14 consecutive days with zero critical `/api` consumers
- 100% internal traffic on `/api/v1`
- No open migration tickets for external consumers
- Staging and production validators pass without compatibility checks
