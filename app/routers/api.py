from fastapi import APIRouter, Depends, HTTPException, status, Request, Form
from sqlalchemy.orm import Session
from app.models import SessionLocal, User, Sale, Product, Redemption, Ticket
from jose import jwt, JWTError
import app.auth as auth_lib

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_current_user(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token:
        return None
    try:
        scheme, token = token.split()
        payload = jwt.decode(token, auth_lib.SECRET_KEY, algorithms=[auth_lib.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
    except (JWTError, ValueError):
        return None

    user = db.query(User).filter(User.username == username).first()
    return user

@router.get("/api/dashboard-stats")
async def get_stats(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not user:
        raise HTTPException(status_code=401)

    sales = db.query(Sale).filter(Sale.consultant_id == user.id).all()
    total_earned = sum(s.commission_earned for s in sales if s.status in ["Validated", "Paid"])
    pending_commission = sum(s.commission_earned for s in sales if s.status == "Pending")

    return {
        "total_earned": total_earned,
        "pending_commission": pending_commission,
        "sales_count": len(sales)
    }

@router.get("/api/products")
async def get_products(db: Session = Depends(get_db)):
    return db.query(Product).filter(Product.is_active == True).all()

@router.post("/api/sales")
async def create_sale(
    product_id: int = Form(...),
    client_name: str = Form(...),
    client_nif: str = Form(...),
    notes: str = Form(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not user:
        raise HTTPException(status_code=401)

    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    new_sale = Sale(
        consultant_id=user.id,
        product_id=product.id,
        client_name=client_name,
        client_nif=client_nif,
        commission_earned=product.commission_value, # Lógica base
        status="Pending",
        notes=notes
    )

    db.add(new_sale)
    db.commit()
    return {"message": "Venda registada com sucesso", "sale_id": new_sale.id}

@router.get("/api/notifications")
async def get_notifications(user: User = Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401)
    # Simulação de notificações
    return [
        {"id": 1, "title": "Bem-vindo!", "message": "O seu portal está pronto a usar.", "date": "Há 1h"},
        {"id": 2, "title": "Nova Campanha", "message": "EDP com comissões a dobrar este fim de semana.", "date": "Há 3h"}
    ]

@router.get("/api/admin/consultants")
async def get_consultants(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not user or not user.is_admin:
        raise HTTPException(status_code=403, detail="Acesso negado")

    consultants = db.query(User).filter(User.is_admin == False).all()
    result = []
    for c in consultants:
        sales = db.query(Sale).filter(Sale.consultant_id == c.id).all()
        total_earned = sum(s.commission_earned for s in sales if s.status in ["Validated", "Paid"])
        result.append({
            "id": c.id,
            "full_name": c.full_name,
            "username": c.username,
            "sales_count": len(sales),
            "total_earned": total_earned,
            "status": "Ativo" # Placeholder
        })
    return result

@router.delete("/api/admin/consultants/{consultant_id}")
async def delete_consultant(consultant_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not user or not user.is_admin:
        raise HTTPException(status_code=403, detail="Acesso negado")

    target = db.query(User).filter(User.id == consultant_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Consultor não encontrado")

    db.delete(target)
    db.commit()
    return {"message": "Consultor removido"}

@router.get("/api/my-sales")
async def get_my_sales(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not user:
        raise HTTPException(status_code=401)

    sales = db.query(Sale).filter(Sale.consultant_id == user.id).order_by(Sale.created_at.desc()).limit(10).all()
    result = []
    for s in sales:
        product = db.query(Product).filter(Product.id == s.product_id).first()
        result.append({
            "id": s.id,
            "product_name": product.name if product else "Desconhecido",
            "client_name": s.client_name,
            "commission": s.commission_earned,
            "status": s.status,
            "date": s.created_at.strftime("%d/%m/%Y")
        })
    return result
