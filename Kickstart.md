# From Blank VSCode to a Working FastAPI Login App
## A Routine Guide You Can Re-Run for Any Scope

**What this document is.** A 14-step routine that takes you from an empty folder in VSCode to a working, verified, committed FastAPI login app — and teaches the *shape* of the thinking so the next time a scope lands in your lap, you already know how to face it.

**The scenario it solves.** You've been given a requirement. VSCode is open. The folder is empty. You don't know where to start. This document is the path out of that blank-page moment, designed so the method outlasts the specific app.

**How to read it.** Every step pairs three things:
- **Why at all** — the conceptual reason this step exists.
- **Why here in the sequence** — what must have happened before, what depends on it after, and what breaks if you flip the order.
- **Do** — the commands or code.
Plus a **Verify** line to close each step cleanly before moving on.

---

## The single rule behind the entire ordering

> **Every step must be verifiable in isolation before the next step adds a new failure surface.**

If two new things are added at once and one breaks, you cannot tell which. One thing at a time means every failure has exactly one suspect. **This is the rule that makes the sequence below non-negotiable.** When a future scope arrives — any scope, on any stack — you design the build order by the same rule: what can be verified in isolation, and what new failure surface does each next step add?

---

## Step 0 — Think on paper (the step that removes blank-page anxiety)

### Why at all
Design on paper is free. Design in code is expensive — every decision made while typing is hard to walk back. Step 0 separates **deciding** from **building**. Each becomes a simple act. Doing both at once *is* what paralysis actually is.

### Why here
- *Must come first.* Every later step is transcription. Transcription is mechanical; inventing-while-transcribing is paralyzing.
- *Skip it and:* you stare at VSCode, type three lines, delete them, google something, type more, delete again. That loop is not "coding" — it's "designing in the most expensive medium available." Step 0 prevents it.

### The four questions — what each produces, what skipping each costs

| Question | What it produces | What skipping it causes |
|---|---|---|
| **What does the user do?** | The user's journey end-to-end | Routes that don't connect to a real flow |
| **What gets stored?** | The data model — tables and columns | Mid-build discovery of a column you never designed |
| **What endpoints are needed?** | The full API surface — verb + URL for each | Reactively adding routes instead of knowing the set upfront |
| **What can go wrong?** | The failure modes and their responses | Happy-path-only code, patched randomly when users hit edges |

### Worked answers for THIS app — what the paper looks like when done

**Q1 — What does the user do?**
- Open `http://localhost:8000` → sees a login form.
- No account yet → click "Create an account" → fill username + password → submit → lands back on login with "account created, log in."
- Credentials typed on login → submit → see `Welcome, <name>` OR `Invalid credentials`.

**Q2 — What gets stored?**
- One table: `users`.
- Columns: `id` (int, primary key), `username` (string, unique, indexed), `hashed_password` (string, never plain).

**Q3 — What endpoints are needed?**

| Verb | URL | Input | Output |
|---|---|---|---|
| GET | `/` | — | login page (HTML) |
| GET | `/register` | — | register page (HTML) |
| POST | `/register` | `username`, `password` (form fields) | login page with success, OR register page with "already taken" |
| POST | `/login` | `username`, `password` (form fields) | login page with welcome, OR login page with "Invalid credentials" |

**Q4 — What can go wrong?**
- Register with an existing username → respond "Username already taken" (not a 500 stack trace).
- Login with an unknown username OR a wrong password → respond **"Invalid credentials"** — identical message for both, so an attacker cannot tell which one was wrong.
- Empty fields → HTML `required` attribute + server-side form validation.

### You are done thinking when

Not when the page is full. Done thinking means:
- You can close your eyes and describe every page the user sees, in order.
- You can name every endpoint without looking.
- You can state what each column in `users` holds.
- You can state the response for each failure case.

If any come out fuzzy, you're not done — go back before opening the editor.

### How to use the paper during the build (the part most people miss)

Keep the paper beside the laptop for Steps 1–13. At every step, ask:

> **"Which answer from Step 0 am I implementing right now?"**

Every line of code should map back to one of the four answers. Concretely, for this app:
- **Step 8 (data layer)** implements **Q2**.
- **Step 9 (real routes)** implements **Q3** and most of **Q4**.
- **Step 10 (register page + link)** implements **Q1**.
- **Step 11 (verification)** is reading **Q1 and Q4** back out of the running app.

If a line of code doesn't map to a Step 0 answer, one of two things is true: the paper was incomplete (update it) or the code is extra weight (delete it). Both outcomes are healthier than leaving it ambiguous.

### The single sentence to remember

> Step 0 turns *"I don't know what to do"* into *"I already decided what to do — I just need to type it."*

That is the anxiety cure. Everything in Steps 1–13 is the typing.

---

## Step 1 — Make a home (folder + open in VSCode)

### Why at all
Every tool you'll use (`venv`, `pip`, `uvicorn`, `git`) runs relative to *some* folder. The folder is the root of everything.

### Why here
- *Must come after:* Step 0 — you should know what you're building before naming a home for it. Calling the folder `fastapi-login-app` is a tiny act of commitment to the decision.
- *Must come before:* the venv (it lives inside this folder) and VSCode opening (VSCode opens a folder, not air).
- *Skip or flip and:* commands run with no consistent working directory. Files scatter. `git init` lands in the wrong place.

### Do
```bash
mkdir fastapi-login-app
cd fastapi-login-app
code .
```

### Verify
VSCode opens with an empty file tree.

---

## Step 2 — Create and activate the virtual environment

### Why at all
Isolate this project's libraries from your laptop's other Python projects. One project may need FastAPI 0.100; another may need 0.110. A venv keeps them from colliding.

### Why here
- *Must come after:* the folder exists — venv has to live somewhere.
- *Must come before:* `pip install`. Pip installs into **whichever Python is currently active**. Without an activated venv, FastAPI lands in your system Python permanently, and the next project will collide with this one.
- *Skip or flip and:* your `requirements.txt` says "FastAPI" but nobody can tell which FastAPI is actually installed, because it lives in a shared Python.

### Do
```bash
python -m venv venv
# Windows PowerShell:
.\venv\Scripts\Activate.ps1
# Windows CMD:
venv\Scripts\activate.bat
# macOS/Linux:
source venv/bin/activate
```

### Verify
The prompt now begins with `(venv)`. If not, installs will land in the wrong place.

---

## Step 3 — Choose and install libraries (one problem per library)

### Why at all
Each library answers one specific problem. Know the problem first, then pick the library — never install blindly.

### Why here
- *Must come after:* venv is **active**. Otherwise installs go to the wrong Python.
- *Must come before:* any code that imports these libraries. Writing `from fastapi import FastAPI` before installing it guarantees an `ImportError` on the first run.
- *Skip or flip and:* you write the whole app, try to run it, get import errors, and the fix is to come back here anyway. Doing it first saves the round trip.

### The mapping for this app

| Problem | Library |
|---|---|
| Build HTTP endpoints | `fastapi` |
| Run the HTTP server | `uvicorn[standard]` |
| Render HTML pages with dynamic data | `jinja2` |
| Read data submitted by HTML forms | `python-multipart` |
| Talk to the DB as Python objects, not raw SQL | `sqlalchemy` |
| Hash passwords safely | `passlib[bcrypt]` |
| Pin a bcrypt version `passlib` agrees with | `bcrypt==4.0.1` |

### Do
Create `requirements.txt`:
```
fastapi
uvicorn[standard]
jinja2
python-multipart
sqlalchemy
passlib[bcrypt]
bcrypt==4.0.1
```
Then:
```bash
pip install -r requirements.txt
```

### Verify
`pip list` shows all seven. No red errors.

---

## Step 4 — The smallest possible FastAPI app ("hello" route)

### Why at all
Prove the pipeline works end-to-end with the fewest moving parts — one route, one response. This is your baseline.

### Why here
- *Must come after:* libraries are installed (Step 3).
- *Must come before:* any feature. **If this minimal app cannot serve a browser request, every later step will also fail — but you won't know why.** Was it the template? The DB? The port? Impossible to tell.
- *The deeper point:* every later step is judged against "did this used to work? does it still work?" Without a known-good baseline, "broken" has no meaning.

### Do
Create `main.py`:
```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def hello():
    return {"message": "hello"}
```
Run:
```bash
uvicorn main:app --reload
```

### Verify
Open `http://localhost:8000`, see `{"message":"hello"}`. **Do not move on if this fails.** The problem is here, and it compounds downstream.

---

## Step 5 — Render HTML instead of JSON

### Why at all
The user needs a form. Browsers render HTML, not JSON. Jinja is the templating engine that lets Python hand HTML to the browser with dynamic values injected.

**A decision you are making now:** server-rendered HTML via Jinja, *not* a separate React app. Server-rendered is simpler for one person learning alone — no CORS, no second build tool, no second port. Pick the simpler option when learning.

### Why here
- *Must come after:* the hello route works (Step 4). Any Jinja failure is now isolated to templating — FastAPI itself is already known-good.
- *Must come before:* form submission (Step 6). A form needs a page to live on. No page = nothing to submit.
- *The lesson:* change exactly one thing between verification points. You're adding Jinja now. If something breaks, Jinja is the only new variable.

### Do
Create `templates/login.html`:
```html
<!DOCTYPE html>
<html>
<head><title>Login</title></head>
<body>
  <h2>Login Page</h2>
  <form method="post" action="/login">
    <label>Username:</label>
    <input type="text" name="username" required><br><br>
    <label>Password:</label>
    <input type="password" name="password" required><br><br>
    <button type="submit">Login</button>
  </form>
  {% if message %}<h3>{{ message }}</h3>{% endif %}
  <p><a href="/register">Create an account</a></p>
</body>
</html>
```
Rewrite `main.py`:
```python
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates

app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get("/")
def login_page(request: Request):
    return templates.TemplateResponse(request=request, name="login.html", context={})
```

### Verify
Browser shows a real login form, not JSON. The "Create an account" link is visible (it will 404 for now — that's expected; Step 10 fixes it).

---

## Step 6 — Walking-stone login (hardcoded, disposable)

### Why at all
Prove the form's POST round-trips through the server. A hardcoded `admin`/`1234` check is a **walking stone** — you step on it once, then delete it. Naming it a walking stone is deliberate: it reminds you this version is temporary.

### Why here
- *Must come after:* the HTML form exists (Step 5). A form that doesn't exist can't submit.
- *Must come before:* the data layer. **This is the critical sequencing insight.** If you add the DB and the POST route at the same time and something breaks, you cannot tell whether it's the DB or the POST wiring. By getting POST working against a fake check *first*, you prove the HTTP half in isolation. When you swap in the DB later (Step 9), any new failure is unambiguously a DB failure.
- *Skip or flip and:* you're debugging two new layers at once, losing hours to "is this the form, the route, the model, or the hash?"

### Do
Append to `main.py`:
```python
from fastapi import Form

@app.post("/login")
def handle_login(request: Request, username: str = Form(...), password: str = Form(...)):
    msg = "Login successful" if (username == "admin" and password == "1234") else "Invalid credentials"
    return templates.TemplateResponse(
        request=request, name="login.html", context={"message": msg}
    )
```

### Verify
Submit `admin`/`1234` → "Login successful." Wrong values → "Invalid credentials."

**Flag this in your head: NOT DONE.** Committing here would ship a fake. Step 9 replaces it.

---

## Step 7 — Design the data layer on paper

### Why at all
Data shape decisions made in code are expensive to reverse. Make them on paper first. This looks like a step that does nothing; it prevents the most common junior mistake — writing code that expresses a shape the author hadn't actually decided on.

### Why here
- *Must come after:* the walking-stone login works (Step 6). The HTTP half is known-good; only data remains.
- *Must come before:* any data code. Writing data code *forces* decisions (table names, column types, constraints) — make them deliberately now or stumble into them later.

### Do
Answer three questions in writing. Your Step 0 paper already has Q2; revisit and refine:

1. **Where does the data live?** → a SQLite file (`users.db`). Single-file, no server to install. Production would use Postgres — not today.
2. **What's the table shape?** → `users`: `id` (int PK), `username` (string, unique, indexed), `hashed_password` (string).
3. **How does Python talk to it?** → SQLAlchemy ORM — declare a Python class, it maps to the table.

### Verify
Close your eyes and recite the three answers. If you can, move on.

---

## Step 8 — Build the data layer (engine, session factory, model, hasher)

### Why at all
Turn the paper design into the four pieces every Python backend uses:
- an **engine** (DB connection handle, process-wide),
- a **session factory** (produces per-request sessions),
- a **model** (Python class ↔ SQL table), and
- a **hasher** (bcrypt for passwords).

### Why here
- *Must come after:* the paper design (Step 7). Otherwise you invent shape while typing it.
- *Must come before:* Step 9 (real login). Step 9 imports the `User` model, calls `get_db`, and uses `pwd_context`. None of those exist until this step.
- *Skip or flip and:* Step 9 becomes a red-squiggle fest — every symbol it references is undefined.

### Do
Extend `main.py`:
```python
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from passlib.context import CryptContext
from fastapi import Depends

engine = create_engine(
    "sqlite:///./users.db",
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)

Base.metadata.create_all(bind=engine)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**Why `get_db` uses `yield`:** it hands a fresh session to each request, and the `finally` block closes it even if the route raises. The session always closes. Never skip this pattern.

### Verify
Restart uvicorn. A file `users.db` appears in the project folder. No errors. **Do not touch routes in this step.** Verify the data layer stands alone — server boots, file exists, nothing uses it yet. That is the baseline before Step 9 changes anything.

---

## Step 9 — Replace the walking stone; add real `/register` and `/login`

### Why at all
The data layer exists but is unused. Wire it to the routes. Kill the hardcode.

### Why here
- *Must come after:* Step 8 (data layer) AND Step 6 (walking stone). You need both — pieces to call, and a working POST route to replace.
- *Must come before:* Step 10 (register UI). **The route must exist before a form can target it.** Otherwise submissions 404 and the error misleadingly looks like a form problem.
- *You might be tempted to* build `/register`'s route and page at the same time. Don't — a form that posts to a broken route gives a confusing error where the cause could be either side. **Backend route first, UI second** keeps the failure surface honest.
- *Skip the walking-stone deletion and:* the hardcode and the real check coexist. Depending on how the `if` is written, the hardcode can silently win — your "real" login becomes decorative.

### Do
```python
from sqlalchemy.exc import IntegrityError

@app.post("/register")
def handle_register(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    new_user = User(username=username, hashed_password=pwd_context.hash(password))
    db.add(new_user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return templates.TemplateResponse(
            request=request, name="register.html",
            context={"message": "Username already taken"},
        )
    return templates.TemplateResponse(
        request=request, name="login.html",
        context={"message": f"User '{username}' created — log in below."},
    )

@app.post("/login")
def handle_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.username == username).first()
    if not user or not pwd_context.verify(password, user.hashed_password):
        return templates.TemplateResponse(
            request=request, name="login.html",
            context={"message": "Invalid credentials"},
        )
    return templates.TemplateResponse(
        request=request, name="login.html",
        context={"message": f"Welcome, {user.username}!"},
    )
```

**Delete** the Step 6 version of `handle_login` entirely. Only one `@app.post("/login")` should remain.

**Why identical messages for wrong-password and user-not-found:** different messages let an attacker enumerate which usernames exist by trial. Same response for both failures.

### Verify
Hit `/register` via Swagger (`http://localhost:8000/docs`) or curl. Confirm a row appears in `users.db`. Then hit `/login` with those credentials. Confirm success. No browser UI yet — that's Step 10.

---

## Step 10 — Add the register page and the link

### Why at all
`POST /register` exists but no browser form drives it yet.

### Why here
- *Must come after:* Step 9 — the route must exist before the form pointing at it.
- *Must come before:* Step 11 (end-to-end test). You can't walk through the user journey without a register page to walk onto.
- *Flip it (UI before route) and:* the form posts to a 404, which looks like a form bug but isn't.

### Do
Create `templates/register.html`:
```html
<!DOCTYPE html>
<html>
<head><title>Register</title></head>
<body>
  <h2>Register</h2>
  <form method="post" action="/register">
    <label>Username:</label>
    <input type="text" name="username" required><br><br>
    <label>Password:</label>
    <input type="password" name="password" required><br><br>
    <button type="submit">Create account</button>
  </form>
  {% if message %}<h3>{{ message }}</h3>{% endif %}
  <p><a href="/">Back to login</a></p>
</body>
</html>
```
Add the GET route to `main.py`:
```python
@app.get("/register")
def register_page(request: Request):
    return templates.TemplateResponse(request=request, name="register.html", context={})
```
The link on `login.html` (`<a href="/register">Create an account</a>` from Step 5) is already in place.

### Verify
Clicking "Create an account" on the login page leads to a working register form.

---

## Step 11 — Verify end-to-end, including failure paths

### Why at all
Typing isn't the finish line. Using the app as a real user is.

### Why here
- *Must come after:* everything. Full-stack verification depends on all prior steps being correct.
- *Must come before:* commit. **Committing unverified code makes the savepoint "code that compiles" — not "code that works."**
- *The one check that matters most:* delete `users.db`, restart, try to log in. Without this, you cannot distinguish "login works because the DB works" from "login works because a hardcode slipped in." This single check is what proves the walking stone (Step 6) is truly gone.

### Do — run all five, in order

1. Register `test` / `secret123` → lands on login with a success message.
2. Log in with `test` / `secret123` → `Welcome, test!`.
3. Log in with `test` / `wrong` → `Invalid credentials`.
4. Register `test` again → `Username already taken`.
5. Stop uvicorn. Delete `users.db`. Restart uvicorn. Log in with `test` / `secret123` → `Invalid credentials`.

### Verify
All five must match. **If step 5 shows `Welcome, test!`, STOP — a hardcode is hiding somewhere.** That is the only possible explanation once the DB is gone.

---

## Step 12 — Commit

### Why at all
Git is a savepoint. A reference point to return to or build from.

### Why here
- *Must come after:* verification (Step 11). A commit is only as valuable as the state it preserves. Committing untested code poisons the savepoint.
- *Must come before:* Step 13 (close). If you close terminals, shut the laptop, and tomorrow git misbehaves, today's work is ambiguous. A commit is certainty; uncommitted work is not.
- *Sub-order inside this step:* `.gitignore` BEFORE `git add`. If you stage before ignoring, `__pycache__/`, `users.db`, and `venv/` end up committed. Removing them after is possible but messy — prevention is a one-liner.

### Do
```bash
# Windows Git Bash / macOS / Linux:
cat > .gitignore << 'EOF'
__pycache__/
*.db
venv/
.venv/
EOF

git init
git add .gitignore requirements.txt main.py templates/
git commit -m "Basic FastAPI login app with register and login"
```

### Verify
`git status` clean. `git log` shows one commit. Nothing unexpected staged.

---

## Step 13 — Close clean

### Why at all
A server that wasn't stopped cleanly can keep holding its port. Tomorrow morning, uvicorn fails with "port 8000 already in use."

### Why here
- *Must come after:* commit. Any issue during shutdown is now irrelevant — the work is preserved.
- *Must come last:* anything after this belongs to tomorrow's session.

### Do
`Ctrl + C` in the uvicorn terminal. Close VSCode.

### Verify
Prompt returns in the terminal. Port 8000 is free.

---

## The meta-pattern — reuse this for any scope

Every adjacent pair of steps above follows the same contract:

```
[Step N]   produces a verified, isolated thing.
[Step N+1] adds exactly one new thing on top of it.
```

That is why:
- **Walking stone (6)** precedes **database (8)** → POST wiring is verified before DB is introduced.
- **Data design on paper (7)** precedes **data code (8)** → shape is decided before it's encoded.
- **Route (9)** precedes **page (10)** → a stable target exists before a form points at it.
- **Verification (11)** precedes **commit (12)** → the savepoint preserves a working state.

When a future scope arrives — password reset, user dashboard, file upload, anything — design the build order by the same rule: *what can be verified in isolation, and what new failure surface does each next step add?* Answer that, and the step order writes itself.

### The 14 slots, in order, for any feature or app

```
 0. Think on paper       — inputs, outputs, data, endpoints, failures
 1. Home                 — folder + editor
 2. Isolate              — venv
 3. Libraries            — one per problem, pinned
 4. Smallest app         — prove the pipeline
 5. Render               — UI surface
 6. Walking stone        — fake logic proves wiring, then dies
 7. Design data          — on paper
 8. Build data           — engine, session, model, hasher
 9. Real logic           — replace the walking stone
10. Connect the UI       — pages + links
11. Verify end-to-end    — real user actions, including failures
12. Commit               — savepoint with .gitignore
13. Close clean          — stop servers
```

Tomorrow's feature walks the same slots. Most will already be done; only the new ones need work. That is how blank-page anxiety becomes a checklist.

---

## End-of-session self-check

Before declaring the day done, answer these from memory:

1. State the one rule behind the ordering in a single sentence.
2. Name the four questions from Step 0.
3. Pick any step 1–13. State why it comes after the previous one and before the next one.
4. Which step proves the DB is actually being used, and not a hidden hardcode? What does it test?
5. Why must `.gitignore` exist before `git add`?
6. Why does `get_db` use `yield` instead of `return`?
7. What is the one sentence that turns *"I don't know what to do"* into *"I already decided what to do — I just need to type it."*?

Fluent answers mean you own the structure. Fuzzy answers mean revisit that step before the next session.
