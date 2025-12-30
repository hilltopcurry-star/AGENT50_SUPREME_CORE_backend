from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import os

# ✅ template_folder='templates' batata hai ke HTML kahan dhoondna hai
app = Flask(__name__, template_folder='templates')

# Sabko allow karo (CORS fix)
CORS(app, resources={r"/*": {"origins": "*"}})

# Fake Database
orders = []

# ✅ HOME ROUTE
@app.route('/')
def home():
    return "Agent 50 Backend is LIVE! 🚀"

# ✅ NEW ADMIN ROUTE (Ye Missing Tha!)
@app.route('/admin')
def admin_panel():
    return render_template('admin.html')

# ✅ GET ORDERS API
@app.route('/orders', methods=['GET'])
def get_orders():
    # Newest orders first
    return jsonify(orders[::-1])

# ✅ ADD ORDER API
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

# ✅ UPDATE ORDER API
@app.route('/orders/<int:order_id>', methods=['PUT'])
def update_order(order_id):
    data = request.json
    for order in orders:
        if order["id"] == order_id:
            order["status"] = data.get("status", order["status"])
            return jsonify(order), 200
    return jsonify({"error": "Order not found"}), 404

# Vercel entry point
if __name__ == '__main__':
    # PORT environment variable zaroori hai Render ke liye
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)