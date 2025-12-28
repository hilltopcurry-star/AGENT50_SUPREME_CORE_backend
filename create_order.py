from backend.app import app
from backend.models import db, User, Restaurant, Order

with app.app_context():
    print("🔄 Setting up data...")

    # 1. Create CUSTOMER (Agar nahi hai)
    customer = User.query.filter_by(email="customer@gmail.com").first()
    if not customer:
        customer = User(email="customer@gmail.com", password_hash="pass123", full_name="Ali Bhai", role="customer")
        db.session.add(customer)
        db.session.commit()
        print("👤 Customer Created: Ali Bhai")
    else:
        print("👤 Customer found: Ali Bhai")

    # 2. Create RESTAURANT OWNER (Agar nahi hai)
    owner = User.query.filter_by(email="owner@gmail.com").first()
    if not owner:
        owner = User(email="owner@gmail.com", password_hash="pass123", full_name="Restaurant Owner", role="owner")
        db.session.add(owner)
        db.session.commit()
        print("👨‍🍳 Owner Created")

    # 3. Create RESTAURANT (Agar nahi hai)
    restaurant = Restaurant.query.filter_by(name="Karachi Biryani House").first()
    if not restaurant:
        restaurant = Restaurant(
            owner_id=owner.id,
            name="Karachi Biryani House",
            address="Liberty Market, Lahore",
            city="Lahore",
            cuisine_type="Pakistani"
        )
        db.session.add(restaurant)
        db.session.commit()
        print("biryani Restaurant Created")
    else:
        print("biryani Restaurant found")

    # 4. Create ORDER (Finally!)
    new_order = Order(
        customer_id=customer.id,
        restaurant_id=restaurant.id,
        total_amount=550.0,  # ✅ 'total_price' nahi 'total_amount'
        status="Ready"
    )
    db.session.add(new_order)
    db.session.commit()

    print("\n-------------------------------------------")
    print("✅ SUCCESS! ORDER CREATED")
    print("🍔 Order: Karachi Biryani House -> Ali Bhai")
    print("💰 Amount: 550.0")
    print("-------------------------------------------\n")