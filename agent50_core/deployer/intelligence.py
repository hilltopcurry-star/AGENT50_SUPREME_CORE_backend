import os

class DeploymentIntelligence:
    def __init__(self, project_path):
        self.project_path = project_path
        self.requirements_path = os.path.join(project_path, "requirements.txt")
        self.procfile_path = os.path.join(project_path, "Procfile")
        self.runtime_path = os.path.join(project_path, "runtime.txt")
        self.app_file = os.path.join(project_path, "app.py")

    def make_deployable(self):
        """Runs all checks to make the app ready for Render/Heroku"""
        logs = []
        logs.append(self._ensure_gunicorn())
        logs.append(self._generate_procfile())
        logs.append(self._generate_runtime())
        logs.append(self._fix_port_binding())
        return [l for l in logs if l] # Return only non-empty logs

    def _ensure_gunicorn(self):
        """Checks if Gunicorn (Production Server) is in requirements"""
        if not os.path.exists(self.requirements_path):
            return "⚠️ Requirements.txt missing!"
        
        with open(self.requirements_path, "r") as f:
            content = f.read()
        
        if "gunicorn" not in content:
            with open(self.requirements_path, "a") as f:
                f.write("\ngunicorn\n")
            return "✅ AUTO-FIX: Added 'gunicorn' to dependencies (Critical for Production)."
        return None

    def _generate_procfile(self):
        """Creates Procfile for Render"""
        # Procfile batata hai ke app start kaise karni hai
        if not os.path.exists(self.procfile_path):
            with open(self.procfile_path, "w") as f:
                f.write("web: gunicorn app:app")
            return "✅ CONFIG: Generated 'Procfile' for Render deployment."
        return None

    def _generate_runtime(self):
        """Sets Python version"""
        if not os.path.exists(self.runtime_path):
            with open(self.runtime_path, "w") as f:
                f.write("python-3.9.18") # Stable version
            return "✅ CONFIG: Generated 'runtime.txt' (Python 3.9)."
        return None

    def _fix_port_binding(self):
        """
        Scans app.py to ensure it uses os.environ.get('PORT').
        If it finds hardcoded 'app.run(debug=True)', it REPLACES it automatically.
        """
        if not os.path.exists(self.app_file): return None

        with open(self.app_file, "r") as f:
            code = f.read()

        # Check agar code mein pehle se PORT logic nahi hai
        if "os.environ.get" not in code and "app.run" in code:
            # Production Ready Code Snippet
            production_logic = """
if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
"""
            # Replace common unsafe patterns
            if "app.run(debug=True)" in code:
                code = code.replace("app.run(debug=True)", "app.run()")
            
            # Append/Replace logic (Simple implementation: Append robust logic at bottom)
            # Behtar approach: Hum poora main block replace karte hain agar wo simple hai
            # Lekin safety ke liye, hum user ko warn karte hain ya safe inject karte hain.
            
            # Let's do a safe replace of the final block if it exists
            lines = code.splitlines()
            new_lines = []
            replaced = False
            for line in lines:
                if "app.run" in line and "__main__" in code:
                    # Skip old run command
                    continue 
                new_lines.append(line)
            
            final_code = "\n".join(new_lines) + production_logic
            
            with open(self.app_file, "w") as f:
                f.write(final_code)
            
            return "✅ AUTO-FIX: Replaced hardcoded port with Cloud-Ready 'os.environ.get(PORT)'."
        
        return None