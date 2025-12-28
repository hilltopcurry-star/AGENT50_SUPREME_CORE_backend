"""
project_planner.py - SUPREME ARCHITECT ENGINE (FINAL FIXED VERSION)
Identity: Full-Stack AI Architect.
Powered by: Google Gemini 2.0 Flash.
"""

from typing import Dict, Any
import uuid
import time
import os
import json
import logging
import google.generativeai as genai
from agent50_core.memory.memory_manager import MemoryManager

class ProjectPlanner:
    def __init__(self, memory_manager: MemoryManager):
        self.memory = memory_manager
        self.logger = logging.getLogger("Agent50.Planner")
        
        # Configure Gemini
        api_key = os.environ.get("GEMINI_API_KEY", "dummy")
        if api_key != "dummy":
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash')
        else:
            self.model = None

    def create_blueprint(self, description: str, project_type: str = "web_app") -> Dict[str, Any]:
        self.logger.info(f"🧠 Architect analyzing request: {description}")
        project_id = f"proj_{int(time.time())}_{uuid.uuid4().hex[:6]}"
        
        # 1. Ask Gemini Architect for the File Structure
        architecture = self._consult_ai_architect(description, project_type)
        
        # 2. Create the Standardized Blueprint Object
        blueprint = {
            "id": project_id,
            "name": f"Project_{project_id}",
            "type": project_type,
            "description": description,
            "created_at": time.time(),
            "status": "blueprint_ready",
            "stack": architecture.get("stack", "Python/Standard"),
            "architecture": {
                "files": architecture.get("files", [])
            }
        }
        
        # 3. Save to Memory
        if hasattr(self.memory, 'save_project_structure'):
            self.memory.save_project_structure(project_id, blueprint)
            
        return blueprint

    def _consult_ai_architect(self, description: str, p_type: str) -> Dict[str, Any]:
        """Forces Gemini to return correct folder structures."""
        if not self.model:
            return {"files": ["main.py"], "stack": "Fallback"}

        try:
            prompt = f"""
            ACT AS: Chief Software Architect (Agent 50 Supreme).
            GOAL: Create a PRODUCTION-READY file structure.
            
            USER REQUEST: "{description}"
            PROJECT TYPE: {p_type}
            
            CRITICAL RULES (DO NOT IGNORE):
            1. If type is 'web_app' (Flask/Django): 
               - You MUST put HTML files inside a 'templates/' folder (e.g., 'templates/index.html').
               - You MUST put CSS/JS inside a 'static/' folder.
            2. If type is 'python':
               - Keep files organized.
            3. RETURN JSON ONLY. NO MARKDOWN.
            
            OUTPUT FORMAT EXAMPLE:
            {{
                "stack": "Flask + SQLite",
                "files": [
                    "app.py", 
                    "requirements.txt", 
                    "templates/index.html", 
                    "templates/login.html",
                    "static/style.css"
                ]
            }}
            """
            
            response = self.model.generate_content(prompt)
            text = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(text)
            
        except Exception as e:
            self.logger.error(f"❌ Architect Error: {e}")
            # Fallback that forces structure if AI fails
            if p_type == "web_app":
                return {
                    "stack": "Flask Fallback", 
                    "files": ["main.py", "templates/index.html", "requirements.txt"]
                }
            return {"files": ["main.py"], "stack": "Error_Fallback"}