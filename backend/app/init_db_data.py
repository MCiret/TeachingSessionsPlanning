"""
Not directly tested module (that is why it is 0% coverage)
but the most important part (initialize_db() function) is tested somewhere else (see app/tests/db/).
"""

import logging
import asyncio

from app.db.init_db import initialize_db
from app.db.db_session import AsyncSessionLocal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def init() -> None:
    db = AsyncSessionLocal()
    await initialize_db(db)


async def main() -> None:
    logger.info("Creating initial data")
    await init()
    logger.info("Initial data created")


if __name__ == "__main__":
    asyncio.run(main())
