import os
from pathlib import Path

class AutoFixer:
    def __init__(self, project_path):
        self.project_path = Path(project_path)

    def apply_fix(self, error_report):
        """
        Error type ke hisaab se dawa (fix) lagata hai.
        """
        e_type = error_report.get("error_type")
        details = error_report.get("details")

        print(f"🛠️ FIXER: Attempting to fix {e_type}...")

        if e_type == "MISSING_DEPENDENCY":
            self.add_requirement(details)
            return "Added missing package to requirements.txt"

        elif e_type == "PROCFILE_ISSUE":
            self.create_procfile()
            return "Created valid Procfile"

        return "No auto-fix available. Manual check required."

    def add_requirement(self, package_name):
        req_path = self.project_path / "requirements.txt"
        with open(req_path, "a") as f:
            f.write(f"\n{package_name}")
        print(f"✅ Added {package_name} to requirements.txt")

    def create_procfile(self):
        proc_path = self.project_path / "Procfile"
        with open(proc_path, "w") as f:
            f.write("web: gunicorn app:app")
        print("✅ Recreated Procfile")