import json
import os
from datetime import datetime
from agent50_core.config import Config

def handle_deployment_failure(error_log):
    print(f"\n⚡ EVENT: Deployment Failed! Analyzing Error...")

    # 1. Error ko categorize karo
    error_type = "UNKNOWN"
    fix_suggestion = "Check logs manually"

    if "ModuleNotFoundError" in error_log:
        error_type = "MISSING_LIBRARY"
        fix_suggestion = "Run: pip freeze > requirements.txt"
    elif "gunicorn: command not found" in error_log:
        error_type = "PROCFILE_ERROR"
        fix_suggestion = "Add 'gunicorn' to requirements.txt"
    elif "Internal Server Error" in error_log:
        error_type = "DATABASE_OR_CODE_ERROR"
        fix_suggestion = "Check Database connection URI"

    # 2. Memory mein save karo (Learning)
    failure_record = {
        "timestamp": str(datetime.now()),
        "error_raw": error_log[-100:], # Last 100 chars
        "type": error_type,
        "suggested_fix": fix_suggestion
    }

    failures_path = os.path.join(Config.MEMORY_DIR, "failures.json")
    
    # Load existing
    history = []
    if os.path.exists(failures_path):
        with open(failures_path, "r") as f:
            try: history = json.load(f)
            except: pass
    
    # Append new
    history.append(failure_record)
    
    # Save back
    with open(failures_path, "w") as f:
        json.dump(history, f, indent=4)

    print(f"🧠 MEMORY UPDATED: Learned from error '{error_type}'.")
    return fix_suggestion