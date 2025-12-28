"""
Dependency Manager for Agent 50.
Generates requirements.txt and package.json based on blueprint.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any

class DependencyManager:
    """Manages project dependencies."""
    
    def __init__(self):
        self.logger = logging.getLogger("Agent50.Builder.Dependencies")
    
    def generate(self, blueprint: Dict[str, Any], output_path: Path):
        """
        Generate dependency files.
        
        Args:
            blueprint: The architectural blueprint containing dependency lists.
            output_path: The root path of the generated project.
        """
        self.logger.info("Generating dependency files...")
        
        dependencies = blueprint.get("dependencies", {})
        
        # 1. Generate Backend Dependencies (requirements.txt)
        backend_deps = dependencies.get("backend", [])
        if backend_deps:
            self._generate_requirements_txt(backend_deps, output_path)
            
        # 2. Generate Frontend Dependencies (package.json)
        frontend_deps = dependencies.get("frontend", [])
        if frontend_deps:
            # We also need basic info for package.json (name, description)
            project_info = {
                "name": blueprint.get("name", "app").lower().replace(" ", "-"),
                "description": blueprint.get("description", ""),
                "version": "1.0.0"
            }
            self._generate_package_json(frontend_deps, project_info, output_path)
            
        self.logger.info("Dependency generation complete")

    def _generate_requirements_txt(self, dependencies: list, output_path: Path):
        """Generate requirements.txt for Python backend."""
        backend_dir = output_path / "backend"
        if not backend_dir.exists():
            # If backend folder doesn't exist (e.g. flat structure), use root
            backend_dir = output_path
            
        requirements_path = backend_dir / "requirements.txt"
        
        lines = []
        for dep in dependencies:
            name = dep.get("name")
            version = dep.get("version")
            if name:
                if version:
                    lines.append(f"{name}=={version}")
                else:
                    lines.append(name)
        
        # Add Gunicorn for production if not present
        if not any("gunicorn" in line for line in lines):
            lines.append("gunicorn==21.2.0")

        content = "\n".join(lines)
        
        # Ensure directory exists before writing
        backend_dir.mkdir(parents=True, exist_ok=True)
        requirements_path.write_text(content)
        self.logger.debug(f"Generated requirements.txt at {requirements_path}")

    def _generate_package_json(self, dependencies: list, project_info: Dict[str, str], output_path: Path):
        """Generate package.json for Node.js frontend."""
        frontend_dir = output_path / "frontend"
        
        # If frontend folder doesn't exist yet, we assume the generator hasn't run or failed,
        # but we should create the dir to avoid error.
        frontend_dir.mkdir(parents=True, exist_ok=True)
        
        package_json_path = frontend_dir / "package.json"
        
        # Construct dependencies object
        deps_obj = {}
        for dep in dependencies:
            name = dep.get("name")
            version = dep.get("version", "latest")
            if name:
                deps_obj[name] = version

        # Basic package.json structure
        package_data = {
            "name": project_info["name"],
            "version": project_info["version"],
            "private": True,
            "description": project_info["description"],
            "scripts": {
                "dev": "vite",
                "build": "vite build",
                "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0",
                "preview": "vite preview"
            },
            "dependencies": deps_obj,
            "devDependencies": {
                "@types/node": "^20.0.0",
                "@types/react": "^18.2.0",
                "@types/react-dom": "^18.2.0",
                "autoprefixer": "^10.4.0",
                "postcss": "^8.4.0",
                "tailwindcss": "^3.3.0",
                "typescript": "^5.0.0",
                "vite": "^5.0.0"
            }
        }
        
        with open(package_json_path, 'w') as f:
            json.dump(package_data, f, indent=2)
            
        self.logger.debug(f"Generated package.json at {package_json_path}")