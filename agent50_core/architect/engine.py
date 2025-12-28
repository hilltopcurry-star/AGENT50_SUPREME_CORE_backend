"""
Architect Engine for Agent 50.
Converts user intent into detailed JSON blueprints.
"""

import json
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
import google.generativeai as genai

from config import get_config
from memory.memory_manager import MemoryManager

class ArchitectEngine:
    """Architect Engine - Converts user intent to architectural blueprints."""
    
    def __init__(self, memory: MemoryManager):
        """Initialize architect engine with memory and Gemini API."""
        self.memory = memory
        self.logger = logging.getLogger("Agent50.Architect")
        self.config = get_config()
        
        # Initialize Gemini API
        genai.configure(api_key=self.config.api.gemini_api_key)
        self.model = genai.GenerativeModel('gemini-pro')
        
        # Load archetypes
        self.archetypes = self._load_archetypes()
        
        self.logger.info("Architect Engine initialized")
    
    def _load_archetypes(self) -> Dict[str, Any]:
        """Load all archetype definitions from JSON files."""
        archetypes = {}
        archetype_dir = Path(__file__).parent / "archetypes"
        
        if not archetype_dir.exists():
            self.logger.error(f"Archetypes directory not found: {archetype_dir}")
            return {}
        
        for archetype_file in archetype_dir.glob("*.json"):
            try:
                with open(archetype_file, 'r') as f:
                    archetype_name = archetype_file.stem
                    archetypes[archetype_name] = json.load(f)
                self.logger.debug(f"Loaded archetype: {archetype_name}")
            except (json.JSONDecodeError, FileNotFoundError) as e:
                self.logger.error(f"Failed to load archetype {archetype_file}: {e}")
        
        return archetypes
    
    def create_blueprint(self, user_intent: str, project_name: str) -> Dict[str, Any]:
        """
        Create architectural blueprint from user intent.
        
        Args:
            user_intent: User's description of the app they want
            project_name: Name of the project
            
        Returns:
            Detailed architectural blueprint
        """
        self.logger.info(f"Creating blueprint for project: {project_name}")
        
        # Update project status
        self.memory.update_project_status({
            "system": "ready",
            "architecture": 25,
            "backend": 0,
            "frontend": 0,
            "deployment": 0,
            "message": "Analyzing user intent..."
        })
        
        try:
            # Step 1: Determine app type
            app_type = self._determine_app_type(user_intent)
            
            # Step 2: Select archetype
            archetype = self._select_archetype(app_type, user_intent)
            
            # Step 3: Generate detailed blueprint using Gemini
            blueprint = self._generate_detailed_blueprint(
                app_type=app_type,
                archetype=archetype,
                user_intent=user_intent,
                project_name=project_name
            )
            
            # Step 4: Validate blueprint
            self._validate_blueprint(blueprint)
            
            # Step 5: Record pattern for learning
            self._record_pattern(blueprint)
            
            # Update project status
            self.memory.update_project_status({
                "system": "ready",
                "architecture": 100,
                "backend": 0,
                "frontend": 0,
                "deployment": 0,
                "message": "Architecture blueprint complete",
                "blueprint": blueprint.get("name", "unnamed")
            })
            
            self.logger.info(f"Blueprint created successfully: {blueprint.get('name', 'unnamed')}")
            return blueprint
            
        except Exception as e:
            self.logger.error(f"Failed to create blueprint: {e}")
            # Update project status with error
            self.memory.update_project_status({
                "system": "error",
                "architecture": 0,
                "backend": 0,
                "frontend": 0,
                "deployment": 0,
                "message": f"Architecture failed: {str(e)[:100]}",
                "error": str(e)
            })
            raise
    
    def _determine_app_type(self, user_intent: str) -> str:
        """Determine the type of application from user intent."""
        intent_lower = user_intent.lower()
        
        # Check for app type keywords
        app_types = {
            "saas": ["subscription", "monthly", "saas", "software as a service", "recurring"],
            "ecommerce": ["shop", "store", "cart", "checkout", "product", "ecommerce", "e-commerce"],
            "ai_app": ["ai", "artificial intelligence", "machine learning", "model", "predict", "llm"],
            "dashboard": ["dashboard", "analytics", "metrics", "charts", "graphs", "monitor"],
            "mobile_backend": ["mobile", "app", "ios", "android", "api", "backend"]
        }
        
        # Find matching app type
        for app_type, keywords in app_types.items():
            if any(keyword in intent_lower for keyword in keywords):
                self.logger.info(f"Determined app type: {app_type}")
                return app_type
        
        # Default to SaaS if no clear match
        self.logger.info("No clear app type match, defaulting to SaaS")
        return "saas"
    
    def _select_archetype(self, app_type: str, user_intent: str) -> Dict[str, Any]:
        """Select the most appropriate archetype for the app type."""
        # Get existing patterns from memory
        existing_patterns = self.memory.get_architecture_patterns(app_type)
        
        if existing_patterns:
            # Sort by success rate and usage count
            existing_patterns.sort(key=lambda x: (
                x.get("success_rate", 0),
                x.get("used_count", 0)
            ), reverse=True)
            
            # Use the most successful pattern
            selected_pattern = existing_patterns[0]
            self.logger.info(f"Selected existing pattern: {selected_pattern.get('name')}")
            return selected_pattern
        
        # If no existing patterns, use archetype from file
        if app_type in self.archetypes:
            self.logger.info(f"Using archetype from file: {app_type}")
            return self.archetypes[app_type]
        
        # Fallback to default archetype
        self.logger.warning(f"No archetype found for {app_type}, using default")
        return self.archetypes.get("saas", {})
    
    def _generate_detailed_blueprint(self, app_type: str, archetype: Dict[str, Any], 
                                   user_intent: str, project_name: str) -> Dict[str, Any]:
        """Generate detailed blueprint using Gemini AI."""
        self.logger.info("Generating detailed blueprint with Gemini...")
        
        # Update project status
        self.memory.update_project_status({
            "system": "ready",
            "architecture": 50,
            "backend": 0,
            "frontend": 0,
            "deployment": 0,
            "message": "Generating detailed architecture..."
        })
        
        # Create prompt for Gemini
        prompt = f"""
        You are an expert software architect. Create a detailed architectural blueprint.
        
        PROJECT DETAILS:
        - Project Name: {project_name}
        - User Intent: {user_intent}
        - App Type: {app_type}
        
        BASE ARCHETYPE (use as reference, but adapt to user needs):
        {json.dumps(archetype, indent=2)}
        
        Create a detailed blueprint with these sections:
        1. Overview (name, description, type)
        2. Architecture (frontend, backend, database choices with reasoning)
        3. Components (list of modules/pages with descriptions)
        4. Dependencies (specific packages with versions)
        5. API Endpoints (if applicable)
        6. Database Schema (if applicable)
        7. Deployment Configuration
        8. Environment Variables needed
        
        IMPORTANT: Be specific about technology choices. For example:
        - If frontend is React, specify if using TypeScript, routing library, state management
        - If backend is FastAPI, specify if using SQLAlchemy, Pydantic models
        - Include specific package names and versions
        
        Return ONLY valid JSON matching this structure:
        {{
            "name": "string",
            "description": "string",
            "type": "string",
            "architecture": {{
                "frontend": {{"framework": "string", "language": "string", "additional": "string"}},
                "backend": {{"framework": "string", "language": "string", "additional": "string"}},
                "database": {{"type": "string", "orm": "string", "additional": "string"}}
            }},
            "components": ["list", "of", "components"],
            "dependencies": {{
                "backend": [{{"name": "string", "version": "string"}}],
                "frontend": [{{"name": "string", "version": "string"}}],
                "database": [{{"name": "string", "version": "string"}}]
            }},
            "api_endpoints": ["list", "of", "endpoints"],
            "database_schema": {{"tables": []}},
            "deployment": {{"platform": "render", "requirements": ["requirements.txt", "Procfile"]}},
            "env_variables": {{"required": [], "optional": []}}
        }}
        """
        
        try:
            # Call Gemini API
            response = self.model.generate_content(prompt)
            blueprint_text = response.text
            
            # Clean the response (remove markdown code blocks if present)
            if "```json" in blueprint_text:
                blueprint_text = blueprint_text.split("```json")[1].split("```")[0].strip()
            elif "```" in blueprint_text:
                blueprint_text = blueprint_text.split("```")[1].split("```")[0].strip()
            
            # Parse JSON
            blueprint = json.loads(blueprint_text)
            
            # Add metadata
            blueprint["project_name"] = project_name
            blueprint["user_intent"] = user_intent
            blueprint["app_type"] = app_type
            blueprint["generated_at"] = self._get_timestamp()
            
            self.logger.info("Blueprint generated successfully")
            return blueprint
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse Gemini response: {e}")
            self.logger.debug(f"Response text: {blueprint_text[:500]}...")
            raise ValueError(f"Invalid blueprint JSON from Gemini: {e}")
        except Exception as e:
            self.logger.error(f"Gemini API error: {e}")
            # Fallback to archetype with minimal customization
            return self._create_fallback_blueprint(app_type, archetype, project_name, user_intent)
    
    def _create_fallback_blueprint(self, app_type: str, archetype: Dict[str, Any], 
                                 project_name: str, user_intent: str) -> Dict[str, Any]:
        """Create a fallback blueprint when Gemini fails."""
        self.logger.warning("Creating fallback blueprint")
        
        blueprint = {
            "name": f"{project_name.replace('_', ' ').title()}",
            "description": f"An application based on: {user_intent[:100]}...",
            "type": app_type,
            "project_name": project_name,
            "user_intent": user_intent,
            "app_type": app_type,
            "generated_at": self._get_timestamp(),
            "architecture": archetype.get("components", {}),
            "components": [],
            "dependencies": archetype.get("dependencies", {}),
            "api_endpoints": [],
            "database_schema": {},
            "deployment": archetype.get("deployment", {}),
            "env_variables": {"required": [], "optional": []}
        }
        
        return blueprint
    
    def _validate_blueprint(self, blueprint: Dict[str, Any]):
        """Validate the generated blueprint."""
        required_fields = ["name", "type", "architecture", "dependencies", "deployment"]
        
        for field in required_fields:
            if field not in blueprint:
                raise ValueError(f"Blueprint missing required field: {field}")
        
        # Validate architecture choices
        arch = blueprint["architecture"]
        if "frontend" not in arch or "backend" not in arch or "database" not in arch:
            raise ValueError("Blueprint architecture missing required sections")
        
        self.logger.info("Blueprint validation passed")
    
    def _record_pattern(self, blueprint: Dict[str, Any]):
        """Record the blueprint as a pattern for future learning."""
        pattern = {
            "name": f"pattern_{blueprint['name'].lower().replace(' ', '_')}",
            "app_type": blueprint.get("app_type", "unknown"),
            "description": blueprint.get("description", ""),
            "components": blueprint.get("architecture", {}),
            "dependencies": blueprint.get("dependencies", {}),
            "deployment": blueprint.get("deployment", {}),
            "used_count": 1,
            "success_rate": 0.0,  # Will be updated after deployment
            "added_at": self._get_timestamp()
        }
        
        self.memory.add_architecture_pattern(pattern)
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_archetype_names(self) -> List[str]:
        """Get list of available archetype names."""
        return list(self.archetypes.keys())
    
    def get_recommended_stack(self, app_type: str) -> Dict[str, Any]:
        """Get recommended technology stack for an app type."""
        if app_type in self.archetypes:
            return {
                "frontend": self.archetypes[app_type].get("components", {}).get("frontend", "react"),
                "backend": self.archetypes[app_type].get("components", {}).get("backend", "fastapi"),
                "database": self.archetypes[app_type].get("components", {}).get("database", "postgres")
            }
        
        # Default recommendations
        return {
            "frontend": "react",
            "backend": "fastapi",
            "database": "postgres"
        }