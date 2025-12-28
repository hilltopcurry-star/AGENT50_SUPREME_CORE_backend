import json
import os
import sys

# Paths setup
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RULES_PATH = os.path.join(BASE_DIR, "agent_50", "frontend_generator_rules.json")
MEMORY_PATH = os.path.join(BASE_DIR, "agent_memory.json")

def activate_universal_rules():
    print("🔄 ACTIVATING UNIVERSAL FRONTEND RULES...")
    
    # 1. Check if Rules File Exists
    if not os.path.exists(RULES_PATH):
        print(f"❌ ERROR: Rules file not found at {RULES_PATH}")
        print("   Please save 'frontend_generator_rules.json' first.")
        return

    # 2. Validate JSON Structure
    try:
        with open(RULES_PATH, 'r') as f:
            rules = json.load(f)
            
        if not rules.get("non_negotiable"):
            print("❌ INVALID RULES: 'non_negotiable' flag missing.")
            return
            
        print("✅ Rules File Validated: Universal Frontend Generator v1.0")
        
    except json.JSONDecodeError:
        print("❌ ERROR: Invalid JSON format in rules file.")
        return

    # 3. Inject into Permanent Memory
    if os.path.exists(MEMORY_PATH):
        with open(MEMORY_PATH, 'r') as f:
            memory = json.load(f)
    else:
        memory = {"system_builds": {}}

    # Updating Memory Core
    memory["active_protocols"] = {
        "frontend_engine": "universal_rules_v1",
        "rules_source": RULES_PATH,
        "status": "ACTIVE",
        "policy": "NO_MANUAL_FRONTEND"
    }
    
    # Save back to memory
    with open(MEMORY_PATH, 'w') as f:
        json.dump(memory, f, indent=2)

    print("\n" + "="*40)
    print("🔒 SYSTEM MODE: ENABLED")
    print("="*40)
    print("✅ Frontend Rules have been fused with Agent Memory.")
    print("✅ From now on, Agent 50 will NOT ask for frontend code.")
    print("✅ It will AUTO-GENERATE based on 'frontend_generator_rules.json'.")

if __name__ == "__main__":
    activate_universal_rules()