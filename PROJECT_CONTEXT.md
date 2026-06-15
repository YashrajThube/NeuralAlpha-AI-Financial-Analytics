# PROJECT_CONTEXT.md

# NeuralAlpha – AI-Powered Financial Analytics Platform

## Project Overview

NeuralAlpha is a full-stack AI-powered financial analytics platform that provides stock prediction, forecasting, sentiment analysis, portfolio management, monitoring, scheduling, and AI-assisted financial insights through a modern web dashboard.

The system combines Machine Learning, Financial Data Analysis, FastAPI backend services, React frontend applications, and Large Language Models to deliver intelligent financial decision-support capabilities.

---

# Core Objectives

1. Predict stock trends using machine learning.
2. Generate future forecasts using historical market data.
3. Analyze market sentiment from financial sources.
4. Provide AI-powered financial assistance through chat.
5. Manage and analyze investment portfolios.
6. Monitor model performance and system health.
7. Provide a scalable and production-ready architecture.

---

# Technology Stack

## Frontend

* React.js
* Vite
* JavaScript
* Tailwind CSS
* Axios
* React Router

## Backend

* FastAPI
* Python 3.x
* Pydantic
* Uvicorn
* JWT Authentication

## Database

* MySQL

## Machine Learning

* Scikit-Learn
* Pandas
* NumPy
* Joblib

## AI Services

* Gemini API
* LLM-powered Financial Assistant

## Infrastructure

* Docker
* Docker Compose
* GitHub Actions

---

# Repository Structure

backend/
frontend/
ml_pipeline/
data/
models/
notebooks/
scripts/
infrastructure/

---

# Backend Structure

backend/app/

api/
core/
db/
middleware/
ml/
models/
schemas/
services/
utils/

main.py

---

# Backend Responsibilities

## Authentication

Endpoints:

/api/v1/auth/register
/api/v1/auth/login

Responsibilities:

* User registration
* User authentication
* JWT token generation
* Access control

---

## Prediction Service

Endpoints:

/api/predict
/api/v1/predict

Responsibilities:

* Stock prediction
* ML model inference
* Prediction history

---

## Forecast Service

Endpoints:

/api/forecast
/api/v1/forecast

Responsibilities:

* Time-series forecasting
* Future price estimation
* Trend analysis

---

## Sentiment Service

Endpoints:

/api/sentiment/{symbol}
/api/v1/sentiment/{symbol}

Responsibilities:

* Market sentiment analysis
* Financial news sentiment
* Symbol-based scoring

---

## AI Chat Service

Endpoints:

/api/chat
/api/v1/chat

Responsibilities:

* Financial assistant
* Investment insights
* User guidance
* LLM integration

---

## Portfolio Service

Endpoints:

/api/v1/portfolio

Responsibilities:

* Portfolio management
* Holdings tracking
* Portfolio analytics

---

## Monitoring Service

Endpoints:

/api/v1/monitoring

Responsibilities:

* Health monitoring
* Performance tracking
* Error monitoring
* Latency metrics

---

## Calendar Scheduling

Endpoints:

/api/v1/calendar/schedule
/api/v1/calendar/events

Responsibilities:

* Event scheduling
* Financial reminders
* Calendar integration

---

# Frontend Responsibilities

Dashboard

Prediction Page

Forecast Page

Chat Interface

Portfolio Dashboard

Sentiment Dashboard

Monitoring Dashboard

User Authentication

Responsive UI

---

# Machine Learning Pipeline

Location:

ml_pipeline/

Responsibilities:

1. Data Collection
2. Data Cleaning
3. Feature Engineering
4. Model Training
5. Evaluation
6. Prediction Serving

Preferred Metrics:

* Accuracy
* Precision
* Recall
* F1 Score
* ROC-AUC
* RMSE
* MAE

---

# Environment Variables

Required:

DATABASE_URL

JWT_SECRET

JWT_ALGORITHM

GEMINI_API_KEY

OPENAI_API_KEY

ALPHA_VANTAGE_API_KEY

FINNHUB_API_KEY

NEWS_API_KEY

CORS_ORIGINS

ENVIRONMENT

---

# Current Known Issue

Dashboard shows:

"API key protection misconfigured"

Several endpoints return:

HTTP 503 Service Unavailable

Affected APIs:

* /api/v1/predict
* /api/v1/forecast
* /api/v1/sentiment
* /api/v1/monitoring
* /api/v1/tickers

Likely causes:

1. Missing API keys
2. Invalid API configuration
3. Database connection issue
4. Missing ML model files
5. Service initialization failure

---

# Coding Standards

* Follow PEP8.
* Use type hints.
* Prefer reusable services.
* Avoid duplicate logic.
* Add proper logging.
* Use dependency injection.
* Maintain clean architecture.
* Keep functions small and testable.

---

# Security Rules

* Never expose secrets.
* Use environment variables.
* Validate all inputs.
* Use JWT authentication.
* Protect sensitive endpoints.
* Prevent SQL injection.
* Follow OWASP best practices.

---

# Performance Goals

* Fast API responses
* Low latency inference
* Efficient database queries
* Optimized frontend rendering
* Scalable architecture

---

# Instructions For Codex

Always read this file before making changes.

When analyzing:

Return only:

1. Root Cause
2. Exact File
3. Required Fix
4. Minimal Code Patch

Avoid large explanations.

Do not rewrite working code.

Prefer minimal changes.

Focus on:

* Bugs
* Security Issues
* Performance Issues
* Architecture Problems

Rank findings:

Critical > High > Medium > Low

Keep responses concise.

Maximum response length: 300 words unless explicitly requested.
