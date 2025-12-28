from backend.app import app
from backend.models import db, Restaurant, MenuItem
import uuid

with app.app_context():
    print("🍛 Adding Menu Items...")
    
    # 1. Restaurant Dhoondo
    rest = Restaurant.query.filter_by(name="Karachi Biryani House").first()
    
    if rest:
        # 2. Menu Items Add Karo
        item1 = MenuItem(id=str(uuid.uuid4()), restaurant_id=rest.id, name="Chicken Biryani (Full)", price=350.0)
        item2 = MenuItem(id=str(uuid.uuid4()), restaurant_id=rest.id, name="Chicken Biryani (Half)", price=200.0)
        item3 = MenuItem(id=str(uuid.uuid4()), restaurant_id=rest.id, name="Raita & Salad", price=50.0)
        item4 = MenuItem(id=str(uuid.uuid4()), restaurant_id=rest.id, name="Cold Drink (1.5L)", price=150.0)

        db.session.add_all([item1, item2, item3, item4])
        db.session.commit()
        print("✅ Menu Added Successfully for Karachi Biryani House!")
    else:
        print("❌ Error: Restaurant nahi mila. Pehle 'create_order.py' chalayen.")