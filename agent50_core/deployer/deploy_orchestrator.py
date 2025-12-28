"""
Deploy Orchestrator for Agent 50.
Manages the deployment process across different platforms.
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional
from memory.memory_manager import MemoryManager
from deployer.render_adapter import RenderAdapter
from deployer.railway_adapter import RailwayAdapter
from deployer.flyio_adapter import FlyIOAdapter
from deployer.docker_adapter import DockerAdapter
from deployer.self_fix_engine import SelfFixEngine

class DeployOrchestrator:
    """Orchestrates deployments."""
    
    def __init__(self, memory: MemoryManager):
        self.memory = memory
        self.logger = logging.getLogger("Agent50.Deployer.Orchestrator")
        self.adapters = {
            "render": RenderAdapter(memory),
            "railway": RailwayAdapter(memory),
            "flyio": FlyIOAdapter(memory),
            "docker": DockerAdapter(memory)
        }
        self.fix_engine = SelfFixEngine(memory)
        
    def deploy(self, project_path: Path, platform: str = "render", environment: str = "production", force: bool = False) -> Dict[str, Any]:
        """
        Main entry point for deployment.
        """
        self.logger.info(f"Orchestrating deployment to {platform} for {project_path}")
        
        adapter = self.adapters.get(platform)
        if not adapter:
            return {"success": False, "error": f"Unsupported platform: {platform}"}
            
        # Attempt deployment
        result = adapter.deploy(project_path, environment)
        
        if result.get("success"):
            self.logger.info(f"Deployment Successful: {result.get('message')}")
            return result
        
        # If failed, try self-healing
        if not force:
            self.logger.warning(f"Deployment failed. Initiating Self-Repair...")
            logs = result.get("error", "")
            
            fixed, fix_msg, fix_data = self.fix_engine.auto_fix(project_path, logs, log_type="deployment")
            
            if fixed:
                self.logger.info(f"Repairs applied: {fix_msg}. Retrying deployment...")
                # Retry deployment once
                result = adapter.deploy(project_path, environment)
                if result.get("success"):
                    self.logger.info(f"Deployment Successful after repairs: {result.get('message')}")
                    return result
                
        self.logger.error("Deployment failed even after self-repair attempts.")
        return result