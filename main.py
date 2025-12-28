#!/usr/bin/env python3
"""
Agent 50 - Universal Full-Stack AI Architect + Builder + Deployer
Main Entry Point

Bootstrap order: memory  architect  builder  validators  deployer  console
Synchronous deterministic flow only.
"""

import os
import sys
import logging
from pathlib import Path

# Add current directory to path for module imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config
from memory.memory_manager import MemoryManager
from architect.engine import ArchitectEngine
from builder.file_generator import FileGenerator
from validators.architecture_check import ArchitectureValidator
from validators.security_check import SecurityValidator
from validators.deploy_readiness import DeployReadinessValidator
from deployer.deploy_validator import DeployValidator
from deployer.render_adapter import RenderAdapter
from console.server import ConsoleServer

class Agent50:
    """Main orchestrator for Agent 50 system."""
    
    def __init__(self):
        """Initialize Agent 50 with configuration and components."""
        self.config = Config()
        self.logger = self._setup_logging()
        self.memory = None
        self.architect = None
        self.builder = None
        self.validators = []
        self.deployer = None
        self.console = None
        
        self.current_project = None
        self.project_blueprint = None
        
    def _setup_logging(self):
        """Configure logging for Agent 50."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('agent50.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        return logging.getLogger('Agent50')
    
    def bootstrap(self):
        """Bootstrap the entire Agent 50 system in strict order."""
        self.logger.info("?? Starting Agent 50 Universal AI System")
        
        try:
            # 1. Initialize Memory
            self.logger.info("?? Initializing Memory System...")
            self.memory = MemoryManager()
            self.memory.initialize()
            
            # 2. Initialize Architect Engine
            self.logger.info("??? Initializing Architect Engine...")
            self.architect = ArchitectEngine(self.memory)
            
            # 3. Initialize Builder
            self.logger.info("?? Initializing Builder...")
            self.builder = FileGenerator(self.memory)
            
            # 4. Initialize Validators
            self.logger.info("?? Initializing Validators...")
            self.validators = [
                ArchitectureValidator(),
                SecurityValidator(),
                DeployReadinessValidator()
            ]
            
            # 5. Initialize Deployer
            self.logger.info("?? Initializing Deployer...")
            self.deployer = RenderAdapter(self.memory)
            
            # 6. Initialize Console Server
            self.logger.info("?? Initializing Console Server...")
            self.console = ConsoleServer(
                memory=self.memory,
                architect=self.architect,
                builder=self.builder,
                validators=self.validators,
                deployer=self.deployer
            )
            
            self.logger.info("? Agent 50 Bootstrap Complete")
            return True
            
        except Exception as e:
            self.logger.error(f"? Bootstrap Failed: {str(e)}")
            raise
    
    def create_project_directory(self, project_name: str) -> Path:
        """Create project directory in ./projects/{project_name}/"""
        projects_root = Path("./projects")
        projects_root.mkdir(exist_ok=True)
        
        project_path = projects_root / project_name
        
        if project_path.exists():
            self.logger.warning(f"?? Project directory already exists: {project_path}")
            # In production, we would handle this differently
            # For now, we'll allow overwrite with warning
            
        project_path.mkdir(exist_ok=True)
        self.current_project = project_path
        return project_path
    
    def run(self):
        """Main execution loop - starts the console server."""
        try:
            # Bootstrap all components
            self.bootstrap()
            
            # Update project status to show system is ready
            self.memory.update_project_status({
                "system": "ready",
                "architecture": 0,
                "backend": 0,
                "frontend": 0,
                "deployment": 0
            })
            
            # Start console server (blocking)
            self.logger.info("?? Starting Agent 50 Console Server...")
            self.console.run()
            
        except KeyboardInterrupt:
            self.logger.info("?? Agent 50 shutting down...")
        except Exception as e:
            self.logger.error(f"?? Fatal Error: {str(e)}")
            sys.exit(1)

def main():
    """Entry point for Agent 50."""
    agent = Agent50()
    agent.run()

if __name__ == "__main__":
    main()