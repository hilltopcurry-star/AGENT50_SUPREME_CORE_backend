"""
fix_lehuyen.py
Description: REPAIR KIT. Rewrites all critical files (App & Requirements) to fix 500 Errors.
"""
import os

# --- CLOUDINARY KEYS ---
CLOUD_NAME = "dvcjw3xla"
API_KEY    = "457921716987727"
API_SECRET = "lujztiw9vI3XA0EpIs0RdIDOPpo"

PROJECT_NAME = "lehuyen_ceramic"
BASE_PATH = os.path.join("projects", PROJECT_NAME)

# Ensure folders exist
os.makedirs(BASE_PATH, exist_ok=True)
os.makedirs(os.path.join(BASE_PATH, "templates"), exist_ok=True)

print(f"🚑 Fixing Project: {PROJECT_NAME}...")

# 1. FIXED REQUIREMENTS (Sabse Zaroori Cheez)
req_code = """
flask==3.0.0
flask-sqlalchemy==3.1.1
psycopg2-binary
flask-login
cloudinary
werkzeug
"""

# 2. FIXED APP CODE
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
    password = db.Column(db.String(200))

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
    try:
        products = Product.query.all()
        return render_template('index.html', products=products)
    except Exception as e:
        return f"Database Error: {{str(e)}}"

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        # Auto-Create Admin (First Time)
        if not user and username == "admin":
            hashed_pw = generate_password_hash("director123", method='pbkdf2:sha256')
            user = User(username="admin", password=hashed_pw)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            return redirect(url_for('admin'))
            
        if user:
            # Check Hash or Plain text (Legacy support)
            if user.password == password:
                user.password = generate_password_hash(password, method='pbkdf2:sha256')
                db.session.commit()
                login_user(user)
                return redirect(url_for('admin'))
            elif check_password_hash(user.password, password):
                login_user(user)
                return redirect(url_for('admin'))

        flash('Wrong Username or Password')
            
    return render_template('login.html')

@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    if request.method == 'POST':
        name = request.form.get('name')
        price = request.form.get('price')
        file = request.files.get('image')
        
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

# Init DB
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
"""

# Saving Files (Force Overwrite)
with open(os.path.join(BASE_PATH, "requirements.txt"), "w", encoding="utf-8") as f:
    f.write(req_code)

with open(os.path.join(BASE_PATH, "app.py"), "w", encoding="utf-8") as f:
    f.write(app_code)

print("✅ REPAIR COMPLETE: requirements.txt and app.py restored.")
print("👉 Please run 'vercel --prod' now.")