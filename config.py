import os

# --- PART 1: FLASK APP KE LIYE ---
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'bhai-ka-super-secret-key'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///site.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

# --- PART 2: DATABASE FILE KE LIYE (Jugaad) ---
class SimpleSettings:
    # Ye wahi same database path hai taake dono ek hi jagah connect hon
    DATABASE_URL = 'sqlite:///site.db'

# Ye line database.py ko shant kar degi
settings = SimpleSettings()