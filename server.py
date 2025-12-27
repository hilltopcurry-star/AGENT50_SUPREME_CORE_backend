from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import func
from datetime import datetime, timedelta
import uuid
import os

app = Flask(__name__, template_folder='templates')
CORS(app)

# ✅ NEON DATABASE CONFIGURATION
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://neondb_owner:npg_1M9UTVEHJrGt@ep-falling-salad-ah3w24sg-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = { "pool_pre_ping": True, "pool_recycle": 300 }

db = SQLAlchemy(app)

# -------------------- 🗄️ DATABASE MODELS --------------------

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.String(50), primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    restaurant_id = db.Column(db.String(50), nullable=True)

class Restaurant(db.Model):
    __tablename__ = 'restaurants'
    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), default="")
    email = db.Column(db.String(50), default="")
    menu = db.Column(db.JSON, nullable=False) 
    def to_dict(self):
        return {"id": self.id, "name": self.name, "menu": self.menu, "phone": self.phone, "email": self.email}

class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.String(50), primary_key=True)
    customer_id = db.Column(db.String(50), nullable=False)
    restaurant_id = db.Column(db.String(50), db.ForeignKey('restaurants.id'), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default="Pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    proof_image = db.Column(db.Text, nullable=True)
    items = db.relationship('OrderItem', backref='order', lazy=True)
    
    def to_dict(self):
        return {
            "id": self.id,
            "restaurant_id": self.restaurant_id,
            "items": [item.name for item in self.items], 
            "total_amount": self.total_amount,
            "status": self.status,
            "date": self.created_at.strftime("%Y-%m-%d %H:%M"),
            "proof_image": self.proof_image
        }

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.String(50), db.ForeignKey('orders.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)

def init_db():
    with app.app_context():
        db.create_all()

# -------------------- 🔐 LOGIN & ADMIN --------------------
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(email=data.get('email')).first()
    if user and check_password_hash(user.password, data.get('password')):
        return jsonify({ "message": "Success", "role": user.role, "restaurant_id": user.restaurant_id })
    return jsonify({"error": "Invalid"}), 401

@app.route('/admin/create_manager', methods=['POST'])
def create_manager():
    data = request.json
    if User.query.filter_by(email=data['email']).first(): return jsonify({"error": "Exists"}), 400
    new_user = User(id=str(uuid.uuid4()), email=data['email'], password=generate_password_hash(data['password']), role="manager", restaurant_id=data['restaurant_id'])
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "Manager Created"})

@app.route('/')
def home(): return "AGENT 50 SERVER LIVE 🚀"

@app.route('/admin')
def admin(): return render_template('admin.html')

@app.route('/dashboard/data', methods=['POST'])
def get_dashboard_data():
    try:
        data = request.json
        res_query = Restaurant.query
        order_query = Order.query
        if data.get('role') == 'manager':
            res_query = res_query.filter_by(id=data.get('restaurant_id'))
            order_query = order_query.filter_by(restaurant_id=data.get('restaurant_id'))
        
        restaurants = res_query.all()
        orders = order_query.order_by(Order.created_at.desc()).limit(50).all()
        sales = db.session.query(func.sum(Order.total_amount)).filter(Order.status=='Delivered').scalar() or 0
        return jsonify({ "restaurants": [r.to_dict() for r in restaurants], "orders": [o.to_dict() for o in orders], "stats": {"sales_today": sales, "total_orders": len(orders)} })
    except Exception as e: return jsonify({"error": str(e)}), 500

# -------------------- 🚚 DRIVER & ORDER APIS (FIXED) --------------------

@app.route('/customer/restaurants', methods=['GET'])
def cust_res(): return jsonify([r.to_dict() for r in Restaurant.query.all()])

@app.route('/restaurant/<rid>/orders', methods=['GET'])
def res_orders(rid): return jsonify([o.to_dict() for o in Order.query.filter_by(restaurant_id=rid).all()])

# 🔥🔥 [CRITICAL FIX: Added 'Pending' to list] 🔥🔥
@app.route('/drivers/orders/available', methods=['GET'])
def driver_orders(): 
    return jsonify([o.to_dict() for o in Order.query.filter(Order.status.in_(['Pending', 'Preparing', 'Ready'])).all()])

@app.route('/orders', methods=['POST'])
def place_order():
    try:
        data = request.json
        oid = str(uuid.uuid4())
        items = data.get('items', [])
        if isinstance(items, str): items = items.split(', ')
        db.session.add(Order(id=oid, customer_id="cust_1", restaurant_id=data['restaurant_id'], total_amount=data['total_amount'], status="Pending"))
        for i in items: db.session.add(OrderItem(order_id=oid, name=i, price=0))
        db.session.commit()
        return jsonify({"message": "Order Placed"})
    except: return jsonify({"error": "Failed"}), 500

@app.route('/restaurant/orders/<oid>/status', methods=['PUT'])
def update_status(oid):
    order = Order.query.get(oid)
    if order:
        order.status = request.json['status']
        db.session.commit()
        return jsonify({"message": "Updated"})
    return jsonify({"error": "Not found"}), 404

@app.route('/drivers/orders/<oid>/accept', methods=['POST'])
def accept(oid): return jsonify({"message": "Ride Started"})

@app.route('/drivers/orders/<oid>/complete', methods=['POST'])
def complete(oid):
    data = request.json
    order = Order.query.get(oid)
    if order:
        order.status = 'Delivered'
        if 'image' in data: order.proof_image = data['image']
        db.session.commit()
    return jsonify({"message": "Done"})

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)