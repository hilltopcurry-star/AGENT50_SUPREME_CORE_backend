import json
import datetime
import hashlib
import os

def update_memory_phase1_step1():
    """Update memory after database schema generation"""
    
    if not os.path.exists('agent_memory.json'):
        print("❌ Memory file not found. Initialize first.")
        return

    with open('agent_memory.json', 'r') as f:
        memory = json.load(f)
    
    if "current_build" not in memory:
         print("❌ No active build found.")
         return

    build = memory["current_build"]
    
    # Calculate Schema Hash for Integrity
    schema_hash = "N/A"
    if os.path.exists('database/schema.sql'):
        with open('database/schema.sql', 'r') as f:
             schema_hash = hashlib.md5(f.read().encode()).hexdigest()

    # Log Completion
    step_record = {
        "step": "database_schema_generation",
        "timestamp": datetime.datetime.now().isoformat(),
        "files_generated": [
            "database/schema.sql",
            "database/migrations/001_initial_schema.py"
        ],
        "schema_hash": schema_hash
    }
    
    build["completed_steps"].append(step_record)
    build["generated_files"].extend([
        "database/schema.sql",
        "database/migrations/001_initial_schema.py"
    ])
    
    build["last_updated"] = datetime.datetime.now().isoformat()
    
    with open('agent_memory.json', 'w') as f:
        json.dump(memory, f, indent=2)
    
    print("✅ Memory updated: Phase 1 (Database) Marked Complete.")

if __name__ == "__main__":
    update_memory_phase1_step1()