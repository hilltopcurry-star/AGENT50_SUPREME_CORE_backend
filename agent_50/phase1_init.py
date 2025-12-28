import json
import datetime
import hashlib
import os

def initialize_phase1():
    """Initialize Phase 1 with permanent memory tracking"""
    
    # Load or create memory
    if os.path.exists('agent_memory.json'):
        with open('agent_memory.json', 'r') as f:
            memory = json.load(f)
    else:
        memory = {"system_builds": {}}
    
    # Create food delivery system tracking
    build_id = hashlib.md5(str(datetime.datetime.now()).encode()).hexdigest()[:8]
    memory["current_build"] = {
        "id": build_id,
        "project": "food_delivery_system",
        "phase": "database_and_backend",
        "started_at": datetime.datetime.now().isoformat(),
        "completed_steps": [],
        "generated_files": [],
        "errors": [],
        "schema_hash": None,
        "last_updated": datetime.datetime.now().isoformat()
    }
    
    # Save memory immediately
    with open('agent_memory.json', 'w') as f:
        json.dump(memory, f, indent=2)
    
    print(f"✅ Memory Initialized. Build ID: {build_id}")
    return build_id

if __name__ == "__main__":
    initialize_phase1()