import json
import os
import time
from agent50_core.config import Config

def handle_feedback(feedback_text, project_name="latest_app"):
    """
    1. Logs the user's feedback.
    2. Updates project state to 'REVISION_NEEDED'.
    3. Appends feedback to a history log for the Builder to read.
    """
    print(f"\n📝 EVENT: Processing Feedback: '{feedback_text}'")

    # Paths
    memory_path = os.path.join(Config.MEMORY_DIR, "project_status.json")
    project_memory = os.path.join(Config.PROJECTS_DIR, project_name, "agent_memory.json")

    # 1. Update Global Status
    status = {}
    if os.path.exists(memory_path):
        with open(memory_path, "r") as f:
            try: status = json.load(f)
            except: pass

    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    
    status["last_update"] = timestamp
    status["current_status"] = "REVISION_PENDING"
    status["latest_feedback"] = feedback_text

    with open(memory_path, "w") as f:
        json.dump(status, f, indent=4)

    # 2. Update Project-Specific History (The "Context")
    # This ensures the agent remembers previous changes
    history_entry = {
        "timestamp": timestamp,
        "action": "USER_FEEDBACK",
        "instruction": feedback_text,
        "status": "QUEUED"
    }

    # Ensure project folder exists before writing memory
    if not os.path.exists(os.path.dirname(project_memory)):
        print("⚠️ Warning: Project folder not found. Feedback saved globally only.")
        return

    project_data = {"history": []}
    if os.path.exists(project_memory):
        with open(project_memory, "r") as f:
            try: project_data = json.load(f)
            except: pass
    
    project_data["history"].append(history_entry)

    with open(project_memory, "w") as f:
        json.dump(project_data, f, indent=4)

    print(f"✅ FEEDBACK LOGGED: '{feedback_text}' added to revision queue.")
    return True