from fastapi import FastAPI, Depends, HTTPException, status, Request, Form
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import app.models as models
from app.models import SessionLocal, engine
import os
from app.routers import auth, api

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
    # This will be protected later
    return templates.TemplateResponse(request, "dashboard.html")

@app.get("/admin")
async def admin_panel(request: Request):
    # This will be protected later
    return templates.TemplateResponse(request, "admin.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
