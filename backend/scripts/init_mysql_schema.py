"""Create MySQL tables from SQLAlchemy models for phase-2 persistence rollout."""

from __future__ import annotations

import asyncio
from pathlib import Path
import sys

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.db.session import init_db_models


async def main() -> None:
    await init_db_models()
    print("MySQL schema initialization completed.")


if __name__ == "__main__":
    asyncio.run(main())
