import json
import os
import time

class MemoryBank:
    def __init__(self):
        # Memory storage location
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.memory_path = os.path.join(current_dir, "memory_data")
        os.makedirs(self.memory_path, exist_ok=True)
        
        # Files
        self.project_log_file = os.path.join(self.memory_path, "projects_log.json")
        self.error_log_file = os.path.join(self.memory_path, "error_patterns.json")
        
        # Init Files if not exist
        self._init_file(self.project_log_file, [])
        self._init_file(self.error_log_file, {})

    def _init_file(self, filepath, default_data):
        if not os.path.exists(filepath):
            with open(filepath, 'w') as f:
                json.dump(default_data, f, indent=4)

    def remember_project(self, blueprint, status="SUCCESS"):
        """Save successful build details"""
        logs = self.recall_projects()
        
        entry = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "project_name": blueprint.get("project_name"),
            "type": blueprint.get("archetype"),
            "stack": blueprint.get("stack"),
            "status": status
        }
        
        logs.append(entry)
        
        with open(self.project_log_file, 'w') as f:
            json.dump(logs, f, indent=4)
        print(f"🧠 MEMORY: Project '{entry['project_name']}' saved to permanent logs.")

    def recall_projects(self):
        """Read past projects"""
        try:
            with open(self.project_log_file, 'r') as f:
                return json.load(f)
        except:
            return []

    def log_error(self, error_msg):
        """Remember mistakes"""
        data = {}
        try:
            with open(self.error_log_file, 'r') as f:
                data = json.load(f)
        except: pass
        
        count = data.get(error_msg, 0)
        data[error_msg] = count + 1
        
        with open(self.error_log_file, 'w') as f:
            json.dump(data, f, indent=4)