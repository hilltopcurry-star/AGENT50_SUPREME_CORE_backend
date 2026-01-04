from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import os
import threading  # ✅ NEW: Background task ke liye
import requests   # ✅ NEW: Agent 50 ko data bhejne ke liye
import json
import time

# ✅ HTML Folder Setup
app = Flask(__name__, template_folder='templates')

# ✅ Sabko allow karo (CORS fix)
CORS(app, resources={r"/*": {"origins": "*"}})

# --- 🕵️‍♂️ AGENT 50 CONNECTION (SILENT OBSERVER) ---
# Ye aapka Render wala naya Backend URL hai
AGENT_50_URL = "https://agent50-supreme-core-backend.onrender.com/webhook/observe"

def send_to_agent50(event_type, details):
    """
    Ye function background mein chalta hai.
    Business logic ko bilkul disturb nahi karega.
    """
    def _send():
        try:
            payload = {
                "event_type": event_type,
                "details": details
            }
            # Timeout 1s rakha hai taake agar Agent 50 down ho to Business app na phanse
            requests.post(AGENT_50_URL, json=payload, timeout=1)
            print(f"📡 Signal sent to Agent 50: {event_type}")
        except Exception as e:
            # Agar error aaye to ignore karo (Business is King)
            print(f"⚠️ Agent 50 unreachable (Ignored): {e}")

    # Fire and Forget (Thread)
    thread = threading.Thread(target=_send)
    thread.daemon = True
    thread.start()

# --- FAKE DATABASE (Memory) ---
orders = []

# ✅ USERS LIST (Admin + Permanent Google Test Driver)
users = [
    {"email": "admin@agent50.com", "password": "admin123", "role": "super_admin", "name": "Super Admin"},
    # 👇 YE RAHA AAPKA PERMANENT DRIVER (Google ke liye)
    {"email": "google@test.com", "password": "123", "role": "driver", "name": "Google Tester", "id": "d-test", "phone": "0000000000"}
]

# ✅ DRIVERS LIST (Taake Dashboard par bhi show ho)
drivers = [
    {"email": "google@test.com", "password": "123", "role": "driver", "name": "Google Tester", "id": "d-test", "phone": "0000000000"}
]

managers = []
restaurants = [{"id": "res1", "name": "Karachi Biryani House", "menu": [], "orders": []}]

# --- ROUTES ---

@app.route('/')
def home():
    return "Agent 50 Backend is LIVE! 🚀"

@app.route('/admin')
def admin_panel():
    return render_template('admin.html')

# 1. LOGIN API
@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')

        # Admin & Driver check (Users list mein)
        for u in users:
            if u['email'] == email and u['password'] == password:
                return jsonify(u), 200
        
        # Manager check
        for m in managers:
            if m['email'] == email and m['password'] == password:
                return jsonify(m), 200
        
        return jsonify({"error": "Invalid Credentials"}), 401
    except:
        return jsonify({"error": "Login Error"}), 500

# 2. DASHBOARD DATA
@app.route('/dashboard/data', methods=['POST', 'GET']) # Allow GET for easier testing
def dashboard_data():
    return jsonify({
        "stats": {
            "sales_today": 5000,
            "total_orders": len(orders)
        },
        "orders": orders[::-1], 
        "restaurants": restaurants,
        "drivers": drivers,
        "managers": managers
    })

# 🔥 NEW: GET ALL DRIVERS (List dikhane ke liye)
@app.route('/admin/get_drivers', methods=['GET'])
def get_drivers():
    return jsonify(drivers), 200

# 3. CREATE DRIVER API (FIXED - No Duplicates)
@app.route('/admin/create_rider', methods=['POST']) # Note: URL match Frontend (/create_rider)
def create_driver():
    try:
        data = request.json
        email = data.get('email')
        
        if not data or not email: 
            return jsonify({"error": "Data missing"}), 400
        
        # 🛑 DUPLICATE CHECK (Agar email pehle se hai to roko)
        for u in users:
            if u['email'] == email:
                return jsonify({"error": "User/Driver already exists!"}), 400

        new_driver = {
            "id": f"d-{len(drivers)+1}",
            "name": data.get('name'),
            "email": email,
            "password": data.get('password'),
            "phone": data.get('phone'),
            "role": "driver"
        }
        
        drivers.append(new_driver)
        users.append(new_driver) # Login allow karo
        
        print(f"✅ Driver Created: {new_driver['name']}")
        return jsonify({"message": "Driver Created Successfully!", "driver": new_driver}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 4. CREATE MANAGER
@app.route('/admin/create_manager', methods=['POST'])
def create_manager():
    data = request.json
    managers.append(data)
    return jsonify({"message": "Manager Created"}), 200

# 5. ADD RESTAURANT
@app.route('/admin/restaurant/add', methods=['POST'])
def add_restaurant():
    data = request.json
    new_res = {
        "id": f"res{len(restaurants)+1}",
        "name": data.get('name'),
        "menu": []
    }
    restaurants.append(new_res)
    return jsonify({"message": "Restaurant Added"}), 200

# 6. ADD CATEGORY
@app.route('/admin/category/add', methods=['POST'])
def add_category():
    data = request.json
    rid = data.get('restaurant_id')
    cat = data.get('category')
    
    for r in restaurants:
        if r['id'] == rid:
            if not any(c['category'] == cat for c in r['menu']):
                r['menu'].append({"category": cat, "items": []})
            return jsonify({"message": "Category Added"}), 200
    return jsonify({"error": "Restaurant not found"}), 404

# 7. ADD MENU ITEM
@app.route('/admin/menu/add', methods=['POST'])
def add_menu_item():
    data = request.json
    rid = data.get('restaurant_id')
    cat = data.get('category')
    name = data.get('name')
    price = data.get('price')

    # Quick hack: If category missing, create "General"
    for r in restaurants:
        if r['id'] == rid:
            # Check if menu has items directly or categories (Handling mixed structure)
            # Simplest for now: Just append to first category or create one
            if not r['menu']:
                r['menu'].append({"category": "Main", "items": []})
            
            # Add to first category for simplicity if cat not specified
            r['menu'][0]['items'].append({"name": name, "price": price})
            return jsonify({"message": "Item Added"}), 200
            
    return jsonify({"error": "Restaurant not found"}), 404

# 8. DELETE MENU ITEM
@app.route('/admin/menu/delete', methods=['POST'])
def delete_item():
    data = request.json
    rid = data.get('restaurant_id')
    name = data.get('name')

    for r in restaurants:
        if r['id'] == rid:
            for c in r['menu']:
                c['items'] = [i for i in c['items'] if i['name'] != name]
            return jsonify({"message": "Deleted"}), 200
    return jsonify({"error": "Error deleting"}), 404

# 9. UPDATE PROFILE
@app.route('/restaurant/update_profile', methods=['POST'])
def update_profile():
    data = request.json
    rid = data.get('id')
    for r in restaurants:
        if r['id'] == rid:
            r['phone'] = data.get('phone')
            r['email'] = data.get('email')
            return jsonify({"message": "Updated"}), 200
    return jsonify({"error": "Error"}), 404

# --- ORDERS API ---

@app.route('/orders', methods=['GET'])
def get_orders():
    return jsonify(orders[::-1])

@app.route('/orders', methods=['POST'])
def add_order():
    data = request.json
    new_order = {
        "id": str(len(orders) + 5501),
        "items": data.get("items", []),
        "total_amount": data.get("total_amount", 0),
        "status": "Pending",
        "customer_name": data.get("customer_name", "Guest")
    }
    orders.append(new_order)
    
    # 🔥 SIGNAL AGENT 50 (Yeh Render wale naye dimaagh ko bata dega)
    # Background mein chalega, customer ko wait nahi karna padega
    send_to_agent50("new_order", new_order)
    
    return jsonify(new_order), 200

@app.route('/orders/<order_id>', methods=['PUT'])
def update_order(order_id):
    data = request.json
    for order in orders:
        if str(order["id"]) == str(order_id):
            order["status"] = data.get("status", order["status"])
            
            # (Optional) Update hone par bhi Agent 50 ko bata sakte hain
            send_to_agent50("order_update", order)
            
            return jsonify(order), 200
    return jsonify({"error": "Order not found"}), 404


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)