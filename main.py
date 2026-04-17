from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates


app = FastAPI()

templates = Jinja2Templates(directory="templates")

@app.get("/")
def login_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={}
    )




@app.post("/login")
def handle_login(request: Request, username: str = Form(...), password: str = Form(...)):

    if username == "admin" and password == "1234":
       return templates.TemplateResponse(
    request=request,
    name="login.html",
    context={"message": "Login successful"}
)

    return templates.TemplateResponse(
    request=request,
    name="login.html",
    context={"message": "Invalid credentials"}
)