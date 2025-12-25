from server import app, db, Order, OrderItem
import uuid

# THIS SCRIPT CREATES A "READY" ORDER DIRECTLY IN THE DATABASE
# SO THE DRIVER APP CAN SEE IT IMMEDIATELY.

with app.app_context():
    print("🚀 Injecting READY Order into Live Database...")
    
    # 1. Create Order ID
    oid = str(uuid.uuid4())
    
    # 2. Create Order Object (STATUS = READY)
    new_order = Order(
        id=oid,
        customer_id="cust_test",
        restaurant_id="res_1",
        total_amount=1200,
        status="Ready"  # ✅ This makes it visible to Driver!
    )
    
    # 3. Add Items
    item1 = OrderItem(order_id=oid, name="Super Zinger Deal", price=1200)
    
    db.session.add(new_order)
    db.session.add(item1)
    db.session.commit()
    
    print("✅ ORDER INJECTED SUCCESSFULLY!")
    print(f"🆔 Order ID: {oid}")
    print("👉 Ab Phone Check Karein, Order Bajna Chahiye!")