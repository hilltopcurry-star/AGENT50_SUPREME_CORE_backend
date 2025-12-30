from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import os

# ✅ template_folder='templates' batata hai ke HTML kahan dhoondna hai
app = Flask(__name__, template_folder='templates')

# Sabko allow karo (CORS fix)
CORS(app, resources={r"/*": {"origins": "*"}})

# --- FAKE DATABASE (Temporary Storage) ---
# 1. Orders (Aapka purana database)
orders = []

# 2. Users (Admin login ke liye zaroori hai)
users = [
    {"email": "admin@agent50.com", "password": "admin123", "role": "super_admin", "name": "Super Admin"}
]

# 3. Drivers & Restaurants (Naya logic)
drivers = []
restaurants = [{"id": "res1", "name": "Karachi Biryani House", "menu": [], "orders": []}]
managers = []


# --- ROUTES ---

# ✅ HOME ROUTE
@app.route('/')
def home():
    return "Agent 50 Backend is LIVE! 🚀"

# ✅ ADMIN PANEL ROUTE (HTML Page)
@app.route('/admin')
def admin_panel():
    return render_template('admin.html')


# --- OLD ORDERS API (Aapka Purana Kaam) ---

@app.route('/orders', methods=['GET'])
def get_orders():
    # Newest orders first
    return jsonify(orders[::-1])

@app.route('/orders', methods=['POST'])
def add_order():
    data = request.json
    # Fake ID generator
    new_order = {
        "id": len(orders) + 5501,
        "items": data.get("items", []),
        "total_amount": data.get("total_amount", 0),
        "status": "Pending",
        "customer_name": data.get("customer_name", "Guest")
    }
    orders.append(new_order)
    return jsonify(new_order), 200

@app.route('/orders/<int:order_id>', methods=['PUT'])
def update_order(order_id):
    data = request.json
    for order in orders:
        if order["id"] == order_id:
            order["status"] = data.get("status", order["status"])
            return jsonify(order), 200
    return jsonify({"error": "Order not found"}), 404


# --- NEW ADMIN API (Ye Error Fix Karega) ---

# 1. LOGIN API (Admin Dashboard kholne ke liye)
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    # Admin check
    for u in users:
        if u['email'] == email and u['password'] == password:
            return jsonify(u), 200
    
    return jsonify({"error": "Invalid Credentials"}), 401

# 2. DASHBOARD DATA API (Graphs aur Tables ke liye)
@app.route('/dashboard/data', methods=['POST'])
def dashboard_data():
    return jsonify({
        "stats": {
            "sales_today": 5000,
            "total_orders": len(orders)
        },
        "orders": orders[::-1], 
        "restaurants": restaurants
    })

# 3. CREATE DRIVER API (Ye raha wo Button ka Logic!) 🚚
@app.route('/admin/create_driver', methods=['POST'])
def create_driver():
    data = request.json
    
    # Validation
    if not data.get('email') or not data.get('password'):
        return jsonify({"error": "Email and Password required"}), 400
    
    new_driver = {
        "id": f"d-{len(drivers)+1}",
        "name": data.get('name'),
        "email": data.get('email'),
        "password": data.get('password'),
        "phone": data.get('phone'),
        "role": "driver"
    }
    
    # Save driver
    drivers.append(new_driver)
    users.append(new_driver) # Login ke liye bhi allow karo
    
    print(f"✅ New Driver Created: {new_driver['name']}")
    return jsonify({"message": "Driver Created Successfully!", "driver": new_driver}), 200

# 4. CREATE MANAGER API
@app.route('/admin/create_manager', methods=['POST'])
def create_manager():
    data = request.json
    new_mgr = {
        "email": data.get('email'),
        "password": data.get('password'),
        "restaurant_id": data.get('restaurant_id'),
        "role": "manager"
    }
    managers.append(new_mgr)
    return jsonify({"message": "Manager Created"}), 200

# 5. ADD RESTAURANT API
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


# --- SERVER START ---
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)