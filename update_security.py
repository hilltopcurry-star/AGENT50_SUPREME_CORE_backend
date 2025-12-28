"""
update_security.py
Description: Adds 'Change Password' feature to Admin Panel.
"""
import os

# --- CLOUDINARY KEYS (PRESERVED) ---
CLOUD_NAME = "dvcjw3xla"
API_KEY    = "457921716987727"
API_SECRET = "lujztiw9vI3XA0EpIs0RdIDOPpo"

PROJECT_NAME = "lehuyen_ceramic"
BASE_PATH = os.path.join("projects", PROJECT_NAME)

print(f"🔐 Adding Security Features to: {PROJECT_NAME}")

# 1. Updated Backend (App.py with Password Change Logic)
app_code = f"""
import os
import cloudinary
import cloudinary.uploader
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "super_secret_google_level_key"

# --- CLOUDINARY CONFIG ---
cloudinary.config(
  cloud_name = "{CLOUD_NAME}",
  api_key = "{API_KEY}",
  api_secret = "{API_SECRET}"
)

# --- DATABASE ---
db_url = os.environ.get('DATABASE_URL')
if not db_url:
    db_url = "postgresql://neondb_owner:npg_1M9UTVEHJrGt@ep-falling-salad-ah3w24sg-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require"

if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# --- MODELS ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200)) # Stores Hashed Password

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    image_url = db.Column(db.String(500), nullable=False)
    price = db.Column(db.String(50))

class Inquiry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100))
    phone = db.Column(db.String(50))
    message = db.Column(db.Text)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- ROUTES ---

@app.route('/')
def home():
    products = Product.query.all()
    return render_template('index.html', products=products)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        # Setup First Admin (if needed)
        if not user and username == "admin":
             # Default: director123
            hashed_pw = generate_password_hash("director123", method='pbkdf2:sha256')
            user = User(username="admin", password=hashed_pw)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            return redirect(url_for('admin'))
            
        # Check Password (supports old plain text AND new hashes)
        if user:
            if user.password == password: # Old check
                # Upgrade to hash automatically
                user.password = generate_password_hash(password, method='pbkdf2:sha256')
                db.session.commit()
                login_user(user)
                return redirect(url_for('admin'))
            elif check_password_hash(user.password, password): # New Secure check
                login_user(user)
                return redirect(url_for('admin'))

        flash('Wrong Username or Password')
            
    return render_template('login.html')

@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    if request.method == 'POST':
        name = request.form['name']
        price = request.form['price']
        file = request.files['image']
        
        if file:
            upload_result = cloudinary.uploader.upload(file)
            image_url = upload_result['secure_url']
            new_product = Product(name=name, price=price, image_url=image_url)
            db.session.add(new_product)
            db.session.commit()
            flash('Product Added Successfully!')
            
    products = Product.query.all()
    messages = Inquiry.query.all()
    return render_template('admin.html', products=products, messages=messages)

@app.route('/change_password', methods=['POST'])
@login_required
def change_password():
    new_pass = request.form.get('new_password')
    if new_pass:
        # Securely hash the new password
        hashed_pw = generate_password_hash(new_pass, method='pbkdf2:sha256')
        current_user.password = hashed_pw
        db.session.commit()
        flash('✅ Password Updated Successfully!')
    return redirect(url_for('admin'))

@app.route('/delete/<int:id>')
@login_required
def delete(id):
    product = Product.query.get(id)
    db.session.delete(product)
    db.session.commit()
    return redirect(url_for('admin'))

@app.route('/contact', methods=['POST'])
def contact():
    name = request.form.get('name')
    phone = request.form.get('phone')
    message = request.form.get('message')
    if name and phone:
        new_inquiry = Inquiry(customer_name=name, phone=phone, message=message)
        db.session.add(new_inquiry)
        db.session.commit()
    return redirect('/')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
"""

# 2. Updated Admin HTML (With Password Change Form)
admin_html = """
<!DOCTYPE html>
<html>
<head>
    <title>Admin Dashboard</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; padding: 20px; background: #fdfbf7; max-width: 1200px; margin: auto; }
        .header { display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #8d6e63; padding-bottom: 20px; }
        h1 { color: #5d4037; }
        .container { display: flex; gap: 20px; margin-top: 20px; flex-wrap: wrap; }
        .panel { background: white; padding: 25px; border-radius: 10px; flex: 1; min-width: 300px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        input, button { width: 100%; padding: 12px; margin: 8px 0; border-radius: 5px; border: 1px solid #ddd; box-sizing: border-box; }
        button { background: #28a745; color: white; border: none; cursor: pointer; font-weight: bold; }
        button:hover { background: #218838; }
        .logout { background: #dc3545; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; font-weight: bold; }
        
        .alert { padding: 10px; background-color: #d4edda; color: #155724; border-radius: 5px; margin-bottom: 15px; }
        
        /* Password Section */
        .security-box { background: #fff3cd; border: 1px solid #ffeeba; padding: 15px; border-radius: 8px; margin-top: 20px; }
        .security-box h3 { margin-top: 0; color: #856404; }
        .security-box button { background: #ffc107; color: #333; }
        
        table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        th { background: #eee; text-align: left; padding: 10px; }
        td { border-bottom: 1px solid #eee; padding: 10px; }
        .delete-btn { color: white; background: #dc3545; padding: 5px 10px; text-decoration: none; border-radius: 4px; font-size: 0.8rem; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🛠️ Dashboard: LỆ HUYỀN CERAMIC</h1>
        <a href="/logout" class="logout">Logout</a>
    </div>

    {% with messages = get_flashed_messages() %}
      {% if messages %}
        {% for message in messages %}
          <div class="alert">{{ message }}</div>
        {% endfor %}
      {% endif %}
    {% endwith %}

    <div class="container">
        <div class="panel">
            <h3 style="margin-top:0;">➕ Add New Product</h3>
            <form method="POST" enctype="multipart/form-data">
                <label>Product Name:</label>
                <input type="text" name="name" placeholder="e.g. Italian Floor Tile" required>
                <label>Price / Description:</label>
                <input type="text" name="price" placeholder="e.g. $25/sqft" required>
                <label>Upload Photo:</label>
                <input type="file" name="image" required style="border:none;">
                <button type="submit">Upload & Save to Cloud</button>
            </form>
            
            <div class="security-box">
                <h3>🔐 Security Settings</h3>
                <form action="/change_password" method="POST">
                    <input type="password" name="new_password" placeholder="New Password" required>
                    <button type="submit">Change Password</button>
                </form>
            </div>
        </div>

        <div class="panel">
            <h3 style="margin-top:0;">📩 Customer Inquiries</h3>
            {% if messages %}
            <table>
                <tr><th>Name</th><th>Phone</th><th>Message</th></tr>
                {% for msg in messages %}
                <tr>
                    <td>{{ msg.customer_name }}</td>
                    <td>{{ msg.phone }}</td>
                    <td>{{ msg.message }}</td>
                </tr>
                {% endfor %}
            </table>
            {% else %}
            <p>No messages yet.</p>
            {% endif %}
        </div>
    </div>

    <div class="panel" style="margin-top: 20px;">
        <h3>📦 Managed Products</h3>
        <table>
            <tr><th>Photo</th><th>Name</th><th>Price</th><th>Action</th></tr>
            {% for p in products %}
            <tr>
                <td><img src="{{ p.image_url }}" width="60" style="border-radius:4px;"></td>
                <td><strong>{{ p.name }}</strong></td>
                <td>{{ p.price }}</td>
                <td><a href="/delete/{{ p.id }}" class="delete-btn">Delete</a></td>
            </tr>
            {% endfor %}
        </table>
    </div>
</body>
</html>
"""

# Files Update Karna
with open(os.path.join(BASE_PATH, "app.py"), "w", encoding="utf-8") as f:
    f.write(app_code)

with open(os.path.join(BASE_PATH, "templates", "admin.html"), "w", encoding="utf-8") as f:
    f.write(admin_html)

print("✅ Security Features Installed!")
print("👉 Director can now change password from Dashboard.")