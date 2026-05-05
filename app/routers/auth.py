from fastapi import APIRouter, Depends, HTTPException, status, Form, Response, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.models import SessionLocal, User, Product
import app.auth as auth_lib
from datetime import timedelta
import app.auth as auth_lib

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/login")
async def login(
    response: Response,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == username).first()
    if not user or not auth_lib.verify_password(password, user.hashed_password):
        return RedirectResponse(url="/login?error=1", status_code=status.HTTP_303_SEE_OTHER)

    access_token = auth_lib.create_access_token(data={"sub": user.username})

    # Em produção usaríamos cookies seguros
    response = RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True)
    return response

@router.get("/logout")
async def logout(response: Response):
    response = RedirectResponse(url="/")
    response.delete_cookie("access_token")
    return response
