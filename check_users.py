from server import app, db, User

with app.app_context():
    users = User.query.all()
    print("\n------- 🔍 DATABASE CHECK -------")
    if not users:
        print("❌ EMPTY: Koi User nahi mila!")
    for u in users:
        print(f"✅ FOUND: {u.email} | Role: {u.role}")
    print("---------------------------------\n")