"""
upgrade_full_system.py
Description: Upgrades Lehuyen Ceramic with Admin Panel, Login, and Cloudinary Image Storage.
"""
import os

# --- AAPKI CLOUDINARY KEYS (SAFE & SECURE) ---
CLOUD_NAME = "dvcjw3xla"
API_KEY    = "457921716987727"
API_SECRET = "lujztiw9vI3XA0EpIs0RdIDOPpo"

# Project setup
PROJECT_NAME = "lehuyen_ceramic"
BASE_PATH = os.path.join("projects", PROJECT_NAME)

print(f"🚀 Upgrading Project to Enterprise Level: {PROJECT_NAME}")

# 1. Update Requirements (Nayi libraries)
req_code = """
flask
flask-sqlalchemy
psycopg2-binary
flask-login
cloudinary
"""

with open(os.path.join(BASE_PATH, "requirements.txt"), "w", encoding="utf-8") as f:
    f.write(req_code)

# 2. Advanced Backend Code (Login + Upload + Database)
app_code = f"""
import os
import cloudinary
import cloudinary.uploader
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.secret_key = "super_secret_google_level_key"

# --- CLOUDINARY CONFIG (IMAGE BANK) ---
cloudinary.config(
  cloud_name = "{CLOUD_NAME}",
  api_key = "{API_KEY}",
  api_secret = "{API_SECRET}"
)

# --- DATABASE CONNECTION ---
db_url = os.environ.get('DATABASE_URL')
if not db_url:
    # Fallback default
    db_url = "postgresql://neondb_owner:npg_1M9UTVEHJrGt@ep-falling-salad-ah3w24sg-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require"

if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# --- TABLES ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))

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
        
        # Auto-Create Admin if not exists
        user = User.query.filter_by(username=username).first()
        if not user and username == "admin" and password == "director123":
            user = User(username="admin", password="director123")
            db.session.add(user)
            db.session.commit()
            
        if user and user.password == password:
            login_user(user)
            return redirect(url_for('admin'))
        else:
            flash('Invalid Credentials')
            
    return render_template('login.html')

@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    if request.method == 'POST':
        name = request.form['name']
        price = request.form['price']
        file = request.files['image']
        
        if file:
            # Upload directly to Cloud
            upload_result = cloudinary.uploader.upload(file)
            image_url = upload_result['secure_url']
            
            new_product = Product(name=name, price=price, image_url=image_url)
            db.session.add(new_product)
            db.session.commit()
            flash('Product Added Successfully!')
            
    products = Product.query.all()
    messages = Inquiry.query.all()
    return render_template('admin.html', products=products, messages=messages)

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

# 3. HTML Templates (Login, Admin, Index)
login_html = """
<!DOCTYPE html>
<html>
<head>
    <title>Director Login</title>
    <style>
        body { font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; background: #f4f4f4; }
        form { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); width: 300px; text-align: center; border-top: 5px solid #8d6e63; }
        input { width: 90%; padding: 10px; margin: 10px 0; border: 1px solid #ddd; border-radius: 5px; }
        button { width: 100%; padding: 10px; background: #8d6e63; color: white; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; }
        button:hover { background: #6d4c41; }
    </style>
</head>
<body>
    <form method="POST">
        <h2>🔒 Director Login</h2>
        <input type="text" name="username" placeholder="Username" required>
        <input type="password" name="password" placeholder="Password" required>
        <button type="submit">Login</button>
    </form>
</body>
</html>
"""

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

index_html = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LỆ HUYỀN CERAMIC | Official Website</title>
    <style>
        body { margin: 0; font-family: 'Segoe UI', sans-serif; background-color: #fdfbf7; color: #333; }
        
        /* Header */
        header { 
            background: linear-gradient(rgba(0,0,0,0.6), rgba(0,0,0,0.6)), url('https://images.unsplash.com/photo-1616486338812-3dadae4b4f9d?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80');
            background-size: cover;
            background-position: center;
            color: white; 
            padding: 100px 20px; 
            text-align: center; 
        }
        h1 { margin: 0; font-size: 3rem; letter-spacing: 2px; text-transform: uppercase; }
        p.subtitle { font-size: 1.2rem; margin-top: 10px; opacity: 0.9; }
        .official-name { font-size: 0.9rem; margin-top: 20px; color: #ffd700; }

        .container { max-width: 1000px; margin: auto; padding: 40px 20px; }

        /* Business Card */
        .biz-card { 
            background: white; 
            padding: 30px; 
            border-radius: 10px; 
            box-shadow: 0 5px 15px rgba(0,0,0,0.1); 
            text-align: center;
            border-top: 4px solid #8d6e63;
        }
        .director { font-size: 1.5rem; font-weight: bold; color: #5d4037; }
        .title { color: #888; margin-bottom: 20px; display: block; }
        .info-row { margin: 10px 0; font-size: 1.1rem; }
        .info-row strong { color: #8d6e63; }

        /* Product Gallery */
        h2 { text-align: center; color: #5d4037; margin-top: 50px; }
        .gallery { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; margin-top: 30px; }
        .item { background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 5px rgba(0,0,0,0.1); transition: transform 0.3s; }
        .item:hover { transform: translateY(-5px); }
        .item img { width: 100%; height: 250px; object-fit: cover; }
        .item-text { padding: 15px; text-align: center; }
        .price { color: #8d6e63; font-weight: bold; font-size: 1.1rem; }

        /* Contact Form */
        .contact-form { background: #5d4037; color: white; padding: 30px; border-radius: 10px; margin-top: 50px; }
        .contact-form h2 { color: white; margin-top: 0; }
        input, textarea, button { width: 100%; padding: 12px; margin: 10px 0; border: none; border-radius: 4px; box-sizing: border-box; }
        button { background: #ffd700; color: #5d4037; font-weight: bold; cursor: pointer; transition: 0.3s; }
        button:hover { background: #ffcc00; }

        footer { text-align: center; margin-top: 50px; padding: 20px; color: #777; font-size: 0.9rem; border-top: 1px solid #ddd; }
        
        .admin-link { position: fixed; bottom: 10px; right: 10px; background: #333; color: white; padding: 5px 10px; font-size: 0.8rem; text-decoration: none; border-radius: 20px; opacity: 0.3; }
        .admin-link:hover { opacity: 1; }
    </style>
</head>
<body>

    <header>
        <h1>LỆ HUYỀN CERAMIC</h1>
        <p class="subtitle">Excellence in Trade & Production</p>
        <p class="official-name">CÔNG TY TNHH ĐẦU TƯ THƯƠNG MẠI VÀ SẢN XUẤT</p>
    </header>

    <div class="container">
        
        <div class="biz-card">
            <span class="director">TRƯƠNG LỆ</span>
            <span class="title">Giám đốc (Director)</span>
            <div class="info-row">📍 <strong>Address:</strong> SP10-24 Đường Biển Hồ 10A, Vinhomes Ocean Park,<br> Xã Đa Tốn, Huyện Gia Lâm</div>
            <div class="info-row">📞 <strong>Phone:</strong> 0913322078</div>
            <div class="info-row">✉️ <strong>Email:</strong> annatruong2268@gmail.com</div>
        </div>

        <h2>Our Collection</h2>
        <div class="gallery">
            {% for p in products %}
            <div class="item">
                <img src="{{ p.image_url }}" alt="{{ p.name }}">
                <div class="item-text">
                    <h3>{{ p.name }}</h3>
                    <p class="price">{{ p.price }}</p>
                </div>
            </div>
            {% else %}
            <p style="text-align:center; width:100%; color:#888;">Adding new products soon...</p>
            {% endfor %}
        </div>

        <div class="contact-form">
            <h2>Liên Hệ (Contact Us)</h2>
            <form action="/contact" method="POST">
                <input type="text" name="name" placeholder="Your Name" required>
                <input type="text" name="phone" placeholder="Phone Number" required>
                <textarea name="message" rows="4" placeholder="Your Message" required></textarea>
                <button type="submit">SEND MESSAGE</button>
            </form>
        </div>

    </div>
    
    <a href="/login" class="admin-link">Staff Login</a>

    <footer>&copy; 2025 LỆ HUYỀN CERAMIC.</footer>

</body>
</html>
"""

# Files Save Karna
with open(os.path.join(BASE_PATH, "app.py"), "w", encoding="utf-8") as f:
    f.write(app_code)

with open(os.path.join(BASE_PATH, "templates", "login.html"), "w", encoding="utf-8") as f:
    f.write(login_html)

with open(os.path.join(BASE_PATH, "templates", "admin.html"), "w", encoding="utf-8") as f:
    f.write(admin_html)

with open(os.path.join(BASE_PATH, "templates", "index.html"), "w", encoding="utf-8") as f:
    f.write(index_html)
    
with open(os.path.join(BASE_PATH, "requirements.txt"), "w", encoding="utf-8") as f:
    f.write(req_code)

print("✅ UPGRADE COMPLETE: Login + Admin + Cloud Storage Installed!")
print("👉 Ab 'deploy_app.py' chalayen.")