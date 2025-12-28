"""
Deploy Validator.
Checks if the project is ready for deployment before attempting push.
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple
from memory.memory_manager import MemoryManager

class DeployValidator:
    """Validates deployment readiness."""
    
    def __init__(self, memory: MemoryManager = None):
        self.logger = logging.getLogger("Agent50.Deployer.Validator")
        self.memory = memory
        
    def validate_project(self, project_path: Path) -> Tuple[bool, List[str], Dict[str, Any]]:
        """
        Validate project for specific platform (Standard Interface).
        Returns: (is_valid, errors, validation_data)
        """
        self.logger.info(f"Validating project deployment readiness: {project_path}")
        errors = []
        validation_data = {"project_path": str(project_path)}
        
        if not project_path.exists():
            return False, ["Project directory does not exist"], validation_data
            
        # Run specific checks
        render_errors = self._validate_render(project_path)
        errors.extend(render_errors)
        
        # Populate validation data
        validation_data["has_backend"] = (project_path / "backend").exists()
        validation_data["has_frontend"] = (project_path / "frontend").exists()
        
        # Basic type detection
        if (project_path / "backend" / "requirements.txt").exists():
            validation_data["backend_type"] = "python"
        elif (project_path / "requirements.txt").exists():
            validation_data["backend_type"] = "python"
        else:
            validation_data["backend_type"] = "unknown"
            
        return len(errors) == 0, errors, validation_data
    
    def _validate_render(self, path: Path) -> List[str]:
        """Validate for Render.com."""
        errors = []
        
        # 1. Check for build files
        has_reqs = (path / "requirements.txt").exists() or (path / "backend" / "requirements.txt").exists()
        has_package = (path / "package.json").exists() or (path / "frontend" / "package.json").exists()
        
        if not (has_reqs or has_package):
            errors.append("Missing dependency definition (requirements.txt or package.json)")
            
        return errors