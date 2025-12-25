from server import app, db, User
from werkzeug.security import generate_password_hash

with app.app_context():
    print("\n🕵️‍♂️ DIAGNOSING DATABASE...")

    # 1. Check Existing Users
    users = User.query.all()
    print(f"👥 Total Users Found: {len(users)}")
    for u in users:
        print(f" - Found: {u.email} (Role: {u.role})")

    # 2. Fix Admin
    print("\n🛠️ FIXING ADMIN ACCOUNT...")
    admin = User.query.filter_by(email='admin@agent50.com').first()
    
    if admin:
        print("⚡ Old Admin found. Deleting to recreate fresh...")
        db.session.delete(admin)
        db.session.commit()
    
    # Create Fresh
    hashed_pw = generate_password_hash("admin123")
    new_admin = User(id="admin_1", email="admin@agent50.com", password=hashed_pw, role="super_admin")
    db.session.add(new_admin)
    db.session.commit()
    
    print("\n✅ SUCCESS! NEW ADMIN CREATED.")
    print("👉 Email: admin@agent50.com")
    print("👉 Pass:  admin123")
    print("---------------------------------\n")