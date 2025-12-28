"""
build_portfolio.py
Description: Builds a Professional Dark-Themed Portfolio with Neon DB integration.
"""
import os

# Project Name
PROJECT_NAME = "my_portfolio"
BASE_PATH = os.path.join("projects", PROJECT_NAME)

# Folders Banana
os.makedirs(BASE_PATH, exist_ok=True)
os.makedirs(os.path.join(BASE_PATH, "templates"), exist_ok=True)
os.makedirs(os.path.join(BASE_PATH, "static"), exist_ok=True)

print(f"🚀 Agent 50 Starting Project: {PROJECT_NAME}")
print("🎨 Applying Theme: Modern Dark Mode")
print("🔗 Linking Database: Neon PostgreSQL")

# 1. Main App Code (Backend)
app_code = """
import os
from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# --- DATABASE CONNECTION (NEON) ---
db_url = os.environ.get('DATABASE_URL')
if not db_url:
    # Fallback (Aapki Neon Key)
    db_url = "postgresql://neondb_owner:npg_1M9UTVEHJrGt@ep-falling-salad-ah3w24sg-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require"

if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Contact Form Data ke liye Table
class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)

with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/contact', methods=['POST'])
def contact():
    name = request.form.get('name')
    email = request.form.get('email')
    message = request.form.get('message')
    
    if name and email:
        new_msg = Contact(name=name, email=email, message=message)
        db.session.add(new_msg)
        db.session.commit()
        return render_template('index.html', success=True)
    
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
"""

# 2. HTML Template (Frontend - Modern Dark Look)
html_code = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ali | AI Full Stack Developer</title>
    <style>
        /* Modern Dark Theme CSS */
        body { margin: 0; font-family: 'Segoe UI', sans-serif; background-color: #121212; color: #e0e0e0; }
        .container { max-width: 900px; margin: auto; padding: 20px; }
        
        /* Header */
        header { text-align: center; padding: 50px 0; }
        h1 { font-size: 3rem; margin: 0; color: #bb86fc; }
        p.subtitle { font-size: 1.2rem; color: #b0b0b0; }
        
        /* Projects Section */
        .section-title { border-bottom: 2px solid #333; padding-bottom: 10px; margin-top: 50px; color: #03dac6; }
        .projects-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-top: 20px; }
        .project-card { background: #1e1e1e; padding: 20px; border-radius: 10px; border: 1px solid #333; transition: transform 0.2s; }
        .project-card:hover { transform: translateY(-5px); border-color: #bb86fc; }
        .project-card h3 { margin-top: 0; }
        .btn { display: inline-block; padding: 10px 20px; background: #bb86fc; color: #000; text-decoration: none; border-radius: 5px; font-weight: bold; margin-top: 10px; }
        .btn:hover { background: #9965f4; }

        /* Contact Form */
        form { display: flex; flex-direction: column; gap: 15px; background: #1e1e1e; padding: 30px; border-radius: 10px; margin-top: 20px; }
        input, textarea { padding: 12px; background: #2c2c2c; border: 1px solid #444; color: white; border-radius: 5px; }
        button { padding: 12px; background: #03dac6; border: none; color: black; font-weight: bold; cursor: pointer; border-radius: 5px; }
        button:hover { background: #01b4a4; }
        
        .success-msg { background: #2e7d32; color: white; padding: 10px; border-radius: 5px; text-align: center; margin-bottom: 20px; }
    </style>
</head>
<body>

    <div class="container">
        <header>
            <h1>Ali Baloch</h1>
            <p class="subtitle">AI Architect & Full Stack Developer</p>
            <p>Building intelligent apps with Python, Flask & Neon DB.</p>
        </header>

        {% if success %}
        <div class="success-msg">✅ Message Sent! I will contact you soon.</div>
        {% endif %}

        <h2 class="section-title">My Projects</h2>
        <div class="projects-grid">
            
            <div class="project-card">
                <h3>🚀 Super Cloud Todo</h3>
                <p>A real-time task manager connected to AWS Cloud Database (Neon Postgres). Data persists across devices.</p>
                <a href="https://super-todo-db.vercel.app" target="_blank" class="btn">View Live App</a>
            </div>

            <div class="project-card">
                <h3>📋 TaskMaster Pro</h3>
                <p>My first AI-generated task management system using Vercel deployment.</p>
                <a href="https://taskmaster-pro-one.vercel.app" target="_blank" class="btn">View Live App</a>
            </div>

        </div>

        <h2 class="section-title">Hire Me</h2>
        <form action="/contact" method="POST">
            <input type="text" name="name" placeholder="Your Name" required>
            <input type="email" name="email" placeholder="Your Email" required>
            <textarea name="message" rows="5" placeholder="How can I help you?" required></textarea>
            <button type="submit">Send Message</button>
        </form>

        <footer style="text-align: center; margin-top: 50px; color: #555;">
            <p>&copy; 2025 Ali Baloch. Powered by Agent 50.</p>
        </footer>
    </div>

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

print("✅ Portfolio Created: projects/my_portfolio")
print("👉 Ab 'deploy_app.py' chalayen aur duniya ko dikhayen!")