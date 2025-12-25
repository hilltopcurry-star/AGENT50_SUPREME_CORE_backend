from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid
import os

app = Flask(__name__, template_folder='templates')
CORS(app)

# ✅ DATABASE CONFIGURATION (Neon DB)
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://neondb_owner:npg_1M9UTVEHJrGt@ep-falling-salad-ah3w24sg-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = { "pool_pre_ping": True, "pool_recycle": 300 }

db = SQLAlchemy(app)

# -------------------- MODELS --------------------
class Restaurant(db.Model):
    __tablename__ = 'restaurants'
    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    menu = db.Column(db.JSON, nullable=False) # Stores Categories & Items
    def to_dict(self):
        return {"id": self.id, "name": self.name, "menu": self.menu}

class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.String(50), primary_key=True)
    customer_id = db.Column(db.String(50), nullable=False)
    restaurant_id = db.Column(db.String(50), db.ForeignKey('restaurants.id'), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default="Pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    items = db.relationship('OrderItem', backref='order', lazy=True)
    def to_dict(self):
        return {
            "id": self.id,
            "restaurant_id": self.restaurant_id,
            "items": [item.name for item in self.items], 
            "total_amount": self.total_amount,
            "status": self.status
        }

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.String(50), db.ForeignKey('orders.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)

def init_db():
    with app.app_context():
        try:
            db.create_all()
            if not Restaurant.query.first():
                print("🌱 Seeding Categories...")
                menu1 = [
                    {"category": "Rice Delights 🍛", "items": [{"name": "Chicken Biryani", "price": 250}]},
                    {"category": "Sides 🥗", "items": [{"name": "Raita", "price": 50}]}
                ]
                menu2 = [
                    {"category": "Burgers 🍔", "items": [{"name": "Zinger Burger", "price": 350}]},
                    {"category": "Drinks 🥤", "items": [{"name": "Cola", "price": 100}]}
                ]
                db.session.add(Restaurant(id="res_1", name="Biryani House", menu=menu1))
                db.session.add(Restaurant(id="res_2", name="Burger King", menu=menu2))
                db.session.commit()
                print("✅ Database Ready!")
        except Exception as e:
            print(f"❌ Database Error: {e}")

# -------------------- ROUTES --------------------
@app.route('/')
def home(): return "SERVER LIVE 🚀"

@app.route('/admin')
def admin(): return render_template('admin.html')

@app.route('/admin/data', methods=['GET'])
def get_data():
    try:
        restaurants = Restaurant.query.all()
        sales = db.session.query(db.func.sum(Order.total_amount)).filter_by(status='Delivered').scalar() or 0
        orders = Order.query.count()
        return jsonify({"restaurants": [r.to_dict() for r in restaurants], "stats": {"sales": sales, "orders": orders}})
    except:
        return jsonify({"restaurants": [], "stats": {"sales": 0, "orders": 0}})

# 🆕 ADD NEW RESTAURANT (SUPER ADMIN POWER)
@app.route('/admin/restaurant/add', methods=['POST'])
def add_new_restaurant():
    try:
        data = request.json
        name = data.get('name')
        if not name: return jsonify({"error": "Name required"}), 400
        
        # Auto-generate ID
        count = Restaurant.query.count()
        new_id = f"res_{count + 1}_{str(uuid.uuid4())[:4]}"

        new_res = Restaurant(id=new_id, name=name, menu=[])
        db.session.add(new_res)
        db.session.commit()
        return jsonify({"message": "Restaurant Added!", "id": new_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 🆕 ADD CATEGORY
@app.route('/admin/category/add', methods=['POST'])
def add_category():
    data = request.json
    res = Restaurant.query.get(data['restaurant_id'])
    if res:
        menu = list(res.menu)
        menu.append({"category": data['category'], "items": []})
        res.menu = menu
        db.session.commit()
        return jsonify({"message": "Category Added"})
    return jsonify({"error": "Error"}), 400

# 🆕 ADD ITEM TO CATEGORY
@app.route('/admin/menu/add', methods=['POST'])
def add_item():
    data = request.json
    res = Restaurant.query.get(data['restaurant_id'])
    if res:
        menu = list(res.menu)
        for cat in menu:
            if cat['category'] == data['category']:
                cat['items'].append({"name": data['name'], "price": float(data['price'])})
                break
        res.menu = menu
        db.session.commit()
        return jsonify({"message": "Item Added"})
    return jsonify({"error": "Error"}), 400

# 🆕 DELETE ITEM
@app.route('/admin/menu/delete', methods=['POST'])
def delete_item():
    data = request.json
    res = Restaurant.query.get(data['restaurant_id'])
    if res:
        menu = list(res.menu)
        for cat in menu:
            if cat['category'] == data['category']:
                cat['items'] = [i for i in cat['items'] if i['name'] != data['name']]
                break
        res.menu = menu
        db.session.commit()
        return jsonify({"message": "Deleted"})
    return jsonify({"error": "Error"}), 400

# --- APP APIs ---
@app.route('/customer/restaurants', methods=['GET'])
def cust_res():
    return jsonify([r.to_dict() for r in Restaurant.query.all()])

@app.route('/restaurant/<rid>/orders', methods=['GET'])
def res_orders(rid):
    return jsonify([o.to_dict() for o in Order.query.filter_by(restaurant_id=rid).all()])

@app.route('/drivers/orders/available', methods=['GET'])
def driver_orders():
    return jsonify([o.to_dict() for o in Order.query.filter(Order.status.in_(['Preparing','Ready'])).all()])

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
    except: return jsonify({"error": "Order Failed"}), 500

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
    order = Order.query.get(oid)
    if order:
        order.status = 'Delivered'
        db.session.commit()
    return jsonify({"message": "Done"})

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)