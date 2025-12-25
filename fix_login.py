from server import app, db, User
from werkzeug.security import generate_password_hash

with app.app_context():
    print("🔍 Checking Database...")
    
    # Check for Admin by EMAIL
    admin = User.query.filter_by(email='admin@agent50.com').first()
    
    if admin:
        print("⚡ Admin already exists, resetting password...")
        admin.password = generate_password_hash("admin123")
        db.session.commit()
    else:
        print("🌱 Creating New Admin with Email...")
        new_admin = User(id="admin_1", email="admin@agent50.com", password=generate_password_hash("admin123"), role="super_admin")
        db.session.add(new_admin)
        db.session.commit()
        
    print("✅ SUCCESS! Use this login:")
    print("👉 Email: admin@agent50.com")
    print("👉 Pass:  admin123")