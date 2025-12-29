from flask import Flask, jsonify, request
from flask_cors import CORS
import os

app = Flask(__name__)
# Sabko allow karo (CORS fix)
CORS(app, resources={r"/*": {"origins": "*"}})

# Fake Database
orders = []

@app.route('/')
def home():
    return "Agent 50 Backend is LIVE! 🚀"

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

# Vercel entry point
if __name__ == '__main__':
    app.run(debug=True)