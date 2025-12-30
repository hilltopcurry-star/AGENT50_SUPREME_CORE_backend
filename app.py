from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import os

# ✅ HTML Folder Setup
app = Flask(__name__, template_folder='templates')

# ✅ Sabko allow karo (CORS fix)
CORS(app, resources={r"/*": {"origins": "*"}})

# --- FAKE DATABASE (Memory) ---

# 1. Orders (Aapka purana data)
orders = []

# 2. Users (Admin login)
users = [
    {"email": "admin@agent50.com", "password": "admin123", "role": "super_admin", "name": "Super Admin"}
]

# 3. Drivers, Managers, Restaurants
drivers = []
managers = []
# ✅ Restaurant Structure (Menu ke liye tayyar)
restaurants = [{"id": "res1", "name": "Karachi Biryani House", "menu": [], "orders": []}]


# --- ROUTES ---

@app.route('/')
def home():
    return "Agent 50 Backend is LIVE! 🚀"

@app.route('/admin')
def admin_panel():
    return render_template('admin.html')

# --- 1. LOGIN API ---
@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')

        # Admin check
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

# --- 2. DASHBOARD DATA ---
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

# --- 3. CREATE DRIVER API (Crash Proof) ---
@app.route('/admin/create_driver', methods=['POST'])
def create_driver():
    try:
        data = request.json
        if not data or not data.get('email'): return jsonify({"error": "Data missing"}), 400
        
        new_driver = {
            "id": f"d-{len(drivers)+1}",
            "name": data.get('name'),
            "email": data.get('email'),
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

# --- 4. CREATE MANAGER ---
@app.route('/admin/create_manager', methods=['POST'])
def create_manager():
    data = request.json
    managers.append(data)
    return jsonify({"message": "Manager Created"}), 200

# --- 5. ADD RESTAURANT ---
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

# --- 6. ADD CATEGORY (Ye Missing Tha!) ---
@app.route('/admin/category/add', methods=['POST'])
def add_category():
    data = request.json
    rid = data.get('restaurant_id')
    cat = data.get('category')
    
    for r in restaurants:
        if r['id'] == rid:
            # Check duplicate category
            if not any(c['category'] == cat for c in r['menu']):
                r['menu'].append({"category": cat, "items": []})
            return jsonify({"message": "Category Added"}), 200
    return jsonify({"error": "Restaurant not found"}), 404

# --- 7. ADD MENU ITEM (Ye bhi Missing Tha!) ---
@app.route('/admin/menu/add', methods=['POST'])
def add_menu_item():
    data = request.json
    rid = data.get('restaurant_id')
    cat = data.get('category')
    name = data.get('name')
    price = data.get('price')

    for r in restaurants:
        if r['id'] == rid:
            for c in r['menu']:
                if c['category'] == cat:
                    c['items'].append({"name": name, "price": price})
                    return jsonify({"message": "Item Added"}), 200
    return jsonify({"error": "Category not found"}), 404

# --- 8. DELETE MENU ITEM ---
@app.route('/admin/menu/delete', methods=['POST'])
def delete_item():
    data = request.json
    rid = data.get('restaurant_id')
    cat = data.get('category')
    name = data.get('name')

    for r in restaurants:
        if r['id'] == rid:
            for c in r['menu']:
                if c['category'] == cat:
                    c['items'] = [i for i in c['items'] if i['name'] != name]
                    return jsonify({"message": "Deleted"}), 200
    return jsonify({"error": "Error deleting"}), 404

# --- 9. UPDATE PROFILE ---
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


# --- OLD ORDERS API ---

@app.route('/orders', methods=['GET'])
def get_orders():
    # Newest orders first
    return jsonify(orders[::-1])

@app.route('/orders', methods=['POST'])
def add_order():
    data = request.json
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


# --- SERVER START ---
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)