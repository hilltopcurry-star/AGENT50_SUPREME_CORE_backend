"""
Render.com deployment adapter for Agent 50.
Handles Render API integration and service management.
"""

import json
import logging
import os
import time
import requests
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from memory.memory_manager import MemoryManager
from .deploy_validator import DeployValidator

class RenderAdapter:
    """Render.com deployment adapter."""
    
    def __init__(self, memory: MemoryManager):
        self.memory = memory
        self.logger = logging.getLogger("Agent50.Deployer.Render")
        self.validator = DeployValidator(memory)
        
        # Render API configuration
        self.api_key = os.environ.get("RENDER_API_KEY")
        self.api_base = "https://api.render.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        if not self.api_key:
            self.logger.warning("RENDER_API_KEY not set in environment")

    def deploy(self, project_path: Path, service_type: str = "web", auto_scale: bool = True) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Deploy project to Render.com.
        """
        self.logger.info(f"Starting deployment to Render: {project_path}")
        
        # 1. Validate
        is_valid, errors, val_data = self.validator.validate_project(project_path)
        if not is_valid:
            return False, f"Validation failed: {errors}", {}

        # 2. Prepare (Generate render.yaml)
        if not self._prepare_deployment(val_data, project_path):
             return False, "Failed to generate render.yaml", {}

        # 3. Trigger (Mock logic if no API key, else real call)
        if not self.api_key:
            return True, "Deployment config generated (API Key missing, skipping push)", {"config_path": str(project_path / "render.yaml")}

        # Real API logic would go here (Create Service -> Push)
        # For this version, we focus on generating the correct configuration
        return True, "Render configuration ready. Push to GitHub to deploy.", {}

    def _prepare_deployment(self, validation_data: Dict[str, Any], project_path: Path) -> bool:
        """Generate render.yaml"""
        try:
            render_config = self._generate_render_yaml(validation_data, project_path.name)
            yaml_path = project_path / "render.yaml"
            with open(yaml_path, 'w') as f:
                yaml.dump(render_config, f, default_flow_style=False)
            return True
        except Exception as e:
            self.logger.error(f"Error preparing deployment: {e}")
            return False

    def _generate_render_yaml(self, val_data: Dict[str, Any], project_name: str) -> Dict[str, Any]:
        """Generate render.yaml content."""
        services = []
        project_slug = project_name.lower().replace(" ", "-")
        
        # Backend Service
        if val_data.get("has_backend"):
            services.append({
                "type": "web",
                "name": f"{project_slug}-api",
                "env": "python",
                "buildCommand": "pip install -r requirements.txt",
                "startCommand": "gunicorn main:app --bind 0.0.0.0:$PORT",
                "envVars": [{"key": "PYTHON_VERSION", "value": "3.11.0"}]
            })
            
        # Frontend Service
        if val_data.get("has_frontend"):
            services.append({
                "type": "web",
                "name": f"{project_slug}-web",
                "env": "node",
                "buildCommand": "npm install && npm run build",
                "startCommand": "npm start",
                "envVars": [{"key": "NODE_VERSION", "value": "20"}]
            })
            
        return {"services": services}