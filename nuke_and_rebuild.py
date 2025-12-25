from server import app, db, User, Restaurant
from werkzeug.security import generate_password_hash
import time

# THIS SCRIPT DESTROYS AND REBUILDS THE DATABASE SCHEMA
# TO MATCH THE NEW EMAIL-BASED CODE EXACTLY.

with app.app_context():
    print("⚠️  WARNING: INITIATING NUCLEAR RESET...")
    print("    Target: Live Neon Database")
    
    # 1. DROP EVERYTHING (Force deletion of old mismatched tables)
    print("💥 Dropping all existing tables (users, orders, etc)...")
    db.drop_all()
    print("✔  Tables Dropped.")

    # 2. CREATE EVERYTHING (Builds new tables with 'email' column)
    print("🏗️  Creating new tables from current Code...")
    db.create_all()
    print("✔  Tables Created.")

    # 3. CREATE ADMIN (The Email Version)
    print("👤 Creating Admin User...")
    hashed_pw = generate_password_hash("admin123")
    new_admin = User(
        id="admin_1", 
        email="admin@agent50.com",  # ✅ Explicitly setting EMAIL
        password=hashed_pw, 
        role="super_admin"
    )
    db.session.add(new_admin)

    # 4. SEED RESTAURANTS (So the app isn't empty)
    print("🍔 Seeding Restaurants...")
    menu1 = [{"category": "Biryani Special 🍛", "items": [{"name": "Chicken Biryani", "price": 250}]}]
    menu2 = [{"category": "Burgers 🍔", "items": [{"name": "Zinger Burger", "price": 350}]}]
    
    db.session.add(Restaurant(id="res_1", name="Biryani House", menu=menu1, email="biryani@test.com"))
    db.session.add(Restaurant(id="res_2", name="Burger King", menu=menu2, email="burger@test.com"))

    # 5. COMMIT
    db.session.commit()
    
    print("\n✅ MISSION COMPLETE: SCHEMA IS NOW SYNCED.")
    print("👉 Login Email: admin@agent50.com")
    print("👉 Password:   admin123")