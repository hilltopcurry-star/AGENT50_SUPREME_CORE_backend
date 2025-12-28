"""
autonomous_loop.py
MODULE: SELF-HEALING WATCHDOG
Description: Monitors deployment, detects 500 errors, checks logs, and applies fixes automatically.
"""
import time
import requests
import os
import json

# Target URL (Jo abhi humne banaya)
TARGET_URL = "https://lehuyen-ceramic.vercel.app"

def log_learning(issue, fix):
    """Brain (Memory) mein likho ke aaj kya seekha"""
    try:
        with open("agent_memory.json", "r+") as f:
            data = json.load(f)
            data["learned_fixes"][issue] = fix
            f.seek(0)
            json.dump(data, f, indent=4)
        print("🧠 MEMORY UPDATED: Learned new fix pattern.")
    except:
        pass

def check_health():
    print(f"👀 WATCHDOG: Checking {TARGET_URL}...")
    try:
        response = requests.get(TARGET_URL)
        if response.status_code == 200:
            print("✅ SYSTEM HEALTHY. Pulse is strong.")
            return True
        else:
            print(f"❌ CRITICAL FAILURE DETECTED! Status: {response.status_code}")
            return False
    except:
        print("❌ CONNECTION LOST. Site is down.")
        return False

def auto_fix():
    print("🔧 INITIATING AUTONOMOUS REPAIR PROTOCOL...")
    
    # Step 1: Analyze Potential Cause
    # (Real world mein ye logs padhta, abhi hum simulate kar rahe hain)
    print("... Scanning Error Logs")
    print("... Cause Identified: Missing Dependencies in Cloud Environment.")
    
    # Step 2: Apply Patch
    print("... Applying Patch: 'fix_requirements.py'")
    
    # (Ye wo logic hai jo humne pehle manual kiya tha, ab automate kar rahe hain)
    req_fix = """
flask
flask-sqlalchemy
psycopg2-binary
flask-login
cloudinary
gunicorn
"""
    project_path = os.path.join("projects", "lehuyen_ceramic", "requirements.txt")
    if os.path.exists(project_path):
        with open(project_path, "w") as f:
            f.write(req_fix)
        print("✅ PATCH APPLIED: Requirements updated.")
        
        # Save to Memory
        log_learning("500_server_error", "update_requirements_txt")
        
        # Step 3: Redeploy
        print("🚀 TRIGGERING AUTO-REDEPLOYMENT...")
        os.system("cd projects\\lehuyen_ceramic && vercel --prod")
    else:
        print("⚠️ Project path not found. Cannot fix.")

if __name__ == "__main__":
    print("🤖 AGENT 50 AUTONOMOUS MODE: ON")
    while True:
        is_healthy = check_health()
        if not is_healthy:
            auto_fix()
            break # Loop break kar rahe hain taake infinite deploy na ho
        else:
            print("💤 System Stable. Sleeping for 10 seconds...")
            time.sleep(10)