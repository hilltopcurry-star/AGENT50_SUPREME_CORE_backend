"""
build_neon_app.py
Description: Triggers Agent 50 to build 'Super_Todo' using the NEW Database Logic.
"""
import os

# Project ka naam
PROJECT_NAME = "super_todo_db"
BASE_PATH = os.path.join("projects", PROJECT_NAME)

# 1. Folder Banana
os.makedirs(BASE_PATH, exist_ok=True)
os.makedirs(os.path.join(BASE_PATH, "templates"), exist_ok=True)

print(f"🚀 Agent 50 Starting Project: {PROJECT_NAME}")
print("🧠 Checking Brain Logic... [DATABASE: DETECTED]")

# 2. Main App Code (Database Wala)
# Note karein: Ye code ab 'sqlite' ya 'json' nahi, balki 'Postgres' use kar raha hai.
app_code = """
import os
from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# --- THE REAL UPGRADE ---
# Agent ab Environment se key uthayega, ya aapki hardcoded key use karega.
# Ye wahi key hai jo aapne Neon se nikali thi.
db_url = os.environ.get('DATABASE_URL')
if not db_url:
    # Fallback for Vercel (Direct Link)
    db_url = "postgresql://neondb_owner:npg_1M9UTVEHJrGt@ep-falling-salad-ah3w24sg-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require"

# Fix for older Postgres urls
if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Database Model (Table Definition)
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)

# App start hone par Table khud bana dega
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    # Database se tasks fetch karna (Real Time)
    tasks = Task.query.all()
    return render_template('index.html', tasks=tasks)

@app.route('/add', methods=['POST'])
def add():
    content = request.form.get('content')
    if content:
        new_task = Task(content=content)
        db.session.add(new_task)
        db.session.commit() # Save to Cloud
    return redirect('/')

@app.route('/delete/<int:id>')
def delete(id):
    task = Task.query.get_or_404(id)
    db.session.delete(task)
    db.session.commit() # Delete from Cloud
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
"""

# 3. HTML Templates (UI)
html_code = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Neon DB Todo</title>
    <style>
        body { font-family: sans-serif; background-color: #f4f4f9; display: flex; justify-content: center; padding-top: 50px; }
        .container { background: white; padding: 2rem; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); width: 400px; }
        h2 { text-align: center; color: #333; }
        form { display: flex; gap: 10px; }
        input { flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }
        button { padding: 10px; background: #28a745; color: white; border: none; border-radius: 5px; cursor: pointer; }
        button:hover { background: #218838; }
        ul { list-style: none; padding: 0; margin-top: 20px; }
        li { background: #fff; border-bottom: 1px solid #eee; padding: 10px; display: flex; justify-content: space-between; align-items: center; }
        .delete-btn { background: #dc3545; padding: 5px 10px; font-size: 0.8rem; }
    </style>
</head>
<body>
    <div class="container">
        <h2>🔥 Super Cloud Todo</h2>
        <form action="/add" method="POST">
            <input type="text" name="content" placeholder="Task for Cloud..." required>
            <button type="submit">Add</button>
        </form>
        <ul>
            {% for task in tasks %}
            <li>
                {{ task.content }}
                <a href="/delete/{{ task.id }}" class="delete-btn" style="text-decoration: none; color: white; border-radius: 3px;">Delete</a>
            </li>
            {% endfor %}
        </ul>
    </div>
</body>
</html>
"""

# 4. Requirements (Zaroori Cheezein)
# Note: 'psycopg2' add ho gaya hai (Postgres ke liye)
req_code = """
flask
flask-sqlalchemy
psycopg2-binary
"""

# Files Write Karna
with open(os.path.join(BASE_PATH, "app.py"), "w", encoding="utf-8") as f:
    f.write(app_code)

with open(os.path.join(BASE_PATH, "templates", "index.html"), "w", encoding="utf-8") as f:
    f.write(html_code)

with open(os.path.join(BASE_PATH, "requirements.txt"), "w", encoding="utf-8") as f:
    f.write(req_code)

print("✅ Project Built Successfully: projects/super_todo_db")
print("📂 File Structure Created.")
print("🔗 Database Linked: Neon PostgreSQL")
print("👉 Ab 'deploy_app.py' se isay Vercel par Live karein!")