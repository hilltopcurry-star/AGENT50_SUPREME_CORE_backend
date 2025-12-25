from flask import Flask, request, jsonify
from flask_cors import CORS
from backend.models import db, User, Restaurant, MenuItem, Order
import os
import uuid

app = Flask(__name__)

# --- CONFIGURATION ---
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'site.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

CORS(app)
db.init_app(app)

# --- ROUTES ---

@app.route('/')
def home():
    return "🚀 Agent 50 Server is Running!", 200

# ==========================
# 🍔 RESTAURANT PANEL (NEW)
# ==========================

# 1. Get Restaurant Orders (Jo Pending ya Preparing hain)
@app.route('/restaurant/<restaurant_id>/orders', methods=['GET'])
def get_restaurant_orders(restaurant_id):
    # Sirf wo orders layen jo abhi complete nahi hue
    orders = Order.query.filter(
        Order.restaurant_id == restaurant_id,
        Order.status.in_(['Pending', 'Preparing', 'Ready'])
    ).all()
    
    output = []
    for order in orders:
        items = [] # Future mein yahan menu items ayenge
        output.append({
            "id": order.id,
            "order_number": order.id[:5].upper(),
            "amount": order.total_amount,
            "status": order.status,
            "customer_id": order.customer_id
        })
    return jsonify(output), 200

# 2. Update Status (Pending -> Preparing -> Ready)
@app.route('/restaurant/orders/<order_id>/status', methods=['PUT'])
def update_order_status(order_id):
    data = request.json
    new_status = data.get('status')
    
    order = Order.query.get(order_id)
    if order:
        order.status = new_status
        db.session.commit()
        return jsonify({"message": f"Order status updated to {new_status}"}), 200
    return jsonify({"error": "Order not found"}), 404


# ==========================
# 🛵 DRIVER ROUTES
# ==========================
@app.route('/drivers/status', methods=['PUT'])
def update_driver_status():
    data = request.json
    user = User.query.filter_by(email="driver@gmail.com").first()
    if user:
        user.is_active = data.get('is_active', False)
        db.session.commit()
        return jsonify({"message": "Status updated"}), 200
    return jsonify({"error": "Driver not found"}), 404

@app.route('/drivers/orders/available', methods=['GET'])
def get_available_orders():
    # ⚠️ DRIVER SIRF 'READY' ORDERS DEKHEGA
    orders = Order.query.filter_by(status="Ready").all()
    output = []
    for order in orders:
        rest = Restaurant.query.get(order.restaurant_id)
        cust = User.query.get(order.customer_id)
        output.append({
            "id": order.id,
            "order_number": order.id[:8].upper(),
            "restaurant": {"name": rest.name, "address": rest.address} if rest else {},
            "delivery_fee": order.total_amount, 
            "customer_name": cust.full_name if cust else "Unknown",
            "status": order.status
        })
    return jsonify({"available": output}), 200

@app.route('/drivers/orders/<string:order_id>/accept', methods=['POST'])
def accept_order(order_id):
    order = Order.query.get(order_id)
    if order:
        order.status = "Accepted" # Driver le gaya
        db.session.commit()
        return jsonify({"message": "Order Accepted"}), 200
    return jsonify({"error": "Order not found"}), 404

# ==========================
# 🙋‍♂️ CUSTOMER ROUTES
# ==========================
@app.route('/customer/restaurants', methods=['GET'])
def get_restaurants():
    restaurants = Restaurant.query.filter_by(is_active=True).all()
    output = []
    for r in restaurants:
        output.append({
            "id": r.id, "name": r.name, "address": r.address, 
            "cuisine": r.cuisine_type, 
            "image": "https://via.placeholder.com/150"
        })
    return jsonify(output), 200

@app.route('/customer/menu/<restaurant_id>', methods=['GET'])
def get_menu(restaurant_id):
    items = MenuItem.query.filter_by(restaurant_id=restaurant_id).all()
    output = []
    for i in items:
        output.append({"id": i.id, "name": i.name, "price": i.price})
    return jsonify(output), 200

@app.route('/customer/order', methods=['POST'])
def place_order():
    data = request.json
    # AB ORDER 'PENDING' STATUS KE SAATH BANEGA
    new_order = Order(
        id=str(uuid.uuid4()),
        customer_id=data.get('customer_id'),
        restaurant_id=data.get('restaurant_id'),
        total_amount=data.get('total_amount'),
        status="Pending" 
    )
    db.session.add(new_order)
    db.session.commit()
    return jsonify({"message": "Order Placed", "order_id": new_order.id}), 201

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)