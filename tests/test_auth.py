import uuid
import re
import pytest
from httpx import AsyncClient
from app.main import app


async def get_csrf(ac: AsyncClient):
    r = await ac.get("/")
    m = re.search(r'name="csrf_token" value="([0-9a-f]+)"', r.text)
    return m.group(1) if m else None


@pytest.mark.asyncio
async def test_register_and_login_flow():
    username = f"testuser_{uuid.uuid4().hex[:8]}"
    password = "Aa1!testpwd"

    async with AsyncClient(app=app, base_url="http://testserver") as ac:

        # -------- REGISTER --------
        csrf = await get_csrf(ac)

        r = await ac.post(
            "/register",
            data={
                "username": username,
                "password": password,
                "confirm_password": password,
                "csrf_token": csrf,
            },
        )

        assert r.status_code == 200
        assert "Account created" in r.text or "Please log in" in r.text

        # -------- LOGIN --------
        csrf = await get_csrf(ac)

        r2 = await ac.post(
            "/login",
            data={
                "username": username,
                "password": password,
                "csrf_token": csrf,
            },
            follow_redirects=False,
        )

        assert r2.status_code in (302, 303)

        # Validate cookie security flags
        set_cookie = r2.headers.get("set-cookie", "")
        assert "HttpOnly" in set_cookie