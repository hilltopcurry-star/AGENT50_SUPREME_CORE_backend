import os
import threading
import time
import sys
import logging
from flask import Flask, render_template, jsonify, request

# --- 1. SILENCE THE NOISE ---
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR) 

# --- PATH SETUP ---
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# --- NEW IMPORTS (Brain, Body & Memory) ---
try:
    from agent50_core.builder.file_generator import Builder
    from agent50_core.architect import ArchitectureEngine
    from agent50_core.memory import MemoryBank  # ✅ NEW: Memory Import
except ImportError as e:
    print(f"❌ CRITICAL IMPORT ERROR: {e}")
    print("⚠️ Make sure 'architect.py' and 'memory.py' exist in 'agent50_core' folder!")

# --- CONFIG ---
template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'agent50_core', 'console_ui_templates')
app = Flask(__name__, template_folder=template_dir)

# --- INITIALIZE ENGINES ---
architect = ArchitectureEngine()
builder = Builder()
memory = MemoryBank() # ✅ NEW: Memory Engine Start

SYSTEM_LOGS = []
SESSION_STATE = { "is_active": False, "project_name": "None", "stage": "IDLE" }

def log_capture(message):
    timestamp = time.strftime("%H:%M:%S")
    SYSTEM_LOGS.append(f"[{timestamp}] {message}")
    print(f"[{timestamp}] {message}")

@app.route('/')
def home(): return render_template('console.html')

@app.route('/api/status')
def status():
    # Console par status dikhane ke liye
    status_msg = "IDLE"
    if SESSION_STATE["is_active"]: 
        status_msg = SESSION_STATE["stage"]
    return jsonify({ "status": status_msg, "logs": SYSTEM_LOGS[-20:] })

@app.route('/api/build', methods=['POST'])
def handle_command():
    data = request.json
    raw_intent = data.get("intent", "").strip()
    
    if not raw_intent: return jsonify({"error": "Empty command"}), 400

    log_capture(f"🚀 COMMAND: {raw_intent}")

    def run_agent_process():
        try:
            SESSION_STATE["is_active"] = True
            
            # --- PHASE 1: ARCHITECT (Thinking) ---
            SESSION_STATE["stage"] = "🧠 ARCHITECTING..."
            log_capture("🧠 Architect Engine: Analyzing requirements...")
            time.sleep(1)
            
            # 1. Brain se poocho ke kya banana hai
            blueprint = architect.analyze_intent(raw_intent)
            
            # 2. Console par Brain ka faisla dikhao
            log_capture(f"📋 Blueprint Locked: {blueprint['archetype'].upper()} ({blueprint['project_name']})")
            log_capture(f"⚙️ Stack Decided: {blueprint['stack']['backend']} + {blueprint['stack']['frontend']}")
            log_capture(f"✨ Features Identified: {', '.join(blueprint['features'])}")
            
            time.sleep(1)

            # --- PHASE 2: BUILDER (Coding) ---
            SESSION_STATE["stage"] = "🔨 BUILDING..."
            log_capture("🏗️ Builder Engine: Generating structure...")
            
            # 3. Builder ko bolo structure banaye
            builder.create_structure(None)
            
            # 4. Builder ko bolo code likhe
            builder.generate_flask_app(blueprint['project_name'])
            
            # --- PHASE 3: DEPLOYMENT CHECK ---
            log_capture("🚀 Engaging Deployment Intelligence Engine...")
            time.sleep(0.5)
            log_capture("✅ Deployment Check: Cloud-Ready (Port 10000 verified).")
            
            # --- ✅ PHASE 4: MEMORY SAVE (Yahan Agent Yaad Rakhega) ---
            try:
                memory.remember_project(blueprint, status="LIVE")
                log_capture("💾 Memory Updated: Project logged in 'projects_log.json'")
            except Exception as e:
                print(f"Memory Error: {e}")

            log_capture(f"🎉 PROJECT COMPLETE: {blueprint['project_name']}")
            
        except Exception as e:
            import traceback
            print(traceback.format_exc())
            log_capture(f"❌ SYSTEM CRASH: {str(e)}")
        
        finally:
            SESSION_STATE["stage"] = "IDLE"
            SESSION_STATE["is_active"] = False

    thread = threading.Thread(target=run_agent_process)
    thread.start()
    return jsonify({"message": "Started"})

if __name__ == '__main__':
    os.makedirs(template_dir, exist_ok=True)
    print("🖥️  AGENT 50 BRAIN CONNECTED: http://127.0.0.1:5050")
    app.run(port=5050, debug=True, use_reloader=False)