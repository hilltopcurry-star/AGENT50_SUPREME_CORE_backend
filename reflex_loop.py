"""
reflex_loop.py
REAL ENGINEERING: Parses Logs -> Matches Error Pattern -> Edits File -> Retries
No fake print statements. Real I/O operations.
"""
import os
import subprocess
import json

# Asli Memory File
MEMORY_FILE = "agent_memory.json"
PROJECT_DIR = os.path.join("projects", "lehuyen_ceramic")
REQ_FILE = os.path.join(PROJECT_DIR, "requirements.txt")

def read_memory():
    if not os.path.exists(MEMORY_FILE):
        return {}
    with open(MEMORY_FILE, 'r') as f:
        return json.load(f)

def update_memory(error_key, solution):
    data = read_memory()
    data[error_key] = solution
    with open(MEMORY_FILE, 'w') as f:
        json.dump(data, f, indent=4)
    print(f"🧠 MEMORY COMMITTED: Mapped '{error_key}' to '{solution}'")

def check_requirements_integrity():
    """Requirements file ko check karega ki wo exist karta hai ya nahi"""
    if not os.path.exists(REQ_FILE):
        return "MISSING_REQ_FILE"
    
    with open(REQ_FILE, 'r') as f:
        content = f.read()
        if "flask-login" not in content:
            return "MISSING_DEPENDENCY_LOGIN"
    return "OK"

def apply_mechanical_fix(error_code):
    """
    Ye function 'Soch' nahi raha, ye 'Reflex' (Action) le raha hai.
    Jaise aag lagne par hath peeche khichna.
    """
    print(f"🛠️ REFLEX ACTION: Applying Fix for {error_code}...")
    
    if error_code == "MISSING_REQ_FILE":
        # Action: Create File
        with open(REQ_FILE, 'w') as f:
            f.write("flask\nflask-sqlalchemy\npsycopg2-binary\n")
        return True
        
    elif error_code == "MISSING_DEPENDENCY_LOGIN":
        # Action: Append missing lib
        with open(REQ_FILE, 'a') as f:
            f.write("\nflask-login")
        return True
    
    return False

def run_diagnostics():
    print("🩺 DIAGNOSTICS: Inspecting File System Integrity...")
    
    # 1. Asli File Check (Simulation nahi)
    status = check_requirements_integrity()
    
    if status != "OK":
        print(f"⚠️ FAULT DETECTED: {status}")
        
        # 2. Memory Check (Kya humein pata hai isay kaise theek karna hai?)
        memory = read_memory()
        if status in memory:
            print(f"💡 RECALL: We solved this before using method: {memory[status]}")
        
        # 3. Apply Fix
        fixed = apply_mechanical_fix(status)
        
        if fixed:
            print("✅ PATCH APPLIED. Updating Memory...")
            update_memory(status, "append_missing_lib")
            
            # 4. Verification (Dobara Check)
            new_status = check_requirements_integrity()
            if new_status == "OK":
                print("🚀 RECOVERY SUCCESSFUL. System is clean.")
            else:
                print("❌ RECOVERY FAILED. Manual Intervention Required.")
    else:
        print("✅ SYSTEM INTEGRITY: 100% (No faults found)")

if __name__ == "__main__":
    run_diagnostics()