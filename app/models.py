from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

SQLALCHEMY_DATABASE_URL = "sqlite:///./portal.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    sales = relationship("Sale", back_populates="consultant")
    redemptions = relationship("Redemption", back_populates="consultant")
    tickets = relationship("Ticket", back_populates="user")

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    category = Column(String)  # Telecom, Energia
    brand = Column(String)     # NOS, MEO, EDP, etc.
    name = Column(String)
    description = Column(Text)
    commission_type = Column(String)  # Fixed, Percentage
    commission_value = Column(Float)
    is_active = Column(Boolean, default=True)

    sales = relationship("Sale", back_populates="product")

class Sale(Base):
    __tablename__ = "sales"
    id = Column(Integer, primary_key=True, index=True)
    consultant_id = Column(Integer, ForeignKey("users.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    client_name = Column(String)
    client_nif = Column(String)
    status = Column(String, default="Pending") # Pending, Validated, Rejected, Paid
    commission_earned = Column(Float)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    consultant = relationship("User", back_populates="sales")
    product = relationship("Product", back_populates="sales")

class Redemption(Base):
    __tablename__ = "redemptions"
    id = Column(Integer, primary_key=True, index=True)
    consultant_id = Column(Integer, ForeignKey("users.id"))
    amount = Column(Float)
    status = Column(String, default="Requested") # Requested, Approved, Paid, Rejected
    request_date = Column(DateTime, default=datetime.utcnow)
    payment_date = Column(DateTime, nullable=True)
    notes = Column(Text)

    consultant = relationship("User", back_populates="redemptions")

class Ticket(Base):
    __tablename__ = "tickets"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    subject = Column(String)
    message = Column(Text)
    status = Column(String, default="Open") # Open, Answered, Closed
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="tickets")

def init_db():
    Base.metadata.create_all(bind=engine)
