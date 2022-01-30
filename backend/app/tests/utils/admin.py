from sqlalchemy.ext.asyncio import AsyncSession
from httpx import AsyncClient

from app import crud
from app.core.config import settings
from app.models import Admin
from app.schemas import AdminCreate
import app.tests.utils as ut


async def create_random_admin(db: AsyncSession, *, email: str = None, api_key: str = None) -> Admin:
    if email is None:
        email = ut.random_email()
    if api_key is None:
        api_key = ut.random_lower_string(32)
    admin_in = AdminCreate(
        email=email,
        api_key=api_key, first_name=ut.random_lower_string(6),
        last_name=ut.random_lower_string(6), slot_time=ut.random_five_multiple_number())
    admin = await crud.admin.create(db=db, obj_in=admin_in)
    return admin


async def get_admin_user_token_headers(client: AsyncClient) -> dict[str, str]:
    """This admin user is in db due to the init_data_tests_db autouse fixture (see conftest.py)."""
    login_data = {
        "username": settings.FIRST_SUPERUSER_EMAIL,
        "password": settings.FIRST_SUPERUSER_PASSWORD,
    }
    r = await client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    tokens = r.json()
    a_token = tokens["access_token"]
    headers = {"Authorization": f"Bearer {a_token}"}
    return headers
