import json
import os
from agent50_core.config import Config

def handle_feedback(feedback_text):
    print(f"\n⚡ EVENT: User Feedback Received: '{feedback_text}'")

    status_path = os.path.join(Config.MEMORY_DIR, "project_status.json")
    
    # Status update karo
    status = {}
    if os.path.exists(status_path):
        with open(status_path, "r") as f:
            status = json.load(f)

    status["last_feedback"] = feedback_text
    status["status"] = "REVISION_NEEDED"

    with open(status_path, "w") as f:
        json.dump(status, f, indent=4)

    print("📝 STATUS UPDATED: Marked project for revision.")