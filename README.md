# NEURALALPHA - Full System Technical Documentation

This document is a long-form, implementation-focused walkthrough of the codebase.
It explains the frontend files, backend files, ML pipeline files, DL files, GenAI files, API routes, and database files in detail.

---

## 1) System Overview

NEURALALPHA is a full-stack financial intelligence platform with:

- Frontend dashboard (React + Vite)
- Backend API (FastAPI + async SQLAlchemy)
- ML and DL training/evaluation pipeline (XGBoost + LSTM)
- GenAI chat support with retrieval and deterministic fallback
- MySQL persistence + Alembic migration setup
- Monitoring, SLO checks, and production validation scripts

Main runtime architecture:

1. Browser calls `frontend/src/services/api.js`
2. Vite proxy forwards `/api/v1/*` to backend (`http://127.0.0.1:8000`)
3. FastAPI routes in `backend/app/api/v1/routes/*`
4. Services in `backend/app/services/*` execute business logic
5. SQLAlchemy models in `backend/app/db/models/*` persist and query MySQL
6. Monitoring and logs are written into `logs` and surfaced via `/monitoring`

---

## 2) Frontend: File-by-File Code + Explanation

Frontend root stack:

- Framework: React 18
- Build/dev: Vite
- Routing: react-router-dom
- API client: Axios
- Styling: Tailwind + custom utility classes

### 2.1 Frontend Infrastructure Files

#### `frontend/package.json`

Purpose:
- Defines frontend scripts and dependencies.
- Standard commands include dev server, build, and tests.

Why it matters:
- This file defines all frontend package versions and CLI behavior.

#### `frontend/vite.config.js`

Purpose:
- Configures Vite plugins, test environment, and dev server proxy.

Important code behavior:

```js
server: {
  port: 5173,
  proxy: {
    '/api/v1': {
      target: 'http://127.0.0.1:8000',
      changeOrigin: true,
    },
  },
}
```

Explanation:
- Requests to `/api/v1/*` from the browser are proxied to backend.
- This avoids cross-origin issues in local development when frontend and backend use different ports.

#### `frontend/index.html`

Purpose:
- Bootstraps the SPA root element.
- Vite injects compiled JS/CSS bundles into this HTML.

#### `frontend/tailwind.config.js`

Purpose:
- Tailwind scanning and theme extensions.
- Controls utility generation and design tokens.

#### `frontend/postcss.config.js`

Purpose:
- CSS transformation pipeline (Tailwind + autoprefixing).

#### `frontend/nginx.conf`

Purpose:
- Production/static serving behavior when frontend is containerized.

#### `frontend/Dockerfile`

Purpose:
- Build and ship frontend container image.

---

### 2.2 Frontend Entry + Shell

#### `frontend/src/main.jsx`

Purpose:
- App entry point.
- Mounts app under React StrictMode and BrowserRouter.

Code flow:

```jsx
ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>
)
```

#### `frontend/src/App.jsx`

Purpose:
- Defines global shell and route map.
- Lazy-loads pages for better load performance.
- Includes sidebar/topbar, skeleton fallback, global loader, and route error boundary.

Key routes:
- `/dashboard`
- `/prediction`
- `/forecast`
- `/chat`
- `/portfolio`
- `/sentiment`
- `/monitoring`

Important UX patterns:
- Escape key closes sidebar.
- Route-level suspense fallback with skeleton.
- Skip-to-content anchor for accessibility.

---

### 2.3 Frontend Services Layer

#### `frontend/src/services/endpoints.js`

Purpose:
- Central endpoint map for all frontend API calls.

Examples:
- Prediction run: `/predict`
- Forecast run: `/forecast`
- Sentiment by symbol: `/sentiment/{symbol}`
- Monitoring: `/monitoring`

Why this is good:
- Prevents route strings from being scattered across many files.

#### `frontend/src/services/api.js`

Purpose:
- Axios instance setup + request/response normalization.

Current behavior highlights:

```js
baseURL: import.meta.env.VITE_API_URL || '/api/v1'
```

Meaning:
- Uses proxy-relative API path by default.
- This is robust for local development and avoids many CORS issues.

Other notable behavior:
- Adds `X-Client: neuralalpha-dashboard` header on every request.
- Normalizes backend error formats into one frontend-consumable shape.
- Unwraps API envelope and returns `data` payload directly when present.

---

### 2.4 Frontend Hooks: File-by-File

#### `frontend/src/hooks/useAuth.js`

Purpose:
- Auth-side request and local auth state lifecycle.

Typical responsibility:
- Login/register trigger
- Request status and normalized error propagation

#### `frontend/src/hooks/usePrediction.js`

Purpose:
- Prediction request orchestration with debounce and cancellation.

Important code behavior:
- Converts string/object payload into normalized API payload.
- Cancels in-flight request via `AbortController`.
- Uses timer debounce (`220ms`) before sending.
- Keeps only latest request result using incremental request ID.

#### `frontend/src/hooks/useForecast.js`

Purpose:
- Trigger forecast requests and expose loading/error/data state.

#### `frontend/src/hooks/useSentiment.js`

Purpose:
- Fetches sentiment by symbol and handles state.

#### `frontend/src/hooks/useMonitoring.js`

Purpose:
- Poll-like monitoring retrieval with optional interval logic.
- Powers dashboard/monitoring pages with live-ish health data.

#### `frontend/src/hooks/usePortfolio.js`

Purpose:
- Portfolio query + update behavior from UI.

#### `frontend/src/hooks/useChat.js`

Purpose:
- Chat request lifecycle and message state transitions.

#### `frontend/src/hooks/useDashboardSummary.js`

Purpose:
- Composes multiple endpoints into dashboard-ready aggregate state.

#### `frontend/src/hooks/useTickers.js`

Purpose:
- Loads tradable symbol list for forms/dropdowns/autocomplete.

---

### 2.5 Frontend Pages: File-by-File

#### `frontend/src/pages/Dashboard.jsx`

Purpose:
- Main overview screen.

What it does:
- Pulls sentiment, monitoring, and summary data.
- Shows KPI cards (sentiment, error rate, p95 latency, predicted value).
- Renders forecast chart and quick-insight cards.

#### `frontend/src/pages/Prediction.jsx`

Purpose:
- Interactive prediction execution UI.

Typical behavior:
- Symbol/model selection
- Trigger prediction API call
- Show predicted value, confidence, timestamps

#### `frontend/src/pages/Forecast.jsx`

Purpose:
- Multi-day forecast execution and chart rendering.

#### `frontend/src/pages/Sentiment.jsx`

Purpose:
- Symbol sentiment query and result display.

#### `frontend/src/pages/Chat.jsx`

Purpose:
- GenAI chat interface with symbol-aware prompts.

#### `frontend/src/pages/Portfolio.jsx`

Purpose:
- Portfolio view + position upsert flows.

#### `frontend/src/pages/Monitoring.jsx`

Purpose:
- Displays monitoring metrics, SLO health, and alerts.

#### `frontend/src/pages/Login.jsx`

Purpose:
- Authentication entry view; in current shell flow it may redirect to dashboard.

---

### 2.6 Frontend Components: File-by-File

#### Charts
- `frontend/src/components/charts/LineChart.jsx`: reusable line chart visualization for numeric series.
- `frontend/src/components/charts/ForecastChart.jsx`: forecast-focused chart rendering wrapper.

#### Chat
- `frontend/src/components/chat/ChatBubble.jsx`: single message bubble rendering.
- `frontend/src/components/chat/ChatWindow.jsx`: full conversation panel + scroll/input behavior.

#### Layout
- `frontend/src/components/layout/Sidebar.jsx`: app navigation rail/drawer.
- `frontend/src/components/layout/Topbar.jsx`: top bar title/actions.

#### UI primitives
- `frontend/src/components/ui/Button.jsx`: consistent button variants/states.
- `frontend/src/components/ui/Card.jsx`: reusable card container.
- `frontend/src/components/ui/Input.jsx`: standardized input field.
- `frontend/src/components/ui/Table.jsx`: table rendering helper.
- `frontend/src/components/ui/Loader.jsx`: inline loading indicator.
- `frontend/src/components/ui/GlobalLoader.jsx`: global overlay loader.
- `frontend/src/components/ui/PageSkeleton.jsx`: route/page placeholder skeleton.
- `frontend/src/components/ui/EmptyState.jsx`: empty list/no-data UI.
- `frontend/src/components/ui/RouteErrorBoundary.jsx`: route failure isolation and fallback UI.

#### Utility + styles
- `frontend/src/lib/utils.js`: class joiner, number/currency formatter, pathname-to-title helper.
- `frontend/src/styles/globals.css`: global base styles and design utilities.

---

## 3) Backend: File-by-File Code + Explanation

Backend stack:

- FastAPI app runtime
- Async SQLAlchemy + MySQL
- Pydantic request/response schemas
- Middleware for API key and rate limit
- Services layer for business logic

### 3.1 Backend Infrastructure Files

#### `backend/requirements.txt`

Purpose:
- Python dependency lock-like manifest for backend runtime.

#### `backend/alembic.ini`

Purpose:
- Alembic migration config and script locations.

#### `backend/pytest.ini`

Purpose:
- Test discovery and pytest behavior.

#### `backend/Dockerfile`

Purpose:
- Backend container build and execution settings.

---

### 3.2 App Bootstrap and Lifecycle

#### `backend/app/main.py`

Purpose:
- Main FastAPI app creation and lifecycle wiring.

What it initializes in lifespan:
- Logging setup
- DB bootstrap (`init_db`)
- Cache bootstrap (`CacheService.init`)
- Optional model warmup
- Optional required-model enforcement

Middlewares added:
- CORS
- API key middleware
- Rate limit middleware

Routes included:
- `/api/v1/*` (primary contract)
- `/api/*` legacy compatibility router

Health endpoint:
- `/health` returns success envelope details.

#### `backend/app/core/config.py`

Purpose:
- Centralized typed settings from `.env` via Pydantic Settings.

Domains configured:
- App identity/environment
- API version and CORS origins
- API key and IP allowlist behavior
- DB URL and JWT settings
- Model loading/validation toggles
- Redis cache configuration
- Rate limiting and request limits
- Gemini GenAI controls and timeouts
- Monitoring thresholds/SLO/anomaly parameters

Important helper properties:
- `cors_origins_list`
- `api_key_allowed_ips`
- `gemini_models`

---

### 3.3 API Routers: File-by-File

#### `backend/app/api/v1/__init__.py`

Purpose:
- Composes and mounts all v1 feature route modules.

#### `backend/app/api/v1/routes/auth.py`

Endpoints:
- `POST /auth/register`
- `POST /auth/login`

Service integration:
- `AuthService.register`
- `AuthService.login`

#### `backend/app/api/v1/routes/prediction.py`

Endpoints:
- `POST /predict`
- `GET /predict/history`

Behavior:
- Creates/gets public user for anonymous dashboard usage.
- Persists and returns prediction result/history.

#### `backend/app/api/v1/routes/forecast.py`

Endpoint:
- `POST /forecast`

Behavior:
- Calls `ForecastService.forecast` and returns normalized response.

#### `backend/app/api/v1/routes/sentiment.py`

Endpoint:
- `GET /sentiment/{symbol}`

Validation:
- Symbol regex and size validation at path level.

#### `backend/app/api/v1/routes/chat.py`

Endpoint:
- `POST /chat`

Behavior:
- Symbol-aware chat request pipeline with DB context.

#### `backend/app/api/v1/routes/monitoring.py`

Endpoint:
- `GET /monitoring`

Behavior:
- Returns computed monitoring + SLO state.

#### `backend/app/api/v1/routes/portfolio.py`

Endpoints:
- `GET /portfolio`
- `POST /portfolio`

Behavior:
- Portfolio summary and upsert operations.

#### `backend/app/api/v1/routes/scheduling.py`

Endpoints:
- `POST /calendar/schedule`
- `GET /calendar/events`

Behavior:
- Creates and lists scheduling events.

#### `backend/app/api/v1/routes/tickers.py`

Endpoint:
- `GET /tickers`

Behavior:
- Returns available market symbols.

---

### 3.4 Legacy Compatibility API

#### `backend/app/api/legacy_routes.py`

Purpose:
- Maintains `/api/*` compatibility while primary contract is `/api/v1/*`.

What it does:
- Mirrors major endpoints (predict/forecast/sentiment/chat/monitoring)
- Transforms output shapes for older clients
- Includes extra endpoint `/ai-insight`

Why this exists:
- Supports gradual migration without breaking old integrations.

---

### 3.5 Middleware: Security + Traffic Control

#### `backend/app/middleware/api_key.py`

Purpose:
- Enforces API key on API routes when enabled.

Behavior details:
- Allows `/health`, `/docs`, `/openapi.json`, `/redoc` without API key.
- Applies checks only under `/api/*`.
- If required and key is missing/mismatch -> 401.
- If key protection enabled but key config absent -> 503.
- Optional per-IP restriction via allowlist -> 403.

#### `backend/app/middleware/rate_limit.py`

Purpose:
- In-memory request limiter + request size guard.

Behavior:
- Rejects request body above configured byte threshold (413).
- Tracks request timestamps per client IP in deque buckets.
- Enforces max requests in configured rolling window.
- Returns 429 with `Retry-After` when exceeded.

---

### 3.6 Services Layer: File-by-File

#### `backend/app/services/prediction_service.py`

Core responsibilities:
- Prediction request execution
- Cache read/write
- Model loading and fallback
- Prediction persistence and logging

Flow summary:
1. Normalize symbol and build cache key.
2. Return cached result if present.
3. Choose model artifact (`xgb_model.pkl` for `ml`).
4. If model exists, build simple symbol-based feature vector and infer.
5. If model missing, deterministic fallback value is generated.
6. Sanitize via `DataQualityService`.
7. Insert row into `predictions` table.
8. Log request latency and model version.
9. Cache response for short TTL.

#### `backend/app/services/forecast_service.py`

Core responsibilities:
- Forecast generation for horizon days
- LSTM+scaler inference when artifacts and history available
- Statistical fallback in low-data or unavailable-model situations

Flow summary:
1. Cache check.
2. Load last up-to-120 close prices from DB.
3. Try `lstm_model.keras` + `scaler.pkl` path.
4. Use first inferred point + drift for remaining horizon.
5. Fallback to baseline/stat model otherwise.
6. Sanitize forecast series.
7. Log latency and model path used.
8. Cache response.

#### `backend/app/services/sentiment_service.py`

Core responsibilities:
- Deterministic symbol sentiment generation
- Persistence into `sentiment_data`
- Cache and observability logging

Output fields:
- `symbol`, `score`, `label`, `timestamp`

#### `backend/app/services/chat_service.py`

This is the main GenAI chat orchestrator.

Core responsibilities:
- Retrieve indexed context chunks from local JSON corpus
- Pull latest symbol prediction/sentiment from DB
- Build structured prompt for Gemini
- Try Gemini models with timeout strategy
- Produce deterministic fallback if Gemini unavailable
- Log latency, fallback status, and model used

Notable internals:
- `_retrieve()` token-overlap retrieval from `genai_chunks.json`
- `_load_symbol_context()` DB query + cache for sentiment/prediction context
- `_build_prompt()` strict sectioned response format instructions
- `_build_fallback_reply()` stable deterministic response path
- `_generate_with_gemini()` model candidate loop with primary/secondary timeout

#### `backend/app/services/genai_service.py`

Purpose:
- Minimal mock service abstraction for legacy endpoints.

Current behavior:
- Returns mock reply/insight strings.

#### `backend/app/services/monitoring_service.py`

Core responsibilities:
- Compute 24h metrics (confidence, error rate, latency percentiles)
- Compute recent-window SLO metrics
- Detect latency anomaly via recent/previous window ratio
- Detect Gemini fallback rates from chat logs
- Generate warning/critical alerts and persist alert logs

Outputs include:
- p95/p99 latency
- error rate
- anomaly flags/scores
- SLO target and breach booleans

#### `backend/app/services/model_loader.py`

Core responsibilities:
- Artifact discovery using alias-aware candidate paths
- Lazy load and cache model/scaler artifacts
- Keras/joblib handling by extension
- Optional hot reload support
- Startup warmup + required model validation

Artifact alias behavior examples:
- `xgb_model.pkl` can resolve `xgb.joblib`
- `lstm_model.keras` can resolve `lstm_close.keras`
- `scaler.pkl` can resolve `close_scaler.pkl`

#### Other service files

- `backend/app/services/auth_service.py`: user auth register/login logic.
- `backend/app/services/portfolio_service.py`: portfolio aggregation and upsert behavior.
- `backend/app/services/market_data_service.py`: symbol/ticker retrieval and market data access.
- `backend/app/services/scheduling_service.py`: calendar event creation and list.
- `backend/app/services/calendar_service.py`: calendar integration utilities.
- `backend/app/services/cache_service.py`: Redis-like cache abstraction used by prediction/forecast/chat/sentiment.
- `backend/app/services/log_service.py`: central log writer into DB `logs` table.
- `backend/app/services/data_quality_service.py`: output sanitation (prediction, sentiment, forecast).
- `backend/app/services/public_user_service.py`: anonymous/public runtime user provisioning.
- `backend/app/services/document_service.py`: document support for retrieval/knowledge features.

---

### 3.7 Schemas Layer (Pydantic Contracts)

Directory: `backend/app/schemas/*`

Purpose:
- Input validation and output shape stability.

Important files:
- `auth.py`: login/register request/response shapes
- `prediction.py`: prediction request and data schema
- `forecast.py`: forecast request and response schema
- `sentiment.py`: sentiment response schema
- `chat.py`: chat request and response schema
- `monitoring.py`: monitoring metrics contract including SLO/anomaly booleans
- `scheduling.py`: scheduling payload contracts
- `common.py`: API response envelope schema
- `contracts.py`: contract helpers/shared types

---

### 3.8 Core Utilities and Dependency Wiring

- `backend/app/core/security.py`: security helpers (JWT/hash related utilities).
- `backend/app/core/dependencies.py`: app dependency providers.
- `backend/app/core/logging.py`: structured logging setup.
- `backend/app/core/exceptions.py`: standardized exception handlers.
- `backend/app/api/deps.py` and `backend/app/deps.py`: dependency adapters for routers/services.
- `backend/app/utils/helpers.py`: common success-response helper and small utilities.

---

## 4) ML, DL, and GenAI: Full Detailed Explanation

### 4.1 ML Mode (Classical Model)

Primary files:
- Training: `ml_pipeline/training/train_xgboost.py`
- Features: `ml_pipeline/preprocessing/feature_engineering.py`
- Runtime load: `backend/app/services/model_loader.py`
- Runtime predict flow: `backend/app/services/prediction_service.py`

What happens in ML training:
1. Read raw market CSV.
2. Create engineered features (`return_1`, `return_5`, `sma_20`, `ema_20`).
3. Build binary target for next-day direction.
4. Train XGBoost classifier.
5. Save model artifact as `ml_pipeline/models/xgb.joblib`.

What happens in backend ML inference:
1. Resolve requested artifact name (`xgb_model.pkl` alias to `xgb.joblib` if needed).
2. Build inference feature vector.
3. Run model prediction if loaded.
4. If missing model, deterministic fallback result still keeps API operational.

### 4.2 DL Mode (Deep Learning)

Primary files:
- Training: `ml_pipeline/training/train_lstm.py`
- Data setup: `ml_pipeline/training/prepare_data.py`
- Runtime forecast: `backend/app/services/forecast_service.py`
- Runtime loading: `backend/app/services/model_loader.py`

What happens in DL training:
1. Read close-price history.
2. Scale with MinMax scaler.
3. Build sliding windows (`WINDOW_SIZE = 10`).
4. Train stacked LSTM network.
5. Save model `lstm_close.keras`.
6. Save scaler artifact dict with metadata:
   - scaler object
   - window size
   - model version

What happens in backend DL forecast:
1. Get recent closes from DB.
2. Load `lstm_model.keras` alias + scaler alias.
3. Predict next value from latest window.
4. Extend horizon via drift extrapolation.
5. If unavailable/insufficient data, switch to statistical fallback.

### 4.3 GenAI Mode (Chat + Context)

Primary files:
- `backend/app/services/chat_service.py`
- `backend/app/services/genai_service.py` (legacy mock abstraction)
- `backend/app/ml/vector_store.py` (vector retrieval utility class)
- Model/data path references under `models/genai/` and `ml_pipeline/models/genai/`

How GenAI response is built:
1. Parse user message and symbol.
2. Retrieve contextual chunks using token overlap from `genai_chunks.json`.
3. Fetch latest sentiment and prediction from DB for same symbol.
4. Build structured prompt with fixed sections.
5. Attempt Gemini call with short timeout policy and candidate models.
6. If unavailable, deterministic fallback response is produced.
7. Log fallback and latency into monitoring logs.

Reliability design:
- GenAI does not hard-fail user flow if provider key/model is missing.
- Fallback path keeps chat route stable in local/offline or outage conditions.

---

## 5) API Documentation (Code-Level)

Base prefixes:
- Primary: `/api/v1`
- Legacy compatibility: `/api`

### 5.1 Auth
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`

### 5.2 Prediction
- `POST /api/v1/predict`
  - Input: symbol + model type
  - Output: predicted value + confidence + timestamp
- `GET /api/v1/predict/history`

### 5.3 Forecast
- `POST /api/v1/forecast`
  - Input: symbol + horizon days
  - Output: forecast array

### 5.4 Sentiment
- `GET /api/v1/sentiment/{symbol}`

### 5.5 Chat
- `POST /api/v1/chat`
  - Input: symbol + message
  - Output: generated reply

### 5.6 Monitoring
- `GET /api/v1/monitoring`
  - Returns 24h metrics + SLO + anomaly + alerts

### 5.7 Portfolio
- `GET /api/v1/portfolio`
- `POST /api/v1/portfolio`

### 5.8 Scheduling
- `POST /api/v1/calendar/schedule`
- `GET /api/v1/calendar/events`

### 5.9 Tickers
- `GET /api/v1/tickers`

---

## 6) Database: File-by-File Code + Explanation

Database layer directories:
- ORM base/session/init: `backend/app/db/*`
- Models: `backend/app/db/models/*`
- Migration runtime: `backend/alembic/*`

### 6.1 DB Boot Files

#### `backend/app/db/base.py`
- Declares SQLAlchemy declarative base class.

#### `backend/app/db/session.py`
- Creates async engine and async session factory.
- Provides `get_db()` dependency with commit/rollback handling.

#### `backend/app/db/init_db.py`
- Imports all models to register metadata.
- Calls `Base.metadata.create_all` on startup.

#### `backend/app/db/crud_examples.py`
- Example CRUD patterns and references for DB operations.

### 6.2 ORM Models (Each Table)

#### `backend/app/db/models/user.py` -> table `users`
Fields:
- id, name, email, password_hash, role, created_at, updated_at
Indexes:
- `ix_users_email`
Relationships:
- predictions, portfolio items, logs

#### `backend/app/db/models/prediction.py` -> table `predictions`
Fields:
- id, user_id, symbol
- legacy compatibility columns: `predicted_price`, `timestamp`
- primary fields: `prediction_value`, `confidence`, `model_version`
- optional `features_json`, `created_at`
Indexes:
- `ix_predictions_symbol`
- `ix_predictions_symbol_created_at`
- `ix_predictions_user_created_at`

#### `backend/app/db/models/market_data.py` -> table `market_data`
Fields:
- symbol, timestamp, open/high/low/close, volume
Indexes:
- symbol, timestamp, composite symbol+timestamp

#### `backend/app/db/models/sentiment.py` -> table `sentiment_data`
Fields:
- symbol, sentiment_score, sentiment_label, source, timestamp
- legacy score alias column preserved
Indexes:
- symbol and symbol+timestamp

#### `backend/app/db/models/portfolio.py` -> table `portfolio`
Fields:
- user_id, symbol, quantity, avg_price, current_price, updated_at
Indexes:
- user+symbol and symbol

#### `backend/app/db/models/logs.py` -> table `logs`
Fields:
- user_id, action, status, message, timestamp
Indexes:
- action+timestamp and user+timestamp

#### `backend/app/db/models/scheduled_event.py` -> table `scheduled_events`
Fields:
- user_id, title, start_time, end_time, sync_status, google_event_id, created_at, updated_at
Indexes:
- start_time, sync_status

#### `backend/app/db/models/__init__.py`
- Exposes model imports for consistency and centralized access.

### 6.3 Alembic Migrations

#### `backend/alembic/env.py`
- Migration environment setup and metadata target resolution.

#### `backend/alembic/versions/20260409_01_initial_mysql_schema.py`
- Initial production schema migration.
- Creates users, market_data, sentiment_data, predictions, portfolio, logs.
- Creates related indexes.
- Includes full downgrade path.

---

## 7) ML Pipeline Evaluation Modules

Directory: `ml_pipeline/evaluation/*`

### `ml_pipeline/evaluation/backtester.py`
- Backtest loop and result structures.

### `ml_pipeline/evaluation/metrics.py`
- Metric calculations (error/quality metrics).

### `ml_pipeline/evaluation/comparison.py`
- Champion/challenger comparison and rollback helpers.

### `ml_pipeline/evaluation/reporting.py`
- Reporting table and summary utilities.

### `ml_pipeline/evaluation/pipeline.py`
- End-to-end orchestrator to evaluate, persist outputs, and choose champion model.

---

## 8) Scripts and Operations (Production/QA)

### Backend scripts (`backend/scripts/*`)

- `deep_system_qa.py`: broad API/system quality checks.
- `validate_production_system.py`: strict production-readiness assertions.
- `smoke_test_stack.py`: quick stack sanity checks.
- `load_test_api.py`: load/performance test utility.
- `failure_mode_checks.py`: resilience and failure-path validation.
- `enforce_api_contract.py`: contract policy guard for API usage.
- `init_mysql_schema.py`: schema init helpers.
- `migrate_mysql_schema_v2.py`: migration helper script.
- `seed_data.py`: test/seed data insertion.

### Root scripts

- `scripts/full_run_mode.ps1`: full-run orchestration for backend + frontend + checks.
- `qa_e2e_runner.py`: end-to-end QA utility.

---

## 9) Environment and Configuration Notes

Main env files:
- `.env`
- `.env.example`
- `backend/.env`
- `backend/.env.example` (if present in your branch)

Important variables:
- `DATABASE_URL`
- `CORS_ORIGINS` / `CORS_ALLOWED_ORIGINS`
- `API_KEY_REQUIRED`
- `PUBLIC_API_KEY`
- `API_KEY_ALLOWED_IPS`
- `ENFORCE_REAL_MODELS`
- `MODEL_DIR`
- `GEMINI_API_KEY` or `GOOGLE_API_KEY`
- Monitoring/SLO variables from `backend/app/core/config.py`

---

## 10) Request-to-Code Traceability (How One User Action Travels)

Example: user runs Prediction page action.

1. UI button in `frontend/src/pages/Prediction.jsx`
2. Hook call in `frontend/src/hooks/usePrediction.js`
3. API call from `frontend/src/services/api.js` to `/api/v1/predict`
4. FastAPI route in `backend/app/api/v1/routes/prediction.py`
5. Service execution in `backend/app/services/prediction_service.py`
6. Model load from `backend/app/services/model_loader.py`
7. DB insert into `predictions` model/table
8. Response envelope returned to UI
9. UI renders value + confidence

Example: user sends Chat message.

1. UI in `frontend/src/pages/Chat.jsx`
2. Hook/service call to `/api/v1/chat`
3. Route in `backend/app/api/v1/routes/chat.py`
4. Context + GenAI pipeline in `backend/app/services/chat_service.py`
5. Optional fallback response path when Gemini unavailable
6. Response displayed in chat bubbles

---

## 11) Detailed Frontend File Checklist

Infrastructure:
- `frontend/Dockerfile`
- `frontend/index.html`
- `frontend/nginx.conf`
- `frontend/package.json`
- `frontend/postcss.config.js`
- `frontend/tailwind.config.js`
- `frontend/vite.config.js`

Runtime core:
- `frontend/src/main.jsx`
- `frontend/src/App.jsx`
- `frontend/src/styles/globals.css`
- `frontend/src/lib/utils.js`

Services:
- `frontend/src/services/api.js`
- `frontend/src/services/endpoints.js`

Hooks:
- `frontend/src/hooks/useAuth.js`
- `frontend/src/hooks/useChat.js`
- `frontend/src/hooks/useDashboardSummary.js`
- `frontend/src/hooks/useForecast.js`
- `frontend/src/hooks/useMonitoring.js`
- `frontend/src/hooks/usePortfolio.js`
- `frontend/src/hooks/usePrediction.js`
- `frontend/src/hooks/useSentiment.js`
- `frontend/src/hooks/useTickers.js`

Pages:
- `frontend/src/pages/Login.jsx`
- `frontend/src/pages/Dashboard.jsx`
- `frontend/src/pages/Prediction.jsx`
- `frontend/src/pages/Forecast.jsx`
- `frontend/src/pages/Chat.jsx`
- `frontend/src/pages/Portfolio.jsx`
- `frontend/src/pages/Sentiment.jsx`
- `frontend/src/pages/Monitoring.jsx`

Components:
- `frontend/src/components/charts/LineChart.jsx`
- `frontend/src/components/charts/ForecastChart.jsx`
- `frontend/src/components/chat/ChatBubble.jsx`
- `frontend/src/components/chat/ChatWindow.jsx`
- `frontend/src/components/layout/Sidebar.jsx`
- `frontend/src/components/layout/Topbar.jsx`
- `frontend/src/components/ui/Button.jsx`
- `frontend/src/components/ui/Card.jsx`
- `frontend/src/components/ui/EmptyState.jsx`
- `frontend/src/components/ui/GlobalLoader.jsx`
- `frontend/src/components/ui/Input.jsx`
- `frontend/src/components/ui/Loader.jsx`
- `frontend/src/components/ui/PageSkeleton.jsx`
- `frontend/src/components/ui/RouteErrorBoundary.jsx`
- `frontend/src/components/ui/Table.jsx`

---

## 12) Detailed Backend Checklist (API + DB + ML + GenAI)

Application core:
- `backend/app/main.py`
- `backend/app/core/config.py`
- `backend/app/core/security.py`
- `backend/app/core/logging.py`
- `backend/app/core/exceptions.py`
- `backend/app/core/dependencies.py`

API:
- `backend/app/api/v1/__init__.py`
- `backend/app/api/v1/routes/auth.py`
- `backend/app/api/v1/routes/prediction.py`
- `backend/app/api/v1/routes/forecast.py`
- `backend/app/api/v1/routes/sentiment.py`
- `backend/app/api/v1/routes/chat.py`
- `backend/app/api/v1/routes/monitoring.py`
- `backend/app/api/v1/routes/portfolio.py`
- `backend/app/api/v1/routes/scheduling.py`
- `backend/app/api/v1/routes/tickers.py`
- `backend/app/api/legacy_routes.py`

Schemas:
- `backend/app/schemas/auth.py`
- `backend/app/schemas/prediction.py`
- `backend/app/schemas/forecast.py`
- `backend/app/schemas/sentiment.py`
- `backend/app/schemas/chat.py`
- `backend/app/schemas/monitoring.py`
- `backend/app/schemas/scheduling.py`
- `backend/app/schemas/common.py`
- `backend/app/schemas/contracts.py`

Services:
- `backend/app/services/auth_service.py`
- `backend/app/services/prediction_service.py`
- `backend/app/services/forecast_service.py`
- `backend/app/services/sentiment_service.py`
- `backend/app/services/chat_service.py`
- `backend/app/services/genai_service.py`
- `backend/app/services/monitoring_service.py`
- `backend/app/services/model_loader.py`
- `backend/app/services/cache_service.py`
- `backend/app/services/log_service.py`
- `backend/app/services/portfolio_service.py`
- `backend/app/services/market_data_service.py`
- `backend/app/services/scheduling_service.py`
- `backend/app/services/public_user_service.py`
- `backend/app/services/data_quality_service.py`
- `backend/app/services/calendar_service.py`
- `backend/app/services/document_service.py`

Middleware:
- `backend/app/middleware/api_key.py`
- `backend/app/middleware/rate_limit.py`
- `backend/app/middleware/contract_middleware.py`

Database:
- `backend/app/db/base.py`
- `backend/app/db/session.py`
- `backend/app/db/init_db.py`
- `backend/app/db/crud_examples.py`
- `backend/app/db/models/user.py`
- `backend/app/db/models/prediction.py`
- `backend/app/db/models/market_data.py`
- `backend/app/db/models/sentiment.py`
- `backend/app/db/models/portfolio.py`
- `backend/app/db/models/logs.py`
- `backend/app/db/models/scheduled_event.py`
- `backend/app/db/models/__init__.py`

ML/DL helpers inside backend:
- `backend/app/ml/feature_engineering.py`
- `backend/app/ml/predictor.py`
- `backend/app/ml/vector_store.py`

Migrations:
- `backend/alembic/env.py`
- `backend/alembic/versions/20260409_01_initial_mysql_schema.py`
- `backend/alembic.ini`

---

## 13) Final Notes

This README is intentionally long and implementation-detailed to serve as:

- Developer onboarding document
- API and architecture reference
- File-by-file map for frontend, backend, ML, DL, GenAI, API, and DB layers

If you want, the next step can be generating a second document (`SYSTEM_CODE_DOCUMENTATION.md`) with:

1. Per-file function/class signatures extracted automatically
2. Sequence diagrams for each endpoint flow
3. Data dictionary for every table column
4. Error catalog (status code, source file, trigger condition)
# NeuralAlpha: AI-Powered Financial Market Intelligence Platform

## 📌 Executive Summary

**NeuralAlpha** is a production-grade, full-stack AI platform for financial market intelligence and price prediction. It combines dual machine learning models (XGBoost + LSTM), real-time chat powered by Anthropic Claude, retrieval-augmented generation for financial documents, sentiment analysis from news/social sources, portfolio analytics, and comprehensive observability for production monitoring.

**Current Repository State**:
- ✅ Frontend (React + Vite) - fully connected to backend APIs
- ✅ Backend (FastAPI) - async SQLAlchemy with MySQL, strict contract validation
- ✅ ML Pipeline (offline) - training/evaluation with champion-challenger framework
- ✅ Production Monitoring - inference auditing, model versioning, performance metrics

## 📚 Documentation Map

This repository includes comprehensive documentation:

1. **README.md** (this file) - Overview, quick start, architecture, component details
2. **SYSTEM_ARCHITECTURE.md** - High-level design, service interactions, data flows
3. **SYSTEM_CODE_DOCUMENTATION.md** - Exhaustive backend file-by-file code walkthrough
4. **FRONTEND_ARCHITECTURE.md** - Frontend components, pages, hooks, styling patterns
5. **API_REFERENCE.md** - All endpoints, request/response contracts, error handling
6. **ML_DL_GENAI_GUIDE.md** - Model training, evaluation, GenAI integration details

## Repository Structure

- frontend/: React app, UI pages/components, hooks, and API client.
- backend/: FastAPI app, API routes, schemas, services, workers, scripts, and tests.
- ml_pipeline/: offline preprocessing, training, and evaluation logic.
- infrastructure/: infrastructure notes/assets.
- docker-compose.yml: local service orchestration.
- .env / .env.example: runtime configuration.

## End-to-End Backend Workflow

### 1) Request Entry

FastAPI app startup and route wiring happen in backend/app/main.py.

Main responsibilities:
- initialize logging and service warmups.
- apply middleware (observability/validation and CORS).
- register route groups under /api.

### 2) API Boundary and Contracts

Route handlers in backend/app/api/routes/* perform:
- request parsing and schema validation.
- service invocation.
- normalized response output.

Contract schemas live in backend/app/schemas/* and include:
- prediction schemas.
- market/sentiment schemas.
- financial intel schemas.
- ai insight schemas.
- strict response contract schemas.

### 3) Service Layer Execution

Core runtime services:
- ML inference: backend/app/services/ml_service/model_loader.py + predictor.py.
- DL forecasting: backend/app/services/dl_service/* and orchestration pathways.
- Financial orchestration: backend/app/services/financial_intel/orchestrator.py.
- GenAI insights: backend/app/services/agent_service/insight_service.py and backend/app/genai/*.
- Monitoring/evaluation: backend/app/services/monitoring/* and backend/app/services/evaluation/*.

### 4) Persistence and State

Database/ORM modules in backend/app/db/* provide:
- SQLAlchemy base/session.
- domain models: market data, predictions, sentiments, users.

### 5) Async Workloads

Background processing is managed in backend/app/workers/* (Celery app and tasks).

### 6) Validation and Remediation Scripts

Operational scripts in backend/scripts:
- validate_production_system.py: runtime readiness and contract checks.
- auto_fix_system.py: automated remediation and diagnostics.

## API Surface (Backend)

The backend exposes endpoint groups under /api via route modules:
- backend/app/api/routes/prediction.py
- backend/app/api/routes/ai_insight.py
- backend/app/api/routes/financial_intel.py
- backend/app/api/routes/market.py
- backend/app/api/routes/sentiment.py
- backend/app/api/routes/chat.py
- backend/app/api/routes/monitoring.py
- backend/app/api/routes/portfolio.py
- backend/app/api/routes/model_runtime.py

Refer to /docs at runtime for authoritative OpenAPI schema.

## ML and DL Operational Flow

### ML Predict Path

1. API receives structured feature input.
2. predictor.py validates input and enforces strict runtime checks.
3. model_loader.py resolves model/scaler artifacts.
4. prediction + confidence + metadata returned in contract-safe shape.

### DL Forecast Path

1. API receives sequence + horizon context.
2. DL service executes sequence model inference.
3. forecast values and confidence are returned using schema constraints.

### Model Artifact Dependencies

Expected artifact families:
- classical model artifact.
- sequence model artifact.
- preprocessing/scaler artifact.

Missing artifacts are surfaced as explicit errors in strict mode rather than silent fallback.

## GenAI Workflow

GenAI modules:
- backend/app/genai/openai_client.py
- backend/app/genai/prompt_engine.py
- backend/app/genai/prompt_templates.py
- backend/app/services/agent_service/insight_service.py

Workflow:
1. AI Insight endpoint receives question/context.
2. Prompt templates compose structured request intent.
3. Provider client executes external model call.
4. Output is validated into strict response schema.
5. Errors/fallbacks are handled explicitly according to configuration flags.

## Configuration and Environment

Primary config module: backend/app/core/config.py.

Common environment concerns:
- model enforcement flags.
- strict API validation flags.
- provider keys and model names.
- DB/cache/runtime service URLs.

Use .env.example as baseline and populate .env for active runtime.

## Security and Platform Concerns

Core security and runtime foundations:
- backend/app/core/security.py: auth/security helpers.
- backend/app/core/logging.py: unified logging initialization.
- backend/app/api/middleware.py: request id, latency, and contract-level middleware behavior.

## Testing Strategy

Test suite location: backend/tests.

Focus areas:
- API behavior and contracts.
- ML inference behavior.
- agent/genai service behavior.

Recommended CI gates:
- schema contract tests.
- strict-mode inference tests.
- no-mock integration checks for critical endpoints.

## Local Setup in 5 Steps

Prerequisites: Python 3.11, MySQL 8.x, Node.js 18+

1. Create MySQL database:

```bash
mysql -u root -p -e "CREATE DATABASE neuralalpha CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
```

2. Configure environment:

```bash
cp backend/.env.example backend/.env
# Edit backend/.env: set DATABASE_URL and ANTHROPIC_API_KEY
```

3. Install backend dependencies:

```bash
cd backend && pip install -r requirements.txt
```

4. Apply migrations and seed data:

```bash
alembic upgrade head && python scripts/seed_data.py
```

5. Start everything:

```bash
bash scripts/run_local.sh
# Backend: http://localhost:8000/docs
# Frontend: http://localhost:3000
```

### Windows full run mode

```powershell
.\scripts\full_run_mode.ps1
```

This starts backend and frontend, waits for readiness, runs deep QA, strict production validation, and smoke tests, then prints one JSON summary.

## Local Development

### Backend startup (without Docker)

```bash
cd backend
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### Frontend startup (without Docker)

```bash
cd frontend
npm install
npm run dev
```

### Docker startup (profile based)

Development profile (hot reload for frontend/backend):

```bash
docker compose --profile dev up --build
```

Production-like profile (nginx frontend + stable backend):

```bash
docker compose --profile prod up -d --build
```

### Health and smoke checks

Health endpoints:
- Backend: `http://localhost:8000/health`
- Frontend (prod profile): `http://localhost:8080/`

Smoke test command:

```bash
cd backend
python scripts\smoke_test_stack.py
```

### Database migrations

```bash
cd backend
python -m alembic upgrade head
```

Rollback one migration step:

```bash
cd backend
python -m alembic downgrade -1
```

## Offline ML Pipeline

Pipeline path: ml_pipeline/

Primary stages:
- preprocessing/: feature engineering and setup logic.
- training/: xgboost and lstm training scripts.
- evaluation/: metrics and comparison tooling.

Typical training commands:

```bash
python ml_pipeline\training\train_xgboost.py
python ml_pipeline\training\train_lstm.py
```

## Full Code-Wise Documentation

For exhaustive file-by-file code with inlined source blocks and per-file purpose notes, open:
- SYSTEM_CODE_DOCUMENTATION.md

This document was generated to cover backend, API, ML/DL/GenAI modules, scripts, tests, and infrastructure docs in the current repository state.

## Deployment Runbook

For release checklist, smoke-test gate, and rollback process, see:
- infrastructure/DEPLOYMENT_RUNBOOK.md
