Manual and automated test notes

Quick manual curl examples used during verification:

1) Register (form):

curl -i -X POST -d "username=manualuser&password=Aa1!testpwd&confirm_password=Aa1!testpwd" http://127.0.0.1:8000/register

Expected: HTML page with "Account created" message (or redirect to login view)

2) Login (form):

curl -i -X POST -d "username=manualuser&password=Aa1!testpwd" http://127.0.0.1:8000/login

Expected: 302 redirect to /dashboard and a `session_user` cookie set in the response headers.

Automated tests:

- Run: `pytest -q`
- The suite contains `tests/test_auth.py` which registers a unique user and asserts registration and login behavior.
