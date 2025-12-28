"""
PostgreSQL database generator for Agent 50.
"""

import logging
from pathlib import Path
from typing import Dict, Any

class PostgresGenerator:
    """Generates PostgreSQL configuration."""
    
    def __init__(self):
        self.logger = logging.getLogger("Agent50.Builder.Postgres")
    
    def generate(self, blueprint: Dict[str, Any], output_path: Path):
        """Generate PostgreSQL configuration."""
        self.logger.info("Configuring PostgreSQL database...")
        
        # Generate docker-compose for local development
        self._generate_docker_compose(blueprint, output_path)
        
        self.logger.info("PostgreSQL configuration complete")

    def _generate_docker_compose(self, blueprint: Dict[str, Any], output_path: Path):
        """Generate docker-compose.yml for local DB."""
        project_name = blueprint.get("name", "app").lower().replace(" ", "_")
        
        compose_content = f"""version: '3.8'

services:
  db:
    image: postgres:15-alpine
    container_name: {project_name}_db
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
      POSTGRES_DB: {project_name}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
"""
        (output_path / "docker-compose.yml").write_text(compose_content)