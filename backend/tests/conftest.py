"""Global pytest configuration for deterministic local backend tests."""

from __future__ import annotations

import os


# Keep tests independent from strict production toggles.
os.environ.setdefault("ENFORCE_REAL_MODELS", "false")
os.environ.setdefault("STRICT_API_VALIDATION", "false")
os.environ.setdefault("ENVIRONMENT", "test")

# Ensure async DB engine creation is always valid during import-time setup.
if os.environ.get("DATABASE_URL", "").startswith("sqlite+pysqlite"):
	os.environ["DATABASE_URL"] = "mysql+aiomysql://neuralalpha:neuralalpha@localhost:3306/neuralalpha"
