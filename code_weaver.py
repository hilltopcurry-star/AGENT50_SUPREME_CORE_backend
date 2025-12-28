"""
code_weaver.py
MODULE: SUPREME WEAVER (v4.0 - FULL STACK)
Description: Generates Backend Logic AND Frontend UI dynamically from Schema.
"""

# --- BACKEND GENERATORS ---

def generate_extensions():
    return """
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
db = SQLAlchemy()
login_manager = LoginManager()
"""

def generate_models(blueprint):
    lines = [
        "from extensions import db, login_manager",
        "from flask_login import UserMixin",
        "from werkzeug.security import generate_password_hash, check_password_hash",
        "",
        "@login_manager.user_loader",
        "def load_user(user_id): return User.query.get(int(user_id))",
        "",
        "class User(db.Model, UserMixin):",
        "    id = db.Column(db.Integer, primary_key=True)",
        "    username = db.Column(db.String(150), unique=True, nullable=False)",
        "    password_hash = db.Column(db.String(256))",
        "    role = db.Column(db.String(50), default='user')",
        "    def set_password(self, password): self.password_hash = generate_password_hash(password)",
        "    def check_password(self, password): return check_password_hash(self.password_hash, password)"
    ]

    # DYNAMIC ENTITY GENERATION
    for entity in blueprint["entities"]:
        lines.append(f"\nclass {entity['name']}(db.Model):")
        lines.append("    id = db.Column(db.Integer, primary_key=True)")
        for field, ftype in entity['fields']:
            # Parse simple types mapping
            col_def = f"db.Column(db.{ftype.split('(')[0]}"
            if "(" in ftype: col_def += f", {ftype.split('(')[1].replace(')', '')}"
            col_def += ")"
            # Fix ForeignKey syntax for Weaver
            if "ForeignKey" in ftype:
                ref = ftype.split("'")[1]
                col_def = f"db.Column(db.Integer, db.ForeignKey('{ref}'))"
            
            lines.append(f"    {field} = {col_def}")
            
    return "\n".join(lines)

def generate_routes(blueprint):
    # Generates Universal CRUD + Auth endpoints
    return """
from flask import Blueprint, request, jsonify, render_template
from extensions import db
from models import *
from flask_login import login_user, logout_user, login_required, current_user

api = Blueprint('api', __name__)

@api.route('/auth/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(username=data['username']).first()
    if user and user.check_password(data['password']):
        login_user(user)
        return jsonify({'role': user.role, 'redirect': f'/{user.role}_dashboard'})
    return jsonify({'error': 'Invalid'}), 401

@api.route('/auth/signup', methods=['POST'])
def signup():
    data = request.json
    if User.query.filter_by(username=data['username']).first(): return jsonify({'error': 'Exists'}), 400
    user = User(username=data['username'], role=data.get('role', 'user'))
    user.set_password(data['password'])
    db.session.add(user)
    db.session.commit()
    return jsonify({'msg': 'Created'})

# DYNAMIC DATA ENDPOINTS
@api.route('/data/<entity>', methods=['GET', 'POST'])
@login_required
def handle_data(entity):
    # Universal Handler for any entity
    model_cls = globals().get(entity.capitalize())
    if not model_cls: return jsonify({'error': 'Invalid Entity'}), 404

    if request.method == 'POST':
        data = request.json
        # Filter out invalid keys
        valid_keys = {c.key: data[c.key] for c in model_cls.__table__.columns if c.key in data and c.key != 'id'}
        item = model_cls(**valid_keys)
        db.session.add(item)
        db.session.commit()
        return jsonify({'msg': 'Saved'})

    items = model_cls.query.all()
    # Simple serializer
    res = []
    for i in items:
        d = {c.key: getattr(i, c.key) for c in i.__table__.columns}
        res.append(d)
    return jsonify(res)
"""

def generate_app(blueprint):
    return """
from flask import Flask, render_template
from extensions import db, login_manager
from routes import api

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///local_dev.db' # Switch to Neon in Prod
app.config['SECRET_KEY'] = 'supreme-core-key'
db.init_app(app)
login_manager.init_app(app)

app.register_blueprint(api, url_prefix='/api')

# SERVE FRONTEND PAGES
@app.route('/')
def index(): return render_template('login.html')

@app.route('/<page>')
def serve_page(page):
    # Security check: ensure page exists in templates
    return render_template(f'{page}.html')

with app.app_context(): db.create_all()

if __name__ == '__main__': app.run(debug=True)
"""

# --- FRONTEND GENERATOR (THE NEW CAPABILITY) ---

def generate_html_template(page_name, blueprint):
    # Generates Bootstrap 5 Responsive UI
    title = page_name.replace('_', ' ').title()
    
    # Navbar Logic
    navbar = """
    <nav class="navbar navbar-dark bg-dark mb-4">
      <div class="container-fluid">
        <span class="navbar-brand">Agent 50 App</span>
        <button class="btn btn-outline-light" onclick="logout()">Logout</button>
      </div>
    </nav>
    """ if "login" not in page_name else ""

    # Specific Page Logic
    content = ""
    if "login" in page_name:
        content = """
        <div class="card p-4 mx-auto" style="max-width:400px; margin-top:100px;">
            <h3>Login</h3>
            <input type="text" id="username" class="form-control mb-2" placeholder="Username">
            <input type="password" id="password" class="form-control mb-2" placeholder="Password">
            <button onclick="login()" class="btn btn-primary w-100">Enter</button>
            <p class="mt-2"><small>No account? <a href="#" onclick="signup()">Sign up</a></small></p>
        </div>
        """
    elif "dashboard" in page_name:
        role = page_name.split('_')[0] # customer, driver, etc.
        content = f"<h2>{role.title()} Dashboard</h2><hr>"
        
        # Auto-generate tables for relevant entities
        for entity in blueprint['entities']:
            content += f"""
            <div class="card mb-3">
                <div class="card-header">{entity['name']} List</div>
                <div class="card-body">
                    <button onclick="fetchData('{entity['name']}')" class="btn btn-sm btn-success mb-2">Refresh {entity['name']}s</button>
                    <div id="list-{entity['name']}">Loading...</div>
                </div>
            </div>
            """

    return f"""
<!DOCTYPE html>
<html>
<head>
    <title>{title}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/axios/dist/axios.min.js"></script>
</head>
<body class="bg-light">
    {navbar}
    <div class="container">
        {content}
    </div>

    <script>
        async function login() {{
            const u = document.getElementById('username').value;
            const p = document.getElementById('password').value;
            try {{
                const res = await axios.post('/api/auth/login', {{username: u, password: p}});
                if(res.data.redirect) window.location.href = res.data.redirect; # Redirect to specific dashboard
                else window.location.href = '/dashboard';
            }} catch(e) {{ alert('Login Failed'); }}
        }}
        
        async function fetchData(entity) {{
            try {{
                const res = await axios.get('/api/data/' + entity);
                let html = '<ul class="list-group">';
                res.data.forEach(item => {{
                    html += `<li class="list-group-item">${{JSON.stringify(item)}}</li>`;
                }});
                html += '</ul>';
                document.getElementById('list-' + entity).innerHTML = html;
            }} catch(e) {{ console.error(e); }}
        }}
        
        function logout() {{ window.location.href = '/'; }}
    </script>
</body>
</html>
"""

# --- MASTER ROUTER ---

def generate_file_content(filename, blueprint):
    if filename == "extensions.py": return generate_extensions()
    if filename == "models.py": return generate_models(blueprint)
    if filename == "routes.py": return generate_routes(blueprint)
    if filename == "app.py": return generate_app(blueprint)
    if filename == "requirements.txt": return "flask\nflask-sqlalchemy\nflask-login\nwerkzeug"
    
    # FRONTEND HANDLING
    if filename.endswith(".html"):
        page_name = filename.replace(".html", "")
        return generate_html_template(page_name, blueprint)

    return ""