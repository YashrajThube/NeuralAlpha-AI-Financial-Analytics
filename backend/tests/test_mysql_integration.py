"""Optional MySQL integration smoke tests.

These tests are skipped unless TEST_DATABASE_URL is provided.
"""

from __future__ import annotations

import os

import pytest
from sqlalchemy import create_engine, text


@pytest.mark.integration
def test_mysql_connectivity_smoke() -> None:
    url = os.getenv("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL is not configured")

    engine = create_engine(url.replace("+aiomysql", "+pymysql"), pool_pre_ping=True)
    try:
        with engine.connect() as conn:
            value = conn.execute(text("SELECT 1")).scalar_one()
            assert value == 1
    finally:
        engine.dispose()
