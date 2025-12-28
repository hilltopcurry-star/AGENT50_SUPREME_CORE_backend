"""
MongoDB database generator for Agent 50.
"""

import logging
from pathlib import Path
from typing import Dict, Any

class MongoGenerator:
    """Generates MongoDB configuration."""
    
    def __init__(self):
        self.logger = logging.getLogger("Agent50.Builder.Mongo")
    
    def generate(self, blueprint: Dict[str, Any], output_path: Path):
        """Generate MongoDB configuration."""
        self.logger.info("Configuring MongoDB database...")
        
        # Generate docker-compose for local development
        self._generate_docker_compose(blueprint, output_path)
        
        self.logger.info("MongoDB configuration complete")

    def _generate_docker_compose(self, blueprint: Dict[str, Any], output_path: Path):
        """Generate docker-compose.yml for local MongoDB."""
        project_name = blueprint.get("name", "app").lower().replace(" ", "_")
        
        compose_content = f"""version: '3.8'

services:
  mongo:
    image: mongo:6.0
    container_name: {project_name}_mongo
    environment:
      MONGO_INITDB_ROOT_USERNAME: user
      MONGO_INITDB_ROOT_PASSWORD: password
    ports:
      - "27017:27017"
    volumes:
      - mongo_data:/data/db

volumes:
  mongo_data:
"""
        (output_path / "docker-compose.yml").write_text(compose_content)