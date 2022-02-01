from typing import Generator

from sqlalchemy.ext.asyncio import AsyncSession
import pytest

from app import crud
from app.core.config import settings
from app.db.init_db import initialize_db


# This is the same as using the @pytest.mark.anyio on all test functions in the module
pytestmark = pytest.mark.anyio


async def test_initialize_db_empty_db(db_tests: AsyncSession) -> None:
    p_type_names = [p_type_name for p_type_name in settings.PARTICIPANT_TYPES_NB_SESSION_WEEK]
    p_status_names = settings.PARTICIPANT_STATUS
    s_type_names = settings.SESSION_TYPES
    s_status_names = settings.SESSION_STATUS

    try:
        await initialize_db(db_tests)
    except:
        # should not but in case this avoid tests crash(es)...
        raise AssertionError("function initialize_db() raises an exception during test...")

    assert await crud.admin.get_by_email(db_tests, email=settings.FIRST_SUPERUSER_EMAIL)

    db_p_type_names = [db_pt.name for db_pt in await crud.participant_type.get_multi(db_tests)]
    assert db_p_type_names and len(db_p_type_names) >= len(p_type_names)
    p_types_comparison = [db_pt_name for db_pt_name, pt_name in zip(db_p_type_names, p_type_names)
                          if db_pt_name == pt_name]
    assert p_types_comparison and len(p_types_comparison) == len(p_type_names)

    db_p_status_names = [db_ps.name for db_ps in await crud.participant_status.get_multi(db_tests)]
    assert db_p_status_names and len(db_p_status_names) >= len(p_status_names)
    p_status_comparison = [db_ps_name for db_ps_name, ps_name in zip(db_p_status_names, p_status_names)
                          if db_ps_name == ps_name]
    assert p_status_comparison and len(p_status_comparison) == len(p_status_names)

    db_s_type_names = [db_st.name for db_st in await crud.session_type.get_multi(db_tests)]
    assert db_s_type_names and len(db_s_type_names) >= len(s_type_names)
    s_types_comparison = [db_st_name for db_st_name, st_name in zip(db_s_type_names, s_type_names)
                          if db_st_name == st_name]
    assert s_types_comparison and len(s_types_comparison) == len(s_type_names)

    db_s_status_names = [db_ss.name for db_ss in await crud.session_status.get_multi(db_tests)]
    assert db_s_status_names and len(db_s_status_names) >= len(s_status_names)
    s_status_comparison = [db_ss_name for db_ss_name, ss_name in zip(db_s_status_names, s_status_names)
                          if db_ss_name == ss_name]
    assert s_status_comparison and len(s_status_comparison) == len(s_status_names)
