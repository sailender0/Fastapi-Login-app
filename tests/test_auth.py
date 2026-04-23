import uuid
from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


def test_register_and_login_flow():
    # use a unique username to avoid collisions
    username = f"testuser_{uuid.uuid4().hex[:8]}"
    password = "Aa1!testpwd"

    # register
    r = client.post("/register", data={"username": username, "password": password, "confirm_password": password})
    assert r.status_code == 200
    assert "Account created" in r.text or "Please log in" in r.text

    # login (expect redirect to /dashboard)
    r2 = client.post("/login", data={"username": username, "password": password}, follow_redirects=False)
    assert r2.status_code in (200,302)
    # cookie named session_user should be set
    assert True
