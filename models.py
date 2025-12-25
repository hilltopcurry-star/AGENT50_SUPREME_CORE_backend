from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
import uuid

# --- DATABASE TOOL ---
db = SQLAlchemy()

# Helper to generate UUID string
def generate_uuid():
    return str(uuid.uuid4())

# --- USER MODEL (Corrected) ---
class User(db.Model):
    __tablename__ = "users"
    
    id = db.Column(db.String, primary_key=True, default=generate_uuid)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20))
    role = db.Column(db.String(50), nullable=False) # 'customer', 'driver', 'owner'
    
    # ✅ FIX: Maine yahan se 'restaurant_id' hata diya hai (Confusion khatam)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())

    # Relationship: User ke paas Restaurant ho sakta hai
    # 'uselist=False' ka matlab ek banda ek hi restaurant ka owner hoga (Filhal ke liye)
    restaurant_owned = db.relationship("Restaurant", back_populates="owner", uselist=False)

# --- RESTAURANT MODEL ---
class Restaurant(db.Model):
    __tablename__ = "restaurants"
    
    id = db.Column(db.String, primary_key=True, default=generate_uuid)
    # Restaurant ko pata hai uska malik kaun hai (Ye sahi hai)
    owner_id = db.Column(db.String, db.ForeignKey("users.id"), nullable=False)
    
    name = db.Column(db.String(255), nullable=False)
    address = db.Column(db.Text, nullable=False)
    city = db.Column(db.String(100), nullable=False)
    cuisine_type = db.Column(db.String(100))
    
    operating_hours = db.Column(db.JSON, default={})
    is_active = db.Column(db.Boolean, default=True)
    is_approved = db.Column(db.Boolean, default=False)
    
    # Relationships
    owner = db.relationship("User", back_populates="restaurant_owned")
    menu_items = db.relationship("MenuItem", back_populates="restaurant")
    orders = db.relationship("Order", back_populates="restaurant")

# --- MENU ITEM MODEL ---
class MenuItem(db.Model):
    __tablename__ = "menu_items"
    
    id = db.Column(db.String, primary_key=True, default=generate_uuid)
    restaurant_id = db.Column(db.String, db.ForeignKey("restaurants.id"), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    price = db.Column(db.Float, nullable=False)
    is_available = db.Column(db.Boolean, default=True)
    
    restaurant = db.relationship("Restaurant", back_populates="menu_items")

# --- ORDER MODEL ---
class Order(db.Model):
    __tablename__ = "orders"
    
    id = db.Column(db.String, primary_key=True, default=generate_uuid)
    customer_id = db.Column(db.String, db.ForeignKey("users.id"), nullable=False)
    restaurant_id = db.Column(db.String, db.ForeignKey("restaurants.id"), nullable=False)
    status = db.Column(db.String(50), default="pending")
    total_amount = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    
    restaurant = db.relationship("Restaurant", back_populates="orders")