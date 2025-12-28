from flask import Flask
from extensions import db, login_manager
from models import User
from auth import auth as auth_bp
from middleware import rate_limit_check

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'PostgreSQL_Neon'
app.config['SECRET_KEY'] = 'agent50-prod-key'
db.init_app(app)
login_manager.init_app(app)
app.register_blueprint(auth_bp, url_prefix='/auth')
app.before_request(rate_limit_check)

with app.app_context(): db.create_all()
@app.route('/')
def home(): return 'Agent 50 - Domain Active'
if __name__ == '__main__': app.run(debug=True)