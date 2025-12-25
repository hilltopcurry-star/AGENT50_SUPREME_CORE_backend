from server import app, db, Restaurant

with app.app_context():
    print("🗑️ Purana Data Saaf kar raha hoon...")
    db.drop_all()  # Purani tables delete
    print("✨ Naya Database bana raha hoon...")
    db.create_all() # Nayi tables create (Category support ke sath)

    # 🍔 NEW DATA SEEDING
    menu1 = [
        {"category": "Biryani Special 🍛", "items": [{"name": "Chicken Biryani", "price": 250}, {"name": "Beef Biryani", "price": 300}]},
        {"category": "Sides 🥗", "items": [{"name": "Raita", "price": 50}, {"name": "Salad", "price": 40}]},
        {"category": "Drinks 🥤", "items": [{"name": "Cold Drink", "price": 100}]}
    ]
    menu2 = [
        {"category": "Burgers 🍔", "items": [{"name": "Zinger Burger", "price": 350}, {"name": "Patty Burger", "price": 200}]},
        {"category": "Snacks 🍟", "items": [{"name": "Fries", "price": 100}, {"name": "Nuggets", "price": 250}]}
    ]
    
    res1 = Restaurant(id="res_1", name="Biryani House 🍛", menu=menu1)
    res2 = Restaurant(id="res_2", name="Burger King 🍔", menu=menu2)
    
    db.session.add(res1)
    db.session.add(res2)
    db.session.commit()
    
    print("✅ MUBARAK HO! Database Reset Complete.")
    print("👉 Ab 'python server.py' chalayen aur Admin Panel check karein.")