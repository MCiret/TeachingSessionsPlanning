from typing import Generator

from sqlalchemy.ext.asyncio import AsyncSession
import pytest

from app import crud, models
from app.core.config import settings
from app.db.init_db import initialize_db
from app.tests.conftest import engine_tests_db, AsyncTestsSessionLocal


# This is the same as using the @pytest.mark.anyio on all test functions in the module
pytestmark = pytest.mark.anyio


@pytest.fixture
async def init_data_tests_db() -> None:
    """
    Overriding this fixture (see tests/conftest.py) that initialized db for tests since this initialize_db()
    function is the one to be tested here.
    """
    pass

@pytest.fixture
async def db_tests() -> Generator:
    """
    Overriding this fixture (see tests/conftest.py) to have an empty db only for this module tests.
    """
    async with engine_tests_db.begin() as conn:
        await conn.run_sync(models.Base.metadata.drop_all)
        await conn.run_sync(models.Base.metadata.create_all)
    async with AsyncTestsSessionLocal() as async_tests_session:
        yield async_tests_session
    # see tips https://docs.sqlalchemy.org/en/14/orm/extensions/asyncio.html#synopsis-core
    await engine_tests_db.dispose()  # see tips https://docs.sqlalchemy.org/en/14/orm/extensions/asyncio.html#synopsis-core


async def test_initialize_db_empty_db(init_data_tests_db, db_tests: AsyncSession) -> None:
    admin_user_email = settings.FIRST_SUPERUSER_EMAIL
    # assert that db is empty
    assert not await crud.user.get_multi(db_tests)

    p_type_names = [p_type_name for p_type_name in settings.PARTICIPANT_TYPES_NB_SESSION_WEEK.values()]
    p_status_names = settings.PARTICIPANT_STATUS
    s_type_names = settings.SESSION_TYPES
    s_status_names = settings.SESSION_STATUS

    await initialize_db(db_tests)

    assert await crud.admin.get_by_email(db_tests, email=admin_user_email)

    db_p_types = await crud.participant_type.get_multi(db_tests)
    assert db_p_types and len(db_p_types) == len(p_type_names)

    db_p_status = await crud.participant_status.get_multi(db_tests)
    assert db_p_status and len(db_p_status) == len(p_status_names)

    db_s_types = await crud.session_type.get_multi(db_tests)
    assert db_s_types and len(db_s_types) == len(s_type_names)

    db_s_status = await crud.session_status.get_multi(db_tests)
    assert db_s_status and len(db_s_status) == len(s_status_names)


async def test_initialize_db_already_initialized(init_data_tests_db, db_tests: AsyncSession) -> None:
    # Initialize db a first time :
    await initialize_db(db_tests)

    admin_user_email = settings.FIRST_SUPERUSER_EMAIL
    p_type_names = [p_type_name for p_type_name in settings.PARTICIPANT_TYPES_NB_SESSION_WEEK.values()]
    p_status_names = settings.PARTICIPANT_STATUS
    s_type_names = settings.SESSION_TYPES
    s_status_names = settings.SESSION_STATUS
    try:
        await initialize_db(db_tests)
    except:
        raise AssertionError("test_initialize_db_already_initialized Failed")

    assert await crud.admin.get_by_email(db_tests, email=admin_user_email)
    assert len(await crud.user.get_multi(db_tests)) == 1

    db_p_types = await crud.participant_type.get_multi(db_tests)
    assert db_p_types and len(db_p_types) == len(p_type_names)

    db_p_status = await crud.participant_status.get_multi(db_tests)
    assert db_p_status and len(db_p_status) == len(p_status_names)

    db_s_types = await crud.session_type.get_multi(db_tests)
    assert db_s_types and len(db_s_types) == len(s_type_names)

    db_s_status = await crud.session_status.get_multi(db_tests)
    assert db_s_status and len(db_s_status) == len(s_status_names)
