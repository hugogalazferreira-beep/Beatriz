from fastapi import FastAPI, Depends, HTTPException, status, Request, Form
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import app.models as models
from app.models import SessionLocal, engine
import os
from app.routers import auth, api
from app.auth import get_current_user_from_cookie
from fastapi.responses import RedirectResponse

models.init_db()

app = FastAPI(title="Portal do Consultor")

# Include routers
app.include_router(auth.router)
app.include_router(api.router)

# Static files and Templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse(request, "index.html")

@app.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html")

@app.get("/dashboard")
async def dashboard(request: Request):
    user = get_current_user_from_cookie(request)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(request, "dashboard.html", {"user": user})

@app.get("/admin")
async def admin_panel(request: Request):
    user = get_current_user_from_cookie(request)
    if not user or not user.is_admin:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(request, "admin.html", {"user": user})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
