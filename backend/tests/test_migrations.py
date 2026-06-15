"""Alembic migration smoke tests.

These tests are skipped unless TEST_DATABASE_URL is explicitly provided.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest


@pytest.mark.integration
def test_alembic_upgrade_head_smoke() -> None:
    url = os.getenv("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL is not configured")

    backend_root = Path(__file__).resolve().parents[1]

    env = os.environ.copy()
    env["DATABASE_URL"] = url

    result = subprocess.run(  # noqa: S603
        ["alembic", "upgrade", "head"],
        cwd=str(backend_root),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
