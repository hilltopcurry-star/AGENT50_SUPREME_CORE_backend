"""
reset_tool.py
Description: EMERGENCY TOOL. Resets the admin password to 'director123'.
Run this only if the user forgets their password.
"""
from werkzeug.security import generate_password_hash
from sqlalchemy import create_engine, text

# Database Connection (Neon)
DB_URL = "postgresql://neondb_owner:npg_1M9UTVEHJrGt@ep-falling-salad-ah3w24sg-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require"

def reset_password():
    print("⚠️  EMERGENCY PASSWORD RESET TOOL ⚠️")
    confirm = input("Are you sure you want to reset 'admin' password to 'director123'? (yes/no): ")
    
    if confirm.lower() == "yes":
        # Create a secure hash for "director123"
        new_hash = generate_password_hash("director123", method='pbkdf2:sha256')
        
        engine = create_engine(DB_URL)
        with engine.connect() as conn:
            # SQL Command to force update
            sql = text("UPDATE user SET password = :pw WHERE username = 'admin'")
            conn.execute(sql, {"pw": new_hash})
            conn.commit()
            
        print("\n✅ SUCCESS! Password has been reset to: director123")
        print("👉 Tell the user to login and change it immediately.")
    else:
        print("❌ Operation Cancelled.")

if __name__ == "__main__":
    reset_password()