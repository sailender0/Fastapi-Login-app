import uuid
import pytest
from httpx import AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_register_and_login_flow():
    username = f"testuser_{uuid.uuid4().hex[:8]}"
    password = "Aa1!testpwd"

    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        r = await ac.post("/register", data={"username": username, "password": password, "confirm_password": password})
        assert r.status_code == 200
        assert "Account created" in r.text or "Please log in" in r.text

        r2 = await ac.post("/login", data={"username": username, "password": password}, follow_redirects=False)
        assert r2.status_code in (200, 302)
        # ensure a cookie was set in the response
        assert r2.cookies
