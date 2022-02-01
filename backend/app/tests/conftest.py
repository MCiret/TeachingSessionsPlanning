from typing import Generator

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.db.init_db import initialize_db
from app.main import app
from app.api.deps import get_async_db
from app import models
from app.tests import utils_for_testing as ut

engine_tests_db = create_async_engine("postgresql+asyncpg://postgres:postgres_key@localhost/p13_tests_db", future=True)
AsyncTestsSessionLocal = sessionmaker(class_=AsyncSession, future=True, expire_on_commit=False,
                                      autocommit=False, autoflush=False, bind=engine_tests_db)


@pytest.fixture(scope="session")
def anyio_backend():
    return 'asyncio'


@pytest.fixture(scope="session")
async def db_tests() -> Generator:
    async with engine_tests_db.begin() as conn:
        await conn.run_sync(models.Base.metadata.drop_all)
        await conn.run_sync(models.Base.metadata.create_all)
    async with AsyncTestsSessionLocal() as async_tests_session:
        yield async_tests_session


async def get_tests_db_dependency_for_overriding() -> Generator:
    async with AsyncTestsSessionLocal() as async_tests_session:
        yield async_tests_session


@pytest.fixture(scope="session", autouse=True)
def override_get_async_db_dep() -> None:
    """To get a db_tests session from the dependency used by endpoints functions."""
    app.dependency_overrides[get_async_db] = get_tests_db_dependency_for_overriding
    yield
    app.dependency_overrides = {}


@pytest.fixture(scope="session", autouse=True)
async def init_data_tests_db(db_tests) -> None:
    """
    Prepopulates test db using data from core/config.py :
    - an Admin (super) user
    - types and status for Participant and Session (which are required for creation)
    """
    await initialize_db(db_tests)


@pytest.fixture(scope="module")
async def async_client() -> Generator:
    async with AsyncClient(app=app, base_url="http://127.0.0.1:8000") as ac:
        yield ac


# Fixtures to have the Bearer Token in header when calling endpoints
@pytest.fixture(scope="module")
async def admin_token_headers(async_client: AsyncClient) -> dict[str, str]:
    """To get an admin Bearer Token for headers param in endpoints calling."""
    return await ut.get_admin_user_token_headers(async_client)


@pytest.fixture(scope="module")
async def speaker_token_headers(async_client: AsyncClient, db_tests: AsyncSession) -> dict[str, str]:
    """To get a speaker Bearer Token for headers param in endpoints calling."""
    return await ut.speaker_authentication_token_from_email(
        client=async_client,
        email=settings.EMAIL_TEST_SPEAKER,
        db=db_tests
    )


@pytest.fixture(scope="module")
async def participant_token_headers(async_client: AsyncClient, db_tests: AsyncSession) -> dict[str, str]:
    """To get a participant Bearer Token for headers param in endpoints calling."""
    return await ut.participant_authentication_token_from_email(
        client=async_client,
        email=settings.EMAIL_TEST_PARTICIPANT,
        db=db_tests
    )
