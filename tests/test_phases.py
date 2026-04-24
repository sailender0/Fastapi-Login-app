import pytest
import re
from httpx import AsyncClient
from sqlalchemy import select
from app.main import app
from app.db.session import engine, AsyncSessionLocal
from app.db.models import Base, User


# -------------------------
# Helpers
# -------------------------

async def get_csrf(client: AsyncClient):
    r = await client.get("/")
    m = re.search(r'name="csrf_token" value="([0-9a-f]+)"', r.text)
    if m:
        return m.group(1)

    r = await client.get("/register")
    m = re.search(r'name="csrf_token" value="([0-9a-f]+)"', r.text)
    return m.group(1) if m else None


async def reset_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


# -------------------------
# Full Phase Test
# -------------------------

@pytest.mark.asyncio
async def test_full_phases():
    await reset_db()
    strong = "Admin@123"

    async with AsyncClient(app=app, base_url="http://test") as client:

        # -------- Phase 1: Weak passwords rejected --------
        for i, pw in enumerate(["123", "password", "admin123"]):
            csrf = await get_csrf(client)
            r = await client.post(
                "/register",
                data={
                    "username": f"p1_{i}",
                    "password": pw,
                    "confirm_password": pw,
                    "csrf_token": csrf,
                },
            )
            assert "Password must be at least" in r.text or "Must include" in r.text

        # Strong password accepted
        csrf = await get_csrf(client)
        r = await client.post(
            "/register",
            data={
                "username": "p1_ok",
                "password": strong,
                "confirm_password": strong,
                "csrf_token": csrf,
            },
        )
        assert r.status_code == 200

        # -------- Phase 2: Password mismatch --------
        csrf = await get_csrf(client)
        r = await client.post(
            "/register",
            data={
                "username": "p2",
                "password": strong,
                "confirm_password": "Admin@12",
                "csrf_token": csrf,
            },
        )
        assert "Passwords do not match" in r.text

        # -------- Phase 3: Brute force blocking --------
        user3 = "p3"
        csrf = await get_csrf(client)
        await client.post(
            "/register",
            data={
                "username": user3,
                "password": strong,
                "confirm_password": strong,
                "csrf_token": csrf,
            },
        )

        blocked = False
        for _ in range(6):
            csrf = await get_csrf(client)
            r = await client.post(
                "/login",
                data={
                    "username": user3,
                    "password": "wrong",
                    "csrf_token": csrf,
                },
            )
            if "Too many failed attempts" in r.text:
                blocked = True
                break

        assert blocked

        # -------- Phase 4: Cookie flags --------
        user4 = "p4"
        csrf = await get_csrf(client)
        await client.post(
            "/register",
            data={
                "username": user4,
                "password": strong,
                "confirm_password": strong,
                "csrf_token": csrf,
            },
        )

        csrf = await get_csrf(client)
        login_resp = await client.post(
            "/login",
            data={
                "username": user4,
                "password": strong,
                "csrf_token": csrf,
            },
            follow_redirects=False,
        )

        set_cookie = login_resp.headers.get("set-cookie", "")
        assert "HttpOnly" in set_cookie
        assert "SameSite" in set_cookie

        # -------- Phase 5: Password hashing --------
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(User).where(User.username == user4))
            u = result.scalar_one_or_none()

            assert u is not None
            assert u.hashed_password != strong
            assert u.hashed_password.startswith("$2")

        # -------- Phase 6: Trim username --------
        csrf = await get_csrf(client)
        await client.post(
            "/register",
            data={
                "username": "  spaced  ",
                "password": strong,
                "confirm_password": strong,
                "csrf_token": csrf,
            },
        )

        csrf = await get_csrf(client)
        resp = await client.post(
            "/login",
            data={
                "username": "spaced",
                "password": strong,
                "csrf_token": csrf,
            },
            follow_redirects=False,
        )

        assert resp.status_code in (302, 303)

        # -------- Phase 7: Duplicate username --------
        csrf = await get_csrf(client)
        await client.post(
            "/register",
            data={
                "username": "dup",
                "password": strong,
                "confirm_password": strong,
                "csrf_token": csrf,
            },
        )

        csrf = await get_csrf(client)
        r2 = await client.post(
            "/register",
            data={
                "username": "dup",
                "password": strong,
                "confirm_password": strong,
                "csrf_token": csrf,
            },
        )

        assert "Username already exists" in r2.text or "Username already taken" in r2.text

        # -------- Phase 8: Missing CSRF --------
        await client.post(
            "/register",
            data={
                "username": "csrf_u2",
                "password": strong,
                "confirm_password": strong,
            },
        )

        r = await client.post(
            "/login",
            data={"username": "csrf_u2", "password": strong},
        )

        assert "Invalid CSRF token" in r.text

        # -------- Phase 10 --------
        assert True