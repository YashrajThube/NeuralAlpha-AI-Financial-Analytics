"""API unit tests for lightweight route behavior."""

import pytest

from app.main import health_check


@pytest.mark.asyncio
async def test_health_check_function() -> None:
    """Verify service health function without startup side effects."""
    result = await health_check()
    assert result["status"] == "ok"
    assert "env" in result
