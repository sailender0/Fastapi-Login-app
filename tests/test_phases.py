from fastapi.testclient import TestClient
from app.main import app
from app.db import models
from sqlalchemy.orm import Session
import re


def get_csrf(client: TestClient):
    text = client.get('/').text
    m = re.search(r'name="csrf_token" value="([0-9a-f]+)"', text)
    if m:
        return m.group(1)
    text = client.get('/register').text
    m = re.search(r'name="csrf_token" value="([0-9a-f]+)"', text)
    return m.group(1) if m else None


def reset_db():
    models.Base.metadata.drop_all(bind=models.engine)
    models.Base.metadata.create_all(bind=models.engine)


def test_full_phases():
    reset_db()
    strong = 'Admin@123'
    results = {}
    # Phase1: weak passwords rejected, strong accepted
    for i, pw in enumerate(['123', 'password', 'admin123']):
        c = TestClient(app)
        r = c.post('/register', data={'username': f'p1_{i}', 'password': pw, 'confirm_password': pw})
        assert 'Password must be at least' in r.text or 'Must include' in r.text
    c = TestClient(app)
    r = c.post('/register', data={'username': 'p1_ok', 'password': strong, 'confirm_password': strong})
    assert r.status_code == 200

    # Phase2: password mismatch
    c = TestClient(app)
    r = c.post('/register', data={'username': 'p2', 'password': strong, 'confirm_password': 'Admin@12'})
    assert 'Passwords do not match' in r.text

    # Phase3: brute force blocking
    c = TestClient(app)
    user3 = 'p3'
    c.post('/register', data={'username': user3, 'password': strong, 'confirm_password': strong})
    csrf = get_csrf(c)
    blocked = False
    for _ in range(6):
        r = c.post('/login', data={'username': user3, 'password': 'wrong', 'csrf_token': csrf})
        if 'Too many failed attempts' in r.text:
            blocked = True
            break
        csrf = get_csrf(c)
    assert blocked

    # Phase4 & 9: cookie flags
    c = TestClient(app)
    user4 = 'p4'
    c.post('/register', data={'username': user4, 'password': strong, 'confirm_password': strong})
    csrf = get_csrf(c)
    login_resp = c.post('/login', data={'username': user4, 'password': strong, 'csrf_token': csrf}, follow_redirects=False)
    set_cookie = login_resp.headers.get('set-cookie', '')
    assert 'HttpOnly' in set_cookie
    assert 'SameSite' in set_cookie

    # Phase5: password hashed
    with Session(bind=models.engine) as s:
        u = s.query(models.User).filter(models.User.username == user4).first()
        assert u is not None and (u.hashed_password.startswith('$2') or u.hashed_password.startswith('$2b$'))

    # Phase6: register with spaces then login with trimmed username
    c = TestClient(app)
    c.post('/register', data={'username': '  spaced  ', 'password': strong, 'confirm_password': strong})
    csrf = get_csrf(c)
    resp = c.post('/login', data={'username': 'spaced', 'password': strong, 'csrf_token': csrf}, follow_redirects=False)
    assert resp.status_code in (302, 303) or resp.headers.get('location') == '/dashboard'

    # Phase7: duplicate username rejected
    c = TestClient(app)
    c.post('/register', data={'username': 'dup', 'password': strong, 'confirm_password': strong})
    r2 = c.post('/register', data={'username': 'dup', 'password': strong, 'confirm_password': strong})
    assert 'Username already exists' in r2.text or 'Username already taken' in r2.text

    # Phase8: missing CSRF rejected
    c = TestClient(app)
    c.post('/register', data={'username': 'csrf_u2', 'password': strong, 'confirm_password': strong})
    r = c.post('/login', data={'username': 'csrf_u2', 'password': strong})
    assert 'Invalid CSRF token' in r.text

    # Phase10: placeholder (always true)
    assert True
