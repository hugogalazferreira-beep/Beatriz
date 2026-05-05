from app.models import SessionLocal, User, Product, init_db
from app.auth import get_password_hash

def seed_data():
    init_db()
    db = SessionLocal()

    # Create Admin
    admin = db.query(User).filter(User.username == "admin").first()
    if not admin:
        admin = User(
            username="admin",
            email="admin@portaldoconsultor.online",
            hashed_password=get_password_hash("portaladmin2026"),
            full_name="Administrador do Portal",
            is_admin=True
        )
        db.add(admin)

    # Create Demo Consultant
    consultant = db.query(User).filter(User.username == "ana.silva").first()
    if not consultant:
        consultant = User(
            username="ana.silva",
            email="ana.silva@email.com",
            hashed_password=get_password_hash("consultor2026"),
            full_name="Ana Silva",
            is_admin=False
        )
        db.add(consultant)

    # Add some products
    if db.query(Product).count() == 0:
        products = [
            Product(category="Telecom", brand="NOS", name="Fibra 1Gbps", commission_type="Fixed", commission_value=50.0),
            Product(category="Telecom", brand="MEO", name="M3O", commission_type="Fixed", commission_value=45.0),
            Product(category="Energia", brand="EDP", name="Dual Comercial", commission_type="Fixed", commission_value=30.0),
            Product(category="Energia", brand="Endesa", name="Tarifa Aniversário", commission_type="Fixed", commission_value=25.0),
        ]
        db.bulk_save_objects(products)

    db.commit()
    db.close()

if __name__ == "__main__":
    seed_data()
