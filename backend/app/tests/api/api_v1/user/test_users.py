import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app import crud
from app.tests import utils_for_testing as ut

# This is the same as using the @pytest.mark.anyio on all test functions in the module
pytestmark = pytest.mark.anyio


async def test_read_all_users_by_admin(async_client: AsyncClient, db_tests: AsyncSession,
                                       admin_token_headers: dict[str, str]) -> None:
    p = await ut.create_random_participant(db_tests)
    s = await ut.create_random_speaker(db_tests)
    a = await ut.create_random_admin(db_tests)
    r = await async_client.get(f"{settings.API_V1_STR}/users/all/", headers=admin_token_headers)
    users = r.json()
    assert len(users) >= 3
    for user in users:
        assert "email" in user
    p_db = await crud.user.get_by_email(db_tests, email=p.email)
    s_db = await crud.user.get_by_email(db_tests, email=s.email)
    a_db = await crud.user.get_by_email(db_tests, email=a.email)
    assert p_db and s_db and a_db
    assert p_db.id == p.id
    assert s_db.id == s.id
    assert a_db.id == a.id


async def test_read_all_users_by_not_admin(async_client: AsyncClient, db_tests: AsyncSession,
                                           speaker_token_headers: dict[str, str]) -> None:
    """Unnecessary test that actually tests the Depends() which is already tested in test_deps.py."""
    await ut.create_random_participant(db_tests)
    await ut.create_random_speaker(db_tests)
    await ut.create_random_admin(db_tests)
    r = await async_client.get(f"{settings.API_V1_STR}/users/all/", headers=speaker_token_headers)
    assert r.status_code == 400
    assert "The user doesn't have enough privileges" in r.json().values()


async def test_read_user_me(async_client: AsyncClient, admin_token_headers: dict[str, str],
                            participant_token_headers: dict[str, str]) -> None:
    r = await async_client.get(f"{settings.API_V1_STR}/users/me", headers=admin_token_headers)
    r2 = await async_client.get(f"{settings.API_V1_STR}/users/me", headers=participant_token_headers)
    assert r.status_code == 200 and r2.status_code == 200
    assert "admin" in r.json().values()
    assert "participant" in r2.json().values()


async def test_update_user_me(async_client: AsyncClient, participant_token_headers: dict[str, str]) -> None:
    data = {"first_name": "Sandra", "email": ut.random_email()}
    r = await async_client.put(f"{settings.API_V1_STR}/users/me", headers=participant_token_headers, json=data)
    assert r.status_code == 200
    assert "Sandra" in r.json().values()


async def test_update_user_me_existing_email(async_client: AsyncClient, db_tests: AsyncSession,
                                             participant_token_headers: dict[str, str]) -> None:
    p = await ut.create_random_participant(db_tests)
    data = {"first_name": "Sandra", "email": p.email}
    r = await async_client.put(f"{settings.API_V1_STR}/users/me", headers=participant_token_headers, json=data)
    assert r.status_code == 400
    assert "A user with this email already exists in the system..." in r.json().values()


async def test_read_user_by_id_by_admin(async_client: AsyncClient, db_tests: AsyncSession,
                                        admin_token_headers: dict[str, str]) -> None:
    p = await ut.create_random_participant(db_tests)
    r = await async_client.get(f"{settings.API_V1_STR}/users/{p.id}", headers=admin_token_headers)
    assert r.status_code == 200
    assert p.email in r.json().values()
    p_db = await crud.user.get_by_email(db_tests, email=p.email)
    assert p_db
    assert p_db.id == p.id


async def test_read_user_by_id_by_not_admin(async_client: AsyncClient, db_tests: AsyncSession,
                                            speaker_token_headers: dict[str, str]) -> None:
    """Unnecessary test that actually tests the Depends() which is already tested in test_deps.py."""
    p = await ut.create_random_participant(db_tests)
    r = await async_client.get(f"{settings.API_V1_STR}/users/{p.id}", headers=speaker_token_headers)
    assert r.status_code == 400
    assert "The user doesn't have enough privileges" in r.json().values()
