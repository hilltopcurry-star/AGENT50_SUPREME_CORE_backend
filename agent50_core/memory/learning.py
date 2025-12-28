import json
import os
import time

class LearningEngine:
    def __init__(self):
        # Paths set karte hain
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.success_db = os.path.join(self.base_dir, "successful_patterns.json")
        self.failure_db = os.path.join(self.base_dir, "known_failures.json")
        
        # Files ensure karein
        self._init_db(self.success_db)
        self._init_db(self.failure_db)

    def _init_db(self, path):
        if not os.path.exists(path):
            with open(path, 'w') as f:
                json.dump([], f)

    def remember_success(self, project_name, app_type, stack):
        """Jab koi project successfully ban jaye, usay yaad rakho"""
        entry = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "project": project_name,
            "type": app_type,
            "stack_used": stack,
            "outcome": "SUCCESS"
        }
        self._save(self.success_db, entry)
        print(f"🧠 MEMORY: Stored successful pattern for '{app_type}'.")

    def remember_failure(self, error_msg, fix_applied):
        """Jab koi error aaye aur hum usay fix karein, to usay yaad rakho"""
        entry = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "error": error_msg,
            "fix": fix_applied,
            "confidence": "HIGH"
        }
        self._save(self.failure_db, entry)
        print(f"🧠 MEMORY: Learned new fix for error: '{error_msg[:30]}...'")

    def recall_fix(self, error_msg):
        """Check karo kya ye ghalti pehle kabhi hui hai?"""
        if not os.path.exists(self.failure_db): return None
        
        with open(self.failure_db, 'r') as f:
            failures = json.load(f)
            
        for f in failures:
            # Agar error message match ho jaye
            if f["error"] in error_msg or error_msg in f["error"]:
                print(f"💡 RECALL: I have seen this error before! Applying known fix: {f['fix']}")
                return f["fix"]
        return None

    def _save(self, path, data):
        current_data = []
        if os.path.exists(path):
            with open(path, 'r') as f:
                try: current_data = json.load(f)
                except: pass
        
        current_data.append(data)
        
        with open(path, 'w') as f:
            json.dump(current_data, f, indent=4)