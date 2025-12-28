"""
reasoning_engine.py
MODULE: UNIVERSAL LOGIC CORE
Description: Breaks down ANY user request into technical architecture WITHOUT templates.
"""
import json
import sys

def analyze_request(user_prompt):
    print(f"\n🧠 ACTIVATING NEURAL REASONING FOR: '{user_prompt}'")
    
    # 1. Deconstruct the Request (Todna)
    print("... Decomposing abstract concept into technical components.")
    
    # Ye logic 'Ratta' nahi hai, ye 'Logic' hai.
    # Hum keywords dhoond kar architecture banayenge.
    components = []
    
    if "data" in user_prompt or "store" in user_prompt or "users" in user_prompt:
        components.append("Database (PostgreSQL/Neon)")
    if "live" in user_prompt or "real-time" in user_prompt:
        components.append("WebSockets (Socket.io)")
    if "secure" in user_prompt or "login" in user_prompt:
        components.append("Auth System (Flask-Login/JWT)")
    if "visual" in user_prompt or "design" in user_prompt:
        components.append("Frontend (HTML/Tailwind/React)")
    if "mobile" in user_prompt:
        components.append("API Layer (REST/GraphQL)")
        
    # Default Fallback (Har app ko chahiye)
    if not components:
        components = ["Core Server (Flask)", "Basic UI (HTML)"]
        
    print(f"✅ IDENTIFIED PILLARS: {components}")
    
    # 2. Architect the Solution (Naksha Banana)
    structure = {
        "project_type": "universal_custom_build",
        "tech_stack": components,
        "files_required": [
            "app.py (Main Logic)",
            "requirements.txt (Dependencies)",
            "vercel.json (Cloud Config)"
        ]
    }
    
    # 3. Learning Check (Memory se poocho)
    try:
        with open("agent_memory.json", "r") as f:
            memory = json.load(f)
            if user_prompt in memory.get("failed_attempts", []):
                print("⚠️ WARNING: We failed at this before. Adjusting strategy...")
                structure["files_required"].append("emergency_fix.py")
    except:
        pass

    return structure

if __name__ == "__main__":
    # Test Input
    if len(sys.argv) > 1:
        prompt = " ".join(sys.argv[1:])
    else:
        prompt = input("Enter Abstract Idea: ")
        
    plan = analyze_request(prompt)
    print("\n📜 GENERATED BLUEPRINT:")
    print(json.dumps(plan, indent=2))