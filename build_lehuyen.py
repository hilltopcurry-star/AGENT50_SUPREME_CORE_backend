"""
build_lehuyen.py
Description: Builds a Surprise Website for 'LỆ HUYỀN CERAMIC' with specific contact details.
"""
import os

# Project Name
PROJECT_NAME = "lehuyen_ceramic"
BASE_PATH = os.path.join("projects", PROJECT_NAME)

# Folders Banana
os.makedirs(BASE_PATH, exist_ok=True)
os.makedirs(os.path.join(BASE_PATH, "templates"), exist_ok=True)
os.makedirs(os.path.join(BASE_PATH, "static"), exist_ok=True)

print(f"🚀 Agent 50 Starting Surprise Project: {PROJECT_NAME}")
print("🏺 Theme: Premium Ceramic & Manufacturing")
print("🔗 Linking Database: Neon PostgreSQL")

# 1. Backend Code (App.py)
app_code = """
import os
from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# --- DATABASE CONNECTION ---
db_url = os.environ.get('DATABASE_URL')
if not db_url:
    # Fallback (Aapki Neon Key)
    db_url = "postgresql://neondb_owner:npg_1M9UTVEHJrGt@ep-falling-salad-ah3w24sg-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require"

if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Customer Inquiry Table
class Inquiry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(50), nullable=False)
    message = db.Column(db.Text, nullable=False)

with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/contact', methods=['POST'])
def contact():
    name = request.form.get('name')
    phone = request.form.get('phone')
    message = request.form.get('message')
    
    if name and phone:
        new_inquiry = Inquiry(customer_name=name, phone=phone, message=message)
        db.session.add(new_inquiry)
        db.session.commit()
        return render_template('index.html', success=True)
    
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
"""

# 2. Frontend Code (HTML with Official Details)
html_code = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LỆ HUYỀN CERAMIC | Official Website</title>
    <style>
        body { margin: 0; font-family: 'Segoe UI', sans-serif; background-color: #fdfbf7; color: #333; }
        
        /* Hero Section */
        header { 
            background: linear-gradient(rgba(0,0,0,0.6), rgba(0,0,0,0.6)), url('https://images.unsplash.com/photo-1616486338812-3dadae4b4f9d?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80');
            background-size: cover;
            background-position: center;
            color: white; 
            padding: 80px 20px; 
            text-align: center; 
        }
        h1 { margin: 0; font-size: 3rem; letter-spacing: 2px; text-transform: uppercase; }
        p.subtitle { font-size: 1.2rem; margin-top: 10px; opacity: 0.9; }
        .official-name { font-size: 0.9rem; margin-top: 20px; color: #ffd700; }

        .container { max-width: 1000px; margin: auto; padding: 40px 20px; }

        /* Business Card Section */
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

        /* Gallery */
        h2 { text-align: center; color: #5d4037; margin-top: 50px; }
        .gallery { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; margin-top: 30px; }
        .item { background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        .item-text { padding: 15px; text-align: center; }

        /* Contact Form */
        .contact-form { background: #5d4037; color: white; padding: 30px; border-radius: 10px; margin-top: 50px; }
        .contact-form h2 { color: white; margin-top: 0; }
        input, textarea, button { width: 100%; padding: 12px; margin: 10px 0; border: none; border-radius: 4px; box-sizing: border-box; }
        button { background: #ffd700; color: #5d4037; font-weight: bold; cursor: pointer; transition: 0.3s; }
        button:hover { background: #ffcc00; }

        .success-msg { background: #4caf50; color: white; padding: 15px; text-align: center; border-radius: 5px; margin-bottom: 20px; }
        
        footer { text-align: center; margin-top: 50px; padding: 20px; color: #777; font-size: 0.9rem; border-top: 1px solid #ddd; }
    </style>
</head>
<body>

    <header>
        <h1>LỆ HUYỀN CERAMIC</h1>
        <p class="subtitle">Excellence in Trade & Production</p>
        <p class="official-name">CÔNG TY TNHH ĐẦU TƯ THƯƠNG MẠI VÀ SẢN XUẤT</p>
    </header>

    <div class="container">
        
        {% if success %}
        <div class="success-msg">✅ Cảm ơn bạn! Chúng tôi sẽ liên hệ lại sớm. (Message Sent!)</div>
        {% endif %}

        <div class="biz-card">
            <span class="director">TRƯƠNG LỆ</span>
            <span class="title">Giám đốc (Director)</span>
            
            <div class="info-row">📍 <strong>Address:</strong> SP10-24 Đường Biển Hồ 10A, Vinhomes Ocean Park,<br> Xã Đa Tốn, Huyện Gia Lâm</div>
            <div class="info-row">📞 <strong>Phone:</strong> <a href="tel:0913322078" style="color: #333;">0913322078</a></div>
            <div class="info-row">✉️ <strong>Email:</strong> <a href="mailto:annatruong2268@gmail.com" style="color: #333;">annatruong2268@gmail.com</a></div>
        </div>

        <h2>Our Collection</h2>
        <div class="gallery">
            <div class="item">
                <div style="height: 200px; background: #eee; display: flex; align-items: center; justify-content: center;">Premium Tiles</div>
                <div class="item-text">
                    <h3>Floor & Wall Tiles</h3>
                    <p>High quality ceramic tiles for modern homes.</p>
                </div>
            </div>
            <div class="item">
                <div style="height: 200px; background: #e0e0e0; display: flex; align-items: center; justify-content: center;">Sanitary Ware</div>
                <div class="item-text">
                    <h3>Luxury Sanitary Ware</h3>
                    <p>Elegant designs for bathrooms.</p>
                </div>
            </div>
            <div class="item">
                <div style="height: 200px; background: #d7ccc8; display: flex; align-items: center; justify-content: center;">Decor</div>
                <div class="item-text">
                    <h3>Interior Decor</h3>
                    <p>Exclusive ceramic art pieces.</p>
                </div>
            </div>
        </div>

        <div class="contact-form">
            <h2>Liên Hệ (Contact Us)</h2>
            <p>Interested in our products? Send us a message directly.</p>
            <form action="/contact" method="POST">
                <input type="text" name="name" placeholder="Your Name (Tên của bạn)" required>
                <input type="text" name="phone" placeholder="Phone Number (Số điện thoại)" required>
                <textarea name="message" rows="4" placeholder="Your Message (Lời nhắn)" required></textarea>
                <button type="submit">SEND MESSAGE</button>
            </form>
        </div>

    </div>

    <footer>
        &copy; 2025 LỆ HUYỀN CERAMIC. All Rights Reserved.<br>
        Built with ❤️ by Ali Baloch.
    </footer>

</body>
</html>
"""

# 3. Requirements
req_code = """
flask
flask-sqlalchemy
psycopg2-binary
"""

# Saving Files
with open(os.path.join(BASE_PATH, "app.py"), "w", encoding="utf-8") as f:
    f.write(app_code)

with open(os.path.join(BASE_PATH, "templates", "index.html"), "w", encoding="utf-8") as f:
    f.write(html_code)

with open(os.path.join(BASE_PATH, "requirements.txt"), "w", encoding="utf-8") as f:
    f.write(req_code)

print("✅ Surprise Website Created: projects/lehuyen_ceramic")
print("👉 Ab jaldi se 'deploy_app.py' chalayen aur link bhej dein!")