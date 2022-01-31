import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.encoders import jsonable_encoder

from app.core.config import settings
from app import crud
from app.schemas import AdminCreate, AdminUpdate
from app.tests import utils as ut

# This is the same as using the @pytest.mark.anyio on all test functions in the module
pytestmark = pytest.mark.anyio


async def test_read_admins_by_admin(async_client: AsyncClient, db_tests: AsyncSession,
                                    admin_token_headers: dict[str, str]) -> None:
    await ut.create_random_participant(db_tests)
    await ut.create_random_speaker(db_tests)
    await ut.create_random_admin(db_tests)
    r = await async_client.get(f"{settings.API_V1_STR}/users/admins/", headers=admin_token_headers)
    admins = r.json()
    assert len(admins) >= 1
    for admin in admins:
        assert "email" in admin
        assert admin["profile"] == "admin"


async def test_read_admins_by_not_admin(async_client: AsyncClient, db_tests: AsyncSession,
                                        speaker_token_headers: dict[str, str]) -> None:
    """Unnecessary test that actually tests the Depends() which is already tested in test_deps.py."""
    await ut.create_random_participant(db_tests)
    await ut.create_random_speaker(db_tests)
    await ut.create_random_admin(db_tests)
    r = await async_client.get(f"{settings.API_V1_STR}/users/admins/", headers=speaker_token_headers)
    assert r.status_code == 400
    assert "The user doesn't have enough privileges" in r.json().values()


async def test_create_admin_by_admin(async_client: AsyncClient, db_tests: AsyncSession,
                                     admin_token_headers: dict[str, str]) -> None:
    data = jsonable_encoder(AdminCreate(email=ut.random_email(),
                                        api_key=ut.random_lower_string(32),
                                        first_name=ut.random_lower_string(8),
                                        last_name=ut.random_lower_string(8))
                            )
    r = await async_client.post(f"{settings.API_V1_STR}/users/admin", headers=admin_token_headers, json=data)
    assert r.status_code == 200
    db_admin_dict = r.json()
    assert "email" in db_admin_dict
    db_admin = await crud.admin.get(db_tests, id=db_admin_dict["id"])
    assert db_admin.email == data["email"]


async def test_create_admin_existing_email_by_admin(async_client: AsyncClient, db_tests: AsyncSession,
                                                    admin_token_headers: dict[str, str]) -> None:
    email = ut.random_email()
    existing_email_user = await ut.create_random_speaker(db_tests, email=email)
    data = jsonable_encoder(AdminCreate(email=email,
                                        api_key=ut.random_lower_string(32),
                                        first_name=ut.random_lower_string(8),
                                        last_name=ut.random_lower_string(8)))
    r = await async_client.post(f"{settings.API_V1_STR}/users/admin", headers=admin_token_headers, json=data)
    assert r.status_code == 400
    assert "A user with this email already exists in the system..." in r.json().values()
    db_existing_email_user = await crud.user.get(db_tests, id=existing_email_user.id)
    assert db_existing_email_user.email == existing_email_user.email


async def test_create_admin_by_not_admin(async_client: AsyncClient, db_tests: AsyncSession,
                                         speaker_token_headers: dict[str, str]) -> None:
    """Unnecessary test that actually tests the Depends() which is already tested in test_deps.py."""
    email = ut.random_email()
    data = jsonable_encoder(AdminCreate(email=email,
                                        api_key=ut.random_lower_string(32),
                                        first_name=ut.random_lower_string(8),
                                        last_name=ut.random_lower_string(8))
                            )
    r = await async_client.post(f"{settings.API_V1_STR}/users/admin", headers=speaker_token_headers, json=data)
    assert r.status_code == 400
    assert "The user doesn't have enough privileges" in r.json().values()
    not_created_db_admin = await crud.user.get_by_email(db_tests, email=email)
    assert not not_created_db_admin


async def test_update_admin_by_id_by_admin(async_client: AsyncClient, db_tests: AsyncSession,
                                           admin_token_headers: dict[str, str]) -> None:
    db_admin = await ut.create_random_admin(db_tests)
    data = jsonable_encoder(AdminUpdate(first_name="Sandra"), exclude_unset=True)
    r = await async_client.put(f"{settings.API_V1_STR}/users/admin/{db_admin.id}",
                               headers=admin_token_headers, json=data)
    assert r.status_code == 200
    assert "Sandra" in r.json().values()


async def test_update_admin_by_id_existing_email_by_admin(async_client: AsyncClient, db_tests: AsyncSession,
                                                          admin_token_headers: dict[str, str]) -> None:
    db_admin = await ut.create_random_admin(db_tests)
    data = jsonable_encoder(AdminUpdate(first_name="Sandra", email=db_admin.email), exclude_unset=True)
    r = await async_client.put(f"{settings.API_V1_STR}/users/admin/{db_admin.id}",
                               headers=admin_token_headers, json=data)
    assert r.status_code == 400
    assert "A user with this email already exists in the system..." in r.json().values()


async def test_update_admin_by_id_not_existing_by_admin(async_client: AsyncClient, db_tests: AsyncSession,
                                                        admin_token_headers: dict[str, str]) -> None:
    # get a not existing admin id
    db_admins = await crud.admin.get_multi(db_tests)
    if db_admins:
        max_id = max([admin.id for admin in db_admins])
    else:
        max_id = 0
    data = jsonable_encoder(AdminUpdate(first_name="Sandra"), exclude_unset=True)
    r = await async_client.put(f"{settings.API_V1_STR}/users/admin/{max_id + 1}",
                               headers=admin_token_headers, json=data)
    assert r.status_code == 404
    assert "An admin user with this id does not exist in the system..." in r.json().values()


async def test_update_admin_by_id_by_not_admin(async_client: AsyncClient, db_tests: AsyncSession,
                                               speaker_token_headers: dict[str, str]) -> None:
    """Unnecessary test that actually tests the Depends() which is already tested in test_deps.py."""
    db_admin = await ut.create_random_admin(db_tests)
    data = jsonable_encoder(AdminUpdate(first_name="Sandra"), exclude_unset=True)
    r = await async_client.put(f"{settings.API_V1_STR}/users/admin/{db_admin.id}",
                               headers=speaker_token_headers, json=data)
    assert r.status_code == 400
    assert "The user doesn't have enough privileges" in r.json().values()
