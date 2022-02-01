import random
import string
from typing import Any

from httpx import AsyncClient, Response

from app.core.config import settings


def random_lower_string(nb_char: int) -> str:
    return "".join(random.choices(string.ascii_lowercase, k=nb_char))


def random_email() -> str:
    return f"{random_lower_string(16)}@{random_lower_string(8)}.com"


def random_five_multiple_number() -> int:
    return random.randrange(10, 90, 5)


def random_list_elem(choices_list: list[Any]) -> Any:
    return random.choice(choices_list)


async def get_not_admin_user_authentication_headers(
    *, client: AsyncClient, email: str, api_key: str
) -> dict[str, str] | Response:
    """
    To login a speaker/participant user (who has to exist in db) and get the corresponding Bearer token.
    See utils/admin.py for equivalent for an admin user.
    """
    data = {"username": email, "password": api_key}
    r = await client.post(f"{settings.API_V1_STR}/login/access-token", data=data)
    response = r.json()
    if "access_token" in response:
        auth_token = response["access_token"]
        headers = {"Authorization": f"Bearer {auth_token}"}
        return headers
