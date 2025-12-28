"""
Docker deployment adapter for Agent 50.
"""

import logging
import subprocess
from pathlib import Path
from typing import Dict, Any
from memory.memory_manager import MemoryManager

class DockerAdapter:
    """Adapter for local Docker deployment."""
    
    def __init__(self, memory: MemoryManager):
        self.memory = memory
        self.logger = logging.getLogger("Agent50.Deployer.Docker")
        
    def deploy(self, project_path: Path, environment: str = "production") -> Dict[str, Any]:
        """Deploy locally using Docker Compose."""
        self.logger.info(f"Starting Local Docker deployment: {project_path}")
        
        # 1. Check Docker
        if not self._check_docker():
            return {"success": False, "error": "Docker daemon not running"}
            
        # 2. Ensure Dockerfile/Compose exists
        if not (project_path / "docker-compose.yml").exists():
             return {"success": False, "error": "docker-compose.yml missing"}

        # 3. Build & Run
        try:
            # Build
            self.logger.info("Building Docker images...")
            subprocess.run(["docker-compose", "build"], cwd=project_path, check=True)
            
            # Up
            self.logger.info("Starting containers...")
            subprocess.run(["docker-compose", "up", "-d"], cwd=project_path, check=True)
            
            return {"success": True, "message": "Docker deployment successful (running in background)"}
            
        except subprocess.CalledProcessError as e:
            return {"success": False, "error": f"Docker command failed: {e}"}
            
    def _check_docker(self) -> bool:
        """Check if Docker is running."""
        try:
            subprocess.run(["docker", "info"], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False