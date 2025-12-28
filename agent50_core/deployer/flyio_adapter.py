"""
Fly.io deployment adapter for Agent 50.
"""

import logging
import subprocess
from pathlib import Path
from typing import Dict, Any, Tuple
from memory.memory_manager import MemoryManager

class FlyIOAdapter:
    """Fly.io deployment adapter."""
    
    def __init__(self, memory: MemoryManager):
        self.memory = memory
        self.logger = logging.getLogger("Agent50.Deployer.FlyIO")
        
    def deploy(self, project_path: Path, environment: str = "production") -> Dict[str, Any]:
        """Deploy to Fly.io."""
        self.logger.info(f"Preparing Fly.io deployment for {project_path}")
        
        # 1. Check for flyctl
        if not self._check_flyctl():
            return {"success": False, "error": "flyctl not found in PATH"}
            
        # 2. Generate fly.toml
        self._generate_fly_toml(project_path)
        
        # 3. Launch/Deploy (Simulation for safety)
        # In a real run, we would execute: subprocess.run(["fly", "deploy"])
        return {
            "success": True, 
            "message": "Fly.io config generated. Run 'fly launch' to deploy.",
            "config": str(project_path / "fly.toml")
        }

    def _check_flyctl(self) -> bool:
        """Check if flyctl is installed."""
        try:
            subprocess.run(["fly", "version"], capture_output=True)
            return True
        except FileNotFoundError:
            return False

    def _generate_fly_toml(self, project_path: Path):
        """Generate fly.toml configuration."""
        app_name = project_path.name.lower().replace("_", "-")
        config = f"""
app = "{app_name}"
primary_region = "iad"

[build]
  builder = "paketobuildpacks/builder:base"

[http_service]
  internal_port = 8080
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 0
  processes = ["app"]
"""
        (project_path / "fly.toml").write_text(config)