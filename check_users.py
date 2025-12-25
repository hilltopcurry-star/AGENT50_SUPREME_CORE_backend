from server import app, db, User

with app.app_context():
    users = User.query.all()
    print("------- DATABASE USERS -------")
    if not users:
        print("❌ Koi User nahi mila! (Database Empty hai)")
    for u in users:
        print(f"🆔 ID: {u.id} | 📧 Email: {u.email} | 🔐 Role: {u.role}")
    print("------------------------------")